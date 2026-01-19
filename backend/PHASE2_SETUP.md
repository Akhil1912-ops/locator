# Phase 2 Setup: Database

Phase 2 adds a real database (SQLite for local dev, PostgreSQL for production).

## Quick Start (SQLite - No Installation Needed)

1. **Install new dependencies:**
   ```powershell
   cd backend
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Seed the database:**
   ```powershell
   python seed_db.py
   ```
   This creates tables and adds demo buses (123, 456) with routes/stops.

3. **Start the server:**
   ```powershell
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Test it:**
   - Login and send location (same as Phase 1)
   - **Restart the server** - data should persist! ✅

## Using PostgreSQL (Production)

1. **Install PostgreSQL** or use a cloud service (Supabase, Railway, Render)

2. **Set environment variable:**
   ```powershell
   $env:DATABASE_URL="postgresql://user:password@localhost:5432/bustracker"
   ```
   Or create a `.env` file in `backend/`:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/bustracker
   ```

3. **Run seed script:**
   ```powershell
   python seed_db.py
   ```

## What Changed

- ✅ All data now stored in database (not memory)
- ✅ Data persists after server restart
- ✅ Same API endpoints (no frontend changes needed)
- ✅ Ready for real routes/stops (replace fake data)

## Database Schema

- `buses` - Bus info and passwords
- `routes` - Route definitions
- `stops` - Stop locations and schedules
- `driver_sessions` - Active driver sessions
- `locations` - Location history
- `delay_info` - Current delay status


