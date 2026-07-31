package com.findora.app.activities;

import android.animation.AnimatorSet;
import android.animation.ObjectAnimator;
import android.animation.PropertyValuesHolder;
import android.animation.ValueAnimator;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.WindowManager;
import android.view.animation.DecelerateInterpolator;
import android.widget.LinearLayout;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.R;
import com.findora.app.utils.SessionManager;

public class SplashActivity extends AppCompatActivity {

    LinearLayout layoutLogo;
    View dot1, dot2, dot3;
    Handler handler = new Handler();
    SessionManager sessionManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_splash);

        if (getSupportActionBar() != null) {
            getSupportActionBar().hide();
        }

        getWindow().setFlags(
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
            WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS
        );

        sessionManager = new SessionManager(this);

        layoutLogo = findViewById(R.id.layoutLogo);
        dot1 = findViewById(R.id.dot1);
        dot2 = findViewById(R.id.dot2);
        dot3 = findViewById(R.id.dot3);

        startAnimations();

        handler.postDelayed(this::navigateNext, 3000);
    }

    private void startAnimations() {
        handler.postDelayed(() -> {
            layoutLogo.animate()
                .alpha(1f)
                .translationY(0f)
                .setDuration(600)
                .setInterpolator(new DecelerateInterpolator())
                .start();
            layoutLogo.setTranslationY(30f); // start 30px below
        }, 200);

        View[] dots = {dot1, dot2, dot3};
        for (int i = 0; i < 3; i++) {
            final int index = i;
            handler.postDelayed(() -> {
                animateDot(dots[index]);
            }, 800 + (index * 150));
        }
    }

    private void animateDot(View dot) {
        ObjectAnimator pulseAlpha = ObjectAnimator.ofFloat(dot, "alpha", 0.3f, 1f, 0.3f);
        ObjectAnimator pulseScale = ObjectAnimator.ofPropertyValuesHolder(dot,
            PropertyValuesHolder.ofFloat("scaleX", 0.7f, 1f, 0.7f),
            PropertyValuesHolder.ofFloat("scaleY", 0.7f, 1f, 0.7f)
        );
        AnimatorSet set = new AnimatorSet();
        set.playTogether(pulseAlpha, pulseScale);
        set.setDuration(800);
        pulseAlpha.setRepeatCount(ValueAnimator.INFINITE);
        pulseScale.setRepeatCount(ValueAnimator.INFINITE);
        set.start();
    }

    private void navigateNext() {
        Intent intent;

        if (sessionManager.isSessionValid() && !sessionManager.isSessionExpired()) {
            // Session is active and within the timeout — go straight to Dashboard
            sessionManager.updateLastActivity();
            intent = new Intent(this, HomeActivity.class);
        } else {
            // No valid session, or session has expired — require login
            sessionManager.clearExpiredSession();
            intent = new Intent(this, LoginActivity.class);
        }

        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        overridePendingTransition(R.anim.fade_in_slow, R.anim.fade_out_slow);
        finish();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        handler.removeCallbacksAndMessages(null);
    }
}
