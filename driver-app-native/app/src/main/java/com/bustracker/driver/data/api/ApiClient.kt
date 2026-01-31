package com.bustracker.driver.data.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {

    private val logging = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttp = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .addInterceptor(logging)
        .build()

    private var retrofit: Retrofit? = null

    fun setBaseUrl(baseUrl: String) {
        var normalized = baseUrl.trim().removeSuffix("/")
        if (!normalized.contains("://")) normalized = "http://$normalized"
        if (!normalized.endsWith("/")) normalized += "/"
        retrofit = Retrofit.Builder()
            .baseUrl(normalized)
            .client(okHttp)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    fun api(): DriverApi {
        return retrofit?.create(DriverApi::class.java)
            ?: throw IllegalStateException("API base URL not set. Call setBaseUrl first.")
    }
}
