package com.findora.app.activities;

import android.os.Bundle;
import com.findora.app.utils.SessionManager;
import android.view.View;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;
import com.findora.app.R;
import com.findora.app.databinding.ActivityUserProfileBinding;
import com.findora.app.models.PublicProfile;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class UserProfileActivity extends BaseActivity {
    

    public static final String EXTRA_USER_ID = "extra_user_id";

    private ActivityUserProfileBinding binding;
    private ApiService apiService;
    private int userId;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityUserProfileBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        userId = getIntent().getIntExtra(EXTRA_USER_ID, -1);
        if (userId == -1) {
            Toast.makeText(this, "Invalid User ID", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());
        binding.btnBack.setOnClickListener(v -> finish());
        binding.btnChat.setOnClickListener(v -> finish()); // Since this is typically opened from Chat

        loadProfile();
    }

    private void loadProfile() {
        binding.progressBar.setVisibility(View.VISIBLE);
        apiService.getPublicProfile(userId).enqueue(new Callback<PublicProfile>() {
            @Override
            public void onResponse(Call<PublicProfile> call, Response<PublicProfile> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    populateUI(response.body());
                } else {
                    Toast.makeText(UserProfileActivity.this, "Failed to load profile", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<PublicProfile> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(UserProfileActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void populateUI(PublicProfile profile) {
        binding.tvFullName.setText(profile.getFullName());
        binding.tvUsername.setText("@" + profile.getUsername());
        
        String role = profile.getRole();
        if (role != null && !role.isEmpty()) {
            binding.chipRole.setText(role.substring(0, 1).toUpperCase() + role.substring(1));
        }

        String createdAt = profile.getCreatedAt();
        if (createdAt != null && createdAt.length() >= 10) {
            // E.g. "2024-05-12T..."
            binding.tvMemberSince.setText("Member since " + createdAt.substring(0, 10));
        }

        binding.tvLostCount.setText(String.valueOf(profile.getLostReports()));
        binding.tvFoundCount.setText(String.valueOf(profile.getFoundReports()));
        binding.tvRecoveredCount.setText(String.valueOf(profile.getRecoveredItems()));

        if (profile.getProfileImage() != null && !profile.getProfileImage().isEmpty()) {
            binding.ivProfilePicture.setImageTintList(null);
            Glide.with(this)
                    .load(profile.getProfileImage())
                    .circleCrop()
                    .placeholder(R.drawable.ic_person)
                    .error(R.drawable.ic_person)
                    .diskCacheStrategy(DiskCacheStrategy.ALL)
                    .into(binding.ivProfilePicture);
        } else {
            binding.ivProfilePicture.setImageTintList(android.content.res.ColorStateList.valueOf(
                    getResources().getColor(R.color.primary_purple, null)));
            binding.ivProfilePicture.setImageResource(R.drawable.ic_person);
        }
    }
}
