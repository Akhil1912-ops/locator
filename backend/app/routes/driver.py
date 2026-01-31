from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
import logging
import math

from .. import schemas

logger = logging.getLogger(__name__)
from ..deps import get_bus_from_session, get_store
from ..db_store import DatabaseStore
from ..websocket_manager import websocket_manager
from ..models import Bus

router = APIRouter(prefix="/driver", tags=["driver"])


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS coordinates in kilometers"""
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def calculate_automatic_delay(store: DatabaseStore, bus_number: str, current_lat: float, current_lon: float, current_time: datetime):
    """Automatically calculate delay based on GPS position and scheduled times"""
    # Get bus start_time
    bus = store.db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus or not bus.start_time:
        return 0, None, None
    
    # Get route stops
    stops = store.get_stops_for_bus(bus_number)
    if not stops or len(stops) < 2:
        return 0, None, None
    
    # Find nearest stop
    min_distance = float('inf')
    nearest_stop_idx = 0
    for idx, stop in enumerate(stops):
        distance = haversine_distance(current_lat, current_lon, stop["latitude"], stop["longitude"])
        if distance < min_distance:
            min_distance = distance
            nearest_stop_idx = idx
    
    nearest_stop = stops[nearest_stop_idx]
    
    # Calculate scheduled arrival time for nearest stop
    # Use pre-calculated scheduled from get_stops_for_bus (already in India/Kolkata)
    if nearest_stop.get("scheduled"):
        scheduled_arrival = nearest_stop["scheduled"]
    elif nearest_stop.get("scheduled_arrival_minutes") is not None:
        from zoneinfo import ZoneInfo
        try:
            india_tz = ZoneInfo("Asia/Kolkata")
        except Exception:
            india_tz = timezone(timedelta(hours=5, minutes=30))
        start_dt = bus.start_time.replace(tzinfo=timezone.utc) if bus.start_time.tzinfo is None else bus.start_time
        start_ist = start_dt.astimezone(india_tz)
        today_ist = datetime.now(india_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        today_start = today_ist.replace(hour=start_ist.hour, minute=start_ist.minute)
        scheduled_arrival = today_start + timedelta(minutes=nearest_stop["scheduled_arrival_minutes"])
    else:
        return 0, None, None
    
    # Calculate delay (current time - scheduled time)
    if isinstance(scheduled_arrival, datetime):
        if scheduled_arrival.tzinfo is None:
            scheduled_arrival = scheduled_arrival.replace(tzinfo=timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        delay_seconds = (current_time - scheduled_arrival).total_seconds()
        delay_minutes = int(delay_seconds / 60)
    else:
        delay_minutes = 0
    
    # Determine current and next stop
    current_stop = nearest_stop["name"]
    next_stop = None
    if nearest_stop_idx < len(stops) - 1:
        next_stop = stops[nearest_stop_idx + 1]["name"]
    
    return delay_minutes, current_stop, next_stop


@router.post("/location", response_model=schemas.LastLocation)
async def update_location(
    payload: schemas.LocationUpdate,
    bus_number: str = Depends(get_bus_from_session),
    store: DatabaseStore = Depends(get_store),
):
    logger.info("Location received: bus=%s lat=%.6f lon=%.6f", bus_number, payload.latitude, payload.longitude)
    saved = store.save_location(bus_number, payload.latitude, payload.longitude, payload.recorded_at)
    
    # Automatically calculate delay based on GPS position
    current_time = payload.recorded_at
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    
    delay_minutes, current_stop, next_stop = calculate_automatic_delay(
        store, bus_number, payload.latitude, payload.longitude, current_time
    )
    
    # Save calculated delay
    if delay_minutes is not None:
        store.save_delay(bus_number, delay_minutes, current_stop, next_stop)
        
        # Broadcast delay update via WebSocket
        await websocket_manager.broadcast_delay(bus_number, {
            "delay_minutes": delay_minutes,
            "current_stop": current_stop,
            "next_stop": next_stop,
        })
    
    delay_info = store.get_delay(bus_number)
    
    # Broadcast location update via WebSocket
    await websocket_manager.broadcast_location(bus_number, {
        "latitude": saved["latitude"],
        "longitude": saved["longitude"],
        "recorded_at": saved["recorded_at"],
    })
    
    return schemas.LastLocation(
        latitude=saved["latitude"],
        longitude=saved["longitude"],
        recorded_at=saved["recorded_at"],
        last_seen_seconds=0,
        running_delay_minutes=delay_info.get("delay_minutes", 0),
        status="online",
        current_stop=delay_info.get("current_stop"),
        next_stop=delay_info.get("next_stop"),
    )


@router.post("/delay")
async def update_delay(
    delay_minutes: int,
    current_stop: str | None = None,
    next_stop: str | None = None,
    bus_number: str = Depends(get_bus_from_session),
    store: DatabaseStore = Depends(get_store),
):
    store.save_delay(bus_number, delay_minutes, current_stop, next_stop)
    
    # Broadcast delay update via WebSocket
    await websocket_manager.broadcast_delay(bus_number, {
        "delay_minutes": delay_minutes,
        "current_stop": current_stop,
        "next_stop": next_stop,
    })
    
    return {"ok": True, "delay_minutes": delay_minutes, "current_stop": current_stop, "next_stop": next_stop}

