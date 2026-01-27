from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
import secrets
import string

from .. import schemas
from ..deps import get_store
from ..db_store import DatabaseStore
from ..websocket_manager import websocket_manager
from ..models import TrackingCode

router = APIRouter(prefix="/passenger", tags=["passenger"])


def _fake_schedule(bus_number: str) -> list:
    """
    Placeholder schedule for demonstration when no database stops are available.
    In production, this should not be used - all buses should have routes configured.
    """
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    stops = []
    for idx, name in enumerate(["Stop A", "Stop B", "Stop C", "Stop D"]):
        stops.append({
            "name": name,
            "scheduled": base + timedelta(minutes=idx * 15),
            "latitude": None,
            "longitude": None,
            "scheduled_arrival_minutes": idx * 15
        })
    return stops


def calculate_bus_status(store: DatabaseStore, bus_number: str, last_location_time: datetime | None) -> str:
    """
    Calculate bus status: not_started, in_transit, completed, or offline
    
    Returns:
        str: Bus status
    """
    from ..models import Bus
    
    bus = store.db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus or not bus.start_time:
        return "not_started"
    
    # Check if bus has started (current time >= start_time today)
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_hour = bus.start_time.hour
    start_minute = bus.start_time.minute
    today_start = today.replace(hour=start_hour, minute=start_minute)
    
    if now < today_start:
        return "not_started"
    
    # Check if bus is offline (no location updates in last 5 minutes)
    if last_location_time:
        if isinstance(last_location_time, datetime):
            if last_location_time.tzinfo is None:
                last_location_time = last_location_time.replace(tzinfo=timezone.utc)
        elif isinstance(last_location_time, str):
            try:
                last_location_time = datetime.fromisoformat(last_location_time.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                return "offline"
        
        last_seen_seconds = int((now - last_location_time).total_seconds())
        if last_seen_seconds > 300:  # 5 minutes
            return "offline"
    
    # Check if route is completed (reached final stop)
    stops = store.get_stops_for_bus(bus_number)
    delay_info = store.get_delay(bus_number)
    current_stop = delay_info.get("current_stop")
    
    if stops and len(stops) > 0:
        final_stop = stops[-1].get("name")
        if current_stop and final_stop and current_stop == final_stop:
            return "completed"
    
    return "in_transit"


@router.get("/bus/{bus_number}", response_model=schemas.LastLocation)
def passenger_bus_status(bus_number: str, store: DatabaseStore = Depends(get_store)):
    """Get current bus status and location"""
    last = store.get_last_location(bus_number)
    if not last:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bus not found or no location data available"
        )
    
    delay_info = store.get_delay(bus_number)
    recorded_at = last.get("recorded_at")
    
    # Parse and normalize datetime
    if isinstance(recorded_at, datetime):
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)
    elif isinstance(recorded_at, str):
        try:
            recorded_at = datetime.fromisoformat(recorded_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            recorded_at = datetime.now(timezone.utc)
    else:
        recorded_at = datetime.now(timezone.utc)
    
    now = datetime.now(timezone.utc)
    last_seen_seconds = max(0, int((now - recorded_at).total_seconds()))
    
    # Calculate bus status
    bus_status = calculate_bus_status(store, bus_number, recorded_at)
    status_label = "online" if last_seen_seconds < 120 else "stale"
    if bus_status == "not_started":
        status_label = "not_started"
    elif bus_status == "completed":
        status_label = "completed"
    elif bus_status == "offline":
        status_label = "offline"
    
    return schemas.LastLocation(
        latitude=last.get("latitude", 0.0),
        longitude=last.get("longitude", 0.0),
        recorded_at=recorded_at,
        last_seen_seconds=last_seen_seconds,
        running_delay_minutes=delay_info.get("delay_minutes", 0),
        status=status_label,
        current_stop=delay_info.get("current_stop"),
        next_stop=delay_info.get("next_stop"),
    )


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two GPS coordinates in kilometers using Haversine formula"""
    import math
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def calculate_eta_from_scheduled_times(current_lat: float, current_lon: float, stops: list, current_time: datetime, target_stop_idx: int):
    """
    Calculate ETA for a target stop using scheduled times and current GPS position.
    This is more accurate than using fixed speed because it uses actual route timing.
    
    Approach:
    1. Calculate cumulative distances between consecutive stops
    2. Find which segment (between two stops) the bus is currently in
    3. Interpolate bus position within that segment
    4. Use scheduled_arrival_minutes to calculate time differences between stops
    5. Interpolate current time position based on bus position
    6. Calculate remaining time to target stop
    
    Returns:
        Tuple[datetime, int]: (ETA, delay_minutes) or (None, None) if calculation fails
    """
    # Validate inputs
    if not stops or target_stop_idx < 0 or target_stop_idx >= len(stops):
        return None, None
    
    if current_lat is None or current_lon is None:
        return None, None
    
    target_stop = stops[target_stop_idx]
    if not target_stop.get("latitude") or not target_stop.get("longitude"):
        return None, None
    
    # Calculate cumulative distances from start for all stops
    route_distances = [0.0]
    for i in range(1, len(stops)):
        prev = stops[i-1]
        curr = stops[i]
        if (prev.get("latitude") and prev.get("longitude") and 
            curr.get("latitude") and curr.get("longitude")):
            dist = haversine_distance(
                prev["latitude"], prev["longitude"],
                curr["latitude"], curr["longitude"]
            )
            route_distances.append(route_distances[-1] + dist)
        else:
            # Missing coordinates - use estimated distance
            route_distances.append(route_distances[-1] + 1.0)
    
    # Find which segment the bus is in and calculate position along route
    min_dist_to_route = float('inf')
    bus_distance_from_start = 0.0
    current_segment_idx = 0
    
    for i in range(len(stops) - 1):
        stop_a = stops[i]
        stop_b = stops[i + 1]
        
        if not (stop_a.get("latitude") and stop_b.get("latitude")):
            continue
        
        # Calculate distances from bus to both stops in this segment
        dist_a = haversine_distance(
            current_lat, current_lon,
            stop_a["latitude"], stop_a["longitude"]
        )
        dist_b = haversine_distance(
            current_lat, current_lon,
            stop_b["latitude"], stop_b["longitude"]
        )
        segment_dist = route_distances[i+1] - route_distances[i]
        
        # Interpolate bus position along segment based on distance ratio
        if segment_dist > 0.001:  # Avoid division by zero
            total_dist = dist_a + dist_b
            if total_dist > 0.001:
                # Progress: closer to A = less progress, closer to B = more progress
                progress_in_segment = dist_a / total_dist
                progress_in_segment = max(0.0, min(1.0, progress_in_segment))
                bus_dist_approx = route_distances[i] + (segment_dist * progress_in_segment)
            else:
                # Bus is exactly at one of the stops
                bus_dist_approx = route_distances[i] if dist_a < dist_b else route_distances[i+1]
        else:
            # Zero-length segment
            bus_dist_approx = route_distances[i]
        
        # Track closest segment
        min_dist_to_segment = min(dist_a, dist_b)
        if min_dist_to_segment < min_dist_to_route:
            min_dist_to_route = min_dist_to_segment
            bus_distance_from_start = bus_dist_approx
            current_segment_idx = i
    
    # If bus is past target stop, ETA is immediate
    if bus_distance_from_start >= route_distances[target_stop_idx]:
        return current_time, 0
    
    # Get scheduled_arrival_minutes for all stops
    scheduled_minutes = []
    for stop in stops:
        minutes = stop.get("scheduled_arrival_minutes")
        if minutes is not None:
            scheduled_minutes.append(minutes)
        elif scheduled_minutes:
            # Estimate: add 10 minutes from previous stop
            scheduled_minutes.append(scheduled_minutes[-1] + 10)
        else:
            scheduled_minutes.append(0)
    
    if len(scheduled_minutes) < 2:
        return None, None
    
    # Calculate current time position (minutes from start) by interpolating within segment
    if current_segment_idx < len(scheduled_minutes) - 1:
        segment_start_minutes = scheduled_minutes[current_segment_idx]
        segment_end_minutes = scheduled_minutes[current_segment_idx + 1]
        segment_distance = route_distances[current_segment_idx + 1] - route_distances[current_segment_idx]
        
        if segment_distance > 0.001:
            progress = (bus_distance_from_start - route_distances[current_segment_idx]) / segment_distance
            progress = max(0.0, min(1.0, progress))
            current_minutes_from_start = segment_start_minutes + (segment_end_minutes - segment_start_minutes) * progress
        else:
            current_minutes_from_start = segment_start_minutes
    else:
        # Bus is at or past last stop
        current_minutes_from_start = scheduled_minutes[-1]
    
    # Calculate remaining time to target stop
    target_minutes_from_start = scheduled_minutes[target_stop_idx]
    remaining_minutes = max(0, target_minutes_from_start - current_minutes_from_start)
    
    # Calculate ETA
    eta = current_time + timedelta(minutes=remaining_minutes)
    
    # Calculate delay (ETA vs scheduled time)
    target_scheduled = target_stop.get("scheduled")
    if target_scheduled:
        if isinstance(target_scheduled, str):
            target_scheduled = datetime.fromisoformat(target_scheduled.replace('Z', '+00:00'))
        if isinstance(target_scheduled, datetime):
            if target_scheduled.tzinfo is None:
                target_scheduled = target_scheduled.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            delay_minutes = int((eta - target_scheduled).total_seconds() / 60)
        else:
            delay_minutes = 0
    else:
        delay_minutes = 0
    
    return eta, delay_minutes


@router.get("/bus/{bus_number}/stops", response_model=schemas.StopEtaResponse)
def passenger_stop_etas(bus_number: str, store: DatabaseStore = Depends(get_store)):
    """Get ETA for all stops using scheduled times and GPS position"""
    delay_info = store.get_delay(bus_number)
    base_delay = delay_info.get("delay_minutes", 0)
    
    # Get current bus location for accurate ETA calculation
    last_location = store.get_last_location(bus_number)
    current_lat = last_location.get("latitude") if last_location else None
    current_lon = last_location.get("longitude") if last_location else None
    
    # Get stops from database
    db_stops = store.get_stops_for_bus(bus_number)
    if not db_stops:
        # Fallback to fake schedule if no database stops
        schedule = _fake_schedule(bus_number)
    else:
        schedule = db_stops
    
    if not schedule or len(schedule) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No stops found for this bus")
    
    stops = []
    india_tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(india_tz)
    
    # Use scheduled times for accurate ETA calculation if GPS and scheduled times are available
    use_scheduled_calculation = (
        current_lat is not None and 
        current_lon is not None and 
        len(schedule) > 0 and
        all(stop.get("scheduled_arrival_minutes") is not None for stop in schedule)
    )
    
    for idx, entry in enumerate(schedule):
        # Parse scheduled time
        scheduled = entry.get("scheduled")
        if isinstance(scheduled, datetime):
            if scheduled.tzinfo is None:
                scheduled = scheduled.replace(tzinfo=india_tz)
        elif scheduled is None:
            # Calculate from start_time + scheduled_arrival_minutes if available
            if entry.get("scheduled_arrival_minutes") is not None:
                # This should already be calculated in get_stops_for_bus, but handle fallback
                scheduled = now.replace(minute=0, second=0, microsecond=0)
            else:
                scheduled = now.replace(minute=0, second=0, microsecond=0)
        else:
            scheduled = now.replace(minute=0, second=0, microsecond=0)
        
        # Calculate ETA using scheduled times and GPS position
        if use_scheduled_calculation and entry.get("latitude") and entry.get("longitude"):
            eta_result = calculate_eta_from_scheduled_times(
                current_lat, current_lon,
                schedule, now, idx
            )
            
            if eta_result and eta_result[0]:
                eta, calculated_delay = eta_result
                delay = calculated_delay
            else:
                # Fallback: use base delay
                eta = scheduled + timedelta(minutes=base_delay)
                delay = base_delay
        else:
            # Fallback: use delay-based calculation
            eta = scheduled + timedelta(minutes=base_delay)
            delay = base_delay
        
        # Determine status
        status_label = "on_time"
        if delay > 1:
            status_label = "delayed"
        elif delay < -1:
            status_label = "early"
        
        stops.append(
            schemas.StopEta(
                stop_name=entry.get("name", f"Stop {idx + 1}"),
                scheduled_time=scheduled,
                eta=eta,
                delay_minutes=delay,
                status=status_label,
                latitude=entry.get("latitude"),
                longitude=entry.get("longitude"),
            )
        )
    
    return schemas.StopEtaResponse(bus_number=bus_number, stops=stops)


@router.get("/track/{code}")
def resolve_tracking_code(code: str, store: DatabaseStore = Depends(get_store)):
    """
    Resolve a tracking code to a bus number.
    Used for short links: passenger/track/abc123 -> redirects to passenger page with bus number
    """
    tracking = store.db.query(TrackingCode).filter(
        TrackingCode.code == code,
        TrackingCode.is_active == True
    ).first()
    
    if not tracking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired tracking code"
        )
    
    # Update access stats
    tracking.access_count += 1
    tracking.last_accessed = datetime.now(timezone.utc)
    store.db.commit()
    
    return {"bus_number": tracking.bus_number, "code": code}


@router.websocket("/ws/bus/{bus_number}")
async def websocket_endpoint(websocket: WebSocket, bus_number: str):
    """WebSocket endpoint for real-time bus location updates"""
    await websocket_manager.connect(websocket, bus_number)
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            data = await websocket.receive_text()
            # Echo back or handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, bus_number)
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket, bus_number)

