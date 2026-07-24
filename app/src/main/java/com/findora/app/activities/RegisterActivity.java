package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityRegisterBinding;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.RegisterRequest;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class RegisterActivity extends AppCompatActivity {

    private ActivityRegisterBinding binding;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityRegisterBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());
        binding.btnRegister.setOnClickListener(v -> attemptRegister());
    }

    private void attemptRegister() {
        String username = binding.etUsername.getText().toString().trim();
        String email = binding.etEmail.getText().toString().trim();
        String firstName = binding.etFirstName.getText().toString().trim();
        String lastName = binding.etLastName.getText().toString().trim();
        String phone = binding.etPhone.getText().toString().trim();
        String password = binding.etPassword.getText().toString().trim();
        String confirmPassword = binding.etConfirmPassword.getText().toString().trim();
        String role = binding.rbOwner.isChecked() ? "owner" : "finder";

        // Validations
        if (username.isEmpty() || email.isEmpty() || password.isEmpty()) {
            showError("Username, email, and password are required.");
            return;
        }

        if (username.length() < 3) {
            showError("Username must be at least 3 characters.");
            return;
        }

        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            showError("Please enter a valid email address.");
            return;
        }

        if (phone.length() != 10) {
            showError("Phone number must be exactly 10 digits.");
            return;
        }

        if (password.length() < 8) {
            showError("Password must be at least 8 characters.");
            return;
        }

        if (!password.equals(confirmPassword)) {
            showError("Passwords do not match.");
            return;
        }

        setLoading(true);

        RegisterRequest request = new RegisterRequest(
                username, email, password, confirmPassword, firstName, lastName, phone, role
        );

        apiService.register(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Toast.makeText(RegisterActivity.this,
                            "Registration successful! Please verify your email.", Toast.LENGTH_LONG).show();

                    Intent intent = new Intent(RegisterActivity.this, VerifyOtpActivity.class);
                    intent.putExtra(Constants.EXTRA_EMAIL, email);
                    intent.putExtra(Constants.EXTRA_OTP_PURPOSE, Constants.OTP_EMAIL_VERIFY);
                    startActivity(intent);
                    finish();
                } else {
                    showError(parseRegisterError(response));
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                showError("Network error: " + t.getMessage());
            }
        });
    }

    private String parseRegisterError(Response<MessageResponse> response) {
        try {
            if (response.errorBody() != null) {
                String errorJson = response.errorBody().string();
                org.json.JSONObject jsonObject = new org.json.JSONObject(errorJson);

                boolean hasUsername = jsonObject.has("username");
                boolean hasEmail = jsonObject.has("email");

                if (hasUsername && hasEmail) {
                    return "Username and email already exist.";
                }

                if (hasUsername) {
                    org.json.JSONArray arr = jsonObject.optJSONArray("username");
                    if (arr != null && arr.length() > 0) {
                        return arr.getString(0);
                    }
                    return jsonObject.optString("username");
                }

                if (hasEmail) {
                    org.json.JSONArray arr = jsonObject.optJSONArray("email");
                    if (arr != null && arr.length() > 0) {
                        return arr.getString(0);
                    }
                    return jsonObject.optString("email");
                }

                if (jsonObject.has("password")) {
                    org.json.JSONArray arr = jsonObject.optJSONArray("password");
                    if (arr != null && arr.length() > 0) {
                        return "Password error: " + arr.getString(0);
                    }
                }

                if (jsonObject.has("non_field_errors")) {
                    org.json.JSONArray arr = jsonObject.optJSONArray("non_field_errors");
                    if (arr != null && arr.length() > 0) {
                        return arr.getString(0);
                    }
                }

                if (jsonObject.has("detail")) {
                    return jsonObject.getString("detail");
                }

                java.util.Iterator<String> keys = jsonObject.keys();
                if (keys.hasNext()) {
                    String key = keys.next();
                    org.json.JSONArray arr = jsonObject.optJSONArray(key);
                    if (arr != null && arr.length() > 0) {
                        return arr.getString(0);
                    }
                    return jsonObject.optString(key);
                }
            }
        } catch (Exception e) {
            // Fallback
        }
        return "Registration failed. Please check your inputs.";
    }

    private void showError(String message) {
        binding.tvError.setText(message);
        binding.tvError.setVisibility(View.VISIBLE);
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnRegister.setEnabled(!loading);
        if (loading) {
            binding.tvError.setVisibility(View.GONE);
        }
    }
}
