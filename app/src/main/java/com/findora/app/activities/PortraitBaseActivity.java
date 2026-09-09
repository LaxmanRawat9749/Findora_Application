package com.findora.app.activities;

import android.content.pm.ActivityInfo;
import android.content.res.Configuration;
import android.os.Build;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.findora.app.R;

/**
 * Common portrait base activity for all screens across the Findora application.
 * Ensures consistent portrait orientation, intercepts configuration changes to
 * prevent unwanted Activity destruction/recreation in emulators (like BlueStacks)
 * and physical devices, and provides seamless zero-flicker window transitions.
 */
public abstract class PortraitBaseActivity extends AppCompatActivity {

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        // Enforce portrait orientation only if not already requested to prevent redundant window manager calls
        if (getRequestedOrientation() != ActivityInfo.SCREEN_ORIENTATION_PORTRAIT) {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        }
        super.onCreate(savedInstanceState);
        getWindow().setBackgroundDrawableResource(R.color.screen_background);
        applySeamlessTransition();
    }

    @Override
    protected void onResume() {
        super.onResume();
        // Restore portrait lock upon returning from external intents (Camera, Gallery, UCrop)
        if (getRequestedOrientation() != ActivityInfo.SCREEN_ORIENTATION_PORTRAIT) {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        }
    }

    @Override
    public void onConfigurationChanged(@NonNull Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        // Ensure orientation remains portrait when configuration changes (e.g. keyboard, window resize, focus change)
        if (getRequestedOrientation() != ActivityInfo.SCREEN_ORIENTATION_PORTRAIT) {
            setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        }
    }

    @Override
    public void recreate() {
        super.recreate();
        applySeamlessTransition();
    }

    @Override
    public void finish() {
        super.finish();
        applySeamlessTransition();
    }

    public void applySeamlessTransition() {
        if (Build.VERSION.SDK_INT >= 34) {
            overrideActivityTransition(OVERRIDE_TRANSITION_OPEN, 0, 0);
            overrideActivityTransition(OVERRIDE_TRANSITION_CLOSE, 0, 0);
        } else {
            overridePendingTransition(0, 0);
        }
    }
}
