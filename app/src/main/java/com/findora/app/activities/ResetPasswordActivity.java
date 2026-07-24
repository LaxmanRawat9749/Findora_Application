package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityResetPasswordBinding;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.ResetPasswordRequest;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ResetPasswordActivity extends AppCompatActivity {

    private ActivityResetPasswordBinding binding;
    private ApiService apiService;
    private String email;
    private EditText[] otpFields;

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

        otpFields = new EditText[]{
                binding.etOtp1, binding.etOtp2, binding.etOtp3,
                binding.etOtp4, binding.etOtp5, binding.etOtp6
        };

        setupOtpTextWatchers();
        setupPasswordStrengthIndicator();

        binding.btnResetPassword.setOnClickListener(v -> resetPassword());
    }

    private void setupOtpTextWatchers() {
        for (int i = 0; i < otpFields.length; i++) {
            final int index = i;
            otpFields[i].addTextChangedListener(new TextWatcher() {
                @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
                @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}

                @Override
                public void afterTextChanged(Editable s) {
                    if (s.length() == 1 && index < otpFields.length - 1) {
                        otpFields[index + 1].requestFocus();
                    }
                    if (s.length() == 0 && index > 0) {
                        otpFields[index - 1].requestFocus();
                    }
                }
            });
        }
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

    private String getOtpCode() {
        StringBuilder sb = new StringBuilder();
        for (EditText field : otpFields) {
            sb.append(field.getText().toString().trim());
        }
        return sb.toString();
    }

    private void resetPassword() {
        String otp = getOtpCode();
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
        binding.btnResetPassword.setEnabled(!loading);
        if (loading) binding.tvError.setVisibility(View.GONE);
    }
}
