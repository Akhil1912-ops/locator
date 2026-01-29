package com.bustracker.driver.data.api

import retrofit2.Response
import retrofit2.http.Body
import com.google.gson.annotations.SerializedName
import retrofit2.http.Header
import retrofit2.http.POST

interface DriverApi {

    @POST("auth/driver/login")
    suspend fun login(@Body req: LoginRequest): Response<LoginResponse>

    @POST("driver/location")
    suspend fun sendLocation(
        @Header("X-Session-Token") token: String,
        @Body req: LocationUpdateRequest,
    ): Response<LocationResponse>
}

data class LocationResponse(
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("recorded_at") val recordedAt: String,
    @SerializedName("last_seen_seconds") val lastSeenSeconds: Int,
    @SerializedName("running_delay_minutes") val runningDelayMinutes: Int,
    @SerializedName("status") val status: String,
    @SerializedName("current_stop") val currentStop: String?,
    @SerializedName("next_stop") val nextStop: String?,
)
