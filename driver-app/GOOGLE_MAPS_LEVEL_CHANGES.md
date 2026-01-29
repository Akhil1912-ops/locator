# Changes Needed to Match Google Maps / Uber Level (Android)

You want **that level** of location tracking. You're fine with **any** level of change, including a **completely new app**. This doc spells out the **exact** changes and the **three options**, from smallest to largest.

---

## The Gap (Why We’re Not There Yet)

| Aspect | Google Maps / Uber / Zomato | Our Current App |
|--------|-----------------------------|------------------|
| **Location API** | Fused Location Provider (FLP) | Same FLP ✅ |
| **How we call it** | **Native Kotlin** → `FusedLocationProviderClient` directly | **expo-location** (JS) → bridge → Expo module → FLP |
| **Foreground service** | Native `Service` + `startForeground()` type `location` | Same via Expo config ✅ |
| **Update control** | Full `LocationRequest`: priority, interval, maxWait, displacement | Limited to what Expo exposes |
| **Background updates** | Native callbacks; no JS wake-up | Task runs in native, but payload goes through RN; OS can defer |
| **Execution** | 100% native for tracking path | JS + bridge in the loop |

**Summary:** Same **underlying tech** (FLP + foreground service). The gap is **native vs React Native**: they use **native Android** for the tracking path; we use **Expo/RN**, so we hit abstraction limits and JS/bridge behavior.

---

## What “That Level” Means (Concretely)

To **match** Maps/Uber we need:

1. **Direct FLP usage** — Kotlin calling `FusedLocationProviderClient` ourselves, no expo-location.
2. **Full `LocationRequest` control** — `PRIORITY_HIGH_ACCURACY`, exact `interval` / `fastestInterval` / `maxWaitTime` / `smallestDisplacement`.
3. **Native foreground service** — our own `Service` with `foregroundServiceType="location"`, not Expo’s.
4. **No JS in the tracking path** — location → send to backend happens entirely in native code (or a dedicated native module). No React Native bridge for each update.
5. **Android-only** — we can ignore iOS and optimize only for Android.

---

## Three Options (Smallest → Largest Change)

### Option A: React Native + Transistorsoft (react-native-background-geolocation)

**What changes:** We **replace expo-location** with **react-native-background-geolocation**. Keep React Native for UI (login, tracking screen, etc.).

**What we build:**
- Install the lib, add Expo config plugin / custom dev client.
- New `LocationService` that uses Transistorsoft’s API (start, stop, onLocation callback).
- Native code stays inside the library; we use it from JS.
- Still have a JS layer, but the **location engine** is their native FLP + motion logic.

**Effort:** Medium (1–2 days). **Cost:** ~$389–749 for Android production license.

**Result:** **Close** to Maps/Uber level. Used by fleets/delivery apps. Much better than expo-location, especially in background. Not 100% native app.

**Pros:** Keeps existing RN app, UI, backend integration. Quick to ship.  
**Cons:** Paid license, still RN; we don’t own the native code.

---

### Option B: React Native + Custom Native Location Module (Kotlin)

**What changes:** We **keep React Native** for UI, but **add a custom Android library** (Kotlin) that owns **all** location logic. No expo-location.

**What we build:**
- **New Kotlin module** (e.g. `android/app/src/.../LocationTrackerModule`):
  - `FusedLocationProviderClient` + `LocationRequest` (high accuracy, our chosen interval/displacement).
  - Our own **foreground `Service`** (type `location`) that receives FLP updates and **HTTP-posts** to our backend (Retrofit/OkHttp).
  - Expose to RN: `startTracking()`, `stopTracking()`, maybe `getLastLocationSentTime()` via events or direct calls.
- **RN side:** Login, TrackingScreen, API base URL config stay. We just call `NativeModules.LocationTracker.startTracking()` etc. instead of using `LocationService.js` + expo-location.
- **Alarm:** Either in native (WorkManager / AlarmManager if no location for X minutes) or keep RN alarm logic using `lastLocationSent` from the module.

**Effort:** High (roughly 1–2 weeks). **Cost:** $0.

**Result:** **Same level** as Maps/Uber for the **tracking path**: direct FLP, native service, no JS in the loop. UI remains RN.

**Pros:** Full control, no license, truly native tracking.  
**Cons:** We maintain Kotlin code, RN bridge, and build tooling.

---

### Option C: Full Native Android App (Kotlin)

