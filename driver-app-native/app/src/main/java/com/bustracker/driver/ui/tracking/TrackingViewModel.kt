package com.bustracker.driver.ui.tracking

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.bustracker.driver.data.prefs.AppPreferences
import com.bustracker.driver.location.LocationTrackerService
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class TrackingUiState(
    val busNumber: String = "",
    val isTracking: Boolean = false,
    val sendError: String? = null,
)

class TrackingViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application
    private val prefs = AppPreferences(application)

    private val _state = MutableStateFlow(TrackingUiState())
    val state: StateFlow<TrackingUiState> = _state.asStateFlow()

    private val _navigateToLogin = MutableSharedFlow<Unit>()
    val navigateToLogin = _navigateToLogin.asSharedFlow()

    init {
        viewModelScope.launch { refreshState() }
    }

    fun startTracking() {
        viewModelScope.launch {
            LocationTrackerService.start(app)
            prefs.setTracking(true)
            _state.value = _state.value.copy(isTracking = true)
        }
    }

    fun stopTracking() {
        viewModelScope.launch {
            LocationTrackerService.stop(app)
            prefs.setTracking(false)
            prefs.setLastSendError(null)
            _state.value = _state.value.copy(isTracking = false, sendError = null)
        }
    }

    fun logout() {
        viewModelScope.launch {
            LocationTrackerService.stop(app)
            prefs.setTracking(false)
            prefs.clearSession()
            _state.value = _state.value.copy(isTracking = false)
            _navigateToLogin.emit(Unit)
        }
    }

    fun refreshState() {
        viewModelScope.launch {
            val bus = prefs.getBusNumber() ?: ""
            val tracking = prefs.isTracking()
            val err = if (tracking) prefs.getLastSendError() else null
            _state.value = _state.value.copy(busNumber = bus, isTracking = tracking, sendError = err)
        }
    }

    fun clearSendError() {
        viewModelScope.launch {
            prefs.setLastSendError(null)
            refreshState()
        }
    }
}
