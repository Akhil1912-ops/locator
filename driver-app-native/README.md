# Bus Driver Tracker (Native Android)

Native Kotlin Android app for bus drivers. Uses **Fused Location Provider** and a **foreground service** for Google Maps–level tracking (same tech as Uber, Zomato).

## Requirements

- Android Studio (Ladybug or newer)
- JDK 17
- Android SDK 35
- Min SDK 26 (Android 8.0)

## Build and run

## Build debug APK

**Option A – Android Studio (recommended)**  
1. Open `driver-app-native` in Android Studio (File → Open).  
2. Let Gradle sync.  
3. **Build → Build Bundle(s) / APK(s) → Build APK(s)**.  
4. APK output: `app/build/outputs/apk/debug/app-debug.apk`.

**Option B – Command line**  
1. Open a **Command Prompt** (not Cursor’s terminal) and `cd` to `driver-app-native`.  
2. Run `build-apk.bat`.  
3. Same APK path as above.

If `build-apk.bat` says “Gradle not found”, use Option A. Android Studio will create the wrapper; you can run `build-apk.bat` again later.

## Run on device

1. Connect an Android device or start an emulator.  
2. In Android Studio: **Run → Run 'app'**.

## Config

- **Server URL**: Set on the login screen (e.g. `http://10.0.2.2:8000` for emulator, or your machine’s LAN IP for a real device).
- **Login**: Use bus number and password from your backend (e.g. `123` / `password123` from seed data).

## Features

- Login with bus number + password; configurable API base URL.
- Start/stop tracking. Location is sent via **Fused Location Provider** (~10 s or 25 m).
- Foreground service with persistent notification while tracking.
- Alert notification if tracking stops unexpectedly (no location sent for ~60 s).
- Links to App settings and Battery optimization.

## Project structure

- `app/src/main/java/.../data/api` — Retrofit API and DTOs.
- `app/src/main/java/.../data/prefs` — DataStore preferences.
- `app/src/main/java/.../location` — `LocationTrackerService` (FLP + foreground service).
- `app/src/main/java/.../ui/login` — Login screen and ViewModel.
- `app/src/main/java/.../ui/tracking` — Tracking screen and ViewModel.

## Backend

Uses the same FastAPI backend as the React Native app:

- `POST /auth/driver/login` — login.
- `POST /driver/location` with `X-Session-Token` — send location.

Run the backend (see project root `README` or `backend/PHASE2_SETUP.md`), then point the app at its URL.
