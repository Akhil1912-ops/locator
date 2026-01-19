from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Header, Query, Request
from typing import List, Optional
from sqlalchemy.orm import Session
import secrets
import string

from .. import schemas
from ..deps import get_db
from ..db_store import DatabaseStore
from ..models import Bus, Route, Stop, DriverSession, Location, DelayInfo, TrackingCode
from ..config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

# Simple admin password (in production, use proper auth)
ADMIN_PASSWORD = "admin123"  # Change this!


def verify_admin_password(admin_password: str = Header(..., alias="X-Admin-Password")):
    """Verify admin password"""
    if admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin password")
    return True


# Bus Management
@router.get("/buses", response_model=List[dict])
def list_buses(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """List all buses"""
    buses = db.query(Bus).all()
    return [
        {
            "bus_number": bus.bus_number,
            "route_name": bus.route_name,
            "start_time": bus.start_time.replace(tzinfo=timezone.utc).isoformat() if bus.start_time else None,
            "is_active": bus.is_active,
            "created_at": bus.created_at.isoformat() if bus.created_at else None,
        }
        for bus in buses
    ]


@router.post("/buses", response_model=dict)
def create_bus(
    bus_number: str,
    password: str,
    route_name: Optional[str] = None,
    start_time: Optional[str] = None,  # ISO format datetime string
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Create a new bus"""
    import bcrypt
    
    # Check if bus already exists
    existing = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bus already exists")
    
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Parse start_time if provided
    start_time_dt = None
    if start_time:
        try:
            start_time_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid start_time format. Use ISO format.")
    
    bus = Bus(
        bus_number=bus_number,
        password_hash=password_hash,
        route_name=route_name,
        start_time=start_time_dt,
        is_active=True,
    )
    db.add(bus)
    db.commit()
    db.refresh(bus)
    
    return {
        "bus_number": bus.bus_number,
        "route_name": bus.route_name,
        "start_time": bus.start_time.isoformat() if bus.start_time else None,
        "is_active": bus.is_active,
    }


@router.put("/buses/{bus_number}")
def update_bus(
    bus_number: str,
    password: Optional[str] = Query(None),
    route_name: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),  # ISO format datetime string
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Update a bus"""
    import bcrypt
    
    print(f"DEBUG update_bus: Called with bus_number={bus_number}")
    print(f"DEBUG update_bus: Parameters received - password={password is not None}, route_name={route_name}, start_time={start_time}, is_active={is_active}")
    print(f"DEBUG update_bus: start_time type: {type(start_time)}, value: '{start_time}'")
    
    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")
    
    if password:
        bus.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    if route_name is not None:
        bus.route_name = route_name
        print(f"DEBUG: Updated route_name to: {route_name}")
    if start_time is not None:
        print(f"DEBUG update_bus: Received start_time='{start_time}' (type={type(start_time)})")
        if start_time == "":
            bus.start_time = None
            print(f"DEBUG: Setting start_time to None (empty string)")
        else:
            try:
                # Parse ISO format datetime string
                start_time_parsed = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                bus.start_time = start_time_parsed
                print(f"DEBUG: Parsed and set start_time to: {bus.start_time}")
            except ValueError as e:
                print(f"DEBUG: Error parsing start_time '{start_time}': {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid start_time format: {e}")
    else:
        print(f"DEBUG update_bus: start_time parameter is None, not updating")
    if is_active is not None:
        bus.is_active = is_active
    
    print(f"DEBUG: Before commit, bus.start_time = {bus.start_time}")
    db.commit()
    db.refresh(bus)
    print(f"DEBUG: After commit and refresh, bus.start_time = {bus.start_time}")
    
    response = {
        "bus_number": bus.bus_number,
        "route_name": bus.route_name,
        "start_time": bus.start_time.replace(tzinfo=timezone.utc).isoformat() if bus.start_time else None,
        "is_active": bus.is_active,
    }
    print(f"DEBUG: Returning response - start_time value: {response.get('start_time')}")
    print(f"DEBUG: Full response dict keys: {list(response.keys())}")
    return response


@router.delete("/buses/{bus_number}")
def delete_bus(
    bus_number: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Delete a bus"""
    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")
    
    db.delete(bus)
    db.commit()
    return {"ok": True, "message": f"Bus {bus_number} deleted"}


# Tracking Code Management - MUST be before /buses/{bus_number}/route to avoid route conflicts
@router.post("/buses/{bus_number}/tracking-code", response_model=dict)
def generate_tracking_code(
    bus_number: str,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Generate or get existing tracking code for a bus"""
    # Check if bus exists
    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")
    
    # Check if tracking code already exists
    existing = db.query(TrackingCode).filter(
        TrackingCode.bus_number == bus_number,
        TrackingCode.is_active == True
    ).first()
    
    # Determine frontend URL
    frontend_url = settings.frontend_url
    if not frontend_url:
        # Auto-detect from request
        referer = request.headers.get("referer", "")
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            frontend_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            # Fallback: use localhost for development
            frontend_url = "http://localhost:3001"
    
    if existing:
        return {
            "code": existing.code,
            "bus_number": bus_number,
            "tracking_url": f"{frontend_url}/passenger/index.html?code={existing.code}",
            "created_at": existing.created_at.isoformat() if existing.created_at else None,
        }
    
    # Generate new code (6 characters: alphanumeric, lowercase)
    code_length = 6
    while True:
        code = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(code_length))
        # Check if code already exists
        if not db.query(TrackingCode).filter(TrackingCode.code == code).first():
            break
    
    # Create tracking code
    tracking = TrackingCode(
        code=code,
        bus_number=bus_number,
        is_active=True
    )
    db.add(tracking)
    db.commit()
    db.refresh(tracking)
    
    return {
        "code": code,
        "bus_number": bus_number,
        "tracking_url": f"{frontend_url}/passenger/index.html?code={code}",
        "created_at": tracking.created_at.isoformat() if tracking.created_at else None,
    }


@router.get("/buses/{bus_number}/tracking-code", response_model=dict)
def get_tracking_code(
    bus_number: str,
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Get existing tracking code for a bus"""
    tracking = db.query(TrackingCode).filter(
        TrackingCode.bus_number == bus_number,
        TrackingCode.is_active == True
    ).first()
    
    if not tracking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No tracking code found for this bus")
    
    # Determine frontend URL
    frontend_url = settings.frontend_url
    if not frontend_url:
        # Auto-detect from request
        referer = request.headers.get("referer", "")
        if referer:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            frontend_url = f"{parsed.scheme}://{parsed.netloc}"
        else:
            # Fallback: use localhost for development
            frontend_url = "http://localhost:3001"
    
    return {
        "code": tracking.code,
        "bus_number": bus_number,
        "tracking_url": f"{frontend_url}/passenger/index.html?code={tracking.code}",
        "access_count": tracking.access_count,
        "last_accessed": tracking.last_accessed.isoformat() if tracking.last_accessed else None,
        "created_at": tracking.created_at.isoformat() if tracking.created_at else None,
    }


# Route & Stop Management
@router.get("/buses/{bus_number}/route")
def get_route(
    bus_number: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Get route and stops for a bus"""
    route = db.query(Route).filter(Route.bus_number == bus_number).first()
    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    
    if not route:
        return {"route": None, "stops": [], "start_time": bus.start_time.isoformat() if bus and bus.start_time else None}
    
    stops = db.query(Stop).filter(Stop.route_id == route.route_id).order_by(Stop.sequence_order).all()
    
    return {
        "route": {
            "route_id": route.route_id,
            "route_name": route.route_name,
            "bus_number": route.bus_number,
        },
        "start_time": bus.start_time.isoformat() if bus and bus.start_time else None,
        "stops": [
            {
                "stop_id": stop.stop_id,
                "stop_name": stop.stop_name,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "sequence_order": stop.sequence_order,
                "scheduled_arrival": stop.scheduled_arrival.isoformat() if stop.scheduled_arrival else None,
                "scheduled_departure": stop.scheduled_departure.isoformat() if stop.scheduled_departure else None,
                "scheduled_arrival_minutes": stop.scheduled_arrival_minutes,
                "scheduled_departure_minutes": stop.scheduled_departure_minutes,
            }
            for stop in stops
        ],
    }


@router.post("/buses/{bus_number}/route")
def create_or_update_route(
    bus_number: str,
    route_name: str,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Create or update route for a bus"""
    # Check bus exists
    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")
    
    route = db.query(Route).filter(Route.bus_number == bus_number).first()
    if route:
        route.route_name = route_name
    else:
        route = Route(bus_number=bus_number, route_name=route_name)
        db.add(route)
    
    db.commit()
    db.refresh(route)
    
    return {
        "route_id": route.route_id,
        "route_name": route.route_name,
        "bus_number": route.bus_number,
    }


@router.post("/buses/{bus_number}/stops")
def add_stop(
    bus_number: str,
    stop_name: str,
    latitude: float,
    longitude: float,
    sequence_order: int,
    scheduled_arrival: Optional[str] = None,  # Legacy datetime format
    scheduled_departure: Optional[str] = None,  # Legacy datetime format
    scheduled_arrival_minutes: Optional[int] = None,  # Minutes from start point
    scheduled_departure_minutes: Optional[int] = None,  # Minutes from start point
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Add a stop to a bus route"""
    route = db.query(Route).filter(Route.bus_number == bus_number).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found. Create route first.")
    
    # Parse scheduled times (legacy datetime format)
    arrival_dt = None
    departure_dt = None
    if scheduled_arrival:
        try:
            arrival_dt = datetime.fromisoformat(scheduled_arrival.replace("Z", "+00:00"))
        except:
            pass
    if scheduled_departure:
        try:
            departure_dt = datetime.fromisoformat(scheduled_departure.replace("Z", "+00:00"))
        except:
            pass
    
    stop = Stop(
        route_id=route.route_id,
        stop_name=stop_name,
        latitude=latitude,
        longitude=longitude,
        sequence_order=sequence_order,
        scheduled_arrival=arrival_dt,
        scheduled_departure=departure_dt,
        scheduled_arrival_minutes=scheduled_arrival_minutes,
        scheduled_departure_minutes=scheduled_departure_minutes,
    )
    db.add(stop)
    db.commit()
    db.refresh(stop)
    
    return {
        "stop_id": stop.stop_id,
        "stop_name": stop.stop_name,
        "latitude": stop.latitude,
        "longitude": stop.longitude,
        "sequence_order": stop.sequence_order,
    }


@router.put("/buses/{bus_number}/stops/{stop_id}")
def update_stop(
    bus_number: str,
    stop_id: int,
    stop_name: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    sequence_order: Optional[int] = None,
    scheduled_arrival: Optional[str] = None,  # Legacy datetime format
    scheduled_departure: Optional[str] = None,  # Legacy datetime format
    scheduled_arrival_minutes: Optional[int] = None,  # Minutes from start point
    scheduled_departure_minutes: Optional[int] = None,  # Minutes from start point
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Update a stop"""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found")
    
    if stop_name is not None:
        stop.stop_name = stop_name
    if latitude is not None:
        stop.latitude = latitude
    if longitude is not None:
        stop.longitude = longitude
    if sequence_order is not None:
        stop.sequence_order = sequence_order
    
    # Handle legacy datetime format
    if scheduled_arrival is not None:
        try:
            stop.scheduled_arrival = datetime.fromisoformat(scheduled_arrival.replace("Z", "+00:00"))
        except:
            pass
    if scheduled_departure is not None:
        try:
            stop.scheduled_departure = datetime.fromisoformat(scheduled_departure.replace("Z", "+00:00"))
        except:
            pass
    
    # Handle minutes format (preferred)
    if scheduled_arrival_minutes is not None:
        stop.scheduled_arrival_minutes = scheduled_arrival_minutes
    if scheduled_departure_minutes is not None:
        stop.scheduled_departure_minutes = scheduled_departure_minutes
    
    db.commit()
    db.refresh(stop)
    
    return {
        "stop_id": stop.stop_id,
        "stop_name": stop.stop_name,
        "latitude": stop.latitude,
        "longitude": stop.longitude,
        "sequence_order": stop.sequence_order,
    }


@router.delete("/buses/{bus_number}/stops/{stop_id}")
def delete_stop(
    bus_number: str,
    stop_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Delete a stop"""
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found")
    
    db.delete(stop)
    db.commit()
    return {"ok": True, "message": f"Stop {stop_id} deleted"}


# Active Drivers
@router.get("/active-drivers", response_model=List[dict])
def get_active_drivers(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Get all active driver sessions"""
    sessions = db.query(DriverSession).filter(
        DriverSession.is_active == True,
        DriverSession.expires_at > datetime.now(timezone.utc)
    ).all()
    
    result = []
    for session in sessions:
        # Get last location
        last_location = db.query(Location).filter(
            Location.bus_number == session.bus_number
        ).order_by(Location.recorded_at.desc()).first()
        
        result.append({
            "bus_number": session.bus_number,
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "last_location": {
                "latitude": last_location.latitude,
                "longitude": last_location.longitude,
                "recorded_at": last_location.recorded_at.isoformat() if last_location else None,
            } if last_location else None,
        })
    
    return result


# Statistics
@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Get system statistics including performance metrics"""
    try:
        total_buses = db.query(Bus).count()
        active_buses = db.query(Bus).filter(Bus.is_active == True).count()
        active_drivers = db.query(DriverSession).filter(
            DriverSession.is_active == True,
            DriverSession.expires_at > datetime.now(timezone.utc)
        ).count()
        total_locations = db.query(Location).count()
        
        # Calculate performance metrics
        delay_infos = db.query(DelayInfo).all()
        total_delays = [d.delay_minutes for d in delay_infos if d.delay_minutes is not None]
        avg_delay = sum(total_delays) / len(total_delays) if total_delays else 0
        
        # Count on-time buses (delay <= 2 minutes)
        on_time_count = sum(1 for d in total_delays if abs(d) <= 2)
        on_time_percentage = (on_time_count / len(total_delays) * 100) if total_delays else 0
        
        # Count buses with routes
        try:
            buses_with_routes = db.query(Bus).join(Route).distinct().count()
        except:
            buses_with_routes = 0
        
        # Count buses currently tracking (sent location in last 5 minutes)
        five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        tracking_buses = db.query(Location.bus_number).filter(
            Location.recorded_at >= five_min_ago
        ).distinct().count()
        
        return {
            "total_buses": total_buses,
            "active_buses": active_buses,
            "active_drivers": active_drivers,
            "total_locations": total_locations,
            "buses_with_routes": buses_with_routes,
            "tracking_buses": tracking_buses,
            "average_delay_minutes": round(avg_delay, 1),
            "on_time_percentage": round(on_time_percentage, 1),
            "on_time_count": on_time_count,
            "total_tracked_buses": len(total_delays),
        }
    except Exception as e:
        # Return basic stats even if some queries fail
        return {
            "total_buses": db.query(Bus).count() if db else 0,
            "active_buses": 0,
            "active_drivers": 0,
            "total_locations": 0,
            "buses_with_routes": 0,
            "tracking_buses": 0,
            "average_delay_minutes": 0,
            "on_time_percentage": 0,
            "on_time_count": 0,
            "total_tracked_buses": 0,
            "error": str(e),
        }

