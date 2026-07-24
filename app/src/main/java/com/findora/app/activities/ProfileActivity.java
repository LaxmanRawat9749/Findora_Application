package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityProfileBinding;
import com.findora.app.models.ChangePasswordRequest;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.RefreshRequest;
import com.findora.app.models.User;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.SessionManager;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ProfileActivity extends AppCompatActivity {

    private ActivityProfileBinding binding;
    private ApiService apiService;
    private SessionManager sessionManager;
    private boolean isPasswordFormVisible = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityProfileBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();
        sessionManager = new SessionManager(this);

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        // Display cached info immediately
        binding.tvFullName.setText(sessionManager.getFullName());
        binding.tvEmail.setText(sessionManager.getEmail());
        binding.tvRole.setText("Role: " + capitalize(sessionManager.getRole()));

        // Load fresh profile from API
        loadProfile();

        // Change password toggle
        binding.btnToggleChangePassword.setOnClickListener(v -> {
            isPasswordFormVisible = !isPasswordFormVisible;
            binding.layoutChangePasswordForm.setVisibility(
                    isPasswordFormVisible ? View.VISIBLE : View.GONE);
            binding.btnToggleChangePassword.setText(isPasswordFormVisible ? "Hide" : "Show");
        });

        // Update password
        binding.btnUpdatePassword.setOnClickListener(v -> changePassword());

        // Logout
        binding.btnLogout.setOnClickListener(v -> logout());
    }

    private void loadProfile() {
        apiService.getProfile().enqueue(new Callback<User>() {
            @Override
            public void onResponse(Call<User> call, Response<User> response) {
                if (response.isSuccessful() && response.body() != null) {
                    User user = response.body();
                    binding.tvFullName.setText(user.getFullName());
                    binding.tvEmail.setText(user.getEmail());
                    binding.tvRole.setText("Role: " + capitalize(user.getRole()));
                }
            }

            @Override
            public void onFailure(Call<User> call, Throwable t) {
                // Use cached data — already displayed
            }
        });
    }

    private void changePassword() {
        String currentPass = binding.etCurrentPassword.getText().toString().trim();
        String newPass = binding.etNewPassword.getText().toString().trim();
        String confirmPass = binding.etConfirmPassword.getText().toString().trim();

        if (currentPass.isEmpty() || newPass.isEmpty() || confirmPass.isEmpty()) {
            showPasswordError("All fields are required.");
            return;
        }

        if (newPass.length() < 8) {
            showPasswordError("New password must be at least 8 characters.");
            return;
        }

        if (!newPass.equals(confirmPass)) {
            showPasswordError("New passwords do not match.");
            return;
        }

        ChangePasswordRequest request = new ChangePasswordRequest(currentPass, newPass);
        apiService.changePassword(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(ProfileActivity.this,
                            "Password updated successfully!", Toast.LENGTH_LONG).show();
                    binding.etCurrentPassword.setText("");
                    binding.etNewPassword.setText("");
                    binding.etConfirmPassword.setText("");
                    binding.tvChangePasswordError.setVisibility(View.GONE);
                } else {
                    showPasswordError("Failed. Current password may be incorrect.");
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                showPasswordError("Network error: " + t.getMessage());
            }
        });
    }

    private void logout() {
        String refreshToken = sessionManager.getRefreshToken();
        if (!refreshToken.isEmpty()) {
            RefreshRequest request = new RefreshRequest(refreshToken);
            apiService.logout(request).enqueue(new Callback<MessageResponse>() {
                @Override
                public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                    performLocalLogout();
                }

                @Override
                public void onFailure(Call<MessageResponse> call, Throwable t) {
                    performLocalLogout();
                }
            });
        } else {
            performLocalLogout();
        }
    }

    private void performLocalLogout() {
        sessionManager.logout();
        Intent intent = new Intent(ProfileActivity.this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    private void showPasswordError(String message) {
        binding.tvChangePasswordError.setText(message);
        binding.tvChangePasswordError.setVisibility(View.VISIBLE);
    }

    private String capitalize(String s) {
        if (s == null || s.isEmpty()) return "";
        return s.substring(0, 1).toUpperCase() + s.substring(1);
    }
}
