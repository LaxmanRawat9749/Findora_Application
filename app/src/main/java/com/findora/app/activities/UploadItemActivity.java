package com.findora.app.activities;

import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityUploadItemBinding;
import com.findora.app.models.Item;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class UploadItemActivity extends AppCompatActivity {

    private ActivityUploadItemBinding binding;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityUploadItemBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        // Setup category spinner
        ArrayAdapter<String> categoryAdapter = new ArrayAdapter<>(
                this, android.R.layout.simple_spinner_item, Constants.CATEGORY_LABELS);
        categoryAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        binding.spinnerCategory.setAdapter(categoryAdapter);

        binding.btnSubmit.setOnClickListener(v -> submitReport());
    }

    private void submitReport() {
        String type = binding.rbLost.isChecked() ? "lost" : "found";
        String title = binding.etTitle.getText().toString().trim();
        String location = binding.etLocation.getText().toString().trim();
        String rewardStr = binding.etReward.getText().toString().trim();
        String description = binding.etDescription.getText().toString().trim();
        int categoryIdx = binding.spinnerCategory.getSelectedItemPosition();
        String category = Constants.CATEGORIES[categoryIdx];

        if (title.isEmpty()) {
            Toast.makeText(this, "Please enter a title.", Toast.LENGTH_SHORT).show();
            return;
        }

        if (description.isEmpty()) {
            Toast.makeText(this, "Please enter a description.", Toast.LENGTH_SHORT).show();
            return;
        }

        setLoading(true);

        Item item = new Item();
        item.setType(type);
        item.setTitle(title);
        item.setDescription(description);
        item.setCategory(category);
        item.setLocation(location);
        if (!rewardStr.isEmpty()) {
            try {
                item.setReward(Double.parseDouble(rewardStr));
            } catch (NumberFormatException e) {
                // ignore invalid reward
            }
        }

        apiService.reportItem(item).enqueue(new Callback<Item>() {
            @Override
            public void onResponse(Call<Item> call, Response<Item> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    Toast.makeText(UploadItemActivity.this,
                            "Item reported successfully! Awaiting admin approval.",
                            Toast.LENGTH_LONG).show();
                    finish();
                } else {
                    Toast.makeText(UploadItemActivity.this,
                            "Failed to submit report. Please try again.",
                            Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<Item> call, Throwable t) {
                setLoading(false);
                Toast.makeText(UploadItemActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnSubmit.setEnabled(!loading);
    }
}
