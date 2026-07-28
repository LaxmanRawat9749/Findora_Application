package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.findora.app.databinding.ActivityLoginBinding;
import com.findora.app.models.AuthResponse;
import com.findora.app.models.LoginRequest;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.SessionManager;

import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class LoginActivity extends AppCompatActivity {

    private static final String TAG = "LoginActivity";

    private ActivityLoginBinding binding;
    private SessionManager sessionManager;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        sessionManager = new SessionManager(this);
        apiService     = RetrofitClient.getInstance(this).getApi();

        // NOTE: The auto-login check (isLoggedIn → navigateToHome) that existed
        // here has been intentionally removed. SplashActivity is now the single
        // authoritative routing point and performs a proper isSessionValid() check
        // (including JWT expiry) before routing here. Repeating a simpler check
        // in LoginActivity was the root cause of unauthenticated users bypassing
        // the Login screen when stale SharedPreferences existed.
        //
        // If SplashActivity routed the user here, it is because there is no valid
        // session — we must always show the Login UI.

        binding.btnLogin.setOnClickListener(v -> attemptLogin());

        binding.tvForgotPassword.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, ForgotPasswordActivity.class)));

        binding.tvRegister.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, RegisterActivity.class)));
    }

    private void attemptLogin() {
        String username = binding.etUsername.getText().toString().trim();
        String password = binding.etPassword.getText().toString().trim();

        if (username.isEmpty() || password.isEmpty()) {
            showError("Please enter username and password");
            return;
        }

        // ── Pre-flight network check ──────────────────────────────────────────
        // Detect the absence of any network connectivity before we even attempt
        // a TCP connection. This surfaces a clear, actionable message immediately
        // rather than waiting 30 seconds for OkHttp to time out.
        if (!RetrofitClient.isNetworkAvailable(this)) {
            showError("No internet connection. Please check your Wi-Fi or mobile data.");
            Log.w(TAG, "Login aborted — device has no active network connection");
            return;
        }

        setLoading(true);
        long requestStartMs = System.currentTimeMillis();
        Log.i(TAG, "Login request started | username=" + username
                + " | endpoint=login/ | time=" + requestStartMs);

        LoginRequest request = new LoginRequest(username, password);
        apiService.login(request).enqueue(new Callback<AuthResponse>() {
            @Override
            public void onResponse(Call<AuthResponse> call, Response<AuthResponse> response) {
                long elapsedMs = System.currentTimeMillis() - requestStartMs;
                setLoading(false);

                Log.i(TAG, "Login response received | username=" + username
                        + " | status=" + response.code()
                        + " | elapsed=" + elapsedMs + " ms");

                if (response.isSuccessful() && response.body() != null) {
                    AuthResponse authResponse = response.body();

                    // Validate the response before saving — guard against a server
                    // returning 200 with null tokens or a null user object.
                    if (authResponse.access == null || authResponse.access.isEmpty()
                            || authResponse.refresh == null || authResponse.refresh.isEmpty()
                            || authResponse.user == null) {
                        showError("Login failed: incomplete server response. Please try again.");
                        Log.e(TAG, "Login failed | reason=incomplete_response | username=" + username);
                        return;
                    }

                    // saveSession() uses commit() — the data is durably on disk
                    // before navigateToHome() is called, so HomeActivity and its
                    // API calls always find a valid token in SharedPreferences.
                    sessionManager.saveSession(
                            authResponse.access,
                            authResponse.refresh,
                            authResponse.user.getUsername(),
                            authResponse.user.getRole(),
                            authResponse.user.getFullName(),
                            authResponse.user.getEmail(),
                            authResponse.user.getId(),
                            authResponse.user.getProfileImage()
                    );

                    Log.i(TAG, "Session saved | username=" + username + " | navigating to Home");
                    navigateToHome();

                } else {
                    showError("Invalid credentials. Please try again.");
                    Log.w(TAG, "Login failed | reason=invalid_credentials | username=" + username
                            + " | http_status=" + response.code());
                }
            }

            @Override
            public void onFailure(Call<AuthResponse> call, Throwable t) {
                long elapsedMs = System.currentTimeMillis() - requestStartMs;
                setLoading(false);

                // ── Distinguish failure types for actionable error messages ──
                // Each exception type maps to a specific root cause so the user
                // sees a helpful message and the developer sees a precise log.
                String userMessage;
                if (t instanceof ConnectException) {
                    // TCP connection was refused — server is not running, or the
                    // server's TCP accept-backlog was full (primary root cause of
                    // the intermittent "Failed to connect" errors we investigated).
                    userMessage = "Cannot reach the server. Please ensure the backend is running.";
                    Log.e(TAG, "Login failed | type=ConnectException"
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage()
                            + " | hint=server_down_or_backlog_full", t);
                } else if (t instanceof SocketTimeoutException) {
                    // Connection was established but the server did not respond
                    // in time — server may be overloaded or blocked on I/O.
                    userMessage = "Request timed out. The server is slow to respond. Please try again.";
                    Log.e(TAG, "Login failed | type=SocketTimeoutException"
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage()
                            + " | hint=server_overloaded_or_blocked", t);
                } else if (t instanceof UnknownHostException) {
                    // DNS resolution failed — BASE_URL hostname is wrong, or device
                    // has no DNS connectivity (e.g., Wi-Fi connected but no internet).
                    userMessage = "Cannot resolve server address. Check your Wi-Fi connection.";
                    Log.e(TAG, "Login failed | type=UnknownHostException"
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage()
                            + " | hint=wrong_base_url_or_no_dns", t);
                } else {
                    // Catch-all for any other IOException (e.g., SSL error, reset)
                    userMessage = "Network error: " + t.getMessage();
                    Log.e(TAG, "Login failed | type=" + t.getClass().getSimpleName()
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage(), t);
                }

                showError(userMessage);
            }
        });
    }

    private void navigateToHome() {
        Intent intent = new Intent(LoginActivity.this, HomeActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    private void showError(String message) {
        binding.tvError.setText(message);
        binding.tvError.setVisibility(View.VISIBLE);
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnLogin.setEnabled(!loading);
        if (loading) {
            binding.tvError.setVisibility(View.GONE);
        }
    }
}
