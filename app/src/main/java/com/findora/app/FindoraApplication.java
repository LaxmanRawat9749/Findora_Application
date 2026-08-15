package com.findora.app;

import android.app.Application;
import android.util.Log;

import com.findora.app.utils.SessionManager;

/**
 * Main Application class.
 * Enforces the policy that a login session only lives as long as the application process.
 */
public class FindoraApplication extends Application {

    private static final String TAG = "FindoraApplication";

    @Override
    public void onCreate() {
        super.onCreate();

        Log.i(TAG, "Application process created. Clearing any previous persistent session.");

        // Clear the session whenever the app process starts from scratch.
        // This ensures the user must log in again on a fresh launch or after
        // the app was killed in the background, fulfilling the process-bound
        // session requirement without rewriting the existing SharedPreferences architecture.
        SessionManager sessionManager = new SessionManager(this);
        
        // Apply saved theme immediately
        androidx.appcompat.app.AppCompatDelegate.setDefaultNightMode(sessionManager.getThemeMode());
        
        sessionManager.logout();
    }
}
