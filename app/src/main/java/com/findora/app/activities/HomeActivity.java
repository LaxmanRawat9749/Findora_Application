package com.findora.app.activities;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Toast;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.R;
import com.findora.app.adapters.ItemAdapter;
import com.findora.app.databinding.ActivityHomeBinding;
import com.findora.app.models.Item;
import com.findora.app.models.Notification;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import com.google.android.material.chip.Chip;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class HomeActivity extends BaseActivity {

    private ActivityHomeBinding binding;
    private ApiService apiService;
    
    private ItemAdapter adapter;

    private String currentType = null; // null = all
    private String currentCategory = null; // null = all
    private String currentSearch = "";
    
    private List<Item> originalItemList = new ArrayList<>();

    private final ActivityResultLauncher<Intent> voiceSearchLauncher = 
            registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    ArrayList<String> matches = result.getData().getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
                    if (matches != null && !matches.isEmpty()) {
                        String query = matches.get(0);
                        binding.etHomeSearch.setVisibility(View.VISIBLE);
                        binding.etHomeSearch.setText(query);
                        // currentSearch is updated by the TextWatcher automatically
                    }
                }
            });

    private final ActivityResultLauncher<String> requestAudioPermissionLauncher = 
            registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
                if (isGranted) {
                    launchVoiceIntent();
                } else {
                    if (!shouldShowRequestPermissionRationale(Manifest.permission.RECORD_AUDIO)) {
                        showSettingsDialog();
                    } else {
                        Toast.makeText(this, "Microphone permission is required for voice search.", Toast.LENGTH_SHORT).show();
                    }
                }
            });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityHomeBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        

        apiService = RetrofitClient.getInstance(this).getApi();

        setupRecyclerView();
        setupChipFilters();
        setupCategoryChips();
        setupSearchBar();
        setupBottomNav();

        binding.btnHomeSearch.setOnClickListener(v -> {
            startActivity(new Intent(this, SearchActivity.class));
        });

        binding.btnNotifications.setOnClickListener(v -> {
            startActivity(new Intent(this, NotificationsActivity.class));
        });

        binding.btnVoiceSearch.setOnClickListener(v -> startVoiceSearch());

        updateGreeting();
        loadItems();
    }

    @Override
    protected void onResume() {
        super.onResume();
        baseSessionManager.updateLastActivity();
        updateGreeting();
        if (binding.bottomNav.getSelectedItemId() != R.id.nav_home) {
            binding.bottomNav.getMenu().findItem(R.id.nav_home).setChecked(true);
        }
        loadItems();
        updateNotificationBadge();
        loadPointsPill();
    }

    private void loadPointsPill() {
        apiService.getReputation().enqueue(new Callback<com.findora.app.models.FinderReputation>() {
            @Override
            public void onResponse(Call<com.findora.app.models.FinderReputation> call, Response<com.findora.app.models.FinderReputation> response) {
                if (response.isSuccessful() && response.body() != null) {
                    int points = response.body().getTotalPoints();
                    if (points > 0) {
                        binding.tvHomePointsPill.setText("🪙 " + points + " pts");
                        binding.tvHomePointsPill.setVisibility(View.VISIBLE);
                        binding.tvHomePointsPill.setOnClickListener(v -> {
                            startActivity(new Intent(HomeActivity.this, PointHistoryActivity.class));
                        });
                    } else {
                        binding.tvHomePointsPill.setVisibility(View.GONE);
                    }
                } else {
                    binding.tvHomePointsPill.setVisibility(View.GONE);
                }
            }

            @Override
            public void onFailure(Call<com.findora.app.models.FinderReputation> call, Throwable t) {
                binding.tvHomePointsPill.setVisibility(View.GONE);
            }
        });
    }

    private void setupRecyclerView() {
        adapter = new ItemAdapter(this, item -> {
            Intent intent = new Intent(HomeActivity.this, ItemDetailActivity.class);
            intent.putExtra(Constants.EXTRA_ITEM_ID, item.getId());
            startActivity(intent);
        });
        binding.rvItems.setLayoutManager(new LinearLayoutManager(this));
        binding.rvItems.setAdapter(adapter);

        binding.swipeRefresh.setColorSchemeColors(
                ContextCompat.getColor(this, R.color.primary_purple));
        binding.swipeRefresh.setOnRefreshListener(this::loadItems);
    }

    private void setupChipFilters() {
        binding.cgType.setOnCheckedStateChangeListener((group, checkedIds) -> {
            if (checkedIds.isEmpty()) {
                binding.chipAll.setChecked(true);
                return;
            }
            int checkedId = checkedIds.get(0);
            if (checkedId == R.id.chipAll) {
                currentType = null;
            } else if (checkedId == R.id.chipLost) {
                currentType = "lost";
            } else if (checkedId == R.id.chipFound) {
                currentType = "found";
            }
            // Clear search when switching tabs
            binding.etHomeSearch.setText("");
            currentSearch = "";
            loadItems();
        });
    }

    private void setupCategoryChips() {
        // Dynamically add category chips
        for (int i = 0; i < Constants.CATEGORIES.length; i++) {
            Chip chip = new Chip(this);
            chip.setText(Constants.CATEGORY_LABELS[i]);
            chip.setCheckable(true);
            final String categoryKey = Constants.CATEGORIES[i];
            chip.setOnCheckedChangeListener((buttonView, isChecked) -> {
                if (isChecked) {
                    currentCategory = categoryKey;
                    binding.chipCatAll.setChecked(false);
                    binding.etHomeSearch.setText("");
                    currentSearch = "";
                    applyFilters();
                }
            });
            binding.cgCategory.addView(chip);
        }

        binding.chipCatAll.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (isChecked) {
                currentCategory = null;
                // Uncheck all other category chips
                for (int i = 1; i < binding.cgCategory.getChildCount(); i++) {
                    View child = binding.cgCategory.getChildAt(i);
                    if (child instanceof Chip) {
                        ((Chip) child).setChecked(false);
                    }
                }
                binding.etHomeSearch.setText("");
                currentSearch = "";
                applyFilters();
            }
        });
    }

    private void setupSearchBar() {
        binding.etHomeSearch.addTextChangedListener(new android.text.TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}

            @Override
            public void onTextChanged(CharSequence s, int start, int before, int count) {}

            @Override
            public void afterTextChanged(android.text.Editable s) {
                currentSearch = s.toString().trim();
                applyFilters();
            }
        });

        binding.etHomeSearch.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                // Focus can be cleared or keyboard hidden here if desired
                return true;
            }
            return false;
        });
    }

    private void setupBottomNav() {
        binding.bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                return true;
            } else if (id == R.id.nav_report) {
                startActivity(new Intent(this, UploadItemActivity.class));
                overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
                return true; 
            } else if (id == R.id.nav_profile) {
                startActivity(new Intent(this, ProfileActivity.class));
                overridePendingTransition(android.R.anim.fade_in, android.R.anim.fade_out);
                return true; 
            }
            return false;
        });
    }

    private void loadItems() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.tvEmptyState.setVisibility(View.GONE);

        Call<List<Item>> call;
        if (currentType != null && !currentType.isEmpty()) {
            call = apiService.filterByType(currentType);
        } else {
            call = apiService.getItems();
        }

        call.enqueue(new Callback<List<Item>>() {
            @Override
            public void onResponse(Call<List<Item>> call, Response<List<Item>> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    originalItemList = response.body();
                    applyFilters();
                } else {
                    originalItemList = new ArrayList<>();
                    applyFilters();
                }
            }

            @Override
            public void onFailure(Call<List<Item>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);
                Toast.makeText(HomeActivity.this, "Error loading items: " + t.getMessage(),
                        Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void applyFilters() {
        if (originalItemList == null) return;
        
        List<Item> filtered = new ArrayList<>();
        String searchLower = currentSearch.toLowerCase().trim();
        
        for (Item item : originalItemList) {
            boolean matchCat = currentCategory == null || currentCategory.equalsIgnoreCase(item.getCategory());
            
            if (!matchCat) continue;
            
            if (searchLower.isEmpty()) {
                filtered.add(item);
            } else {
                String catLower = item.getCategory() != null ? item.getCategory().toLowerCase().trim() : "";
                String titleLower = item.getTitle() != null ? item.getTitle().toLowerCase().trim() : "";
                String descLower = item.getDescription() != null ? item.getDescription().toLowerCase().trim() : "";
                
                if (catLower.equals(searchLower) || catLower.contains(searchLower) || 
                    titleLower.contains(searchLower) || descLower.contains(searchLower)) {
                    filtered.add(item);
                }
            }
        }
        
        
        adapter.setItems(filtered);
        binding.tvEmptyState.setVisibility(filtered.isEmpty() ? View.VISIBLE : View.GONE);
    }
    
    private int getMatchScore(Item item, String searchLower) {
        String catLower = item.getCategory() != null ? item.getCategory().toLowerCase().trim() : "";
        String titleLower = item.getTitle() != null ? item.getTitle().toLowerCase().trim() : "";
        String descLower = item.getDescription() != null ? item.getDescription().toLowerCase().trim() : "";
        
        if (catLower.equals(searchLower)) return 4;
        if (catLower.contains(searchLower)) return 3;
        if (titleLower.contains(searchLower)) return 2;
        if (descLower.contains(searchLower)) return 1;
        
        return 0;
    }

    private void updateNotificationBadge() {
        apiService.getNotifications().enqueue(new Callback<List<Notification>>() {
            @Override
            public void onResponse(Call<List<Notification>> call, Response<List<Notification>> response) {
                if (response.isSuccessful() && response.body() != null) {
                    int unreadCount = 0;
                    for (Notification n : response.body()) {
                        if (!n.isRead()) {
                            unreadCount++;
                        }
                    }
                    if (unreadCount > 0) {
                        binding.tvNotificationBadge.setVisibility(View.VISIBLE);
                        binding.tvNotificationBadge.setText(unreadCount > 99 ? "99+" : String.valueOf(unreadCount));
                    } else {
                        binding.tvNotificationBadge.setVisibility(View.GONE);
                    }
                }
            }

            @Override
            public void onFailure(Call<List<Notification>> call, Throwable t) {
                // Do nothing on failure for badge
            }
        });
    }

    private void updateGreeting() {
        String fullName = baseSessionManager.getFullName();
        String username = baseSessionManager.getUsername();
        String nameToDisplay = null;

        if (fullName != null && !fullName.trim().isEmpty()) {
            nameToDisplay = fullName.trim();
        } else if (username != null && !username.trim().isEmpty()) {
            nameToDisplay = username.trim();
        }

        if (nameToDisplay != null && !nameToDisplay.isEmpty()) {
            binding.tvGreeting.setText("Hello, " + nameToDisplay + " 👋");
        } else {
            binding.tvGreeting.setText("Hello 👋");
        }
    }

    private void startVoiceSearch() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            launchVoiceIntent();
        } else {
            requestAudioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO);
        }
    }

    private void launchVoiceIntent() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Speak now to search");
        
        try {
            voiceSearchLauncher.launch(intent);
        } catch (Exception e) {
            Toast.makeText(this, "Speech recognition is not supported on this device.", Toast.LENGTH_SHORT).show();
        }
    }

    private void showSettingsDialog() {
        new com.google.android.material.dialog.MaterialAlertDialogBuilder(this)
            .setTitle("Permission Required")
            .setMessage("Microphone permission is required for voice search. Please enable it in app settings.")
            .setPositiveButton("Settings", (dialog, which) -> {
                Intent intent = new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                android.net.Uri uri = android.net.Uri.fromParts("package", getPackageName(), null);
                intent.setData(uri);
                startActivity(intent);
            })
            .setNegativeButton("Cancel", null)
            .show();
    }
}
