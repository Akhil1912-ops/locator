from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Header, Query, Request, Body
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
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


class BusUpdateBody(BaseModel):
    """JSON body for bus update - avoids URL encoding issues with start_time"""
    password: Optional[str] = None
    route_name: Optional[str] = None
    start_time: Optional[str] = None  # ISO format, UTC (e.g. 2026-01-31T14:00:00.000Z for 19:30 IST)
    is_active: Optional[bool] = None


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
            "start_time": _start_time_to_iso(bus),
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
    
    # Parse start_time if provided - store as naive UTC
    start_time_dt = None
    if start_time:
        try:
            s = start_time.strip().replace('Z', '+00:00')
            if not ('+' in s or s.count('-') > 2):
                s = s + '+00:00'
            dt = datetime.fromisoformat(s)
            if dt.tzinfo:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            start_time_dt = dt
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
        "start_time": _start_time_to_iso(bus),
        "is_active": bus.is_active,
    }


def _parse_and_store_start_time(bus: Bus, start_time: Optional[str]) -> None:
    """Parse start_time (ISO UTC) and store as naive UTC in DB (avoids SQLite timezone quirks)."""
    if start_time is None:
        return
    if start_time == "":
        bus.start_time = None
        return
    try:
        # Parse as UTC - ensure Z or +00:00
        s = start_time.strip().replace('Z', '+00:00')
        if not ('+' in s or s.count('-') > 2):  # No timezone suffix
            s = s + '+00:00'
        dt = datetime.fromisoformat(s)
        # Normalize to UTC and store as naive (SQLite has no timezone)
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        bus.start_time = dt
    except (ValueError, AttributeError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid start_time format: {e}")


def _start_time_to_iso(bus: Bus) -> Optional[str]:
    """Return start_time as ISO string with Z (always UTC)."""
    if not bus.start_time:
        return None
    dt = bus.start_time
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    s = dt.isoformat()
    return s if s.endswith('Z') or '+' in s else s + 'Z'


@router.put("/buses/{bus_number}")
def update_bus(
    bus_number: str,
    body: Optional[BusUpdateBody] = Body(None),
    password: Optional[str] = Query(None),
    route_name: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_admin_password),
):
    """Update a bus. Prefer JSON body to avoid URL encoding issues with start_time."""
    import bcrypt

    bus = db.query(Bus).filter(Bus.bus_number == bus_number).first()
    if not bus:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bus not found")

    if body:
        if body.password:
            bus.password_hash = bcrypt.hashpw(body.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if body.route_name is not None:
            bus.route_name = body.route_name
        if body.start_time is not None:
            _parse_and_store_start_time(bus, body.start_time)
        if body.is_active is not None:
            bus.is_active = body.is_active
    else:
        if password:
            bus.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        if route_name is not None:
            bus.route_name = route_name
        if start_time is not None:
            _parse_and_store_start_time(bus, start_time)
        if is_active is not None:
            bus.is_active = is_active

    db.commit()
    db.refresh(bus)

    return {
        "bus_number": bus.bus_number,
        "route_name": bus.route_name,
        "start_time": _start_time_to_iso(bus),
        "is_active": bus.is_active,
    }


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
    
    # Keep bus route_name in sync for list display
    bus.route_name = route_name
    
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

    if sequence_order < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sequence_order must be a positive integer")
    if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid coordinates")
    duplicate = db.query(Stop).filter(Stop.route_id == route.route_id, Stop.sequence_order == sequence_order).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sequence order already exists for this route")
    
    # Parse scheduled times (legacy datetime format)
    arrival_dt = None
    departure_dt = None
    if scheduled_arrival:
        try:
            arrival_dt = datetime.fromisoformat(scheduled_arrival.replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid scheduled_arrival: {exc}")
    if scheduled_departure:
        try:
            departure_dt = datetime.fromisoformat(scheduled_departure.replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid scheduled_departure: {exc}")
    if scheduled_arrival_minutes is not None and scheduled_arrival_minutes < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scheduled_arrival_minutes must be >= 0")
    if scheduled_departure_minutes is not None and scheduled_departure_minutes < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="scheduled_departure_minutes must be >= 0")
    
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
    route = db.query(Route).filter(Route.bus_number == bus_number).first()
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    stop = db.query(Stop).filter(Stop.stop_id == stop_id).first()
    if not stop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop not found")
    if stop.route_id != route.route_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stop does not belong to this route")
    
    if stop_name is not None:
        stop.stop_name = stop_name
    if latitude is not None:
        if latitude < -90 or latitude > 90:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid latitude")
        stop.latitude = latitude
    if longitude is not None:
        if longitude < -180 or longitude > 180:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid longitude")
        stop.longitude = longitude
    if sequence_order is not None:
        if sequence_order < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sequence_order must be a positive integer")
        duplicate = db.query(Stop).filter(
            Stop.route_id == route.route_id,
            Stop.sequence_order == sequence_order,
            Stop.stop_id != stop_id
        ).first()
        if duplicate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sequence order already exists for this route")
        stop.sequence_order = sequence_order
    
    # Handle legacy datetime format
    if scheduled_arrival is not None:
        try:
            stop.scheduled_arrival = datetime.fromisoformat(scheduled_arrival.replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid scheduled_arrival: {exc}")
    if scheduled_departure is not None:
        try:
            stop.scheduled_departure = datetime.fromisoformat(scheduled_departure.replace("Z", "+00:00"))
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid scheduled_departure: {exc}")
    
    # Handle minutes format (preferred)
    if scheduled_arrival_minutes is not None:
        if scheduled_arrival_minutes < 0:
            stop.scheduled_arrival_minutes = None
        else:
            stop.scheduled_arrival_minutes = scheduled_arrival_minutes
    if scheduled_departure_minutes is not None:
        if scheduled_departure_minutes < 0:
            stop.scheduled_departure_minutes = None
        else:
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
        
        def _dt_iso(dt):
            if not dt:
                return None
            d = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
            s = d.isoformat()
            return s if (s.endswith('Z') or '+' in s) else s + 'Z'

        result.append({
            "bus_number": session.bus_number,
            "session_id": session.session_id,
            "started_at": _dt_iso(session.started_at),
            "expires_at": _dt_iso(session.expires_at),
            "last_location": {
                "latitude": last_location.latitude,
                "longitude": last_location.longitude,
                "recorded_at": _dt_iso(last_location.recorded_at),
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

