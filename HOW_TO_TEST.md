# How to Test the Bus Tracker Application

This guide helps evaluators/interviewers run and test the project for the vibe coding intern submission.

---

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| **Python 3.10+** | Backend server |
| **cloudflared** | Expose local server to internet (for driver app on phone) |
| **Android phone** or emulator | Driver app (APK) |
| **Web browser** | Admin panel + Passenger page |

**Install cloudflared:** [https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)

---

## Quick Start (3 Steps)

### 1. Setup Backend (first time only)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python seed_db.py
```
Then start the server:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
**Or on Windows:** Double-click `start-backend.bat` (after running the setup above once).

### 2. Start Tunnel
Open a **new terminal** and run:
```powershell
cloudflared tunnel --url http://127.0.0.1:8000 --protocol http2
```
A URL like `https://xxxxx.trycloudflare.com` will appear. **Copy it** — this is your base URL.

### 3. Test the App

| Part | URL | Credentials |
|------|-----|-------------|
| **Admin Panel** | `https://YOUR_TUNNEL_URL/ui/admin/` | Password: `admin123` |
| **Passenger Page** | `https://YOUR_TUNNEL_URL/ui/passenger/?bus=123` | No login |
| **Driver App** | Install APK, set Server URL = tunnel URL | Bus: `123` / Password: `password123` |

---

## Step-by-Step Testing

### A. Admin Panel
1. Open `https://YOUR_TUNNEL_URL/ui/admin/` in browser
2. Enter password: **admin123**
3. You should see: dashboard with bus list, stats
4. Try: **Add Bus**, **Edit Route**, **Add Stop** (needs Google Maps API key for location search, or type lat/lng manually)
5. Click **Monitor** on a bus to see live view (similar to passenger page)

### B. Passenger Page
1. Open `https://YOUR_TUNNEL_URL/ui/passenger/?bus=123` in browser (or phone)
2. Initially shows "Bus not tracking yet" (no location data)
3. **After driver app sends location:** Timeline updates with live position, current/next stop, ETAs
4. Try **"My Stop"** notifications: tap 🔔 on any stop → get alerted at 2 stops away, 1 stop away, arrived (allow notifications when prompted)

### C. Driver App
1. Build APK: Open `driver-app-native` in Android Studio → **Build → Build APK(s)**  
   - Or use pre-built APK if provided
2. Install on Android phone (or emulator)
3. Open app → set **Server URL** = `https://YOUR_TUNNEL_URL` (no trailing slash)
4. Tap **Save URL & Login**
5. Enter Bus number: **123**, Password: **password123**
6. Tap **Login**
7. Tap **Start Tracking** — GPS is sent every ~10 seconds
8. Switch to **Passenger page** (browser) — you should see live bus position updating

---

## Demo Flow (End-to-End)

1. Start backend + tunnel
2. Open **Admin** → login with `admin123` → verify dashboard
3. Open **Passenger** page `?bus=123` → shows "Bus not tracking"
4. Open **Driver app** on phone → login `123`/`password123` → **Start Tracking**
5. Refresh **Passenger** page → bus position appears, timeline updates in real time
6. Tap 🔔 on a stop in Passenger page → enable "My Stop" notifications

---

## Demo Credentials

| Role | Credential |
|------|------------|
| Admin password | `admin123` |
| Bus 123 | `123` / `password123` |
| Bus 456 | `456` / `password456` |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Bus not tracking" on Passenger | Driver app must be running and "Start Tracking" tapped |
| Admin "Invalid password" | Use `admin123` exactly |
| Driver app "Cannot reach server" | Ensure tunnel URL is correct, no trailing slash; backend + tunnel must be running |
| No autocomplete when adding stop | Google Maps API key — add in `docs/admin/index.html` (see `GOOGLE_MAPS_SETUP.md`) or enter lat/lng manually |
| Tunnel URL changes each run | Expected — Cloudflare quick tunnels are temporary; copy new URL when you restart |

---

## Files to Review

- `PROJECT_PDF.html` — Project overview (save as PDF for submission)
- `backend/` — FastAPI + SQLite
- `docs/admin/index.html` — Admin UI
- `docs/passenger/index.html` — Passenger UI
- `driver-app-native/` — Android driver app (Kotlin)
