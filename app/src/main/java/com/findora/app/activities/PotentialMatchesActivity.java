package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.R;
import com.findora.app.adapters.PotentialMatchAdapter;
import com.findora.app.databinding.ActivityPotentialMatchesBinding;
import com.findora.app.models.PotentialMatch;
import com.findora.app.models.StartVerificationRequest;
import com.findora.app.models.VerificationSession;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;
import java.util.List;

public class PotentialMatchesActivity extends BaseActivity implements PotentialMatchAdapter.OnMatchActionListener {

    private ActivityPotentialMatchesBinding binding;
    private ApiService apiService;
    private PotentialMatchAdapter adapter;
    private int itemId = -1;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityPotentialMatchesBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        if (getIntent() != null && getIntent().hasExtra(Constants.EXTRA_ITEM_ID)) {
            itemId = getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, -1);
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());
        if (itemId > 0) {
            binding.toolbar.setTitle("Item Matches");
        }

        int currentUserId = baseSessionManager.getUserId();
        adapter = new PotentialMatchAdapter(this, currentUserId, this);
        binding.rvPotentialMatches.setLayoutManager(new LinearLayoutManager(this));
        binding.rvPotentialMatches.setAdapter(adapter);

        binding.swipeRefreshLayout.setOnRefreshListener(this::loadPotentialMatches);

        loadPotentialMatches();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadPotentialMatches();
    }

    private void loadPotentialMatches() {
        binding.swipeRefreshLayout.setRefreshing(true);
        binding.layoutEmptyState.setVisibility(View.GONE);

        Call<List<PotentialMatch>> call;
        if (itemId > 0) {
            call = apiService.getItemPotentialMatches(itemId);
        } else {
            call = apiService.getPotentialMatches();
        }

        call.enqueue(new Callback<List<PotentialMatch>>() {
            @Override
            public void onResponse(Call<List<PotentialMatch>> call, Response<List<PotentialMatch>> response) {
                binding.swipeRefreshLayout.setRefreshing(false);
                if (response.isSuccessful() && response.body() != null) {
                    List<PotentialMatch> matches = response.body();
                    adapter.setMatches(matches);
                    if (matches.isEmpty()) {
                        binding.layoutEmptyState.setVisibility(View.VISIBLE);
                        binding.rvPotentialMatches.setVisibility(View.GONE);
                    } else {
                        binding.layoutEmptyState.setVisibility(View.GONE);
                        binding.rvPotentialMatches.setVisibility(View.VISIBLE);
                    }
                } else {
                    binding.layoutEmptyState.setVisibility(View.VISIBLE);
                    binding.rvPotentialMatches.setVisibility(View.GONE);
                }
            }

            @Override
            public void onFailure(Call<List<PotentialMatch>> call, Throwable t) {
                binding.swipeRefreshLayout.setRefreshing(false);
                Toast.makeText(PotentialMatchesActivity.this, "Failed to load matches: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    @Override
    public void onViewItemClick(int counterpartItemId) {
        if (counterpartItemId <= 0) return;
        Intent intent = new Intent(this, ItemDetailActivity.class);
        intent.putExtra(Constants.EXTRA_ITEM_ID, counterpartItemId);
        startActivity(intent);
    }

    @Override
    public void onVerifyClick(PotentialMatch match) {
        if (match == null) return;

        if (match.getVerificationRequestId() != null && match.getVerificationRequestId() > 0) {
            // Already has an active verification session, open it directly
            Intent intent = new Intent(this, VerificationActivity.class);
            intent.putExtra(VerificationActivity.EXTRA_VERIFICATION_ID, match.getVerificationRequestId());
            startActivity(intent);
        } else {
            // Start a new verification session
            binding.progressBar.setVisibility(View.VISIBLE);
            StartVerificationRequest req = new StartVerificationRequest(
                    match.getLostItem(),
                    match.getFoundItem(),
                    match.getId()
            );

            apiService.startVerification(req).enqueue(new Callback<VerificationSession>() {
                @Override
                public void onResponse(Call<VerificationSession> call, Response<VerificationSession> response) {
                    binding.progressBar.setVisibility(View.GONE);
                    if (response.isSuccessful() && response.body() != null) {
                        Intent intent = new Intent(PotentialMatchesActivity.this, VerificationActivity.class);
                        intent.putExtra(VerificationActivity.EXTRA_VERIFICATION_ID, response.body().getId());
                        startActivity(intent);
                    } else {
                        Toast.makeText(PotentialMatchesActivity.this, "Could not start verification session.", Toast.LENGTH_SHORT).show();
                    }
                }

                @Override
                public void onFailure(Call<VerificationSession> call, Throwable t) {
                    binding.progressBar.setVisibility(View.GONE);
                    Toast.makeText(PotentialMatchesActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        }
    }
}
