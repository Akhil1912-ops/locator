package com.bustracker.driver

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.bustracker.driver.data.prefs.AppPreferences
import com.bustracker.driver.ui.login.LoginScreen
import com.bustracker.driver.ui.login.LoginViewModel
import com.bustracker.driver.ui.theme.BusDriverTheme
import com.bustracker.driver.ui.tracking.TrackingScreen
import com.bustracker.driver.ui.tracking.TrackingViewModel
import kotlinx.coroutines.flow.first

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            BusDriverTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.surface) {
                    var start by remember { mutableStateOf<String?>(null) }
                    LaunchedEffect(Unit) {
                        start = try {
                            val prefs = AppPreferences(this@MainActivity)
                            val token = prefs.sessionToken.first()
                            if (token.isNullOrBlank()) "login" else "tracking"
                        } catch (e: Exception) {
                            "login"
                        }
                    }
                    when (val s = start) {
                        null -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                            CircularProgressIndicator()
                        }
                        else -> AppNav(s)
                    }
                }
            }
        }
    }

    @Composable
    private fun AppNav(startDestination: String) {
        val nav = rememberNavController()
        NavHost(
            navController = nav,
            startDestination = startDestination,
        ) {
            composable("login") {
                val vm: LoginViewModel = viewModel()
                LoginScreen(viewModel = vm) {
                    nav.navigate("tracking") { popUpTo("login") { inclusive = true } }
                }
            }
            composable("tracking") {
                val vm: TrackingViewModel = viewModel()
                TrackingScreen(viewModel = vm) {
                    nav.navigate("login") { popUpTo("tracking") { inclusive = true } }
                }
            }
        }
    }
}
