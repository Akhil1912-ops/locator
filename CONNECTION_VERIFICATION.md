# Connection Verification: Admin, Passenger, Driver App

All three clients are **correctly wired** to the backend. The connections match.

---

## Backend API Structure

| Prefix | Routes | Purpose |
|--------|--------|---------|
| `/auth` | `/driver/login` | Driver login |
| `/driver` | `/location` | Receive location updates (needs session token) |
| `/passenger` | `/bus/{bus}`, `/bus/{bus}/stops`, `/ws/bus/{bus}` | Bus status, stops, WebSocket |
| `/admin` | `/buses`, `/stats`, `/active-drivers`, etc. | Admin management |

---

## 1. Admin Page (GitHub Pages)

| What | How |
|------|-----|
| **API URL** | `localStorage.apiBase` or `?api=URL` in link |
| **Auth** | `X-Admin-Password: admin123` header |
| **Endpoints** | `GET/POST /admin/buses`, `GET /admin/stats`, `GET /admin/active-drivers`, etc. |
| **CORS** | Allowed (`*`) |
| **Status** | ✅ Correct |

---

## 2. Passenger Page (GitHub Pages)

| What | How |
|------|-----|
| **API URL** | `localStorage.apiBase` or `?api=URL` in link |
| **Endpoints** | `GET /passenger/bus/{bus}`, `GET /passenger/bus/{bus}/stops`, `WebSocket /passenger/ws/bus/{bus}` |
| **CORS** | Allowed (`*`) |
| **Status** | ✅ Correct |

---

## 3. Driver App (Android)

| What | How |
|------|-----|
| **API URL** | Stored in DataStore, set at login |
| **Login** | `POST /auth/driver/login` with `{bus_number, password}` |
| **Location** | `POST /driver/location` with `X-Session-Token` + `{latitude, longitude, recorded_at}` |
| **Status** | ✅ Endpoints and payloads match backend |

---

## Required: Same Base URL Everywhere

All three must use the **same API base URL** (the tunnel URL), e.g.:
```
https://xxxxx.trycloudflare.com
```

- **Admin:** Open with `?api=https://xxxxx.trycloudflare.com` once to save
- **Passenger:** Same, add `&bus=222` (or your bus number)
- **Driver app:** Enter URL in login screen before logging in

---

## Why "Bus not tracking yet"?

The connections are correct. The problem is that **location updates never reach the backend** (no `POST /driver/location` in logs).

Possible causes:
1. **Wrong API URL on phone** – Old tunnel URL, typo
2. **Phone can't reach tunnel** – Different network, firewall, VPN
3. **GPS not giving updates** – Indoors, permission denied
4. **Service stops early** – If URL or token blank, service exits without sending

The updated app shows a red error card when location send fails – that should narrow it down.
