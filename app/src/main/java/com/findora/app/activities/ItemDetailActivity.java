package com.findora.app.activities;

import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.databinding.ActivityItemDetailBinding;
import com.findora.app.models.Claim;
import com.findora.app.models.Item;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.WriterException;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import android.graphics.Bitmap;
import android.graphics.Color;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ItemDetailActivity extends AppCompatActivity {

    private ActivityItemDetailBinding binding;
    private ApiService apiService;
    private SessionManager sessionManager;
    private Item currentItem;
    private int itemId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityItemDetailBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();
        sessionManager = new SessionManager(this);

        itemId = getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, -1);
        if (itemId == -1) {
            Toast.makeText(this, "Error: Item not found.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        binding.btnChat.setOnClickListener(v -> {
            if (currentItem != null) {
                Intent intent = new Intent(this, ChatActivity.class);
                intent.putExtra(Constants.EXTRA_ITEM_ID, currentItem.getId());
                intent.putExtra(Constants.EXTRA_RECEIVER_ID, currentItem.getUser());
                startActivity(intent);
            }
        });

        binding.btnClaim.setOnClickListener(v -> showClaimDialog());
        binding.btnViewQr.setOnClickListener(v -> showQrDialog());
        binding.btnViewMap.setOnClickListener(v -> openMap());

        loadItemDetail();
    }

    private void loadItemDetail() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.scrollContent.setVisibility(View.GONE);

        apiService.getItemDetail(itemId).enqueue(new Callback<Item>() {
            @Override
            public void onResponse(Call<Item> call, Response<Item> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    currentItem = response.body();
                    displayItem(currentItem);
                    binding.scrollContent.setVisibility(View.VISIBLE);
                } else {
                    Toast.makeText(ItemDetailActivity.this,
                            "Failed to load item details.", Toast.LENGTH_SHORT).show();
                    finish();
                }
            }

            @Override
            public void onFailure(Call<Item> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(ItemDetailActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                finish();
            }
        });
    }

    private void displayItem(Item item) {
        binding.tvTitle.setText(item.getTitle());
        binding.tvDescription.setText(item.getDescription());

        boolean isLost = "lost".equalsIgnoreCase(item.getType());
        binding.tvTypeBadge.setText(isLost ? "LOST" : "FOUND");
        binding.tvTypeBadge.setBackgroundColor(
                ContextCompat.getColor(this, isLost ? R.color.light_red : R.color.light_green));
        binding.tvTypeBadge.setTextColor(
                ContextCompat.getColor(this, isLost ? R.color.error_red : R.color.success_green));

        binding.tvCategory.setText(item.getCategory() != null ?
                item.getCategory().replace('_', ' ') : "");

        String reporterText = "Reported by " +
                (item.getUserName() != null ? item.getUserName() : "Unknown") +
                " (" + (item.getUserRole() != null ? item.getUserRole() : "") + ")";
        binding.tvReporter.setText(reporterText);

        if (item.getLocation() != null && !item.getLocation().isEmpty()) {
            binding.layoutLocation.setVisibility(View.VISIBLE);
            binding.tvLocation.setText(item.getLocation());
        } else {
            binding.layoutLocation.setVisibility(View.GONE);
        }

        if (item.getReward() > 0) {
            binding.tvReward.setVisibility(View.VISIBLE);
            binding.tvReward.setText("Reward: Rs. " + (int) item.getReward());
        } else {
            binding.tvReward.setVisibility(View.GONE);
        }

        String imageUrl = item.getImageUrl() != null ? item.getImageUrl() : item.getImage();
        if (imageUrl != null && !imageUrl.isEmpty()) {
            binding.ivItemImage.setVisibility(View.VISIBLE);
            Glide.with(this).load(imageUrl).centerCrop().into(binding.ivItemImage);
        }

        // Hide chat/claim if user is the owner
        if (item.getUser() == sessionManager.getUserId()) {
            binding.btnChat.setVisibility(View.GONE);
            binding.btnClaim.setVisibility(View.GONE);
        }
    }

    private void showClaimDialog() {
        if (currentItem == null) return;

        EditText etDescription = new EditText(this);
        etDescription.setHint("Describe why you believe this is yours...");
        etDescription.setMinLines(3);

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(48, 32, 48, 16);
        layout.addView(etDescription);

        new AlertDialog.Builder(this)
                .setTitle("Claim This Item")
                .setMessage("Provide a description to verify your claim.")
                .setView(layout)
                .setPositiveButton("Submit Claim", (dialog, which) -> {
                    String desc = etDescription.getText().toString().trim();
                    if (desc.isEmpty()) {
                        Toast.makeText(this, "Please enter a claim description.", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    submitClaim(desc);
                })
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void submitClaim(String description) {
        Claim claim = new Claim(currentItem.getId(), description);

        apiService.submitClaim(claim).enqueue(new Callback<Claim>() {
            @Override
            public void onResponse(Call<Claim> call, Response<Claim> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(ItemDetailActivity.this,
                            "Claim submitted successfully!", Toast.LENGTH_LONG).show();
                } else {
                    Toast.makeText(ItemDetailActivity.this,
                            "Failed to submit claim.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<Claim> call, Throwable t) {
                Toast.makeText(ItemDetailActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void showQrDialog() {
        if (currentItem == null || currentItem.getQrCode() == null) {
            Toast.makeText(this, "No QR code available for this item.", Toast.LENGTH_SHORT).show();
            return;
        }

        try {
            QRCodeWriter writer = new QRCodeWriter();
            BitMatrix matrix = writer.encode(currentItem.getQrCode(),
                    BarcodeFormat.QR_CODE, 512, 512);

            int width = matrix.getWidth();
            int height = matrix.getHeight();
            Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.RGB_565);
            for (int x = 0; x < width; x++) {
                for (int y = 0; y < height; y++) {
                    bitmap.setPixel(x, y, matrix.get(x, y) ? Color.BLACK : Color.WHITE);
                }
            }

            ImageView imageView = new ImageView(this);
            imageView.setImageBitmap(bitmap);
            int padding = (int) (24 * getResources().getDisplayMetrics().density);
            imageView.setPadding(padding, padding, padding, padding);

            new AlertDialog.Builder(this)
                    .setTitle("QR Verification Code")
                    .setView(imageView)
                    .setPositiveButton("Close", null)
                    .show();
        } catch (WriterException e) {
            Toast.makeText(this, "Error generating QR code.", Toast.LENGTH_SHORT).show();
        }
    }

    private void openMap() {
        if (currentItem == null) return;

        if (currentItem.getLatitude() != null && currentItem.getLongitude() != null) {
            Uri uri = Uri.parse("geo:" + currentItem.getLatitude() + "," +
                    currentItem.getLongitude() + "?q=" + currentItem.getLatitude() +
                    "," + currentItem.getLongitude() + "(" + currentItem.getTitle() + ")");
            Intent intent = new Intent(Intent.ACTION_VIEW, uri);
            intent.setPackage("com.google.android.apps.maps");
            if (intent.resolveActivity(getPackageManager()) != null) {
                startActivity(intent);
            } else {
                Toast.makeText(this, "Google Maps not installed.", Toast.LENGTH_SHORT).show();
            }
        } else if (currentItem.getLocation() != null && !currentItem.getLocation().isEmpty()) {
            Uri uri = Uri.parse("geo:0,0?q=" + Uri.encode(currentItem.getLocation()));
            Intent intent = new Intent(Intent.ACTION_VIEW, uri);
            startActivity(intent);
        } else {
            Toast.makeText(this, "No location data available.", Toast.LENGTH_SHORT).show();
        }
    }
}
