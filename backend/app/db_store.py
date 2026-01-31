from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Dict, Optional
from sqlalchemy.orm import Session
import bcrypt

from .models import Bus, DriverSession, Location, DelayInfo, Route, Stop, StopArrival
from .config import settings

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance between two points in km."""
    import math
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt directly"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


class DatabaseStore:
    """Database-backed store replacing InMemoryStore"""

    def __init__(self, db: Session):
        self.db = db

    def login(self, bus_number: str, password: str) -> Optional[Dict]:
        """Authenticate driver and create session"""
        bus = self.db.query(Bus).filter(Bus.bus_number == bus_number).first()
        if not bus or not verify_password(password, bus.password_hash):
            return None

        # Create session token
        import secrets
        token = secrets.token_urlsafe(24)
        expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

        session = DriverSession(
            bus_number=bus_number,
            token=token,
            expires_at=expires,
            is_active=True,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return {"token": token, "expires": expires}

    def get_session(self, token: str) -> Optional[str]:
        """Get bus_number from session token"""
        session = self.db.query(DriverSession).filter(
            DriverSession.token == token,
            DriverSession.is_active == True,
            DriverSession.expires_at > datetime.now(timezone.utc)
        ).first()

        if not session:
            return None

        return session.bus_number

    def save_location(self, bus_number: str, latitude: float, longitude: float, recorded_at: datetime) -> Dict:
        """Save location update"""
        # Get active session for this bus (optional, for tracking)
        session = self.db.query(DriverSession).filter(
            DriverSession.bus_number == bus_number,
            DriverSession.is_active == True
        ).order_by(DriverSession.started_at.desc()).first()

        location = Location(
            bus_number=bus_number,
            session_id=session.session_id if session else None,
            latitude=latitude,
            longitude=longitude,
            recorded_at=recorded_at,
        )
        self.db.add(location)
        self.db.commit()
        self.db.refresh(location)

        return {
            "latitude": latitude,
            "longitude": longitude,
            "recorded_at": recorded_at,
            "session_id": session.session_id if session else None,
        }

    def record_stop_arrivals_if_near(
        self, bus_number: str, session_id: Optional[int],
        latitude: float, longitude: float, recorded_at: datetime
    ) -> None:
        """If bus is within 20m of any stop not yet recorded for this session, record arrival."""
        if session_id is None:
            return
        stops_raw = self.get_stops_for_bus(bus_number)
        if not stops_raw:
            return
        arrived_stop_ids = {
            a.stop_id for a in self.db.query(StopArrival).filter(
                StopArrival.session_id == session_id
            ).all()
        }
        for stop in stops_raw:
            if stop["stop_id"] in arrived_stop_ids:
                continue
            dist_km = _haversine_km(latitude, longitude, stop["latitude"], stop["longitude"])
            if dist_km <= 0.02:  # 20 meters
                self.db.add(StopArrival(session_id=session_id, stop_id=stop["stop_id"], arrived_at=recorded_at))
                self.db.commit()
                arrived_stop_ids.add(stop["stop_id"])

    def get_stop_arrivals_for_session(self, session_id: Optional[int]) -> Dict[int, datetime]:
        """Return {stop_id: arrived_at} for the given session."""
        if session_id is None:
            return {}
        rows = self.db.query(StopArrival).filter(StopArrival.session_id == session_id).all()
        return {r.stop_id: r.arrived_at for r in rows}

    def get_last_location(self, bus_number: str) -> Optional[Dict]:
        """Get most recent location for bus"""
        location = self.db.query(Location).filter(
            Location.bus_number == bus_number
        ).order_by(Location.recorded_at.desc()).first()

        if not location:
            return None

        return {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "recorded_at": location.recorded_at,
            "session_id": location.session_id,
        }

    def save_delay(self, bus_number: str, delay_minutes: int, current_stop: Optional[str], next_stop: Optional[str]) -> None:
        """Save delay information"""
        delay = self.db.query(DelayInfo).filter(DelayInfo.bus_number == bus_number).first()
        if delay:
            delay.delay_minutes = delay_minutes
            delay.current_stop = current_stop
            delay.next_stop = next_stop
            delay.updated_at = datetime.now(timezone.utc)
        else:
            delay = DelayInfo(
                bus_number=bus_number,
                delay_minutes=delay_minutes,
                current_stop=current_stop,
                next_stop=next_stop,
            )
            self.db.add(delay)
        self.db.commit()

    def get_delay(self, bus_number: str) -> Dict:
        """Get delay information"""
        delay = self.db.query(DelayInfo).filter(DelayInfo.bus_number == bus_number).first()
        if not delay:
            return {"delay_minutes": 0, "current_stop": None, "next_stop": None}
        return {
            "delay_minutes": delay.delay_minutes,
            "current_stop": delay.current_stop,
            "next_stop": delay.next_stop,
        }

    def get_stops_for_bus(self, bus_number: str) -> list:
        """Get all stops for a bus's route, calculating scheduled times from start_time + scheduled_arrival_minutes"""
        route = self.db.query(Route).filter(Route.bus_number == bus_number).first()
        if not route:
            return []
        
        # Get bus to access start_time
        bus = self.db.query(Bus).filter(Bus.bus_number == bus_number).first()
        start_time = bus.start_time if bus else None
        
        stops = self.db.query(Stop).filter(
            Stop.route_id == route.route_id
        ).order_by(Stop.sequence_order).all()
        try:
            india_tz = ZoneInfo("Asia/Kolkata")
        except Exception:
            india_tz = timezone(timedelta(hours=5, minutes=30))
        result = []
        for stop in stops:
            # Calculate scheduled time from start_time + scheduled_arrival_minutes
            # Use today's date + the time from start_time (since start_time is daily)
            scheduled = None
            if start_time and stop.scheduled_arrival_minutes is not None:
                # start_time is stored as UTC (admin sends IST converted to UTC)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=timezone.utc)
                start_time_ist = start_time.astimezone(india_tz)
                today = datetime.now(india_tz).replace(hour=0, minute=0, second=0, microsecond=0)
                today_start = today.replace(hour=start_time_ist.hour, minute=start_time_ist.minute)
                scheduled = today_start + timedelta(minutes=stop.scheduled_arrival_minutes)
            elif stop.scheduled_arrival:
                scheduled = stop.scheduled_arrival
            elif stop.scheduled_departure:
                scheduled = stop.scheduled_departure
            
            result.append({
                "stop_id": stop.stop_id,
                "name": stop.stop_name,
                "scheduled": scheduled,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "scheduled_arrival_minutes": stop.scheduled_arrival_minutes,
                "sequence_order": stop.sequence_order,
            })
        
        return result

