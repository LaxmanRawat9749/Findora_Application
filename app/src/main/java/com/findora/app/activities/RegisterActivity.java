package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
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

    // ──────────────────────────────────────────────────────────────────
    // Validation constants (single source of truth — no duplication)
    // ──────────────────────────────────────────────────────────────────
    private static final int MIN_USERNAME_LENGTH  = 3;
    private static final int MIN_PASSWORD_LENGTH  = 8;
    private static final int EXACT_PHONE_LENGTH   = 10;

    private ActivityRegisterBinding binding;
    private ApiService apiService;

    // ──────────────────────────────────────────────────────────────────
    // Lifecycle
    // ──────────────────────────────────────────────────────────────────

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityRegisterBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());
        binding.btnRegister.setOnClickListener(v -> attemptRegister());

        // ── Real-time inline error clearing ───────────────────────────
        // Each TextWatcher clears the error on its own TextInputLayout
        // as soon as the user starts correcting the field, so stale
        // error messages never linger after the user has fixed the input.

        attachClearErrorWatcher(binding.etUsername,  binding.tilUsername);
        attachClearErrorWatcher(binding.etEmail,     binding.tilEmail);
        attachClearErrorWatcher(binding.etPhone,     binding.tilPhone);

        // Password field clears its own error AND the confirm-password
        // mismatch error simultaneously (because editing the base password
        // invalidates any previously shown mismatch on confirm).
        binding.etPassword.addTextChangedListener(new SimpleTextWatcher() {
            @Override
            public void afterTextChanged(Editable s) {
                binding.tilPassword.setError(null);
                binding.tilPassword.setErrorEnabled(false);
                // Also clear confirm mismatch when password changes
                binding.tilConfirmPassword.setError(null);
                binding.tilConfirmPassword.setErrorEnabled(false);
                clearGlobalError();
            }
        });

        // Confirm password clears only its own mismatch error.
        binding.etConfirmPassword.addTextChangedListener(new SimpleTextWatcher() {
            @Override
            public void afterTextChanged(Editable s) {
                binding.tilConfirmPassword.setError(null);
                binding.tilConfirmPassword.setErrorEnabled(false);
                clearGlobalError();
            }
        });
    }

    // ──────────────────────────────────────────────────────────────────
    // Validation & Registration
    // ──────────────────────────────────────────────────────────────────

    /**
     * Validates all fields in the defined order and, if every check passes,
     * dispatches the registration API call.
     *
     * Validation order:
     *  1. Required fields (username, email, password)
     *  2. Username minimum length
     *  3. Valid e-mail format
     *  4. Phone number length
     *  5. Password minimum length  ← new inline TextInputLayout error
     *  6. Password confirmation match ← new inline TextInputLayout error
     *  7. API call
     */
    private void attemptRegister() {
        // Clear all previous inline errors before re-validating
        clearAllErrors();

        String username        = binding.etUsername.getText().toString().trim();
        String email           = binding.etEmail.getText().toString().trim();
        String firstName       = binding.etFirstName.getText().toString().trim();
        String lastName        = binding.etLastName.getText().toString().trim();
        String phone           = binding.etPhone.getText().toString().trim();
        String password        = binding.etPassword.getText().toString().trim();
        String confirmPassword = binding.etConfirmPassword.getText().toString().trim();
        String role            = "user";

        // ── Step 1: Required fields ────────────────────────────────────
        boolean hasRequiredError = false;
        if (username.isEmpty()) {
            binding.tilUsername.setError("Username is required.");
            hasRequiredError = true;
        }
        if (email.isEmpty()) {
            binding.tilEmail.setError("Email address is required.");
            hasRequiredError = true;
        }
        if (password.isEmpty()) {
            binding.tilPassword.setError("Password is required.");
            hasRequiredError = true;
        }
        if (hasRequiredError) return;

        // ── Step 2: Username minimum length ────────────────────────────
        if (username.length() < MIN_USERNAME_LENGTH) {
            binding.tilUsername.setError("Username must be at least " + MIN_USERNAME_LENGTH + " characters.");
            return;
        }

        // ── Step 3: Valid e-mail format ────────────────────────────────
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.tilEmail.setError("Please enter a valid email address.");
            return;
        }

        // ── Step 4: Phone number length (optional — only validate if entered) ──
        if (!phone.isEmpty() && phone.length() != EXACT_PHONE_LENGTH) {
            binding.tilPhone.setError("Phone number must be exactly 10 digits.");
            return;
        }

        // ── Step 5: Password minimum length ───────────────────────────
        if (password.length() < MIN_PASSWORD_LENGTH) {
            binding.tilPassword.setError(
                    "Password must be at least " + MIN_PASSWORD_LENGTH + " characters long.");
            return;
        }

        // ── Step 6: Passwords must match ──────────────────────────────
        if (!password.equals(confirmPassword)) {
            binding.tilConfirmPassword.setError("Passwords do not match.");
            return;
        }

        // ── Step 7: All validations passed — call the API ─────────────
        setLoading(true);

        RegisterRequest request = new RegisterRequest(
                username, email, password, confirmPassword, firstName, lastName, phone, role
        );

        apiService.register(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Toast.makeText(
                            RegisterActivity.this,
                            "Registration successful! Please verify your email.",
                            Toast.LENGTH_LONG
                    ).show();

                    Intent intent = new Intent(RegisterActivity.this, VerifyOtpActivity.class);
                    intent.putExtra(Constants.EXTRA_EMAIL, email);
                    intent.putExtra(Constants.EXTRA_OTP_PURPOSE, Constants.OTP_EMAIL_VERIFY);
                    startActivity(intent);
                    finish();
                } else {
                    showServerError(parseRegisterError(response));
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                setLoading(false);
                showError("Network error: " + t.getMessage());
            }
        });
    }

    // ──────────────────────────────────────────────────────────────────
    // Server error parsing
    // ──────────────────────────────────────────────────────────────────

    /**
     * Parses the Django REST Framework validation error response and maps
     * field-specific errors directly onto the corresponding TextInputLayout,
     * or falls back to the global tvError for non-field errors.
     */
    private void showServerError(ParsedError error) {
        // Field-specific server validation errors go inline on the field
        if (error.passwordError != null) {
            binding.tilPassword.setError(error.passwordError);
        }
        if (error.confirmPasswordError != null) {
            binding.tilConfirmPassword.setError(error.confirmPasswordError);
        }
        if (error.usernameError != null) {
            binding.tilUsername.setError(error.usernameError);
        }
        if (error.emailError != null) {
            binding.tilEmail.setError(error.emailError);
        }
        // General (non-field) errors go to the global error view
        if (error.generalError != null) {
            showError(error.generalError);
        }
    }

    private ParsedError parseRegisterError(Response<MessageResponse> response) {
        ParsedError result = new ParsedError();
        try {
            if (response.errorBody() == null) {
                result.generalError = "Registration failed. Please check your inputs.";
                return result;
            }

            String errorJson = response.errorBody().string();
            org.json.JSONObject json = new org.json.JSONObject(errorJson);

            // Map each known field to its inline location
            result.usernameError        = extractFirstMessage(json, "username");
            result.emailError           = extractFirstMessage(json, "email");
            result.passwordError        = extractFirstMessage(json, "password");
            result.confirmPasswordError = extractFirstMessage(json, "confirm_password");

            // Combine username + email if both exist (common "already taken" scenario)
            if (result.usernameError != null && result.emailError != null) {
                result.generalError = "Username and email are already registered.";
                result.usernameError = null;
                result.emailError = null;
            }

            // Non-field errors
            if (result.usernameError == null && result.emailError == null
                    && result.passwordError == null && result.confirmPasswordError == null) {
                String nonField = extractFirstMessage(json, "non_field_errors");
                if (nonField != null) {
                    result.generalError = nonField;
                } else if (json.has("detail")) {
                    result.generalError = json.getString("detail");
                } else {
                    // Last-resort: return first value from any key
                    java.util.Iterator<String> keys = json.keys();
                    if (keys.hasNext()) {
                        String key = keys.next();
                        result.generalError = extractFirstMessage(json, key);
                    }
                    if (result.generalError == null) {
                        result.generalError = "Registration failed. Please check your inputs.";
                    }
                }
            }
        } catch (Exception e) {
            result.generalError = "Registration failed. Please check your inputs.";
        }
        return result;
    }

    /** Extracts the first string from a field that may be a JSONArray or a plain string. */
    private String extractFirstMessage(org.json.JSONObject json, String key) {
        if (!json.has(key)) return null;
        try {
            org.json.JSONArray arr = json.optJSONArray(key);
            if (arr != null && arr.length() > 0) return arr.getString(0);
            String val = json.optString(key, null);
            return (val != null && !val.isEmpty()) ? val : null;
        } catch (Exception e) {
            return null;
        }
    }

    // ──────────────────────────────────────────────────────────────────
    // UI helpers
    // ──────────────────────────────────────────────────────────────────

    /** Shows a message in the global error TextView (non-field errors). */
    private void showError(String message) {
        binding.tvError.setText(message);
        binding.tvError.setVisibility(View.VISIBLE);
    }

    private void clearGlobalError() {
        binding.tvError.setVisibility(View.GONE);
    }

    /** Clears all inline field errors and the global error banner. */
    private void clearAllErrors() {
        clearFieldError(binding.tilUsername);
        clearFieldError(binding.tilEmail);
        clearFieldError(binding.tilPhone);
        clearFieldError(binding.tilPassword);
        clearFieldError(binding.tilConfirmPassword);
        clearGlobalError();
    }

    private void clearFieldError(com.google.android.material.textfield.TextInputLayout til) {
        til.setError(null);
        til.setErrorEnabled(false);
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnRegister.setEnabled(!loading);
        if (loading) clearGlobalError();
    }

    /**
     * Attaches a TextWatcher to {@code editText} that clears the error on
     * {@code inputLayout} as soon as the user modifies the field.
     */
    private void attachClearErrorWatcher(
            android.widget.EditText editText,
            com.google.android.material.textfield.TextInputLayout inputLayout) {
        editText.addTextChangedListener(new SimpleTextWatcher() {
            @Override
            public void afterTextChanged(Editable s) {
                inputLayout.setError(null);
                inputLayout.setErrorEnabled(false);
                clearGlobalError();
            }
        });
    }

    // ──────────────────────────────────────────────────────────────────
    // Inner helpers
    // ──────────────────────────────────────────────────────────────────

    /**
     * Convenience adapter so callers only override {@link #afterTextChanged}.
     */
    private abstract static class SimpleTextWatcher implements TextWatcher {
        @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
        @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
    }

    /** Value-object carrying field-specific and general errors parsed from the server response. */
    private static class ParsedError {
        String usernameError;
        String emailError;
        String passwordError;
        String confirmPasswordError;
        String generalError;
    }
}
