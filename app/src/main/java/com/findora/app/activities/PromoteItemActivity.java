package com.findora.app.activities;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

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

    private boolean isPaymentInProgress = false;
    private boolean isWaitingForPaymentReturn = false;
    private String activeTransactionUuid = null;

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

        binding.btnPay.setOnClickListener(v -> {
            if (isPaymentInProgress) {
                return;
            }
            if (selectedPackage.isEmpty()) {
                Toast.makeText(this, "Please select a promotion package", Toast.LENGTH_SHORT).show();
                return;
            }
            if (selectedProvider.isEmpty()) {
                selectedProvider = "esewa";
            }
            initiatePayment();
        });

        // Handle deep link if activity started via intent
        handleDeepLinkIntent(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        handleDeepLinkIntent(intent);
    }

    private void handleDeepLinkIntent(Intent intent) {
        if (intent != null && intent.getData() != null) {
            Uri data = intent.getData();
            String pidx = data.getQueryParameter("pidx");
            String status = data.getQueryParameter("status");

            if (pidx != null && !pidx.isEmpty()) {
                activeTransactionUuid = pidx;
                isWaitingForPaymentReturn = false;
                showLoading("Payment processing... Checking payment status...");
                verifyPayment(pidx);
            }
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        // If user returns from eSewa / browser, check payment status
        if (isWaitingForPaymentReturn && activeTransactionUuid != null) {
            isWaitingForPaymentReturn = false;
            showLoading("Payment processing... Checking payment status...");
            verifyPayment(activeTransactionUuid);
        }
    }

    private static final int REQUEST_CODE_PAYMENT = 1001;

    private void initiatePayment() {
        isPaymentInProgress = true;
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
                    String formUrl = response.body().getFormUrl();
                    String postData = response.body().getPostData();
                    String formHtml = response.body().getFormHtml();

                    if ((paymentUrl != null && !paymentUrl.isEmpty()) || (formUrl != null && !formUrl.isEmpty()) || (formHtml != null && !formHtml.isEmpty())) {
                        activeTransactionUuid = pidx;
                        setLoadingText("Opening eSewa payment...");
                        launchPaymentWebView(paymentUrl, pidx, formUrl, postData, formHtml);
                    } else {
                        isPaymentInProgress = false;
                        hideLoading();
                        binding.btnPay.setEnabled(true);
                        showStatusMessage("Failed to obtain secure payment link. Please try again.", true);
                    }
                } else {
                    isPaymentInProgress = false;
                    hideLoading();
                    binding.btnPay.setEnabled(true);
                    String errorMsg = extractErrorMessage(response, "Unable to start payment. Please try again.");
                    showStatusMessage(errorMsg, true);
                    Toast.makeText(PromoteItemActivity.this, errorMsg, Toast.LENGTH_LONG).show();
                }
            }

            @Override
            public void onFailure(Call<PaymentResponse.Initiate> call, Throwable t) {
                isPaymentInProgress = false;
                hideLoading();
                binding.btnPay.setEnabled(true);
                String errorMsg = "Unable to connect to payment server. Please check your internet connection.";
                showStatusMessage(errorMsg, true);
                Toast.makeText(PromoteItemActivity.this, errorMsg, Toast.LENGTH_LONG).show();
            }
        });
    }

    private void launchPaymentWebView(String paymentUrl, String pidx, String formUrl, String postData, String formHtml) {
        hideLoading();
        Intent intent = new Intent(this, KhaltiWebViewActivity.class);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_URL, paymentUrl);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_PIDX, pidx);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_FORM_URL, formUrl);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_POST_DATA, postData);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_FORM_HTML, formHtml);
        intent.putExtra(KhaltiWebViewActivity.EXTRA_TITLE, "eSewa Checkout");
        startActivityForResult(intent, REQUEST_CODE_PAYMENT);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == REQUEST_CODE_PAYMENT) {
            isPaymentInProgress = false;
            if (resultCode == RESULT_OK && data != null) {
                String status = data.getStringExtra(KhaltiWebViewActivity.EXTRA_STATUS);
                String pidx = data.getStringExtra(KhaltiWebViewActivity.EXTRA_PIDX);

                if ("Completed".equalsIgnoreCase(status) && pidx != null && !pidx.isEmpty()) {
                    showLoading("Payment processing... Checking payment status...");
                    verifyPayment(pidx);
                } else if ("Canceled".equalsIgnoreCase(status) || "User canceled".equalsIgnoreCase(status)) {
                    hideLoading();
                    binding.btnPay.setEnabled(true);
                    showStatusMessage("Payment canceled.", false);
                } else {
                    hideLoading();
                    binding.btnPay.setEnabled(true);
                    String msg = (status != null && !status.isEmpty()) ? "Payment " + status : "Payment failed. Please try again.";
                    showStatusMessage(msg, true);
                    Toast.makeText(this, msg, Toast.LENGTH_SHORT).show();
                }
            } else {
                hideLoading();
                binding.btnPay.setEnabled(true);
                showStatusMessage("Payment canceled.", false);
            }
        }
    }

    private void verifyPayment(String pidx) {
        setLoadingText("Payment pending — checking payment status...");

        PaymentRequest.Verify request = new PaymentRequest.Verify(pidx);
        apiService.verifyPayment(request).enqueue(new Callback<PaymentResponse.Verify>() {
            @Override
            public void onResponse(Call<PaymentResponse.Verify> call, Response<PaymentResponse.Verify> response) {
                isPaymentInProgress = false;
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
                isPaymentInProgress = false;
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
