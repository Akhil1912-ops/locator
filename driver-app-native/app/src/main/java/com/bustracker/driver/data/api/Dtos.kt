package com.bustracker.driver.data.api

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    @SerializedName("bus_number") val busNumber: String,
    @SerializedName("password") val password: String,
)

data class LoginResponse(
    @SerializedName("session_token") val sessionToken: String,
    @SerializedName("expires_at") val expiresAt: String,
)

data class LocationUpdateRequest(
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("recorded_at") val recordedAt: String, // ISO-8601
)
