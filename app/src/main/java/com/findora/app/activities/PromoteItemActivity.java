package com.findora.app.activities;

import android.app.AlertDialog;
import android.content.Intent;
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

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class PromoteItemActivity extends BaseActivity {

    private ActivityPromoteItemBinding binding;
    private ApiService apiService;
    private int itemId = -1;
    private String selectedPackage = "";

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

        binding.rgPackages.setOnCheckedChangeListener((group, checkedId) -> {
            if (checkedId == R.id.rb_24h) {
                selectedPackage = "24h";
            } else if (checkedId == R.id.rb_3d) {
                selectedPackage = "3d";
            } else if (checkedId == R.id.rb_7d) {
                selectedPackage = "7d";
            }
        });

        binding.btnPay.setOnClickListener(v -> {
            if (selectedPackage.isEmpty()) {
                Toast.makeText(this, "Please select a package", Toast.LENGTH_SHORT).show();
                return;
            }
            initiatePayment();
        });
    }

    private void initiatePayment() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.btnPay.setEnabled(false);

        PaymentRequest.Initiate request = new PaymentRequest.Initiate(itemId, selectedPackage);
        apiService.initiatePayment(request).enqueue(new Callback<PaymentResponse.Initiate>() {
            @Override
            public void onResponse(Call<PaymentResponse.Initiate> call, Response<PaymentResponse.Initiate> response) {
                if (response.isSuccessful() && response.body() != null) {
                    // Mock Khalti Payment flow here.
                    // In a real app, you would pass these details to the Khalti SDK
                    // and wait for the success callback to get the token.
                    mockKhaltiPaymentFlow(response.body().getPaymentId());
                } else {
                    binding.progressBar.setVisibility(View.GONE);
                    binding.btnPay.setEnabled(true);
                    Toast.makeText(PromoteItemActivity.this, "Failed to initiate payment", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<PaymentResponse.Initiate> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnPay.setEnabled(true);
                Toast.makeText(PromoteItemActivity.this, "Network error", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void mockKhaltiPaymentFlow(int paymentId) {
        // Simulating the Khalti SDK opening and user paying successfully.
        new AlertDialog.Builder(this)
                .setTitle("Mock Khalti Payment")
                .setMessage("Simulating successful payment via Khalti SDK...")
                .setCancelable(false)
                .setPositiveButton("Pay Success", (dialog, which) -> {
                    verifyPayment(paymentId, "mock_khalti_token_123");
                })
                .setNegativeButton("Cancel", (dialog, which) -> {
                    binding.progressBar.setVisibility(View.GONE);
                    binding.btnPay.setEnabled(true);
                    Toast.makeText(PromoteItemActivity.this, "Payment cancelled", Toast.LENGTH_SHORT).show();
                })
                .show();
    }

    private void verifyPayment(int paymentId, String token) {
        PaymentRequest.Verify request = new PaymentRequest.Verify(paymentId, token);
        apiService.verifyPayment(request).enqueue(new Callback<PaymentResponse.Verify>() {
            @Override
            public void onResponse(Call<PaymentResponse.Verify> call, Response<PaymentResponse.Verify> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnPay.setEnabled(true);
                
                if (response.isSuccessful() && response.body() != null) {
                    Toast.makeText(PromoteItemActivity.this, "Promotion Successful!", Toast.LENGTH_SHORT).show();
                    
                    // Return to Home Activity and clear stack so the list refreshes
                    Intent intent = new Intent(PromoteItemActivity.this, HomeActivity.class);
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
                    startActivity(intent);
                    finish();
                } else {
                    Toast.makeText(PromoteItemActivity.this, "Verification failed", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<PaymentResponse.Verify> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnPay.setEnabled(true);
                Toast.makeText(PromoteItemActivity.this, "Network error during verification", Toast.LENGTH_SHORT).show();
            }
        });
    }
}
