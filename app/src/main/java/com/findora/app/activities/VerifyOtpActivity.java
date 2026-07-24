package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.os.CountDownTimer;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityVerifyOtpBinding;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.OtpRequest;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class VerifyOtpActivity extends AppCompatActivity {

    private ActivityVerifyOtpBinding binding;
    private ApiService apiService;
    private String email;
    private String purpose;
    private CountDownTimer countDownTimer;
    private EditText[] otpFields;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityVerifyOtpBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        email = getIntent().getStringExtra(Constants.EXTRA_EMAIL);
        purpose = getIntent().getStringExtra(Constants.EXTRA_OTP_PURPOSE);

        if (email == null) {
            Toast.makeText(this, "Error: Email not provided.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.tvEmailSubtitle.setText("We sent a 6-digit OTP code to " + email);
        binding.toolbar.setNavigationOnClickListener(v -> finish());

        otpFields = new EditText[]{
                binding.etOtp1, binding.etOtp2, binding.etOtp3,
                binding.etOtp4, binding.etOtp5, binding.etOtp6
        };

        setupOtpTextWatchers();
        startTimer();

        binding.btnVerify.setOnClickListener(v -> verifyOtp());
        binding.btnResend.setOnClickListener(v -> resendOtp());
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

    private String getOtpCode() {
        StringBuilder sb = new StringBuilder();
        for (EditText field : otpFields) {
            sb.append(field.getText().toString().trim());
        }
        return sb.toString();
    }

    private void verifyOtp() {
        String otp = getOtpCode();
        if (otp.length() != 6) {
            showError("Please enter all 6 digits of the OTP code.");
            return;
        }

        setLoading(true);
        OtpRequest request = new OtpRequest(email, otp, purpose != null ? purpose : Constants.OTP_EMAIL_VERIFY);

        apiService.verifyOtp(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    MessageResponse msgResponse = response.body();
                    String msg = msgResponse.message != null ? msgResponse.message : "Email verified successfully!";
                    Toast.makeText(VerifyOtpActivity.this, msg, Toast.LENGTH_LONG).show();

                    if (Constants.OTP_PASSWORD_RESET.equals(purpose)) {
                        finish();
                    } else {
                        // Go to Login
                        Intent intent = new Intent(VerifyOtpActivity.this, LoginActivity.class);
                        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                        startActivity(intent);
                        finish();
                    }
                } else {
                    showError(parseErrorMessage(response, "Invalid or expired OTP code. Please try again."));
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                showError("Network error: " + t.getMessage());
            }
        });
    }

    private void resendOtp() {
        setLoading(true);
        OtpRequest request = new OtpRequest(email, "", purpose != null ? purpose : Constants.OTP_EMAIL_VERIFY);

        apiService.resendOtp(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful() && response.body() != null) {
                    MessageResponse msgResponse = response.body();
                    String msg = msgResponse.message != null ? msgResponse.message : "OTP resent successfully!";
                    Toast.makeText(VerifyOtpActivity.this, msg, Toast.LENGTH_SHORT).show();
                    startTimer();
                } else {
                    showError(parseErrorMessage(response, "Failed to resend OTP. Try again later."));
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                showError("Network error: " + t.getMessage());
            }
        });
    }

    private String parseErrorMessage(Response<MessageResponse> response, String fallback) {
        try {
            if (response.errorBody() != null) {
                String errorJson = response.errorBody().string();
                org.json.JSONObject jsonObject = new org.json.JSONObject(errorJson);
                if (jsonObject.has("error")) {
                    return jsonObject.getString("error");
                }
                if (jsonObject.has("message")) {
                    return jsonObject.getString("message");
                }
                if (jsonObject.has("detail")) {
                    return jsonObject.getString("detail");
                }
            }
        } catch (Exception ignored) {}
        return fallback;
    }

    private void startTimer() {
        if (countDownTimer != null) countDownTimer.cancel();
        countDownTimer = new CountDownTimer(600000, 1000) { // 10 minutes
            @Override
            public void onTick(long millisUntilFinished) {
                long mins = millisUntilFinished / 60000;
                long secs = (millisUntilFinished % 60000) / 1000;
                binding.tvTimer.setText(String.format("OTP expires in: %d:%02d", mins, secs));
            }

            @Override
            public void onFinish() {
                binding.tvTimer.setText("OTP expired. Please resend.");
            }
        }.start();
    }

    private void showError(String message) {
        binding.tvError.setText(message);
        binding.tvError.setVisibility(View.VISIBLE);
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnVerify.setEnabled(!loading);
        binding.btnResend.setEnabled(!loading);
        if (loading) binding.tvError.setVisibility(View.GONE);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (countDownTimer != null) countDownTimer.cancel();
    }
}
