# Bus Driver App - Setup Instructions

## Prerequisites

1. **Node.js** (v16 or higher)
2. **Expo CLI**: `npm install -g expo-cli`
3. **Android Studio** (for Android development)
4. **Expo Go app** on your Android phone (for testing)

## Installation

1. **Navigate to driver-app folder:**
   ```bash
   cd driver-app
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Update API URL:**
   - You can set the server URL directly in the app on the login screen
   - For local testing: Use your computer's IP address (e.g., `http://192.168.1.100:8000`)

## Running the App

### Option 1: Expo Go (Easiest for Testing)

1. **Start Expo:**
   ```bash
   npm start
   ```

2. **Scan QR code** with Expo Go app on your phone

### Option 2: Android Build

1. **Build APK:**
   ```bash
   expo build:android
   ```

2. **Or use EAS Build:**
   ```bash
   eas build --platform android
   ```

## Features

- ✅ Login with bus number and password
- ✅ Background GPS tracking (every 15 seconds)
- ✅ Alarm when tracking stops unexpectedly
- ✅ Works even when app is minimized
- ✅ Offline location queue (syncs when online)

## Important Notes

1. **Permissions:** App requires:
   - Location (Always)
   - Background Location
   - Notifications

2. **Battery:** Background tracking uses battery. Keep phone charged.

3. **Testing:** 
   - Use your computer's IP address for API_BASE_URL when testing on device
   - Make sure backend server is accessible from your phone's network

## Troubleshooting

- **Location not updating:** Check location permissions in phone settings
- **Alarm not working:** Check notification permissions
- **Can't connect to backend:** Verify API_BASE_URL and network connection


