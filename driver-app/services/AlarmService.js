import * as Notifications from 'expo-notifications';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getLastLocationSentTime } from './LocationService';

let alarmInterval = null;
let isAlarmActive = false;

// Configure notification sound
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export const setupAlarmSystem = async () => {
  // Request notification permissions
  const { status } = await Notifications.requestPermissionsAsync();
  if (status !== 'granted') {
    console.warn('Notification permission not granted');
    return;
  }

  // Clear any existing alarm check
  if (alarmInterval) {
    clearInterval(alarmInterval);
  }

  // Check every 10 seconds if tracking has stopped
  alarmInterval = setInterval(async () => {
    await checkTrackingStatus();
  }, 10000); // Check every 10 seconds
};

const checkTrackingStatus = async () => {
  try {
    const isTracking = await AsyncStorage.getItem('isTracking');
    const sessionToken = await AsyncStorage.getItem('sessionToken');
    
    // Only check if user is logged in and tracking should be active
    if (sessionToken && isTracking === 'true') {
      const lastSent = await getLastLocationSentTime();
      const now = Date.now();
      
      // If no location sent in last 45 seconds (30s + 15s buffer), trigger alarm
      if (lastSent && (now - lastSent) > 45000) {
        if (!isAlarmActive) {
          triggerAlarm();
        }
      } else if (lastSent && (now - lastSent) <= 45000) {
        // Tracking is working, stop alarm if active
        if (isAlarmActive) {
          stopAlarm();
        }
      }
    }
  } catch (error) {
    console.error('Error checking tracking status:', error);
  }
};

const triggerAlarm = async () => {
  if (isAlarmActive) return;
  
  isAlarmActive = true;
  
  // Send persistent notification with sound
  await Notifications.scheduleNotificationAsync({
    content: {
      title: '⚠️ Tracking Stopped!',
      body: 'Location tracking has stopped. Please restart the app.',
      sound: true,
      priority: Notifications.AndroidNotificationPriority.HIGH,
      vibrate: [0, 250, 250, 250],
    },
    trigger: {
      seconds: 1,
      repeats: true, // Repeat every second
    },
  });

  // Also schedule a repeating alarm notification
  await Notifications.scheduleNotificationAsync({
    content: {
      title: 'ALARM: Tracking Not Working',
      body: 'Your location is not being sent. Please check the app!',
      sound: true,
      priority: Notifications.AndroidNotificationPriority.MAX,
    },
    trigger: {
      seconds: 5,
      repeats: true,
    },
  });
};

export const stopAlarm = async () => {
  if (!isAlarmActive) return;
  
  isAlarmActive = false;
  
  // Cancel all notifications
  await Notifications.cancelAllScheduledNotificationsAsync();
};

export const clearAlarmInterval = () => {
  if (alarmInterval) {
    clearInterval(alarmInterval);
    alarmInterval = null;
  }
};


