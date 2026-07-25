package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.animation.AccelerateDecelerateInterpolator;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.view.animation.ScaleAnimation;
import android.view.animation.TranslateAnimation;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.findora.app.R;
import com.findora.app.utils.SessionManager;

public class SplashActivity extends AppCompatActivity {

    private static final int SPLASH_DURATION = 2500;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        ImageView logo    = findViewById(R.id.splash_logo);
        TextView  name    = findViewById(R.id.splash_name);
        TextView  tagline = findViewById(R.id.splash_tagline);

        // Logo Scale and Fade In
        ScaleAnimation scaleAnim = new ScaleAnimation(0.5f, 1.0f, 0.5f, 1.0f,
                Animation.RELATIVE_TO_SELF, 0.5f, Animation.RELATIVE_TO_SELF, 0.5f);
        scaleAnim.setDuration(1000);
        scaleAnim.setInterpolator(new AccelerateDecelerateInterpolator());

        AlphaAnimation fadeIn = new AlphaAnimation(0.0f, 1.0f);
        fadeIn.setDuration(1000);

        logo.startAnimation(scaleAnim);
        logo.startAnimation(fadeIn);

        // Text Animations
        new Handler().postDelayed(() -> {
            name.setVisibility(View.VISIBLE);
            tagline.setVisibility(View.VISIBLE);

            TranslateAnimation moveUp = new TranslateAnimation(0, 0, 50, 0);
            moveUp.setDuration(800);
            moveUp.setInterpolator(new AccelerateDecelerateInterpolator());

            AlphaAnimation textFadeIn = new AlphaAnimation(0.0f, 1.0f);
            textFadeIn.setDuration(800);

            name.startAnimation(moveUp);
            name.startAnimation(textFadeIn);
            name.setAlpha(1.0f);

            tagline.startAnimation(moveUp);
            tagline.startAnimation(textFadeIn);
            tagline.setAlpha(1.0f);
        }, 500);

        // Navigate based on session validity — this is the single authoritative
        // routing decision point for the application on startup.
        new Handler().postDelayed(() -> {
            SessionManager sessionManager = new SessionManager(SplashActivity.this);

            Class<?> destination;
            if (sessionManager.isSessionValid()) {
                // A valid, non-expired session exists — go directly to Home
                destination = HomeActivity.class;
            } else {
                // No valid session (first launch, logout, expired token, stale
                // SharedPreferences from another user, etc.) — go to Login.
                // Clear any stale data so the next user starts with a clean slate.
                sessionManager.logout();
                destination = LoginActivity.class;
            }

            Intent intent = new Intent(SplashActivity.this, destination);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
            startActivity(intent);
            finish();
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
        }, SPLASH_DURATION);
    }
}