**What changes:** **Remove React Native entirely.** New **Android app** (Kotlin) that does everything the driver app does today.

**What we build:**
- **New Android project** (Kotlin, Jetpack Compose or XML views):
  - **Login screen:** Bus number + password + server URL → `POST /auth/driver/login`, store token.
  - **Tracking screen:** Start / Stop tracking, logout, links to Settings + Battery optimization.
  - **Location:** Same as Option B — `FusedLocationProviderClient`, our own foreground `Service` (type `location`), HTTP POST to `POST /driver/location` with `X-Session-Token`.
  - **Alarm:** If no location sent for e.g. 45–60 seconds while “tracking,” show notification / sound (WorkManager or similar).
- **Stack:** Kotlin, Retrofit/OkHttp for API, DataStore or SharedPreferences for token/URL, optional Hilt for DI.

**Effort:** Highest (about 2–4 weeks for one dev, depending on experience). **Cost:** $0.

**Result:** **Same stack** as Google Maps, Uber, Zomato on Android: **100% native**. No RN, no Expo, no JS. Full control over FLP, service, and process.

**Pros:** Matches “that level” exactly; no bridge or abstraction.  
**Cons:** Complete rewrite; no shared code with current RN app.

---

## Comparison

| | Option A (Transistorsoft) | Option B (RN + native module) | Option C (Full native app) |
|--|---------------------------|-------------------------------|----------------------------|
| **Tracking level** | Close to Maps/Uber | Same as Maps/Uber | Same as Maps/Uber |
| **UI** | React Native (keep current) | React Native (keep current) | Kotlin (new) |
| **Location path** | Their native lib | Our Kotlin module | Our Kotlin code |
| **Effort** | Medium | High | Highest |
| **Cost** | $389+ | $0 | $0 |
| **Maintenance** | Third-party lib | We own native + RN | We own everything |

---

## Recommendation (Given “Whatever It Takes”)

- **If you want the fastest upgrade** and are okay paying for a license: **Option A**.  
- **If you want Maps/Uber-level tracking, keep RN UI, and avoid license:** **Option B**.  
- **If you want to match them 1:1 and are fine rebuilding the app:** **Option C**.

You said you’re ready for **including a completely new app**, so **Option C** is valid. It’s the **only** way to have the **exact** same tech and architecture as those apps (native Android, direct FLP, our own foreground service).

---

## What “Full Native App” (Option C) Would Contain

Rough structure:

```
driver-app-native/          # New Android project
├── app/
│   ├── src/main/
│   │   ├── java/.../
│   │   │   ├── MainActivity.kt
│   │   │   ├── login/
│   │   │   │   └── LoginViewModel.kt, LoginScreen.kt
│   │   │   ├── tracking/
│   │   │   │   └── TrackingViewModel.kt, TrackingScreen.kt
│   │   │   ├── location/
│   │   │   │   ├── LocationTrackerService.kt   # Foreground service, FLP
│   │   │   │   ├── LocationRepository.kt       # HTTP -> backend
│   │   │   │   └── FusedLocationClient.kt      # FLP wrapper
│   │   │   ├── api/
│   │   │   │   └── DriverApi.kt                # Retrofit: login, location
│   │   │   └── alarm/
│   │   │       └── TrackingAlarmManager.kt     # “Tracking stopped” notifications
│   │   ├── AndroidManifest.xml                 # Service, permissions
│   │   └── res/...
│   └── build.gradle.kts
└── build.gradle.kts
```

- **Permissions:** `ACCESS_FINE_LOCATION`, `ACCESS_BACKGROUND_LOCATION`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_LOCATION`.
- **Service:** `android:foregroundServiceType="location"`, `startForeground()` with a sticky notification.
- **FLP:** `LocationRequest` with `PRIORITY_HIGH_ACCURACY`, interval e.g. 10s, `smallestDisplacement` e.g. 25m, `setMaxWaitTime` if needed.
- **API:** Same endpoints as today — `POST /auth/driver/login`, `POST /driver/location` with header `X-Session-Token`.

---

## Next Step

Choose one:

1. **Option A** — Integrate Transistorsoft into the existing RN app.  
2. **Option B** — Add a Kotlin location module to the RN app and switch off expo-location.  
3. **Option C** — Create a new native Android app and implement the structure above.

Once you pick, we can break it down into **concrete tasks** (files to add, APIs to call, config to change) and implement step by step.
