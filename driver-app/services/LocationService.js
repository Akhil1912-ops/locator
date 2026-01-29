import { Platform } from 'react-native';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sendLocation } from './ApiService';

const ACCURACY = Location.Accuracy.BestForNavigation;
const TIME_INTERVAL_MS = 10000;  // 10 seconds
const DISTANCE_INTERVAL_M = 25;  // 25 meters

let foregroundSubscription = null;

/**
 * Call after successfully sending a location to the backend.
 * Persists lastLocationSent for "tracking stopped?" checks and alarms.
 */
export const recordLocationSent = async () => {
  const now = Date.now();
  try {
    await AsyncStorage.setItem('lastLocationSent', now.toString());
  } catch (e) {
    console.warn('Failed to persist lastLocationSent:', e);
  }
};

async function sendAndRecord(sessionToken, latitude, longitude) {
  await sendLocation(sessionToken, latitude, longitude);
  await recordLocationSent();
}

export const startLocationTracking = async (taskName) => {
  try {
    // Android: ask user to enable high-accuracy mode (Wi‑Fi + cell + GPS)
    if (Platform.OS === 'android') {
      try {
        await Location.enableNetworkProviderAsync();
      } catch (e) {
        console.warn('enableNetworkProviderAsync failed (user may have dismissed):', e?.message);
      }
    }

    await Location.startLocationUpdatesAsync(taskName, {
      accuracy: ACCURACY,
      timeInterval: TIME_INTERVAL_MS,
      distanceInterval: DISTANCE_INTERVAL_M,
      deferredUpdatesDistance: 0,
      deferredUpdatesInterval: 0,
      foregroundService: {
        notificationTitle: 'Bus Tracking Active',
        notificationBody: 'Your location is being sent with best available accuracy.',
        notificationColor: '#4CAF50',
      },
      pausesUpdatesAutomatically: false,
      activityType: Location.ActivityType.AutomotiveNavigation,
    });

    await startForegroundTracking();
    return true;
  } catch (error) {
    console.error('Error starting location tracking:', error);
    throw error;
  }
};

async function startForegroundTracking() {
  if (foregroundSubscription) {
    foregroundSubscription.remove();
    foregroundSubscription = null;
  }

  const callback = async (location) => {
    try {
      const { status } = await Location.getForegroundPermissionsAsync();
      if (status !== 'granted') return;

      const sessionToken = await AsyncStorage.getItem('sessionToken');
      if (!sessionToken) return;

      const { latitude, longitude } = location.coords;
      await sendAndRecord(sessionToken, latitude, longitude);
    } catch (error) {
      console.error('Foreground location send error:', error);
    }
  };

  const options = {
    accuracy: ACCURACY,
    timeInterval: TIME_INTERVAL_MS,
    distanceInterval: DISTANCE_INTERVAL_M,
  };

  try {
    const sub = await Location.watchPositionAsync(options, callback, (err) => {
      console.warn('watchPositionAsync error:', err);
    });
    foregroundSubscription = sub;
  } catch (e) {
    console.error('Failed to start watchPositionAsync:', e);
  }
}

export const stopLocationTracking = async (taskName) => {
  try {
    await Location.stopLocationUpdatesAsync(taskName);

    if (foregroundSubscription) {
      foregroundSubscription.remove();
      foregroundSubscription = null;
    }

    return true;
  } catch (error) {
    console.error('Error stopping location tracking:', error);
    throw error;
  }
};

export const checkTrackingStatus = async () => {
  try {
    const isTracking = await AsyncStorage.getItem('isTracking');
    return isTracking === 'true';
  } catch (error) {
    return false;
  }
};

export const getLastLocationSentTime = async () => {
  try {
    const timestamp = await AsyncStorage.getItem('lastLocationSent');
    return timestamp ? parseInt(timestamp, 10) : null;
  } catch (error) {
    return null;
  }
};
