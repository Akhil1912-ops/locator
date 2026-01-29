import React from 'react';
import { StyleSheet, View, Text, TouchableOpacity, Alert } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function TrackingScreen({
  busNumber,
  isTracking,
  onStartTracking,
  onStopTracking,
  onLogout,
  trackingWarning,
  onOpenSettings,
  onOpenBatterySettings,
}) {
  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.busNumber}>Bus {busNumber}</Text>
        <TouchableOpacity onPress={onLogout} style={styles.logoutButton}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        <View style={styles.statusContainer}>
          <Ionicons
            name={isTracking ? 'location' : 'location-outline'}
            size={80}
            color={isTracking ? '#4CAF50' : '#ccc'}
          />
          <Text style={[styles.statusText, isTracking && styles.statusActive]}>
            {isTracking ? 'Tracking Active' : 'Tracking Stopped'}
          </Text>
          <Text style={styles.statusSubtext}>
            {isTracking
              ? 'Best accuracy • ~10 s or 25 m updates • works in background'
              : 'Tap Start to begin tracking'}
          </Text>
        </View>

        <View style={styles.buttonContainer}>
          {isTracking ? (
            <TouchableOpacity
              style={[styles.button, styles.stopButton]}
              onPress={() => {
                Alert.alert(
                  'Stop Tracking',
                  'Are you sure you want to stop tracking?',
                  [
                    { text: 'Cancel', style: 'cancel' },
                    { text: 'Stop', style: 'destructive', onPress: onStopTracking },
                  ]
                );
              }}
            >
              <Ionicons name="stop-circle" size={24} color="#fff" />
              <Text style={styles.buttonText}>Stop Tracking</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity
              style={[styles.button, styles.startButton]}
              onPress={onStartTracking}
            >
              <Ionicons name="play-circle" size={24} color="#fff" />
              <Text style={styles.buttonText}>Start Tracking</Text>
            </TouchableOpacity>
          )}
        </View>

        {trackingWarning ? (
          <View style={styles.warningBox}>
            <Text style={styles.warningTitle}>Warning</Text>
            <Text style={styles.warningText}>{trackingWarning}</Text>
            <TouchableOpacity style={styles.settingsButton} onPress={onOpenSettings}>
              <Text style={styles.settingsButtonText}>Open App Settings</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.settingsButton} onPress={onOpenBatterySettings}>
              <Text style={styles.settingsButtonText}>Battery Optimization</Text>
            </TouchableOpacity>
          </View>
        ) : null}

        <View style={styles.infoBox}>
          <Text style={styles.infoTitle}>Important:</Text>
          <Text style={styles.infoText}>
            • We use navigation-grade accuracy (like Google Maps){'\n'}
            • Keep the app running in background; do not force close{'\n'}
            • Disable battery optimization for best results{'\n'}
            • An alarm will sound if tracking stops unexpectedly
          </Text>
          <TouchableOpacity style={styles.settingsButton} onPress={onOpenSettings}>
            <Text style={styles.settingsButtonText}>Open App Settings</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.settingsButton} onPress={onOpenBatterySettings}>
            <Text style={styles.settingsButtonText}>Battery Optimization</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    paddingTop: 50,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  busNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  logoutButton: {
    padding: 8,
  },
  logoutText: {
    color: '#007AFF',
    fontSize: 16,
  },
  content: {
    flex: 1,
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statusContainer: {
    alignItems: 'center',
    marginBottom: 40,
  },
  statusText: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 20,
    color: '#999',
  },
  statusActive: {
    color: '#4CAF50',
  },
  statusSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 10,
    textAlign: 'center',
  },
  buttonContainer: {
    width: '100%',
    maxWidth: 300,
    marginBottom: 30,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 18,
    borderRadius: 12,
    gap: 10,
  },
  startButton: {
    backgroundColor: '#4CAF50',
  },
  stopButton: {
    backgroundColor: '#f44336',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoBox: {
    backgroundColor: '#fff3cd',
    padding: 15,
    borderRadius: 8,
    width: '100%',
    maxWidth: 300,
    borderWidth: 1,
    borderColor: '#ffc107',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#856404',
  },
  infoText: {
    fontSize: 14,
    color: '#856404',
    lineHeight: 20,
  },
  warningBox: {
    backgroundColor: '#fee2e2',
    padding: 15,
    borderRadius: 8,
    width: '100%',
    maxWidth: 300,
    borderWidth: 1,
    borderColor: '#fecaca',
    marginBottom: 20,
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 6,
    color: '#991b1b',
  },
  warningText: {
    fontSize: 14,
    color: '#7f1d1d',
    marginBottom: 10,
    lineHeight: 20,
  },
  settingsButton: {
    backgroundColor: '#1f2937',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginTop: 8,
  },
  settingsButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
});

