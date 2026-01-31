package com.bustracker.driver.ui.login

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.bustracker.driver.data.api.ApiClient
import com.bustracker.driver.data.api.LoginRequest
import com.bustracker.driver.data.prefs.AppPreferences
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class LoginUiState(
    val busNumber: String = "",
    val password: String = "",
    val apiBaseUrl: String = "",
    val loading: Boolean = false,
    val error: String? = null,
)

class LoginViewModel(application: Application) : AndroidViewModel(application) {

    private val prefs = AppPreferences(application)

    private val _state = MutableStateFlow(LoginUiState())
    val state: StateFlow<LoginUiState> = _state.asStateFlow()

    private val _navigateToTracking = MutableSharedFlow<Unit>()
    val navigateToTracking = _navigateToTracking.asSharedFlow()

    init {
        viewModelScope.launch {
            val url = prefs.getApiBaseUrl() ?: DEFAULT_BASE_URL
            val bus = prefs.getBusNumber() ?: ""
            _state.value = _state.value.copy(apiBaseUrl = url, busNumber = bus)
        }
    }

    fun updateBusNumber(s: String) { _state.value = _state.value.copy(busNumber = s, error = null) }
    fun updatePassword(s: String) { _state.value = _state.value.copy(password = s, error = null) }
    fun updateApiBaseUrl(s: String) { _state.value = _state.value.copy(apiBaseUrl = s, error = null) }

    fun saveBaseUrlAndLogin() {
        val url = _state.value.apiBaseUrl.trim()
        if (url.isBlank()) {
            _state.value = _state.value.copy(error = "Enter server URL")
            return
        }
        viewModelScope.launch {
            prefs.setApiBaseUrl(url)
            _state.value = _state.value.copy(apiBaseUrl = url)
            login()
        }
    }

    fun login() {
        val bus = _state.value.busNumber
        val pass = _state.value.password
        val url = _state.value.apiBaseUrl.trim().ifBlank { DEFAULT_BASE_URL }
        if (bus.isBlank() || pass.isBlank()) {
            _state.value = _state.value.copy(error = "Enter bus number and password")
            return
        }
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            try {
                prefs.setApiBaseUrl(url)
                ApiClient.setBaseUrl(url)
                val res = ApiClient.api().login(LoginRequest(busNumber = bus, password = pass))
                if (res.isSuccessful) {
                    val body = res.body()!!
                    prefs.setLoggedIn(body.sessionToken, bus)
                    _state.value = _state.value.copy(loading = false, error = null)
                    _navigateToTracking.emit(Unit)
                } else {
                    _state.value = _state.value.copy(loading = false, error = "Invalid credentials")
                }
            } catch (e: Exception) {
                _state.value = _state.value.copy(
                    loading = false,
                    error = e.message ?: "Network error"
                )
            }
        }
    }

    fun clearError() { _state.value = _state.value.copy(error = null) }

    companion object {
        private const val DEFAULT_BASE_URL = "http://10.0.2.2:8000"
    }
}
