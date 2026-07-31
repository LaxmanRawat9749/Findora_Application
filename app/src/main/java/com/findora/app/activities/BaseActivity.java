package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.findora.app.utils.SessionManager;

/**
 * Base Activity for all protected screens in the application.
 * Ensures that no unauthenticated user can ever access a protected screen,
 * completely preventing layout inflation or API calls if the session is invalid.
 */
public class BaseActivity extends AppCompatActivity {

    private static final String TAG = "AuthAudit";
    protected SessionManager baseSessionManager;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        // We log the current activity attempting to start
        Log.i(TAG, "Current Activity starting: " + this.getClass().getSimpleName());

        baseSessionManager = new SessionManager(this);

        Log.i(TAG, "SessionManager.isLoggedIn(): " + baseSessionManager.isLoggedIn());
        Log.i(TAG, "Token value (truncated): " + getTruncatedToken(baseSessionManager.getToken()));
        Log.i(TAG, "Username: " + baseSessionManager.getUsername());
        Log.i(TAG, "SharedPreferences values - LastActivity: " + baseSessionManager.getLastActivity());

        // Perform the strict validation check BEFORE super.onCreate() and setContentView()
        if (!baseSessionManager.checkAndRequireSession(this)) {
            Log.w(TAG, "Authentication bypassed or invalid session detected in " + this.getClass().getSimpleName());
            Log.w(TAG, "Navigation decision: Redirecting to LoginActivity and finishing.");
            
            // The activity is finishing; do not proceed with the lifecycle.
            super.onCreate(savedInstanceState);
            finish();
            return;
        }

        Log.i(TAG, "Navigation decision: Session valid. Proceeding with " + this.getClass().getSimpleName());
        super.onCreate(savedInstanceState);
    }

    private String getTruncatedToken(String token) {
        if (token == null || token.isEmpty()) {
            return "NULL_OR_EMPTY";
        }
        if (token.length() > 10) {
            return token.substring(0, 10) + "...";
        }
        return token;
    }
}
