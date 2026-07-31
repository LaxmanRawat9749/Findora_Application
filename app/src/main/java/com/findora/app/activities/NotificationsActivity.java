package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import com.findora.app.utils.SessionManager;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.adapters.NotificationAdapter;
import com.findora.app.databinding.ActivityNotificationsBinding;
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

        adapter = new NotificationAdapter(this, notification -> {
            // Mark as read
            markAsRead(notification);

            // Navigate to related item if exists
            if (notification.getRelatedItem() != null && notification.getRelatedItem() > 0) {
                Intent intent = new Intent(NotificationsActivity.this, ItemDetailActivity.class);
                intent.putExtra(Constants.EXTRA_ITEM_ID, notification.getRelatedItem().intValue());
                startActivity(intent);
            }
        });

        binding.rvNotifications.setLayoutManager(new LinearLayoutManager(this));
        binding.rvNotifications.setAdapter(adapter);

        loadNotifications();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadNotifications();
    }

    private void loadNotifications() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.tvEmptyState.setVisibility(View.GONE);

        apiService.getNotifications().enqueue(new Callback<List<Notification>>() {
            @Override
            public void onResponse(Call<List<Notification>> call, Response<List<Notification>> response) {
                binding.progressBar.setVisibility(View.GONE);

                if (response.isSuccessful() && response.body() != null) {
                    List<Notification> notifications = response.body();
                    adapter.setNotifications(notifications);
                    binding.tvEmptyState.setVisibility(
                            notifications.isEmpty() ? View.VISIBLE : View.GONE);
                } else {
                    adapter.setNotifications(new ArrayList<>());
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<List<Notification>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(NotificationsActivity.this,
                        "Error loading notifications.", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void markAsRead(Notification notification) {
        if (notification.isRead()) return;

        apiService.markNotificationRead(notification.getId()).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                // Silently mark as read — refresh on resume will update state
                notification.setRead(true);
                adapter.notifyDataSetChanged();
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                // Ignore — non-critical
            }
        });
    }
}
