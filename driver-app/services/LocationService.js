import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { sendLocation } from './ApiService';

let locationInterval = null;
let lastLocationSent = null;

export const startLocationTracking = async (taskName) => {
  try {
    // Start background location updates
    await Location.startLocationUpdatesAsync(taskName, {
      accuracy: Location.Accuracy.Balanced,
      timeInterval: 15000, // 15 seconds
      distanceInterval: 0,
      foregroundService: {
        notificationTitle: 'Bus Tracking Active',
        notificationBody: 'Your location is being tracked',
        notificationColor: '#4CAF50',
      },
      pausesUpdatesAutomatically: false,
      activityType: Location.ActivityType.AutomotiveNavigation,
    });

    // Also set up foreground tracking as backup
    startForegroundTracking();

    return true;
  } catch (error) {
    console.error('Error starting location tracking:', error);
    throw error;
  }
};

const startForegroundTracking = async () => {
  // Clear any existing interval
  if (locationInterval) {
    clearInterval(locationInterval);
  }

  // Send location every 15 seconds
  locationInterval = setInterval(async () => {
    try {
      const { status } = await Location.getForegroundPermissionsAsync();
      if (status === 'granted') {
        const location = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Balanced,
        });

        const sessionToken = await AsyncStorage.getItem('sessionToken');
        if (sessionToken) {
          await sendLocation(
            sessionToken,
            location.coords.latitude,
            location.coords.longitude
          );
          lastLocationSent = Date.now();
          await AsyncStorage.setItem('lastLocationSent', lastLocationSent.toString());
        }
      }
    } catch (error) {
      console.error('Error in foreground tracking:', error);
    }
  }, 15000); // 15 seconds
};

export const stopLocationTracking = async (taskName) => {
  try {
    await Location.stopLocationUpdatesAsync(taskName);
    
    // Clear foreground tracking
    if (locationInterval) {
      clearInterval(locationInterval);
      locationInterval = null;
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


