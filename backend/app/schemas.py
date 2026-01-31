from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DriverLoginRequest(BaseModel):
    bus_number: str
    password: str


class DriverLoginResponse(BaseModel):
    session_token: str
    expires_at: datetime


class LocationUpdate(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    recorded_at: datetime


class LastLocation(BaseModel):
    latitude: float
    longitude: float
    recorded_at: datetime
    last_seen_seconds: int
    running_delay_minutes: int
    status: str
    current_stop: Optional[str]
    next_stop: Optional[str]


class StopEta(BaseModel):
    stop_name: str
    scheduled_time: datetime
    eta: Optional[datetime] = None  # None for passed/at-stop
    actual_arrived_at: Optional[datetime] = None  # When bus actually reached this stop
    delay_minutes: int
    status: str  # on_time / delayed / early / at_stop
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class StopEtaResponse(BaseModel):
    bus_number: str
    stops: List[StopEta]

