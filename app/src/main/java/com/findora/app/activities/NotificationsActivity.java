package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.adapters.NotificationAdapter;
import com.findora.app.databinding.ActivityNotificationsBinding;
import com.findora.app.models.ConversationInitRequest;
import com.findora.app.models.ConversationInitResponse;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.Notification;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import java.util.ArrayList;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class NotificationsActivity extends BaseActivity {

    public static List<Notification> cachedNotifications = null;

    private ActivityNotificationsBinding binding;
    private ApiService apiService;
    private NotificationAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityNotificationsBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        adapter = new NotificationAdapter(this, this::handleNotificationClick);

        binding.rvNotifications.setLayoutManager(new LinearLayoutManager(this));
        binding.rvNotifications.setAdapter(adapter);

        if (cachedNotifications != null && !cachedNotifications.isEmpty()) {
            adapter.setNotifications(cachedNotifications);
            binding.progressBar.setVisibility(View.GONE);
            binding.tvEmptyState.setVisibility(View.GONE);
            loadNotifications(false);
        } else {
            loadNotifications(true);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (cachedNotifications != null && !cachedNotifications.isEmpty()) {
            loadNotifications(false);
        }
    }

    private void handleNotificationClick(Notification notification) {
        if (notification == null) return;

        // Mark as read in background
        markAsRead(notification);

        String type = notification.getType() != null ? notification.getType().trim().toLowerCase() : "";
        String message = notification.getMessage() != null ? notification.getMessage() : "";
        Integer relatedItem = notification.getRelatedItem();

        boolean isReturn = isReturnNotification(type, message);

        // 1. CHAT NOTIFICATION
        if ("message".equals(type) && !isReturn) {
            openChatNotification(notification);
            return;
        }

        // 2. RETURN NOTIFICATION
        if (isReturn || "claim".equals(type)) {
            openReturnNotification(notification);
            return;
        }

        // 3. RATING NOTIFICATION
        if ("rating".equals(type) || message.toLowerCase().contains("rate your finder")) {
            openRatingNotification(notification);
            return;
        }

        // 4. REPUTATION / BADGE NOTIFICATION
        if ("badge".equals(type)) {
            Intent intent = new Intent(this, ProfileActivity.class);
            startActivity(intent);
            return;
        }
        if ("reputation".equals(type)) {
            Intent intent = new Intent(this, PointHistoryActivity.class);
            startActivity(intent);
            return;
        }

        // 5. ITEM NOTIFICATION (approved, rejected, match)
        if ("approved".equals(type) || "rejected".equals(type) || "match".equals(type)) {
            if (relatedItem != null && relatedItem > 0) {
                Intent intent = new Intent(this, ItemDetailActivity.class);
                intent.putExtra(Constants.EXTRA_ITEM_ID, relatedItem.intValue());
                startActivity(intent);
            } else {
                Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
            }
            return;
        }

        // 6. GENERAL NOTIFICATION / Fallback
        if (relatedItem != null && relatedItem > 0 && !"message".equals(type)) {
            Intent intent = new Intent(this, ItemDetailActivity.class);
            intent.putExtra(Constants.EXTRA_ITEM_ID, relatedItem.intValue());
            startActivity(intent);
        } else {
            Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
        }
    }

    private boolean isReturnNotification(String type, String message) {
        if ("claim".equalsIgnoreCase(type)) {
            return true;
        }
        if (message == null) return false;
        String lower = message.toLowerCase();
        return (lower.contains("marked") && lower.contains("returned"))
                || lower.contains("confirmed the return")
                || lower.contains("return confirmation")
                || lower.contains("item is now resolved");
    }

    private void openChatNotification(Notification notification) {
        if (notification.getConversationId() != null && notification.getConversationId() > 0) {
            Intent intent = new Intent(this, ChatActivity.class);
            intent.putExtra(Constants.EXTRA_CONVERSATION_ID, notification.getConversationId().intValue());
            if (notification.getRelatedItem() != null && notification.getRelatedItem() > 0) {
                intent.putExtra("ITEM_ID", notification.getRelatedItem().intValue());
            }
            startActivity(intent);
        } else if (notification.getRelatedItem() != null && notification.getRelatedItem() > 0) {
            binding.progressBar.setVisibility(View.VISIBLE);
            apiService.initConversation(new ConversationInitRequest(notification.getRelatedItem().intValue()))
                    .enqueue(new Callback<ConversationInitResponse>() {
                        @Override
                        public void onResponse(Call<ConversationInitResponse> call, Response<ConversationInitResponse> response) {
                            binding.progressBar.setVisibility(View.GONE);
                            if (response.isSuccessful() && response.body() != null) {
                                int convId = response.body().getConversationId();
                                notification.setConversationId(convId);
                                Intent intent = new Intent(NotificationsActivity.this, ChatActivity.class);
                                intent.putExtra(Constants.EXTRA_CONVERSATION_ID, convId);
                                intent.putExtra("ITEM_ID", notification.getRelatedItem().intValue());
                                startActivity(intent);
                            } else {
                                Toast.makeText(NotificationsActivity.this, "Unable to open conversation.", Toast.LENGTH_SHORT).show();
                            }
                        }

                        @Override
                        public void onFailure(Call<ConversationInitResponse> call, Throwable t) {
                            binding.progressBar.setVisibility(View.GONE);
                            Toast.makeText(NotificationsActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                        }
                    });
        } else {
            Toast.makeText(this, notification.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void openReturnNotification(Notification notification) {
        if (notification.getRelatedItem() != null && notification.getRelatedItem() > 0) {
            Intent intent = new Intent(this, ItemDetailActivity.class);
            intent.putExtra(Constants.EXTRA_ITEM_ID, notification.getRelatedItem().intValue());
            startActivity(intent);
        } else {
            Toast.makeText(this, notification.getMessage(), Toast.LENGTH_SHORT).show();
        }
    }

    private void openRatingNotification(Notification notification) {
        String msg = notification.getMessage() != null ? notification.getMessage().toLowerCase() : "";
        if (msg.contains("you received") || "finder".equalsIgnoreCase(baseSessionManager.getRole())) {
            if (notification.getRelatedItem() != null && notification.getRelatedItem() > 0) {
                Intent intent = new Intent(this, ItemDetailActivity.class);
                intent.putExtra(Constants.EXTRA_ITEM_ID, notification.getRelatedItem().intValue());
                startActivity(intent);
            } else {
                Intent intent = new Intent(this, PointHistoryActivity.class);
                startActivity(intent);
            }
        } else {
            if (notification.getRelatedItem() != null && notification.getRelatedItem() > 0) {
                Intent intent = new Intent(this, ItemDetailActivity.class);
                intent.putExtra(Constants.EXTRA_ITEM_ID, notification.getRelatedItem().intValue());
                intent.putExtra(ItemDetailActivity.EXTRA_AUTO_OPEN_RATING, true);
                startActivity(intent);
            } else {
                Toast.makeText(this, notification.getMessage(), Toast.LENGTH_SHORT).show();
            }
        }
    }

    private void loadNotifications(boolean showProgress) {
        if (showProgress) {
            binding.progressBar.setVisibility(View.VISIBLE);
            binding.tvEmptyState.setVisibility(View.GONE);
        }

        apiService.getNotifications().enqueue(new Callback<List<Notification>>() {
            @Override
            public void onResponse(Call<List<Notification>> call, Response<List<Notification>> response) {
                binding.progressBar.setVisibility(View.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    List<Notification> notifications = response.body();
                    cachedNotifications = notifications;
                    adapter.setNotifications(notifications);
                    binding.tvEmptyState.setVisibility(
                            notifications.isEmpty() ? View.VISIBLE : View.GONE);
                } else if (cachedNotifications == null || cachedNotifications.isEmpty()) {
                    cachedNotifications = new ArrayList<>();
                    adapter.setNotifications(cachedNotifications);
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<List<Notification>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                if (cachedNotifications == null || cachedNotifications.isEmpty()) {
                    Toast.makeText(NotificationsActivity.this,
                            "Error loading notifications.", Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void markAsRead(Notification notification) {
        if (notification.isRead()) return;

        apiService.markNotificationRead(notification.getId()).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                notification.setRead(true);
                if (cachedNotifications != null) {
                    for (Notification n : cachedNotifications) {
                        if (n.getId() == notification.getId()) {
                            n.setRead(true);
                            break;
                        }
                    }
                }
                adapter.notifyDataSetChanged();
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                // Ignore — non-critical
            }
        });
    }
}
