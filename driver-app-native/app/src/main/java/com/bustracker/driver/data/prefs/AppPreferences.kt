package com.bustracker.driver.data.prefs

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "bus_driver_prefs")

class AppPreferences(private val context: Context) {

    private object Keys {
        val sessionToken = stringPreferencesKey("session_token")
        val busNumber = stringPreferencesKey("bus_number")
        val apiBaseUrl = stringPreferencesKey("api_base_url")
        val isTracking = stringPreferencesKey("is_tracking")
        val lastLocationSentMs = longPreferencesKey("last_location_sent_ms")
    }

    val sessionToken: Flow<String?> = context.dataStore.data.map { it[Keys.sessionToken] }
    val busNumber: Flow<String?> = context.dataStore.data.map { it[Keys.busNumber] }
    val apiBaseUrl: Flow<String?> = context.dataStore.data.map { it[Keys.apiBaseUrl] }

    suspend fun setLoggedIn(token: String, bus: String) {
        context.dataStore.edit { prefs ->
            prefs[Keys.sessionToken] = token
            prefs[Keys.busNumber] = bus
        }
    }

    suspend fun clearSession() {
        context.dataStore.edit { prefs ->
            prefs.remove(Keys.sessionToken)
            prefs.remove(Keys.busNumber)
            prefs[Keys.isTracking] = "false"
        }
    }

    suspend fun setApiBaseUrl(url: String) {
        context.dataStore.edit { it[Keys.apiBaseUrl] = url }
    }

    suspend fun getApiBaseUrl(): String? =
        context.dataStore.data.map { it[Keys.apiBaseUrl] }.first()

    suspend fun getSessionToken(): String? =
        context.dataStore.data.map { it[Keys.sessionToken] }.first()

    suspend fun getBusNumber(): String? =
        context.dataStore.data.map { it[Keys.busNumber] }.first()

    suspend fun setTracking(active: Boolean) {
        context.dataStore.edit { it[Keys.isTracking] = active.toString() }
    }

    suspend fun isTracking(): Boolean =
        context.dataStore.data.map { it[Keys.isTracking] == "true" }.first()

    suspend fun setLastLocationSentMs(ms: Long) {
        context.dataStore.edit { it[Keys.lastLocationSentMs] = ms }
    }

    suspend fun getLastLocationSentMs(): Long? {
        val v = context.dataStore.data.map { it[Keys.lastLocationSentMs] }.first()
        return if (v != null && v > 0) v else null
    }
}
