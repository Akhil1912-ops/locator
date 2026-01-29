package com.bustracker.driver.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val Primary = Color(0xFF2563EB)
private val OnPrimary = Color.White
private val Surface = Color(0xFFFAFAFA)
private val OnSurface = Color(0xFF1A1A1A)
private val OnSurfaceVariant = Color(0xFF6B7280)
private val Outline = Color(0xFFE5E7EB)
private val Error = Color(0xFFDC2626)
private val Success = Color(0xFF16A34A)

private val lightScheme = lightColorScheme(
    primary = Primary,
    onPrimary = OnPrimary,
    surface = Surface,
    onSurface = OnSurface,
    onSurfaceVariant = OnSurfaceVariant,
    outline = Outline,
    error = Error,
    onError = Color.White,
)

@Composable
fun BusDriverTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    val scheme = lightScheme
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val w = (view.context as? Activity)?.window ?: return@SideEffect
            w.statusBarColor = Color.Transparent.toArgb()
            WindowCompat.getInsetsController(w, view).isAppearanceLightStatusBars = true
        }
    }
    MaterialTheme(
        colorScheme = scheme,
        typography = Typography,
        content = content,
    )
}

object ThemeColors {
    val success = Success
}
