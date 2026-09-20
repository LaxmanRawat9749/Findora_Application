package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.core.content.ContextCompat;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.databinding.ActivityMatchDetailBinding;
import com.findora.app.models.ConversationInitRequest;
import com.findora.app.models.ConversationInitResponse;
import com.findora.app.models.Item;
import com.findora.app.models.MatchedItem;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import java.util.Map;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MatchDetailActivity extends BaseActivity {

    private ActivityMatchDetailBinding binding;
    private ApiService apiService;
    private MatchedItem match;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        if (isFinishing()) return;

        binding = ActivityMatchDetailBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();
        binding.toolbar.setNavigationOnClickListener(v -> finish());

        if (getIntent() != null && getIntent().hasExtra("extra_match")) {
            match = (MatchedItem) getIntent().getSerializableExtra("extra_match");
            displayMatchDetails(match);
        } else if (getIntent() != null && getIntent().hasExtra("extra_match_id")) {
            int matchId = getIntent().getIntExtra("extra_match_id", 0);
            loadMatchDetail(matchId);
        } else {
            Toast.makeText(this, "Match details not found.", Toast.LENGTH_SHORT).show();
            finish();
        }
    }

    private void loadMatchDetail(int matchId) {
        apiService.getMatchDetail(matchId).enqueue(new Callback<MatchedItem>() {
            @Override
            public void onResponse(Call<MatchedItem> call, Response<MatchedItem> response) {
                if (response.isSuccessful() && response.body() != null) {
                    match = response.body();
                    displayMatchDetails(match);
                } else {
                    Toast.makeText(MatchDetailActivity.this, "Failed to load match details.", Toast.LENGTH_SHORT).show();
                    finish();
                }
            }

            @Override
            public void onFailure(Call<MatchedItem> call, Throwable t) {
                Toast.makeText(MatchDetailActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                finish();
            }
        });
    }

    private void displayMatchDetails(MatchedItem match) {
        if (match == null) return;

        int score = match.getMatchScore();
        binding.tvMatchScoreLarge.setText(score + "%");

        if (score >= 75) {
            binding.tvConfidenceLevel.setText("HIGH CONFIDENCE MATCH");
            binding.tvConfidenceLevel.setTextColor(ContextCompat.getColor(this, R.color.success_green));
            binding.tvConfidenceLevel.setBackgroundResource(R.drawable.bg_badge_found);
            binding.tvMatchScoreLarge.setTextColor(ContextCompat.getColor(this, R.color.primary_purple));
        } else {
            binding.tvConfidenceLevel.setText("POTENTIAL MATCH");
            binding.tvConfidenceLevel.setTextColor(ContextCompat.getColor(this, R.color.warning_orange));
            binding.tvConfidenceLevel.setBackgroundResource(R.drawable.bg_badge_warning);
            binding.tvMatchScoreLarge.setTextColor(ContextCompat.getColor(this, R.color.warning_orange));
        }

        // Display match reasons
        if (match.getMatchedReasons() != null && !match.getMatchedReasons().isEmpty()) {
            StringBuilder sb = new StringBuilder();
            for (String reason : match.getMatchedReasons()) {
                sb.append("✓  ").append(reason).append("\n");
            }
            binding.tvReasonsList.setText(sb.toString().trim());
            binding.layoutReasons.setVisibility(View.VISIBLE);
        } else {
            binding.layoutReasons.setVisibility(View.GONE);
        }

        Item lost = match.getLostItem();
        Item found = match.getFoundItem();

        // Populate Lost Item Card
        if (lost != null) {
            binding.tvLostDetailTitle.setText(lost.getTitle());
            binding.tvLostDetailReporter.setText("Reported by: " + (lost.getUserName() != null ? lost.getUserName() : "Owner"));
            
            String loc = lost.getLocation() != null ? lost.getLocation() : "Unknown location";
            String date = lost.getItemDate() != null ? lost.getItemDate() : (lost.getReportedAt() != null ? lost.getReportedAt().substring(0, Math.min(10, lost.getReportedAt().length())) : "");
            binding.tvLostDetailLocationDate.setText("Location: " + loc + " | Date: " + date);
            binding.tvLostDetailDesc.setText(lost.getDescription() != null ? lost.getDescription() : "");

            formatAttributes(binding.tvLostDetailCredentials, lost.getCategoryAttributes());

            if (lost.getImageUrl() != null && !lost.getImageUrl().isEmpty()) {
                binding.ivLostPhoto.setVisibility(View.VISIBLE);
                Glide.with(this).load(lost.getImageUrl()).into(binding.ivLostPhoto);
            } else {
                binding.ivLostPhoto.setVisibility(View.GONE);
            }
        }

        // Populate Found Item Card
        if (found != null) {
            binding.tvFoundDetailTitle.setText(found.getTitle());
            binding.tvFoundDetailReporter.setText("Reported by: " + (found.getUserName() != null ? found.getUserName() : "Finder"));

            String loc = found.getLocation() != null ? found.getLocation() : "Unknown location";
            String date = found.getItemDate() != null ? found.getItemDate() : (found.getReportedAt() != null ? found.getReportedAt().substring(0, Math.min(10, found.getReportedAt().length())) : "");
            binding.tvFoundDetailLocationDate.setText("Location: " + loc + " | Date: " + date);
            binding.tvFoundDetailDesc.setText(found.getDescription() != null ? found.getDescription() : "");

            formatAttributes(binding.tvFoundDetailCredentials, found.getCategoryAttributes());

            if (found.getImageUrl() != null && !found.getImageUrl().isEmpty()) {
                binding.ivFoundPhoto.setVisibility(View.VISIBLE);
                Glide.with(this).load(found.getImageUrl()).into(binding.ivFoundPhoto);
            } else {
                binding.ivFoundPhoto.setVisibility(View.GONE);
            }
        }

        // Setup Chat Button
        boolean isOwner = "owner".equalsIgnoreCase(baseSessionManager.getRole());
        String targetName = isOwner 
                ? (found != null && found.getUserName() != null ? found.getUserName() : "Finder")
                : (lost != null && lost.getUserName() != null ? lost.getUserName() : "Owner");
        binding.btnChat.setText("Message " + targetName);

        binding.btnChat.setOnClickListener(v -> initiateChat(match));
    }

    private void formatAttributes(android.widget.TextView textView, Map<String, String> attrs) {
        if (attrs != null && !attrs.isEmpty()) {
            StringBuilder sb = new StringBuilder("Verification Credentials:\n");
            for (Map.Entry<String, String> entry : attrs.entrySet()) {
                String key = entry.getKey().replace('_', ' ');
                key = key.substring(0, 1).toUpperCase() + key.substring(1);
                sb.append("• ").append(key).append(": ").append(entry.getValue()).append("\n");
            }
            textView.setText(sb.toString().trim());
            textView.setVisibility(View.VISIBLE);
        } else {
            textView.setVisibility(View.GONE);
        }
    }

    private void initiateChat(MatchedItem match) {
        int targetItemId = match.getFoundItem() != null ? match.getFoundItem().getId() : (match.getLostItem() != null ? match.getLostItem().getId() : 0);
        if (targetItemId == 0) {
            Toast.makeText(this, "Cannot initiate chat for this item.", Toast.LENGTH_SHORT).show();
            return;
        }

        binding.btnChat.setEnabled(false);
        apiService.initConversation(new ConversationInitRequest(targetItemId)).enqueue(new Callback<ConversationInitResponse>() {
            @Override
            public void onResponse(Call<ConversationInitResponse> call, Response<ConversationInitResponse> response) {
                binding.btnChat.setEnabled(true);
                if (response.isSuccessful() && response.body() != null && response.body().getConversationId() > 0) {
                    Intent intent = new Intent(MatchDetailActivity.this, ChatActivity.class);
                    intent.putExtra(Constants.EXTRA_CONVERSATION_ID, response.body().getConversationId());
                    intent.putExtra("ITEM_ID", targetItemId);
                    startActivity(intent);
                } else {
                    Toast.makeText(MatchDetailActivity.this, "Failed to start conversation.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ConversationInitResponse> call, Throwable t) {
                binding.btnChat.setEnabled(true);
                Toast.makeText(MatchDetailActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
