"""
Migration script to add stop_arrivals table.
Records actual arrival times per stop per driver session (trip).
Run once, or rely on create_all() at app startup.
"""
from app.database import engine, Base
from app.models import StopArrival

def migrate():
    print("Creating stop_arrivals table...")
    StopArrival.__table__.create(engine, checkfirst=True)
    print("Migration complete! stop_arrivals table created.")

if __name__ == "__main__":
    migrate()
