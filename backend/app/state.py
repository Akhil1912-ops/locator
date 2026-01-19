from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets

from .config import settings


class InMemoryStore:
    """
    Minimal in-memory store to keep the prototype running without a DB.
    Replace with Postgres in production.
    """

    def __init__(self) -> None:
        # Demo buses: bus_number -> password (plaintext for prototype)
        self.buses: Dict[str, str] = {
            "123": "password123",
            "456": "password456",
        }
        # session_token -> {"bus_number": str, "expires": datetime}
        self.sessions: Dict[str, Dict] = {}
        # bus_number -> last location payload
        self.last_locations: Dict[str, Dict] = {}
        # bus_number -> simple delay minutes and stop info
        self.delays: Dict[str, Dict] = {}

    def login(self, bus_number: str, password: str) -> Optional[Dict]:
        stored = self.buses.get(bus_number)
        if not stored or stored != password:
            return None
        token = secrets.token_urlsafe(24)
        expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        self.sessions[token] = {"bus_number": bus_number, "expires": expires}
        return {"token": token, "expires": expires}

    def get_session(self, token: str) -> Optional[str]:
        session = self.sessions.get(token)
        if not session:
            return None
        if session["expires"] < datetime.utcnow():
            self.sessions.pop(token, None)
            return None
        return session["bus_number"]

    def save_location(self, bus_number: str, latitude: float, longitude: float, recorded_at: datetime) -> Dict:
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "recorded_at": recorded_at,
        }
        self.last_locations[bus_number] = payload
        return payload

    def get_last_location(self, bus_number: str) -> Optional[Dict]:
        return self.last_locations.get(bus_number)

    def save_delay(self, bus_number: str, delay_minutes: int, current_stop: Optional[str], next_stop: Optional[str]) -> None:
        self.delays[bus_number] = {
            "delay_minutes": delay_minutes,
            "current_stop": current_stop,
            "next_stop": next_stop,
        }

    def get_delay(self, bus_number: str) -> Dict:
        return self.delays.get(bus_number, {"delay_minutes": 0, "current_stop": None, "next_stop": None})


store = InMemoryStore()

