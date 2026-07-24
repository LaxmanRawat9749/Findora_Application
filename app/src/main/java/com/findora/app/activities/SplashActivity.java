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

public class SplashActivity extends AppCompatActivity {

    private static final int SPLASH_DURATION = 2500;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        ImageView logo = findViewById(R.id.splash_logo);
        TextView name = findViewById(R.id.splash_name);
        TextView tagline = findViewById(R.id.splash_tagline);

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

        // Transition to Login
        new Handler().postDelayed(() -> {
            Intent intent = new Intent(SplashActivity.this, LoginActivity.class);
            startActivity(intent);
            finish();
            overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
        }, SPLASH_DURATION);
    }
}
