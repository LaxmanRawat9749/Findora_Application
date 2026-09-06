package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;

import com.findora.app.R;
import com.findora.app.databinding.ActivityPromoteItemBinding;
import com.findora.app.models.PaymentRequest;
import com.findora.app.models.PaymentResponse;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.cache.FindoraCache;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class PromoteItemActivity extends BaseActivity {

    private ActivityPromoteItemBinding binding;
    private ApiService apiService;
    private int itemId = -1;
    private String selectedPackage = "24h";
    private String selectedProvider = "esewa";

    private ActivityResultLauncher<Intent> paymentLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityPromoteItemBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        itemId = getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, -1);
        if (itemId == -1) {
            Toast.makeText(this, "Error: Item not found.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        // Default package is 24 Hours
        binding.rb24h.setChecked(true);
        selectedPackage = "24h";

        binding.rgPackages.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.rb_24h) {
                selectedPackage = "24h";
            } else if (checkedId == R.id.rb_3d) {
                selectedPackage = "3d";
            } else if (checkedId == R.id.rb_7d) {
                selectedPackage = "7d";
            }
        });

        selectedProvider = "esewa";
        binding.rgProviders.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.rb_esewa) {
                selectedProvider = "esewa";
            }
        });

        // Register modern ActivityResultLauncher
        paymentLauncher = registerForActivityResult(
                new ActivityResultContracts.StartActivityForResult(),
                result -> {
                    hideLoading();
                    if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                        String status = result.getData().getStringExtra(KhaltiWebViewActivity.EXTRA_STATUS);
                        String pidx = result.getData().getStringExtra(KhaltiWebViewActivity.EXTRA_PIDX);

                        if (status != null && (status.equalsIgnoreCase("Completed") || status.equalsIgnoreCase("Success") || status.equalsIgnoreCase("SUCCESS"))) {
                            if (pidx != null && !pidx.isEmpty()) {
                                showLoading("Payment processing... Checking payment status...");
                                verifyPayment(pidx);
                            } else {
                                showStatusMessage("Payment completed, missing transaction reference.", true);
                            }
                        } else if (status != null && (status.equalsIgnoreCase("Canceled") || status.equalsIgnoreCase("User canceled"))) {
                            showStatusMessage("Payment canceled.", false);
                            Toast.makeText(this, "Payment canceled.", Toast.LENGTH_SHORT).show();
                        } else {
                            showStatusMessage("Payment failed: " + (status != null ? status : "Unknown error"), true);
                            Toast.makeText(this, "Payment failed.", Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        showStatusMessage("Payment canceled.", false);
                    }
                }
        );

        binding.btnPay.setOnClickListener(v -> {
            if (selectedPackage.isEmpty()) {
                Toast.makeText(this, "Please select a promotion package", Toast.LENGTH_SHORT).show();
                return;
            }
            if (selectedProvider.isEmpty()) {
                selectedProvider = "esewa";
            }
            initiatePayment();
        });
    }

    private void initiatePayment() {
        showLoading("Preparing payment...");
        binding.btnPay.setEnabled(false);
        binding.tvStatusMessage.setVisibility(View.GONE);

        PaymentRequest.Initiate request = new PaymentRequest.Initiate(itemId, selectedPackage, selectedProvider);
        apiService.initiatePayment(request).enqueue(new Callback<PaymentResponse.Initiate>() {
            @Override
            public void onResponse(Call<PaymentResponse.Initiate> call, Response<PaymentResponse.Initiate> response) {
                if (response.isSuccessful() && response.body() != null) {
                    String paymentUrl = response.body().getPaymentUrl();
                    String pidx = response.body().getPidx();

                    if (paymentUrl != null && !paymentUrl.isEmpty()) {
                        setLoadingText("Redirecting to eSewa...");
                        new Handler(Looper.getMainLooper()).postDelayed(() -> {
                            launchPaymentGateway(paymentUrl, pidx);
                        }, 300);
                    } else {
                        hideLoading();
                        binding.btnPay.setEnabled(true);
                        showStatusMessage("Failed to obtain secure payment link. Please try again.", true);
                    }
                } else {
                    hideLoading();
                    binding.btnPay.setEnabled(true);
                    String errorMsg = extractErrorMessage(response, "Unable to start payment. Please try again.");
                    showStatusMessage(errorMsg, true);
                    Toast.makeText(PromoteItemActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onFailure(Call<PaymentResponse.Initiate> call, Throwable t) {
                hideLoading();
                binding.btnPay.setEnabled(true);
                String errorMsg = "Unable to connect to payment server. Please check your internet connection.";
                showStatusMessage(errorMsg, true);
                Toast.makeText(PromoteItemActivity.this, errorMsg, Toast.LENGTH_LONG).show();
            }
        });
    }

    private void launchPaymentGateway(String paymentUrl, String pidx) {
        Intent intent = new Intent(this, KhaltiWebViewActivity.class);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_URL, paymentUrl);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_PIDX, pidx);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_TITLE, "eSewa Checkout");
        paymentLauncher.launch(intent);
    }

    private void verifyPayment(String pidx) {
        setLoadingText("Payment pending — checking payment status...");

        PaymentRequest.Verify request = new PaymentRequest.Verify(pidx);
        apiService.verifyPayment(request).enqueue(new Callback<PaymentResponse.Verify>() {
            @Override
            public void onResponse(Call<PaymentResponse.Verify> call, Response<PaymentResponse.Verify> response) {
                hideLoading();
                binding.btnPay.setEnabled(true);

                if (response.isSuccessful() && response.body() != null && response.body().isSuccess()) {
                    // Invalidate caches so home feed and item details show the active featured badge
                    FindoraCache.getInstance(PromoteItemActivity.this).clearAll();

                    Toast.makeText(PromoteItemActivity.this, "Payment successful — Item promoted successfully!", Toast.LENGTH_LONG).show();

                    // Return to HomeActivity and clear previous stack so the home feed refreshes
                    Intent intent = new Intent(PromoteItemActivity.this, HomeActivity.class);
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                    finish();
                } else {
                    String errorMsg = extractErrorMessage(response, "Unable to verify payment — try again.");
                    showStatusMessage(errorMsg, true);
                    Toast.makeText(PromoteItemActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onFailure(Call<PaymentResponse.Verify> call, Throwable t) {
                hideLoading();
                binding.btnPay.setEnabled(true);
                String errorMsg = "Unable to verify payment — try again.";
                showStatusMessage(errorMsg, true);
                Toast.makeText(PromoteItemActivity.this, errorMsg, Toast.LENGTH_LONG).show();
            }
        });
    }

    private void showLoading(String message) {
        binding.tvLoadingText.setText(message);
        binding.loadingOverlay.setVisibility(View.VISIBLE);
        binding.btnPay.setEnabled(false);
    }

    private void setLoadingText(String message) {
        binding.tvLoadingText.setText(message);
    }

    private void hideLoading() {
        binding.loadingOverlay.setVisibility(View.GONE);
        binding.btnPay.setEnabled(true);
    }

    private void showStatusMessage(String message, boolean isError) {
        binding.tvStatusMessage.setVisibility(View.VISIBLE);
        binding.tvStatusMessage.setText(message);
        binding.tvStatusMessage.setTextColor(getResources().getColor(
                isError ? R.color.error_red : R.color.primary_purple, getTheme()
        ));
    }

    private String extractErrorMessage(Response<?> response, String fallback) {
        try {
            if (response.errorBody() != null) {
                String errBody = response.errorBody().string();
                if (errBody.contains("\"error\"")) {
                    int start = errBody.indexOf("\"error\":\"") + 9;
                    int end = errBody.indexOf("\"", start);
                    if (start > 8 && end > start) {
                        return errBody.substring(start, end);
                    }
                }
            }
        } catch (Exception ignored) {}

        if (response.code() == 401) {
            return "Session expired or unauthorized. Please login again.";
        } else if (response.code() == 403) {
            return "You are only authorized to promote your own lost items.";
        } else if (response.code() >= 500) {
            return "Payment service is temporarily unavailable. Please try again.";
        }
        return fallback;
    }
}
