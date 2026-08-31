package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import com.findora.app.cache.FindoraCache;
import com.findora.app.utils.SessionManager;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.adapters.ConversationAdapter;
import com.findora.app.databinding.ActivityConversationListBinding;
import com.findora.app.models.Conversation;
import com.findora.app.network.RetrofitClient;
import com.findora.app.network.ApiService;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ConversationListActivity extends BaseActivity {

    private ActivityConversationListBinding binding;
    private ConversationAdapter adapter;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityConversationListBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        setupToolbar();
        setupRecyclerView();

        // Cache-First: Display cached conversations immediately
        List<Conversation> cached = FindoraCache.getInstance(this).getCachedConversations();
        if (cached != null && !cached.isEmpty()) {
            adapter.setConversations(cached);
            binding.tvEmptyState.setVisibility(View.GONE);
            binding.progressBar.setVisibility(View.GONE);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        List<Conversation> cached = FindoraCache.getInstance(this).getCachedConversations();
        if (cached != null && !cached.isEmpty()) {
            adapter.setConversations(cached);
            binding.tvEmptyState.setVisibility(View.GONE);
        }
        loadConversations();
    }

    private void setupToolbar() {
        setSupportActionBar(binding.toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setDisplayShowTitleEnabled(true);
            getSupportActionBar().setTitle("Conversations");
        }
        binding.toolbar.setNavigationOnClickListener(v -> onBackPressed());
    }

    private void setupRecyclerView() {
        adapter = new ConversationAdapter(this, userId -> {
            Intent intent = new Intent(this, UserProfileActivity.class);
            intent.putExtra(UserProfileActivity.EXTRA_USER_ID, userId);
            startActivity(intent);
        });
        binding.rvConversations.setLayoutManager(new LinearLayoutManager(this));
        binding.rvConversations.setAdapter(adapter);
    }

    private void loadConversations() {
        if (adapter.getItemCount() == 0) {
            binding.progressBar.setVisibility(View.VISIBLE);
        }
        binding.tvEmptyState.setVisibility(View.GONE);

        apiService.getConversations().enqueue(new Callback<List<Conversation>>() {
            @Override
            public void onResponse(Call<List<Conversation>> call, Response<List<Conversation>> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    List<Conversation> list = response.body();
                    FindoraCache.getInstance(ConversationListActivity.this).saveConversations(list);
                    adapter.setConversations(list);
                    if (list.isEmpty()) {
                        binding.tvEmptyState.setVisibility(View.VISIBLE);
                    }
                } else if (adapter.getItemCount() == 0) {
                    Toast.makeText(ConversationListActivity.this, "Failed to load conversations", Toast.LENGTH_SHORT).show();
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<List<Conversation>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                if (adapter.getItemCount() == 0) {
                    Toast.makeText(ConversationListActivity.this, "Network error", Toast.LENGTH_SHORT).show();
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
                }
            }
        });
    }
}
