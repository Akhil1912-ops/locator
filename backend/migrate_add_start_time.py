"""
Migration script to add start_time column to buses table.
Run this once after updating the Bus model.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "bustracker.db"

def migrate():
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(buses)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'start_time' in columns:
            print("Column 'start_time' already exists. Migration not needed.")
            return
        
        # Add start_time column
        cursor.execute("ALTER TABLE buses ADD COLUMN start_time DATETIME")
        conn.commit()
        print("Successfully added 'start_time' column to buses table.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
