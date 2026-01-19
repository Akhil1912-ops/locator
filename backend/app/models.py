from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class Bus(Base):
    __tablename__ = "buses"

    bus_number = Column(String, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)
    route_name = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)  # When the bus starts its route (reference time)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("DriverSession", back_populates="bus", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="bus", cascade="all, delete-orphan")
    delay_info = relationship("DelayInfo", back_populates="bus", uselist=False, cascade="all, delete-orphan")


class Route(Base):
    __tablename__ = "routes"

    route_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bus_number = Column(String, ForeignKey("buses.bus_number"), nullable=False, unique=True)
    route_name = Column(String, nullable=False)

    # Relationships
    stops = relationship("Stop", back_populates="route", order_by="Stop.sequence_order", cascade="all, delete-orphan")


class Stop(Base):
    __tablename__ = "stops"

    stop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    route_id = Column(Integer, ForeignKey("routes.route_id"), nullable=False)
    stop_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    sequence_order = Column(Integer, nullable=False)  # Order in route (1, 2, 3...)
    scheduled_arrival = Column(DateTime, nullable=True)  # Scheduled time for this stop (legacy)
    scheduled_departure = Column(DateTime, nullable=True)  # Legacy
    scheduled_arrival_minutes = Column(Integer, nullable=True)  # Minutes from start point
    scheduled_departure_minutes = Column(Integer, nullable=True)  # Minutes from start point
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    route = relationship("Route", back_populates="stops")


class DriverSession(Base):
    __tablename__ = "driver_sessions"

    session_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bus_number = Column(String, ForeignKey("buses.bus_number"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    bus = relationship("Bus", back_populates="sessions")
    locations = relationship("Location", back_populates="session", cascade="all, delete-orphan")


class Location(Base):
    __tablename__ = "locations"

    location_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bus_number = Column(String, ForeignKey("buses.bus_number"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("driver_sessions.session_id"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bus = relationship("Bus", back_populates="locations")
    session = relationship("DriverSession", back_populates="locations")


class DelayInfo(Base):
    __tablename__ = "delay_info"

    delay_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bus_number = Column(String, ForeignKey("buses.bus_number"), nullable=False, unique=True)
    delay_minutes = Column(Integer, default=0)
    current_stop = Column(String, nullable=True)
    next_stop = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bus = relationship("Bus", back_populates="delay_info")


class TrackingCode(Base):
    __tablename__ = "tracking_codes"

    code = Column(String, primary_key=True, index=True)  # Short code (e.g., "abc123")
    bus_number = Column(String, ForeignKey("buses.bus_number"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Optional: for analytics
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)


