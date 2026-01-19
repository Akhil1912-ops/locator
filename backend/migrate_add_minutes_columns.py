"""Add scheduled_arrival_minutes and scheduled_departure_minutes columns to stops table"""
from sqlalchemy import text, inspect
from app.database import engine

def migrate():
    conn = engine.connect()
    try:
        # Check if columns already exist
        inspector = inspect(engine)
        existing_cols = [c['name'] for c in inspector.get_columns('stops')]
        
        if 'scheduled_arrival_minutes' not in existing_cols:
            conn.execute(text('ALTER TABLE stops ADD COLUMN scheduled_arrival_minutes INTEGER'))
            print('[OK] Added scheduled_arrival_minutes column')
        else:
            print('[OK] scheduled_arrival_minutes column already exists')
            
        if 'scheduled_departure_minutes' not in existing_cols:
            conn.execute(text('ALTER TABLE stops ADD COLUMN scheduled_departure_minutes INTEGER'))
            print('[OK] Added scheduled_departure_minutes column')
        else:
            print('[OK] scheduled_departure_minutes column already exists')
            
        conn.commit()
        print('Migration completed successfully!')
    except Exception as e:
        print(f'Error during migration: {e}')
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
