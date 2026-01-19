"""
Seed script to populate initial database data.
Run this once after setting up the database.
"""
from datetime import datetime, timedelta, timezone
import bcrypt
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Base, Bus, Route, Stop, DelayInfo
from app.config import settings

def hash_password(password: str) -> str:
    """Hash password using bcrypt directly"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def seed_database():
    """Seed initial data"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create demo buses
        bus1 = db.query(Bus).filter(Bus.bus_number == "123").first()
        if not bus1:
            bus1 = Bus(
                bus_number="123",
                password_hash=hash_password("password123"),
                route_name="Route A",
                is_active=True,
            )
            db.add(bus1)
        
        bus2 = db.query(Bus).filter(Bus.bus_number == "456").first()
        if not bus2:
            bus2 = Bus(
                bus_number="456",
                password_hash=hash_password("password456"),
                route_name="Route B",
                is_active=True,
            )
            db.add(bus2)
        
        db.commit()
        
        # Create routes
        route1 = db.query(Route).filter(Route.bus_number == "123").first()
        if not route1:
            route1 = Route(bus_number="123", route_name="Route A")
            db.add(route1)
            db.flush()
        
        route2 = db.query(Route).filter(Route.bus_number == "456").first()
        if not route2:
            route2 = Route(bus_number="456", route_name="Route B")
            db.add(route2)
            db.flush()
        
        db.commit()
        
        # Create stops for Route A (bus 123)
        stops1 = db.query(Stop).filter(Stop.route_id == route1.route_id).count()
        if stops1 == 0:
            base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            stop_data = [
                ("Stop A", 19.0760, 72.8777, base_time + timedelta(minutes=0)),
                ("Stop B", 19.0860, 72.8877, base_time + timedelta(minutes=15)),
                ("Stop C", 19.0960, 72.8977, base_time + timedelta(minutes=30)),
                ("Stop D", 19.1060, 72.9077, base_time + timedelta(minutes=45)),
            ]
            for idx, (name, lat, lng, scheduled) in enumerate(stop_data, 1):
                stop = Stop(
                    route_id=route1.route_id,
                    stop_name=name,
                    latitude=lat,
                    longitude=lng,
                    sequence_order=idx,
                    scheduled_arrival=scheduled,
                    scheduled_departure=scheduled + timedelta(minutes=2),
                )
                db.add(stop)
        
        # Create stops for Route B (bus 456)
        stops2 = db.query(Stop).filter(Stop.route_id == route2.route_id).count()
        if stops2 == 0:
            base_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
            stop_data = [
                ("Stop X", 19.0760, 72.8777, base_time + timedelta(minutes=0)),
                ("Stop Y", 19.0860, 72.8877, base_time + timedelta(minutes=20)),
                ("Stop Z", 19.0960, 72.8977, base_time + timedelta(minutes=40)),
            ]
            for idx, (name, lat, lng, scheduled) in enumerate(stop_data, 1):
                stop = Stop(
                    route_id=route2.route_id,
                    stop_name=name,
                    latitude=lat,
                    longitude=lng,
                    sequence_order=idx,
                    scheduled_arrival=scheduled,
                    scheduled_departure=scheduled + timedelta(minutes=2),
                )
                db.add(stop)
        
        db.commit()
        print("Database seeded successfully!")
        print("   - Buses: 123, 456")
        print("   - Routes: Route A, Route B")
        print("   - Stops: Created for both routes")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

