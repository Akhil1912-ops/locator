package com.bustracker.driver.location

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.Looper
import androidx.core.app.NotificationCompat
import com.bustracker.driver.MainActivity
import com.bustracker.driver.R
import com.bustracker.driver.data.api.ApiClient
import com.bustracker.driver.data.api.LocationUpdateRequest
import com.bustracker.driver.data.prefs.AppPreferences
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.Instant

private const val CHANNEL_ID = "bus_tracking"
private const val NOTIF_TRACKING = 1
private const val NOTIF_ALARM = 2
private const val INTERVAL_MS = 10_000L
private const val MIN_DISTANCE_M = 25f
private const val ALARM_CHECK_MS = 30_000L
private const val ALARM_THRESHOLD_MS = 60_000L

class LocationTrackerService : Service() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private lateinit var prefs: AppPreferences
    private var fusedClient: com.google.android.gms.location.FusedLocationProviderClient? = null
    private var locationCallback: LocationCallback? = null

    override fun onCreate() {
        super.onCreate()
        prefs = AppPreferences(this)
        fusedClient = LocationServices.getFusedLocationProviderClient(this)
        createChannels()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        scope.launch {
            val baseUrl = prefs.getApiBaseUrl()
            val token = prefs.getSessionToken()
            if (baseUrl.isNullOrBlank() || token.isNullOrBlank()) {
                stopSelf(startId)
                return@launch
            }
            ApiClient.setBaseUrl(baseUrl)
            val notif = buildTrackingNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                startForeground(NOTIF_TRACKING, notif, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
            } else {
                startForeground(NOTIF_TRACKING, notif)
            }
            startLocationUpdates(token)
            startAlarmCheckLoop()
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        stopLocationUpdates()
        scope.cancel()
        super.onDestroy()
    }

    private fun createChannels() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val m = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        m.createNotificationChannel(
            NotificationChannel(
                CHANNEL_ID,
                getString(R.string.notif_channel_tracking),
                NotificationManager.IMPORTANCE_LOW
            ).apply { setShowBadge(false) }
        )
        m.createNotificationChannel(
            NotificationChannel(
                "${CHANNEL_ID}_alarm",
                getString(R.string.notif_channel_alarm),
                NotificationManager.IMPORTANCE_HIGH
            ).apply { setShowBadge(true); enableVibration(true) }
        )
    }

    private fun buildTrackingNotification(): Notification {
        val open = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.notif_tracking_title))
            .setContentText(getString(R.string.notif_tracking_text))
            .setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setColor(0xFF2563EB.toInt())
            .setContentIntent(open)
            .setOngoing(true)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    private fun startLocationUpdates(token: String) {
        val client = fusedClient ?: return
        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, INTERVAL_MS)
            .setMinUpdateIntervalMillis(5000)
            .setMinUpdateDistanceMeters(MIN_DISTANCE_M)
            .setWaitForAccurateLocation(false)
            .setMaxUpdates(0)
            .build()

        val cb = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation ?: return
                scope.launch { sendAndRecord(token, result.lastLocation!!) }
            }
        }
        locationCallback = cb
        client.requestLocationUpdates(request, cb, Looper.getMainLooper())
    }

    private suspend fun sendAndRecord(token: String, location: android.location.Location) =
        withContext(Dispatchers.IO) {
            try {
                val api = ApiClient.api()
                val req = LocationUpdateRequest(
                    latitude = location.latitude,
                    longitude = location.longitude,
                    recordedAt = Instant.now().toString()
                )
                val res = api.sendLocation(token, req)
                if (res.isSuccessful) {
                    prefs.setLastLocationSentMs(System.currentTimeMillis())
                }
            } catch (_: Exception) { /* log? */ }
        }

    private fun stopLocationUpdates() {
        locationCallback?.let { fusedClient?.removeLocationUpdates(it) }
        locationCallback = null
    }

    private fun startAlarmCheckLoop() {
        scope.launch {
            while (isActive) {
                delay(ALARM_CHECK_MS)
                if (!isActive) break
                val tracking = prefs.isTracking()
                if (!tracking) continue
                val last = prefs.getLastLocationSentMs() ?: 0L
                val elapsed = System.currentTimeMillis() - last
                if (last > 0 && elapsed > ALARM_THRESHOLD_MS) {
                    showAlarmNotification()
                }
            }
        }
    }

    private fun showAlarmNotification() {
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val n = NotificationCompat.Builder(this, "${CHANNEL_ID}_alarm")
            .setContentTitle(getString(R.string.notif_alarm_title))
            .setContentText(getString(R.string.notif_alarm_text))
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(
                PendingIntent.getActivity(
                    this, 0,
                    Intent(this, MainActivity::class.java),
                    PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
            )
            .build()
        nm.notify(NOTIF_ALARM, n)
    }

    companion object {
        fun start(context: Context) {
            val i = Intent(context, LocationTrackerService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(i)
            } else {
                context.startService(i)
            }
        }

        fun stop(context: Context) {
            context.stopService(Intent(context, LocationTrackerService::class.java))
        }
    }
}
