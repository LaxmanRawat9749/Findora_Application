package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityResetPasswordBinding;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.ResetPasswordRequest;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.OtpFieldManager;
import android.widget.TextView;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ResetPasswordActivity extends AppCompatActivity {

    private ActivityResetPasswordBinding binding;
    private ApiService apiService;
    private String email;
    private OtpFieldManager otpManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityResetPasswordBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();
        email = getIntent().getStringExtra(Constants.EXTRA_EMAIL);

        if (email == null) {
            Toast.makeText(this, "Error: Email not provided.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.tvEmailSubtitle.setText("Enter the 6-digit OTP sent to " + email);
        binding.toolbar.setNavigationOnClickListener(v -> finish());

        TextView[] visualBoxes = new TextView[]{
                binding.tvOtp1, binding.tvOtp2, binding.tvOtp3,
                binding.tvOtp4, binding.tvOtp5, binding.tvOtp6
        };

        // Initialize Reset button disabled until OTP is fully entered
        binding.btnResetPassword.setEnabled(false);

        otpManager = new OtpFieldManager(binding.etHiddenOtp, visualBoxes, (otp, isComplete) -> {
            binding.btnResetPassword.setEnabled(isComplete);
        });

        setupPasswordStrengthIndicator();

        binding.btnResetPassword.setOnClickListener(v -> resetPassword());
    }

    private void setupPasswordStrengthIndicator() {
        binding.etNewPassword.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(Editable s) {
                String password = s.toString();
                if (password.isEmpty()) {
                    binding.tvStrength.setVisibility(View.GONE);
                    return;
                }

                binding.tvStrength.setVisibility(View.VISIBLE);
                int strength = 0;
                if (password.length() >= 8) strength++;
                if (password.matches(".*[A-Z].*")) strength++;
                if (password.matches(".*[0-9].*")) strength++;
                if (password.matches(".*[!@#$%^&*].*")) strength++;

                if (strength <= 1) {
                    binding.tvStrength.setText("Strength: Weak");
                    binding.tvStrength.setTextColor(getResources().getColor(com.findora.app.R.color.error_red));
                } else if (strength == 2) {
                    binding.tvStrength.setText("Strength: Medium");
                    binding.tvStrength.setTextColor(getResources().getColor(com.findora.app.R.color.warning_orange));
                } else {
                    binding.tvStrength.setText("Strength: Strong");
                    binding.tvStrength.setTextColor(getResources().getColor(com.findora.app.R.color.success_green));
                }
            }
        });
    }

    private void resetPassword() {
        String otp = otpManager.getOtp();
        String newPassword = binding.etNewPassword.getText().toString().trim();
        String confirmPassword = binding.etConfirmPassword.getText().toString().trim();

        if (otp.length() != 6) {
            showError("Please enter all 6 digits of the OTP code.");
            return;
        }

        if (newPassword.length() < 8) {
            showError("Password must be at least 8 characters.");
            return;
        }

        if (!newPassword.equals(confirmPassword)) {
            showError("Passwords do not match.");
            return;
        }

        setLoading(true);

        ResetPasswordRequest request = new ResetPasswordRequest(email, otp, newPassword);
        apiService.resetPassword(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Toast.makeText(ResetPasswordActivity.this,
                            "Password reset successfully! Please log in.", Toast.LENGTH_LONG).show();

                    Intent intent = new Intent(ResetPasswordActivity.this, LoginActivity.class);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                    startActivity(intent);
                    finish();
                } else {
                    showError("Invalid or expired OTP. Please try again.");
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                showError("Network error: " + t.getMessage());
            }
        });
    }

    private void showError(String message) {
        binding.tvError.setText(message);
        binding.tvError.setVisibility(View.VISIBLE);
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        if (loading) {
            binding.btnResetPassword.setEnabled(false);
            binding.tvError.setVisibility(View.GONE);
        } else {
            binding.btnResetPassword.setEnabled(otpManager != null && otpManager.getOtp().length() == 6);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (otpManager != null) {
            otpManager.requestOtpFocus();
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (otpManager != null) {
            otpManager.cleanup();
        }
    }
}
