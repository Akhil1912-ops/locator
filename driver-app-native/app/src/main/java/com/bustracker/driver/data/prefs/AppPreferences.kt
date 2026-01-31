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

class AppPreferences(context: Context) {

    private val ctx = context.applicationContext

    private object Keys {
        val sessionToken = stringPreferencesKey("session_token")
        val busNumber = stringPreferencesKey("bus_number")
        val apiBaseUrl = stringPreferencesKey("api_base_url")
        val isTracking = stringPreferencesKey("is_tracking")
        val lastLocationSentMs = longPreferencesKey("last_location_sent_ms")
        val lastSendError = stringPreferencesKey("last_send_error")
    }

    val sessionToken: Flow<String?> = ctx.dataStore.data.map { it[Keys.sessionToken] }
    val busNumber: Flow<String?> = ctx.dataStore.data.map { it[Keys.busNumber] }
    val apiBaseUrl: Flow<String?> = ctx.dataStore.data.map { it[Keys.apiBaseUrl] }

    suspend fun setLoggedIn(token: String, bus: String) {
        ctx.dataStore.edit { prefs ->
            prefs[Keys.sessionToken] = token
            prefs[Keys.busNumber] = bus
        }
    }

    suspend fun clearSession() {
        ctx.dataStore.edit { prefs ->
            prefs.remove(Keys.sessionToken)
            prefs.remove(Keys.busNumber)
            prefs[Keys.isTracking] = "false"
        }
    }

    suspend fun setApiBaseUrl(url: String) {
        ctx.dataStore.edit { it[Keys.apiBaseUrl] = url }
    }

    suspend fun getApiBaseUrl(): String? =
        ctx.dataStore.data.map { it[Keys.apiBaseUrl] }.first()

    suspend fun getSessionToken(): String? =
        ctx.dataStore.data.map { it[Keys.sessionToken] }.first()

    suspend fun getBusNumber(): String? =
        ctx.dataStore.data.map { it[Keys.busNumber] }.first()

    suspend fun setTracking(active: Boolean) {
        ctx.dataStore.edit { it[Keys.isTracking] = active.toString() }
    }

    suspend fun isTracking(): Boolean =
        ctx.dataStore.data.map { it[Keys.isTracking] == "true" }.first()

    suspend fun setLastLocationSentMs(ms: Long) {
        ctx.dataStore.edit { it[Keys.lastLocationSentMs] = ms }
    }

    suspend fun getLastLocationSentMs(): Long? {
        val v = ctx.dataStore.data.map { it[Keys.lastLocationSentMs] }.first()
        return if (v != null && v > 0) v else null
    }

    suspend fun setLastSendError(error: String?) {
        ctx.dataStore.edit { it[Keys.lastSendError] = error ?: "" }
    }

    suspend fun getLastSendError(): String? {
        val v = ctx.dataStore.data.map { it[Keys.lastSendError] }.first()
        return if (v.isNullOrBlank()) null else v
    }
}
