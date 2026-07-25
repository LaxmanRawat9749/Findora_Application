package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.findora.app.databinding.ActivityLoginBinding;
import com.findora.app.models.AuthResponse;
import com.findora.app.models.LoginRequest;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.SessionManager;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class LoginActivity extends AppCompatActivity {

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

        setLoading(true);

        LoginRequest request = new LoginRequest(username, password);
        apiService.login(request).enqueue(new Callback<AuthResponse>() {
            @Override
            public void onResponse(Call<AuthResponse> call, Response<AuthResponse> response) {
                setLoading(false);

                if (response.isSuccessful() && response.body() != null) {
                    AuthResponse authResponse = response.body();

                    // Validate the response before saving — guard against a server
                    // returning 200 with null tokens or a null user object.
                    if (authResponse.access == null || authResponse.access.isEmpty()
                            || authResponse.refresh == null || authResponse.refresh.isEmpty()
                            || authResponse.user == null) {
                        showError("Login failed: incomplete server response. Please try again.");
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
                            authResponse.user.getId()
                    );

                    navigateToHome();

                } else {
                    showError("Invalid credentials. Please try again.");
                }
            }

            @Override
            public void onFailure(Call<AuthResponse> call, Throwable t) {
                setLoading(false);
                showError("Network error: " + t.getMessage());
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
