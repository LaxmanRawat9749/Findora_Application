package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.R;
import com.findora.app.adapters.MatchedItemAdapter;
import com.findora.app.databinding.ActivityMatchedItemsBinding;
import com.findora.app.models.MatchedItem;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MatchedItemsActivity extends BaseActivity {

    private ActivityMatchedItemsBinding binding;
    private ApiService apiService;
    private MatchedItemAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMatchedItemsBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        setupRecyclerView();
        loadMatches();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadMatches();
    }

    private void setupRecyclerView() {
        adapter = new MatchedItemAdapter(this, match -> {
            Intent intent = new Intent(MatchedItemsActivity.this, MatchDetailActivity.class);
            intent.putExtra("extra_match", match);
            intent.putExtra("extra_match_id", match.getId());
            startActivity(intent);
        });

        binding.rvMatches.setLayoutManager(new LinearLayoutManager(this));
        binding.rvMatches.setAdapter(adapter);

        binding.swipeRefresh.setColorSchemeColors(
                ContextCompat.getColor(this, R.color.primary_purple));
        binding.swipeRefresh.setOnRefreshListener(this::loadMatches);
    }

    private void loadMatches() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.layoutEmptyState.setVisibility(View.GONE);

        apiService.getMatches().enqueue(new Callback<List<MatchedItem>>() {
            @Override
            public void onResponse(Call<List<MatchedItem>> call, Response<List<MatchedItem>> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    List<MatchedItem> list = response.body();
                    adapter.setMatches(list);
                    if (list.isEmpty()) {
                        binding.layoutEmptyState.setVisibility(View.VISIBLE);
                    } else {
                        binding.layoutEmptyState.setVisibility(View.GONE);
                    }
                } else {
                    binding.layoutEmptyState.setVisibility(View.VISIBLE);
                }
            }

            @Override
            public void onFailure(Call<List<MatchedItem>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);
                Toast.makeText(MatchedItemsActivity.this, "Failed to load matches: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
