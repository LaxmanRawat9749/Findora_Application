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
import com.findora.app.models.Item;
import com.findora.app.models.ItemImage;
import com.findora.app.models.ConversationInitRequest;
import com.findora.app.models.ConversationInitResponse;
import com.findora.app.adapters.ItemImagePagerAdapter;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ItemDetailActivity extends AppCompatActivity {

    private ActivityItemDetailBinding binding;
    private ApiService apiService;
    private SessionManager sessionManager;
    private Item currentItem;
    private int itemId;
    private Call<Item> itemDetailCall;
    private Call<ConversationInitResponse> conversationInitCall;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityItemDetailBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        this.sessionManager = new SessionManager(this);
        if (!sessionManager.checkAndRequireSession(this)) return;

        apiService = RetrofitClient.getInstance(this).getApi();

        itemId = getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, -1);
        if (itemId == -1) {
            Toast.makeText(this, "Error: Item not found.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        binding.btnChat.setOnClickListener(v -> {
            if (currentItem != null) {
                if (currentItem.getUser() == sessionManager.getUserId()) {
                    Intent intent = new Intent(this, ConversationListActivity.class);
                    startActivity(intent);
                } else {
                    initConversation(currentItem.getId());
                }
            }
        });

        binding.btnContactFinder.setOnClickListener(v -> {
            if (currentItem != null) {
                initConversation(currentItem.getId());
            }
        });

        binding.btnViewConversations.setOnClickListener(v -> {
            Intent intent = new Intent(this, ConversationListActivity.class);
            startActivity(intent);
        });

        binding.btnViewMap.setOnClickListener(v -> openMap());

        loadItemDetail();
    }

    private void loadItemDetail() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.scrollContent.setVisibility(View.GONE);

        if (itemDetailCall != null) itemDetailCall.cancel();
        itemDetailCall = apiService.getItemDetail(itemId);
        itemDetailCall.enqueue(new Callback<Item>() {
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
                if (call.isCanceled()) return;
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
        
        if (item.getUserProfileImage() != null && !item.getUserProfileImage().isEmpty()) {
            Glide.with(this)
                    .load(item.getUserProfileImage())
                    .circleCrop()
                    .placeholder(R.drawable.ic_person)
                    .error(R.drawable.ic_person)
                    .into(binding.ivReporterAvatar);
        } else {
            binding.ivReporterAvatar.setImageResource(R.drawable.ic_person);
        }

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

        if (item.getImages() != null && !item.getImages().isEmpty()) {
            binding.vpImages.setVisibility(View.VISIBLE);
            ItemImagePagerAdapter adapter = new ItemImagePagerAdapter(item.getImages(), url -> {
                Intent intent = new Intent(this, FullScreenImageActivity.class);
                intent.putExtra(FullScreenImageActivity.EXTRA_IMAGE_URL, url);
                startActivity(intent);
            });
            binding.vpImages.setAdapter(adapter);
        } else {
            // Backwards compatibility for old items with single image
            String imageUrl = item.getImageUrl() != null ? item.getImageUrl() : item.getImage();
            if (imageUrl != null && !imageUrl.isEmpty()) {
                ItemImage oldImage = new ItemImage();
                oldImage.setImageUrl(imageUrl);
                java.util.List<ItemImage> list = new java.util.ArrayList<>();
                list.add(oldImage);
                
                binding.vpImages.setVisibility(View.VISIBLE);
                ItemImagePagerAdapter adapter = new ItemImagePagerAdapter(list, url -> {
                    Intent intent = new Intent(this, FullScreenImageActivity.class);
                    intent.putExtra(FullScreenImageActivity.EXTRA_IMAGE_URL, url);
                    startActivity(intent);
                });
                binding.vpImages.setAdapter(adapter);
            } else {
                binding.vpImages.setVisibility(View.GONE);
            }
        }

        // Check if user is the poster of the item
        if (item.getUser() == sessionManager.getUserId()) {
            binding.layoutDefaultActions.setVisibility(View.VISIBLE);
            binding.layoutFoundActions.setVisibility(View.GONE);
            binding.btnChat.setVisibility(View.VISIBLE);
            binding.btnChat.setText("View Conversations");
        } else {
            if ("found".equalsIgnoreCase(item.getType())) {
                binding.layoutDefaultActions.setVisibility(View.GONE);
                binding.layoutFoundActions.setVisibility(View.VISIBLE);
            } else {
                binding.layoutDefaultActions.setVisibility(View.VISIBLE);
                binding.layoutFoundActions.setVisibility(View.GONE);
                binding.btnChat.setVisibility(View.VISIBLE);
                binding.btnChat.setText("Contact Owner");
            }
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
    
    private void initConversation(int id) {
        binding.progressBar.setVisibility(View.VISIBLE);
        ConversationInitRequest request = new ConversationInitRequest(id);
        
        android.util.Log.e("ChatBug", "initConversation called from ItemDetailActivity! item_id=" + id + 
                ", sessionUserId=" + sessionManager.getUserId() + 
                ", currentItemOwner=" + (currentItem != null ? currentItem.getUser() : -1));

        if (conversationInitCall != null) conversationInitCall.cancel();
        conversationInitCall = apiService.initConversation(request);
        conversationInitCall.enqueue(new Callback<ConversationInitResponse>() {
            @Override
            public void onResponse(Call<ConversationInitResponse> call, Response<ConversationInitResponse> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    int conversationId = response.body().getConversationId();
                    
                    android.util.Log.e("ChatBug", "initConversation SUCCESS! returned conversation_id=" + conversationId);
                    
                    Intent intent = new Intent(ItemDetailActivity.this, ChatActivity.class);
                    intent.putExtra(Constants.EXTRA_CONVERSATION_ID, conversationId);
                    String ownerName = currentItem.getUserName() != null ? currentItem.getUserName() : "Owner";
                    intent.putExtra("other_user_name", ownerName);
                    startActivity(intent);
                } else {
                    android.util.Log.e("ChatBug", "initConversation FAILED! response code=" + response.code());
                    Toast.makeText(ItemDetailActivity.this,
                            "Failed to initiate conversation.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ConversationInitResponse> call, Throwable t) {
                if (call.isCanceled()) return;
                binding.progressBar.setVisibility(View.GONE);
                android.util.Log.e("ChatBug", "initConversation ERROR! " + t.getMessage());
                Toast.makeText(ItemDetailActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (itemDetailCall != null) itemDetailCall.cancel();
        if (conversationInitCall != null) conversationInitCall.cancel();
    }
}
