package com.findora.app.activities;

import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.adapters.ChatAdapter;
import com.findora.app.databinding.ActivityChatBinding;
import com.findora.app.models.ChatMessage;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ChatActivity extends AppCompatActivity {

    private ActivityChatBinding binding;
    private ApiService apiService;
    private SessionManager sessionManager;
    private ChatAdapter adapter;
    private int itemId;
    private int receiverId;
    private Handler pollHandler;
    private Runnable pollRunnable;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityChatBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();
        sessionManager = new SessionManager(this);

        itemId = getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, -1);
        receiverId = getIntent().getIntExtra(Constants.EXTRA_RECEIVER_ID, -1);

        if (itemId == -1) {
            Toast.makeText(this, "Error: Invalid chat context.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        adapter = new ChatAdapter(this, sessionManager.getUserId());
        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        layoutManager.setStackFromEnd(true);
        binding.rvMessages.setLayoutManager(layoutManager);
        binding.rvMessages.setAdapter(adapter);

        binding.btnSend.setOnClickListener(v -> sendMessage());

        // Start polling for messages
        pollHandler = new Handler(Looper.getMainLooper());
        pollRunnable = new Runnable() {
            @Override
            public void run() {
                loadMessages();
                pollHandler.postDelayed(this, Constants.CHAT_REFRESH_INTERVAL);
            }
        };

        loadMessages();
    }

    @Override
    protected void onResume() {
        super.onResume();
        pollHandler.postDelayed(pollRunnable, Constants.CHAT_REFRESH_INTERVAL);
    }

    @Override
    protected void onPause() {
        super.onPause();
        pollHandler.removeCallbacks(pollRunnable);
    }

    private void loadMessages() {
        apiService.getMessages(itemId).enqueue(new Callback<List<ChatMessage>>() {
            @Override
            public void onResponse(Call<List<ChatMessage>> call, Response<List<ChatMessage>> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    List<ChatMessage> messages = response.body();
                    adapter.setMessages(messages);
                    binding.tvEmptyState.setVisibility(messages.isEmpty() ? View.VISIBLE : View.GONE);
                    if (!messages.isEmpty()) {
                        binding.rvMessages.scrollToPosition(messages.size() - 1);
                    }
                }
            }

            @Override
            public void onFailure(Call<List<ChatMessage>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                // Silently fail on polling errors
            }
        });
    }

    private void sendMessage() {
        String text = binding.etMessage.getText().toString().trim();
        if (text.isEmpty()) return;

        binding.etMessage.setText("");

        ChatMessage msg = new ChatMessage(receiverId, itemId, text);
        apiService.sendMessage(msg).enqueue(new Callback<ChatMessage>() {
            @Override
            public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                if (response.isSuccessful() && response.body() != null) {
                    adapter.addMessage(response.body());
                    binding.rvMessages.scrollToPosition(adapter.getItemCount() - 1);
                    binding.tvEmptyState.setVisibility(View.GONE);
                } else {
                    Toast.makeText(ChatActivity.this,
                            "Failed to send message.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ChatMessage> call, Throwable t) {
                Toast.makeText(ChatActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        pollHandler.removeCallbacks(pollRunnable);
    }
}
