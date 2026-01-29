import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, Alert, StatusBar, Linking, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import * as Notifications from 'expo-notifications';
import * as IntentLauncher from 'expo-intent-launcher';
import { startLocationTracking, stopLocationTracking, checkTrackingStatus, getLastLocationSentTime, recordLocationSent } from './services/LocationService';
import { loginDriver, sendLocation, setApiBaseUrl, getApiBaseUrl } from './services/ApiService';
import { setupAlarmSystem, stopAlarm } from './services/AlarmService';
import TrackingScreen from './screens/TrackingScreen';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

const LOCATION_TASK_NAME = 'background-location-task';

// Background location task
TaskManager.defineTask(LOCATION_TASK_NAME, ({ data, error }) => {
  if (error) {
    console.error('Location task error:', error);
    return;
  }
  if (data) {
    const { locations } = data;
    const location = locations[locations.length - 1];
    // Send location to backend
    sendLocationToBackend(location);
  }
});

async function sendLocationToBackend(location) {
  try {
    const sessionToken = await AsyncStorage.getItem('sessionToken');
    if (sessionToken) {
      await sendLocation(
        sessionToken,
        location.coords.latitude,
        location.coords.longitude
      );
      await recordLocationSent();
    }
  } catch (error) {
    console.error('Error sending location:', error);
  }
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isTracking, setIsTracking] = useState(false);
  const [busNumber, setBusNumber] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiBaseUrl, setApiBaseUrlState] = useState('');
  const [apiBaseUrlInput, setApiBaseUrlInput] = useState('');
  const [trackingWarning, setTrackingWarning] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    checkLoginStatus();
    loadApiBaseUrl();
    setupAlarmSystem();
  }, []);

  useEffect(() => {
    let intervalId = null;
    if (isLoggedIn) {
      intervalId = setInterval(async () => {
        if (!isTracking) {
          setTrackingWarning('');
          return;
        }
        const lastSent = await getLastLocationSentTime();
        if (!lastSent) {
          setTrackingWarning('No location updates sent yet. Check permissions and keep the app open.');
          return;
        }
        const ageMs = Date.now() - lastSent;
        if (ageMs > 60000) {
          setTrackingWarning('Location updates are delayed. Disable battery optimization and keep the app open.');
        } else {
          setTrackingWarning('');
        }
      }, 15000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isLoggedIn, isTracking]);

  const loadApiBaseUrl = async () => {
    const storedUrl = await AsyncStorage.getItem('apiBaseUrl');
    if (storedUrl) {
      setApiBaseUrl(storedUrl);
      setApiBaseUrlState(storedUrl);
      setApiBaseUrlInput(storedUrl);
      return;
    }
    const currentUrl = getApiBaseUrl();
    setApiBaseUrlState(currentUrl);
    setApiBaseUrlInput(currentUrl);
  };

  const checkLoginStatus = async () => {
    const token = await AsyncStorage.getItem('sessionToken');
    const savedBusNumber = await AsyncStorage.getItem('busNumber');
    if (token && savedBusNumber) {
      setIsLoggedIn(true);
      setBusNumber(savedBusNumber);
      // Check if tracking is active
      const tracking = await checkTrackingStatus();
      setIsTracking(tracking);
    }
  };

  const handleLogin = async () => {
    if (!busNumber || !password) {
      Alert.alert('Error', 'Please enter bus number and password');
      return;
    }

    setLoading(true);
    try {
      const response = await loginDriver(busNumber, password);
      if (response.session_token) {
        await AsyncStorage.setItem('sessionToken', response.session_token);
        await AsyncStorage.setItem('busNumber', busNumber);
        setIsLoggedIn(true);
        Alert.alert('Success', 'Logged in successfully');
        // Start tracking automatically after login
        await startTracking();
      }
    } catch (error) {
      Alert.alert('Login Failed', error.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const startTracking = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission Denied', 'Location permission is required');
        return;
      }

      const backgroundStatus = await Location.requestBackgroundPermissionsAsync();
      if (backgroundStatus.status !== 'granted') {
        Alert.alert('Permission Denied', 'Background location permission is required');
        return;
      }

      await startLocationTracking(LOCATION_TASK_NAME);
      setIsTracking(true);
      await AsyncStorage.setItem('isTracking', 'true');
      
      // Setup alarm monitoring
      setupAlarmSystem();
      
      Alert.alert('Tracking Started', 'Your location is being tracked');
    } catch (error) {
      Alert.alert('Error', 'Failed to start tracking: ' + error.message);
    }
  };

  const stopTracking = async () => {
    try {
      await stopLocationTracking(LOCATION_TASK_NAME);
      setIsTracking(false);
      await AsyncStorage.setItem('isTracking', 'false');
      stopAlarm();
      Alert.alert('Tracking Stopped', 'Location tracking has been stopped');
    } catch (error) {
      Alert.alert('Error', 'Failed to stop tracking: ' + error.message);
    }
  };

  const handleLogout = async () => {
    await stopTracking();
    await AsyncStorage.removeItem('sessionToken');
    await AsyncStorage.removeItem('busNumber');
    await AsyncStorage.removeItem('isTracking');
    setIsLoggedIn(false);
    setBusNumber('');
    setPassword('');
  };

  const handleSaveApiBaseUrl = async () => {
    const trimmed = apiBaseUrlInput.trim();
    if (!trimmed) {
      Alert.alert('Invalid URL', 'Please enter a server URL');
      return;
    }
    setApiBaseUrl(trimmed);
    await AsyncStorage.setItem('apiBaseUrl', trimmed);
    setApiBaseUrlState(trimmed);
    Alert.alert('Saved', 'Server URL updated');
  };

  const handleOpenAppSettings = async () => {
    try {
      await Linking.openSettings();
    } catch (error) {
      Alert.alert('Error', 'Could not open app settings');
    }
  };

  const handleOpenBatterySettings = async () => {
    if (Platform.OS !== 'android') {
      Alert.alert('Not supported', 'Battery optimization settings are only available on Android.');
      return;
    }
    try {
      await IntentLauncher.startActivityAsync(
        IntentLauncher.ActivityAction.IGNORE_BATTERY_OPTIMIZATION_SETTINGS
      );
    } catch (error) {
      Alert.alert('Error', 'Could not open battery optimization settings');
    }
  };

  if (isLoggedIn) {
    return (
      <TrackingScreen
        busNumber={busNumber}
        isTracking={isTracking}
        onStartTracking={startTracking}
        onStopTracking={stopTracking}
        onLogout={handleLogout}
        trackingWarning={trackingWarning}
        onOpenSettings={handleOpenAppSettings}
        onOpenBatterySettings={handleOpenBatterySettings}
      />
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <Text style={styles.title}>Bus Driver Tracker</Text>
      <Text style={styles.subtitle}>Login to start tracking</Text>
      
      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Bus Number"
          value={busNumber}
          onChangeText={setBusNumber}
          keyboardType="numeric"
          autoCapitalize="none"
        />
        
        <View style={styles.passwordRow}>
          <TextInput
            style={[styles.input, styles.passwordInput]}
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            autoCapitalize="none"
          />
          <TouchableOpacity
            style={styles.passwordToggle}
            onPress={() => setShowPassword(prev => !prev)}
            accessibilityLabel={showPassword ? 'Hide password' : 'Show password'}
          >
            <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} color="#374151" />
          </TouchableOpacity>
        </View>

        <Text style={styles.fieldLabel}>Server URL</Text>
        <TextInput
          style={styles.input}
          placeholder="http://192.168.1.100:8000"
          value={apiBaseUrlInput}
          onChangeText={setApiBaseUrlInput}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="url"
        />
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton]}
          onPress={handleSaveApiBaseUrl}
          disabled={loading}
        >
          <Text style={styles.buttonText}>Save Server URL</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? 'Logging in...' : 'Login'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 40,
  },
  form: {
    width: '100%',
    maxWidth: 400,
  },
  fieldLabel: {
    fontSize: 14,
    color: '#555',
    marginBottom: 6,
    marginTop: 6,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 15,
    marginBottom: 15,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  passwordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  passwordInput: {
    flex: 1,
    marginBottom: 0,
  },
  passwordToggle: {
    marginLeft: 10,
    backgroundColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 15,
    alignItems: 'center',
    marginTop: 10,
  },
  secondaryButton: {
    backgroundColor: '#6b7280',
    marginTop: 0,
    marginBottom: 10,
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});


