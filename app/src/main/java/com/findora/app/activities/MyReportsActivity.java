package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.recyclerview.widget.LinearLayoutManager;

import com.findora.app.adapters.ItemAdapter;
import com.findora.app.databinding.ActivityMyReportsBinding;
import com.findora.app.models.Item;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;

import java.util.ArrayList;
import java.util.List;

import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class MyReportsActivity extends BaseActivity {

    public static final String EXTRA_FILTER_TYPE = "extra_filter_type";

    private ActivityMyReportsBinding binding;
    private ItemAdapter adapter;
    private List<Item> itemList = new ArrayList<>();
    private ApiService apiService;
    private String filterType;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityMyReportsBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        filterType = getIntent().getStringExtra(EXTRA_FILTER_TYPE);
        if ("lost".equalsIgnoreCase(filterType)) {
            binding.toolbar.setTitle("My Lost Reports");
        } else if ("found".equalsIgnoreCase(filterType)) {
            binding.toolbar.setTitle("My Found Reports");
        } else if ("resolved".equalsIgnoreCase(filterType)) {
            binding.toolbar.setTitle("My Recovered Items");
        }

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        adapter = new ItemAdapter(this, true, item -> {
            Intent intent = new Intent(this, ItemDetailActivity.class);
            intent.putExtra(Constants.EXTRA_ITEM_ID, item.getId());
            startActivity(intent);
        });

        binding.recyclerView.setLayoutManager(new LinearLayoutManager(this));
        binding.recyclerView.setAdapter(adapter);

        binding.swipeRefresh.setOnRefreshListener(this::loadItems);

        loadItems();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadItems();
    }

    private void loadItems() {
        binding.swipeRefresh.setRefreshing(true);
        apiService.getMyReports().enqueue(new Callback<List<Item>>() {
            @Override
            public void onResponse(Call<List<Item>> call, Response<List<Item>> response) {
                binding.swipeRefresh.setRefreshing(false);
                if (response.isSuccessful() && response.body() != null) {
                    itemList.clear();
                    List<Item> allItems = response.body();
                    if (filterType != null && !filterType.isEmpty()) {
                        for (Item item : allItems) {
                            if ("lost".equalsIgnoreCase(filterType) && "lost".equalsIgnoreCase(item.getType())) {
                                itemList.add(item);
                            } else if ("found".equalsIgnoreCase(filterType) && "found".equalsIgnoreCase(item.getType())) {
                                itemList.add(item);
                            } else if ("resolved".equalsIgnoreCase(filterType) && ("resolved".equalsIgnoreCase(item.getStatus()) || item.isFinderReturnedConfirm())) {
                                itemList.add(item);
                            }
                        }
                    } else {
                        itemList.addAll(allItems);
                    }
                    adapter.setItems(itemList);
                    updateEmptyState();
                } else {
                    Toast.makeText(MyReportsActivity.this, "Failed to load reports", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<List<Item>> call, Throwable t) {
                binding.swipeRefresh.setRefreshing(false);
                Toast.makeText(MyReportsActivity.this, "Network error", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void updateEmptyState() {
        if (itemList.isEmpty()) {
            binding.recyclerView.setVisibility(View.GONE);
            binding.layoutEmpty.setVisibility(View.VISIBLE);
        } else {
            binding.recyclerView.setVisibility(View.VISIBLE);
            binding.layoutEmpty.setVisibility(View.GONE);
        }
    }
}
