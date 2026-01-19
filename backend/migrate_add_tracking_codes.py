"""
Migration script to add tracking_codes table
Run this once to create the tracking_codes table in your database
"""
from app.database import engine, Base
from app.models import TrackingCode

def migrate():
    print("Creating tracking_codes table...")
    TrackingCode.__table__.create(engine, checkfirst=True)
    print("Migration complete! tracking_codes table created.")

if __name__ == "__main__":
    migrate()
