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

public class LoginActivity extends PortraitBaseActivity {

    private static final String TAG = "LoginActivity";

    private ActivityLoginBinding binding;
    private SessionManager sessionManager;
    private ApiService apiService;
    private Call<AuthResponse> loginCall;
    private boolean isLoggingIn = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        sessionManager = new SessionManager(this);
        apiService     = RetrofitClient.getInstance(this).getApi();

        binding.btnLogin.setOnClickListener(v -> attemptLogin());

        binding.tvForgotPassword.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, ForgotPasswordActivity.class)));

        binding.tvRegister.setOnClickListener(v ->
                startActivity(new Intent(LoginActivity.this, RegisterActivity.class)));
    }

    private void attemptLogin() {
        if (isLoggingIn) {
            Log.d(TAG, "Login attempt ignored — request already in flight");
            return;
        }

        String username = binding.etUsername.getText().toString().trim();
        String password = binding.etPassword.getText().toString().trim();

        if (username.isEmpty() || password.isEmpty()) {
            showError("Please enter username and password");
            return;
        }

        // ── Pre-flight network check ──────────────────────────────────────────
        // Detect the absence of any network connectivity before we even attempt
        // a TCP connection. This surfaces a clear, actionable message immediately
        // rather than waiting for OkHttp to time out.
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
        loginCall = apiService.login(request);
        loginCall.enqueue(new Callback<AuthResponse>() {
            @Override
            public void onResponse(Call<AuthResponse> call, Response<AuthResponse> response) {
                if (isFinishing() || isDestroyed()) return;

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
                    String errorMsg = "Invalid credentials. Please try again.";
                    try {
                        if (response.errorBody() != null) {
                            String errorJson = response.errorBody().string();
                            org.json.JSONObject obj = new org.json.JSONObject(errorJson);
                            if (obj.has("error")) {
                                errorMsg = obj.getString("error");
                            } else if (obj.has("detail")) {
                                errorMsg = obj.getString("detail");
                            }

                            // If unverified email, allow immediate navigation to OTP verification
                            if (response.code() == 403 && "verify".equals(obj.optString("action"))) {
                                String verifyEmail = obj.optString("email", "");
                                if (!verifyEmail.isEmpty()) {
                                    Toast.makeText(LoginActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                                    Intent verifyIntent = new Intent(LoginActivity.this, VerifyOtpActivity.class);
                                    verifyIntent.putExtra(com.findora.app.utils.Constants.EXTRA_EMAIL, verifyEmail);
                                    verifyIntent.putExtra(com.findora.app.utils.Constants.EXTRA_OTP_PURPOSE, com.findora.app.utils.Constants.OTP_EMAIL_VERIFY);
                                    startActivity(verifyIntent);
                                    return;
                                }
                            }
                        }
                    } catch (Exception ignored) {}

                    if (response.code() >= 500) {
                        errorMsg = "Server is starting up or temporarily busy. Please try again in a moment.";
                    }

                    showError(errorMsg);
                    Log.w(TAG, "Login failed | reason=invalid_response | username=" + username
                            + " | http_status=" + response.code() + " | message=" + errorMsg);
                }
            }

            @Override
            public void onFailure(Call<AuthResponse> call, Throwable t) {
                if (isFinishing() || isDestroyed()) return;
                if (call.isCanceled()) {
                    Log.d(TAG, "Login call was canceled");
                    return;
                }

                long elapsedMs = System.currentTimeMillis() - requestStartMs;
                setLoading(false);

                // ── Distinguish failure types for actionable error messages ──
                String userMessage;
                if (t instanceof ConnectException) {
                    // TCP connection was refused — server is not running or backlog full
                    userMessage = "Cannot reach the server. Please ensure the backend is running.";
                    Log.e(TAG, "Login failed | type=ConnectException"
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage(), t);
                } else if (t instanceof SocketTimeoutException) {
                    // Timeout — server cold-start or slow response
                    userMessage = "Request timed out. The server was slow to respond. Please tap Login again.";
                    Log.e(TAG, "Login failed | type=SocketTimeoutException"
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage(), t);
                } else if (t instanceof UnknownHostException) {
                    // DNS resolution failed
                    userMessage = "Cannot resolve server address. Check your Wi-Fi or mobile data connection.";
                    Log.e(TAG, "Login failed | type=UnknownHostException"
                            + " | username=" + username
                            + " | elapsed=" + elapsedMs + " ms"
                            + " | cause=" + t.getMessage(), t);
                } else {
                    // Catch-all for other IO exceptions
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
        isLoggingIn = loading;
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnLogin.setEnabled(!loading);
        binding.etUsername.setEnabled(!loading);
        binding.etPassword.setEnabled(!loading);
        if (loading) {
            binding.tvError.setVisibility(View.GONE);
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (loginCall != null && !loginCall.isCanceled()) {
            loginCall.cancel();
        }
    }
}
