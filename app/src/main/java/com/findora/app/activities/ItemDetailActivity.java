package com.findora.app.activities;

import android.app.AlertDialog;
import android.content.res.ColorStateList;
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
import com.findora.app.models.MessageResponse;

public class ItemDetailActivity extends BaseActivity {

    private ActivityItemDetailBinding binding;
    private ApiService apiService;
    
    private Item currentItem;
    private int itemId;
    private int passedConversationId = -1;
    private Call<Item> itemDetailCall;
    private Call<ConversationInitResponse> conversationInitCall;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityItemDetailBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        itemId = getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, -1);
        passedConversationId = getIntent().getIntExtra(Constants.EXTRA_CONVERSATION_ID, -1);
        if (itemId == -1) {
            Toast.makeText(this, "Error: Item not found.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        binding.btnChat.setOnClickListener(v -> {
            if (passedConversationId != -1) {
                openChatForConversation(passedConversationId);
            } else if (currentItem != null) {
                initConversation(currentItem.getId());
            }
        });

        binding.btnContactFinder.setOnClickListener(v -> {
            if (passedConversationId != -1) {
                openChatForConversation(passedConversationId);
            } else if (currentItem != null) {
                initConversation(currentItem.getId());
            }
        });

        binding.btnViewConversations.setOnClickListener(v -> {
            if (passedConversationId != -1) {
                openChatForConversation(passedConversationId);
            } else if (currentItem != null) {
                initConversation(currentItem.getId());
            } else {
                Intent intent = new Intent(this, ConversationListActivity.class);
                startActivity(intent);
            }
        });

        binding.btnViewMap.setOnClickListener(v -> openMap());

        binding.btnMarkReturned.setOnClickListener(v -> handleMarkReturned());
        binding.btnConfirmReturn.setOnClickListener(v -> handleConfirmReturn());

        binding.layoutReporter.setOnClickListener(v -> {
            if (currentItem != null && currentItem.getUser() != -1) {
                Intent intent = new Intent(this, UserProfileActivity.class);
                intent.putExtra(UserProfileActivity.EXTRA_USER_ID, currentItem.getUser());
                startActivity(intent);
            }
        });

        binding.btnPromote.setOnClickListener(v -> {
            if (currentItem != null) {
                Intent intent = new Intent(this, PromoteItemActivity.class);
                intent.putExtra(Constants.EXTRA_ITEM_ID, currentItem.getId());
                startActivity(intent);
            }
        });

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

        if (item.isFeatured()) {
            binding.tvFeaturedBadge.setVisibility(View.VISIBLE);
        } else {
            binding.tvFeaturedBadge.setVisibility(View.GONE);
        }

        binding.tvCategory.setText(item.getCategory() != null ?
                item.getCategory().replace('_', ' ') : "");

        String reporterText = "Reported by " +
                (item.getUserName() != null ? item.getUserName() : "Unknown") +
                " (" + (item.getUserRole() != null ? item.getUserRole() : "") + ")";
        binding.tvReporter.setText(reporterText);
        
        if (item.getUserProfileImage() != null && !item.getUserProfileImage().isEmpty()) {
            binding.ivReporterAvatar.setImageTintList(null);
            Glide.with(this)
                    .load(item.getUserProfileImage())
                    .circleCrop()
                    .placeholder(R.drawable.ic_person)
                    .error(R.drawable.ic_person)
                    .into(binding.ivReporterAvatar);
        } else {
            binding.ivReporterAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                    ContextCompat.getColor(this, R.color.primary_purple)));
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

        binding.layoutReturnActions.setVisibility(View.GONE);
        binding.layoutOwnerActions.setVisibility(View.GONE);
        binding.btnMarkReturned.setVisibility(View.GONE);
        binding.btnConfirmReturn.setVisibility(View.GONE);
        binding.tvReturnedBadge.setVisibility(View.GONE);
        binding.cvRateFinder.setVisibility(View.GONE);

        if ("resolved".equalsIgnoreCase(item.getStatus())) {
            binding.layoutDefaultActions.setVisibility(View.GONE);
            binding.layoutFoundActions.setVisibility(View.GONE);
            binding.tvReturnedBadge.setVisibility(View.VISIBLE);
            checkRatingStatus();
        } else {
            // Check if user is the poster of the item
            if (item.getUser() == baseSessionManager.getUserId()) {
                if (!item.isFeatured()) {
                    binding.layoutOwnerActions.setVisibility(View.VISIBLE);
                }
                binding.layoutDefaultActions.setVisibility(View.VISIBLE);
                binding.layoutFoundActions.setVisibility(View.GONE);
                binding.btnChat.setVisibility(View.VISIBLE);
                binding.btnChat.setText("View Conversations");
                
                if (!item.isOwnerReturnedConfirm()) {
                    binding.layoutReturnActions.setVisibility(View.VISIBLE);
                    binding.btnMarkReturned.setVisibility(View.VISIBLE);
                }
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
                
                if (item.isOwnerReturnedConfirm() && !item.isFinderReturnedConfirm()) {
                    binding.layoutReturnActions.setVisibility(View.VISIBLE);
                    binding.btnConfirmReturn.setVisibility(View.VISIBLE);
                }
            }
        }
    }

    private void checkRatingStatus() {
        if (currentItem == null || !"owner".equalsIgnoreCase(baseSessionManager.getRole())) {
            binding.cvRateFinder.setVisibility(View.GONE);
            return;
        }
        apiService.getRatingStatus(currentItem.getId()).enqueue(new Callback<com.findora.app.models.RatingStatusResponse>() {
            @Override
            public void onResponse(Call<com.findora.app.models.RatingStatusResponse> call, Response<com.findora.app.models.RatingStatusResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    com.findora.app.models.RatingStatusResponse status = response.body();
                    if (status.isCanRate() && !status.isHasRated()) {
                        binding.cvRateFinder.setVisibility(View.VISIBLE);
                        binding.tvRateTitle.setText("Rate the Finder");
                        binding.tvRateSubtitle.setText("Reward your finder with positive reputation & points");
                        binding.btnRateFinder.setText("Rate ⭐");
                        binding.btnRateFinder.setEnabled(true);
                        binding.btnRateFinder.setOnClickListener(v -> showRatingDialog());
                    } else if (status.isHasRated() && status.getRating() != null) {
                        binding.cvRateFinder.setVisibility(View.VISIBLE);
                        binding.tvRateTitle.setText("Finder Rated");
                        binding.tvRateSubtitle.setText("You gave " + status.getRating().getRating() + " / 5 stars ⭐");
                        binding.btnRateFinder.setText("Rated ✓");
                        binding.btnRateFinder.setEnabled(false);
                    } else {
                        binding.cvRateFinder.setVisibility(View.GONE);
                    }
                }
            }

            @Override
            public void onFailure(Call<com.findora.app.models.RatingStatusResponse> call, Throwable t) {
                // Non-critical
            }
        });
    }

    private int selectedRatingValue = 0;

    private void showRatingDialog() {
        if (currentItem == null) return;

        com.google.android.material.bottomsheet.BottomSheetDialog dialog =
                new com.google.android.material.bottomsheet.BottomSheetDialog(this);
        com.findora.app.databinding.DialogRateFinderBinding dialogBinding =
                com.findora.app.databinding.DialogRateFinderBinding.inflate(getLayoutInflater());
        dialog.setContentView(dialogBinding.getRoot());

        selectedRatingValue = 0;
        updateStarViews(dialogBinding, selectedRatingValue);

        dialogBinding.ivStar1.setOnClickListener(v -> { selectedRatingValue = 1; updateStarViews(dialogBinding, 1); });
        dialogBinding.ivStar2.setOnClickListener(v -> { selectedRatingValue = 2; updateStarViews(dialogBinding, 2); });
        dialogBinding.ivStar3.setOnClickListener(v -> { selectedRatingValue = 3; updateStarViews(dialogBinding, 3); });
        dialogBinding.ivStar4.setOnClickListener(v -> { selectedRatingValue = 4; updateStarViews(dialogBinding, 4); });
        dialogBinding.ivStar5.setOnClickListener(v -> { selectedRatingValue = 5; updateStarViews(dialogBinding, 5); });

        dialogBinding.btnCancelRating.setOnClickListener(v -> dialog.dismiss());

        dialogBinding.btnSubmitRating.setOnClickListener(v -> {
            if (selectedRatingValue < 1 || selectedRatingValue > 5) {
                Toast.makeText(ItemDetailActivity.this, "Please select a rating.", Toast.LENGTH_SHORT).show();
                return;
            }

            String review = dialogBinding.etReview.getText() != null ?
                    dialogBinding.etReview.getText().toString().trim() : "";

            dialogBinding.pbRatingLoading.setVisibility(View.VISIBLE);
            dialogBinding.btnSubmitRating.setEnabled(false);

            com.findora.app.models.RateRequest request =
                    new com.findora.app.models.RateRequest(currentItem.getId(), selectedRatingValue, review);

            apiService.rateFinder(request).enqueue(new Callback<com.findora.app.models.FinderRating>() {
                @Override
                public void onResponse(Call<com.findora.app.models.FinderRating> call, Response<com.findora.app.models.FinderRating> response) {
                    dialogBinding.pbRatingLoading.setVisibility(View.GONE);
                    if (response.isSuccessful()) {
                        Toast.makeText(ItemDetailActivity.this, "Thank you for rating the Finder.", Toast.LENGTH_SHORT).show();
                        dialog.dismiss();
                        checkRatingStatus();
                    } else {
                        dialogBinding.btnSubmitRating.setEnabled(true);
                        Toast.makeText(ItemDetailActivity.this, "Failed to submit rating.", Toast.LENGTH_SHORT).show();
                    }
                }

                @Override
                public void onFailure(Call<com.findora.app.models.FinderRating> call, Throwable t) {
                    dialogBinding.pbRatingLoading.setVisibility(View.GONE);
                    dialogBinding.btnSubmitRating.setEnabled(true);
                    Toast.makeText(ItemDetailActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        });

        dialog.show();
    }

    private void updateStarViews(com.findora.app.databinding.DialogRateFinderBinding db, int rating) {
        ImageView[] stars = { db.ivStar1, db.ivStar2, db.ivStar3, db.ivStar4, db.ivStar5 };
        int yellowColor = ContextCompat.getColor(this, R.color.warning_orange);
        int grayColor = ContextCompat.getColor(this, R.color.text_disabled);

        for (int i = 0; i < 5; i++) {
            if (i < rating) {
                stars[i].setImageResource(android.R.drawable.star_big_on);
                stars[i].setImageTintList(ColorStateList.valueOf(yellowColor));
            } else {
                stars[i].setImageResource(android.R.drawable.star_big_off);
                stars[i].setImageTintList(ColorStateList.valueOf(grayColor));
            }
        }

        switch (rating) {
            case 5:
                db.tvRatingHint.setText("5 Stars — Excellent (+10 Finder Points)");
                db.tvRatingHint.setTextColor(ContextCompat.getColor(this, R.color.primary_purple));
                break;
            case 4:
                db.tvRatingHint.setText("4 Stars — Good (+10 Finder Points)");
                db.tvRatingHint.setTextColor(ContextCompat.getColor(this, R.color.primary_purple));
                break;
            case 3:
                db.tvRatingHint.setText("3 Stars — Average");
                db.tvRatingHint.setTextColor(ContextCompat.getColor(this, R.color.text_gray));
                break;
            case 2:
                db.tvRatingHint.setText("2 Stars — Below Average");
                db.tvRatingHint.setTextColor(ContextCompat.getColor(this, R.color.text_gray));
                break;
            case 1:
                db.tvRatingHint.setText("1 Star — Poor");
                db.tvRatingHint.setTextColor(ContextCompat.getColor(this, R.color.text_gray));
                break;
            default:
                db.tvRatingHint.setText("Tap a star to rate");
                db.tvRatingHint.setTextColor(ContextCompat.getColor(this, R.color.text_gray));
                break;
        }
    }

    private void handleMarkReturned() {
        if (currentItem == null) return;
        new AlertDialog.Builder(this)
                .setTitle("Mark as Returned")
                .setMessage("Are you sure you want to mark this item as returned? The finder will be notified to confirm.")
                .setPositiveButton("Yes", (dialog, which) -> callMarkReturned())
                .setNegativeButton("No", null)
                .show();
    }

    private void callMarkReturned() {
        binding.progressBar.setVisibility(View.VISIBLE);
        apiService.markItemReturned(currentItem.getId()).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful()) {
                    Toast.makeText(ItemDetailActivity.this, "Item marked as returned", Toast.LENGTH_SHORT).show();
                    loadItemDetail();
                } else {
                    Toast.makeText(ItemDetailActivity.this, "Failed to mark as returned", Toast.LENGTH_SHORT).show();
                }
            }
            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(ItemDetailActivity.this, "Network error", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void handleConfirmReturn() {
        if (currentItem == null) return;
        new AlertDialog.Builder(this)
                .setTitle("Confirm Return")
                .setMessage("Are you sure you want to confirm the return of this item? This will resolve the listing.")
                .setPositiveButton("Yes", (dialog, which) -> callConfirmReturn())
                .setNegativeButton("No", null)
                .show();
    }

    private void callConfirmReturn() {
        binding.progressBar.setVisibility(View.VISIBLE);
        apiService.confirmItemReturn(currentItem.getId()).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful()) {
                    Toast.makeText(ItemDetailActivity.this, "Return confirmed successfully", Toast.LENGTH_SHORT).show();
                    loadItemDetail();
                } else {
                    Toast.makeText(ItemDetailActivity.this, "Failed to confirm return", Toast.LENGTH_SHORT).show();
                }
            }
            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(ItemDetailActivity.this, "Network error", Toast.LENGTH_SHORT).show();
            }
        });
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
    
    private void openChatForConversation(int convId) {
        Intent intent = new Intent(ItemDetailActivity.this, ChatActivity.class);
        intent.putExtra(Constants.EXTRA_CONVERSATION_ID, convId);
        intent.putExtra("ITEM_ID", currentItem != null ? currentItem.getId() : itemId);
        if (currentItem != null) {
            if ("lost".equalsIgnoreCase(currentItem.getType())) {
                intent.putExtra("OWNER_ID", currentItem.getUser());
                intent.putExtra("FINDER_ID", baseSessionManager.getUserId());
            } else {
                intent.putExtra("OWNER_ID", baseSessionManager.getUserId());
                intent.putExtra("FINDER_ID", currentItem.getUser());
            }
            String otherName = currentItem.getUserName() != null ? currentItem.getUserName() : "Chat";
            intent.putExtra("other_user_name", otherName);
        }
        startActivity(intent);
    }
    
    private void initConversation(int id) {
        binding.progressBar.setVisibility(View.VISIBLE);
        ConversationInitRequest request = new ConversationInitRequest(id);
        
        android.util.Log.e("ChatBug", "initConversation called from ItemDetailActivity! item_id=" + id + 
                ", sessionUserId=" + baseSessionManager.getUserId() + 
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
                    openChatForConversation(conversationId);
                } else {
                    android.util.Log.e("ChatBug", "initConversation FAILED! response code=" + response.code());
                    if (currentItem != null && currentItem.getUser() == baseSessionManager.getUserId()) {
                        Intent intent = new Intent(ItemDetailActivity.this, ConversationListActivity.class);
                        startActivity(intent);
                    } else {
                        Toast.makeText(ItemDetailActivity.this,
                                "Failed to initiate conversation.", Toast.LENGTH_SHORT).show();
                    }
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
