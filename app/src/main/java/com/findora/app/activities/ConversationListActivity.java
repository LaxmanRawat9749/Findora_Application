package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
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

public class ConversationListActivity extends AppCompatActivity {
    private SessionManager sessionManager;

    private ActivityConversationListBinding binding;
    private ConversationAdapter adapter;
    private ApiService apiService;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityConversationListBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        this.sessionManager = new SessionManager(this);
        if (!sessionManager.checkAndRequireSession(this)) return;

        apiService = RetrofitClient.getInstance(this).getApi();

        setupToolbar();
        setupRecyclerView();
    }

    @Override
    protected void onResume() {
        super.onResume();
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
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.tvEmptyState.setVisibility(View.GONE);

        apiService.getConversations().enqueue(new Callback<List<Conversation>>() {
            @Override
            public void onResponse(Call<List<Conversation>> call, Response<List<Conversation>> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    List<Conversation> list = response.body();
                    adapter.setConversations(list);
                    if (list.isEmpty()) {
                        binding.tvEmptyState.setVisibility(View.VISIBLE);
                    }
                } else {
                    Toast.makeText(ConversationListActivity.this, "Failed to load conversations", Toast.LENGTH_SHORT).show();
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<List<Conversation>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(ConversationListActivity.this, "Network error", Toast.LENGTH_SHORT).show();
                binding.tvEmptyState.setVisibility(View.VISIBLE);
            }
        });
    }
}
