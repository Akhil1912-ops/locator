# Location Tracking: Best Possible Setup

You want **Google Maps–level** accuracy and reliability: coordinates sent reliably even when the app is **backgrounded** or the phone is **sleeping**. This doc is an honest summary of the tech, its limits, and what we’ve done.

---

## 1. What We Use Today

| Layer | Technology |
|-------|------------|
| **Library** | `expo-location` + `expo-task-manager` |
| **Android** | Google Play Services **Fused Location Provider** (same as Google Maps) |
| **iOS** | Apple **Core Location** (same as Google Maps, Uber, etc.) |

So we use the **same underlying systems** as Google Maps. The gap is **how we use them** (accuracy, update strategy, background behavior) and **platform constraints** (Android battery optimization, background limits).

---

## 2. Honest Limitation: expo-location Background Updates

- On **Android**, background location updates are often **deferred** by the system.
- With `expo-location`, people report **5–12+ minutes** between background updates on some devices, **even when** we set `timeInterval` / `distanceInterval` to aggressive values.
- This is a known limitation of the current stack. We **cannot** fully fix it by only tuning expo-location.

So:

- **Foreground** (app open): we can get **frequent, accurate** updates.
- **Background / sleeping**: we can improve things (accuracy, config, foreground service), but **expo-location alone has a ceiling** on how often the OS delivers updates.

---

## 3. Two Paths to “Best” Tracking

### Path 1: Maximize expo-location (what we implement first)

**No new cost, no new deps.** We squeeze everything we can from expo-location:

- **Accuracy**: `BestForNavigation` (or `Highest`) for both foreground and background.
- **Android high-accuracy mode**: call `Location.enableNetworkProviderAsync()` so the user enables “Improve location accuracy” (Wi‑Fi + cell + GPS).
- **Foreground**: use `watchPositionAsync` (continuous subscription) instead of `getCurrentPositionAsync` in a timer.
- **Background**: `startLocationUpdatesAsync` with best accuracy, `timeInterval` + `distanceInterval`, `pausesUpdatesAutomatically: false`, `AutomotiveNavigation`, and a proper **foreground service** (notification).
- **Config**: enable background location + foreground service in `app.json` via the expo-location plugin (`isAndroidBackgroundLocationEnabled`, `isAndroidForegroundServiceEnabled`).
- **Reliability**: always persist `lastLocationSent` when we successfully send a position (foreground and background). Use that for “tracking stopped?” checks and alarms.
- **Battery**: guide users to disable battery optimization for the app (we already have links; keep them).

**Result**: Best we can get **without changing libraries**. Much better than before, but on some Android devices we may still see **gaps of several minutes** when the app is backgrounded or the phone is asleep.

---

### Path 2: Switch to react-native-background-geolocation (Transistorsoft)

**Paid, but built for fleet / delivery tracking.**

- Uses **motion detection** (accelerometer, etc.) to decide when to sample location.
- **More reliable** background updates than expo-location on Android.
- Used in production by fleet / delivery apps.
- **Expo-compatible** (config plugin, custom dev client). Not supported in Expo Go.
- **Licensing**: Android **release** builds need a **commercial license** (~$389–$749). Debug builds are free.

**When to consider**: If, after Path 1, you still see **unacceptable gaps** when the app is backgrounded or sleeping (e.g. buses “disappearing” for 5–10 minutes), switching to **react-native-background-geolocation** is the next step toward “best” behavior.

**We are not implementing Path 2 in this PR.** We implement Path 1 and document Path 2 for later.

---

## 4. What We Implemented (Path 1)

1. **`app.json`**
   - expo-location plugin: `isAndroidBackgroundLocationEnabled: true`, `isAndroidForegroundServiceEnabled: true` so background + foreground service are correctly configured (including Android 14+ `location` foreground service type).

2. **`LocationService.js`**
   - **Accuracy**: `BestForNavigation` for background and foreground.
   - **Android**: call `enableNetworkProviderAsync()` when starting tracking.
   - **Foreground**: `watchPositionAsync` with `BestForNavigation`; no more `setInterval` + `getCurrentPositionAsync`.
   - **Background**: `startLocationUpdatesAsync` with `BestForNavigation`, `timeInterval`, `distanceInterval`, `pausesUpdatesAutomatically: false`, `ActivityType.AutomotiveNavigation`, and foreground service options.
   - **`recordLocationSent()`**: exported helper. Called whenever we **successfully** send a location (foreground or background). Persists `lastLocationSent` for alarms and “tracking stopped?” logic.

3. **`App.js`**
   - Background task: after a **successful** `sendLocation` call, we call `recordLocationSent()` so background updates are counted.

4. **AlarmService**
   - Still uses `getLastLocationSentTime()`. No change to thresholds for now; we can tune later if we change intervals.

5. **TrackingScreen**
   - Copy updated to mention “best available accuracy” and that we use navigation-grade location (no functional change).

---

## 5. What You Should Do

- **Rebuild your app** (e.g. `npx expo prebuild --clean` then `eas build` or `npx expo run:android`). We changed `app.json` (expo-location plugin: background + foreground service). A new native binary is required.
- **Test on real devices**, especially:
  - App in **foreground**: expect frequent updates, good accuracy.
  - App **backgrounded** (home button, another app on top): observe update frequency.
  - **Screen off** / “sleeping”: same.
- **Test on multiple Android brands** (e.g. Samsung, Xiaomi, Huawei, Pixel). Battery optimization varies; we still guide users to disable it for our app.

If foreground is solid but **background/sleeping** remains too weak for your use case, the next move is **Path 2** (react-native-background-geolocation).

---

## 6. Summary

| Goal | Approach |
|------|----------|
| **Best accuracy** | `BestForNavigation` + `enableNetworkProviderAsync` on Android. |
| **Best foreground updates** | `watchPositionAsync` (continuous), same accuracy. |
| **Best background we can get with expo-location** | Optimized `startLocationUpdatesAsync` + foreground service + correct plugin config. |
| **Reliability / “tracking stopped?”** | Always `recordLocationSent()` on successful send; use `lastLocationSent` for checks and alarms. |
| **Beyond expo-location** | Path 2: react-native-background-geolocation (paid) when you need truly “best” background/sleep behavior. |

We’re not cutting corners: we’re doing the **best we can with the current stack**, and we’re explicit about when a different stack is needed.
