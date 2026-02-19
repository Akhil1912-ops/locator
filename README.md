# Bus Tracker MVP (Driver + Passenger)

**How to test:** See [HOW_TO_TEST.md](HOW_TO_TEST.md) for step-by-step instructions to run and demo the app.

---
Original plan:
- Android driver app (15s updates) using bus number + password login.
- Passenger web (per-bus URL) with stop list, ETAs, “last seen”, and a toggleable mini-map.
- Backend: FastAPI + in-memory store for the prototype; swap to Postgres later.

## Structure
- `backend/` — FastAPI app (prototype auth, location ingest, passenger APIs).
- `passenger/` — Static passenger UI (list-first with optional mini-map using Leaflet/OSM CDN).

## Running the backend (dev)
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Prototype data:
- Buses: `123/password123`, `456/password456`
- Login: `POST /auth/driver/login` with `{"bus_number":"123","password":"password123"}`
- Send location: `POST /driver/location` with headers `X-Session-Token: <token>` and body `{"latitude":19.07,"longitude":72.87,"recorded_at":"2026-01-06T09:00:00Z"}`
- Passenger view: `GET /passenger/bus/123` and `/passenger/bus/123/stops`

## Passenger UI (static demo)
Serve `passenger/index.html` with any static server (or open in browser). It calls the backend at `http://localhost:8000`. Use `?bus=123` to pick a bus, e.g.:
```
file:///.../passenger/index.html?bus=123
```

## Next steps
- Replace in-memory store with Postgres (Supabase), add tables for buses, routes, stops, driver_sessions, locations.
- Implement WebSocket broadcast for real-time updates to passengers.
- Add driver app (React Native) with background location + 15s heartbeat.
- Replace fake stop coordinates with real route data; add stop-arrival detection and delay calculation.

