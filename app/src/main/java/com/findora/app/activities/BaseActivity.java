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
        setRequestedOrientation(android.content.pm.ActivityInfo.SCREEN_ORIENTATION_PORTRAIT);
        super.onCreate(savedInstanceState);

        baseSessionManager = new SessionManager(this);

        Log.i(TAG, "Current Activity starting: " + this.getClass().getSimpleName());
        Log.i(TAG, "SessionManager.isLoggedIn(): " + baseSessionManager.isLoggedIn());

        // Perform strict validation check on activity launch
        if (!baseSessionManager.checkAndRequireSession(this)) {
            Log.w(TAG, "Unauthorized access detected in " + this.getClass().getSimpleName() + " -> Redirecting to LoginActivity");
            finish();
            return;
        }

        getWindow().setBackgroundDrawableResource(com.findora.app.R.color.screen_background);
        applySeamlessTransition();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (baseSessionManager != null && !baseSessionManager.checkAndRequireSession(this)) {
            Log.w(TAG, "Session expired or invalid on resume in " + this.getClass().getSimpleName() + " -> Redirecting to LoginActivity");
            finish();
            return;
        }
        applySeamlessTransition();
    }

    @Override
    public void recreate() {
        super.recreate();
        applySeamlessTransition();
    }

    @Override
    protected void onPause() {
        super.onPause();
        applySeamlessTransition();
    }

    @Override
    public void finish() {
        super.finish();
        applySeamlessTransition();
    }

    public void applySeamlessTransition() {
        if (android.os.Build.VERSION.SDK_INT >= 34) {
            overrideActivityTransition(OVERRIDE_TRANSITION_OPEN, 0, 0);
            overrideActivityTransition(OVERRIDE_TRANSITION_CLOSE, 0, 0);
        } else {
            overridePendingTransition(0, 0);
        }
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
