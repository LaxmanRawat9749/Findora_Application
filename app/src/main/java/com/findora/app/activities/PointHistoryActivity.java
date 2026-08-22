package com.findora.app.activities;

import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.adapters.PointTransactionAdapter;
import com.findora.app.databinding.ActivityPointHistoryBinding;
import com.findora.app.models.FinderReputation;
import com.findora.app.models.PointTransaction;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import java.util.List;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class PointHistoryActivity extends BaseActivity {

    private ActivityPointHistoryBinding binding;
    private ApiService apiService;
    private PointTransactionAdapter adapter;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityPointHistoryBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        adapter = new PointTransactionAdapter(this);
        binding.rvTransactions.setLayoutManager(new LinearLayoutManager(this));
        binding.rvTransactions.setAdapter(adapter);

        binding.swipeRefresh.setOnRefreshListener(this::loadData);

        loadData();
    }

    private void loadData() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.layoutEmptyState.setVisibility(View.GONE);

        // 1. Fetch current reputation & total points
        apiService.getReputation().enqueue(new Callback<FinderReputation>() {
            @Override
            public void onResponse(Call<FinderReputation> call, Response<FinderReputation> response) {
                if (response.isSuccessful() && response.body() != null) {
                    binding.tvTotalPoints.setText(String.valueOf(response.body().getTotalPoints()));
                }
            }

            @Override
            public void onFailure(Call<FinderReputation> call, Throwable t) {
                // Non-fatal, fallback to previous value
            }
        });

        // 2. Fetch point ledger transactions
        apiService.getPointHistory().enqueue(new Callback<List<PointTransaction>>() {
            @Override
            public void onResponse(Call<List<PointTransaction>> call, Response<List<PointTransaction>> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    List<PointTransaction> transactions = response.body();
                    adapter.setTransactions(transactions);
                    binding.layoutEmptyState.setVisibility(transactions.isEmpty() ? View.VISIBLE : View.GONE);
                } else {
                    binding.layoutEmptyState.setVisibility(View.VISIBLE);
                    Toast.makeText(PointHistoryActivity.this, "Failed to load transaction history.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<PointTransaction>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);
                binding.layoutEmptyState.setVisibility(View.VISIBLE);
                Toast.makeText(PointHistoryActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }
}
