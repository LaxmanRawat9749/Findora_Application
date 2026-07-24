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
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.R;
import com.findora.app.adapters.ItemAdapter;
import com.findora.app.databinding.ActivityHomeBinding;
import com.findora.app.models.Item;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import com.google.android.material.chip.Chip;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class HomeActivity extends AppCompatActivity {

    private static final int RC_AUDIO_PERM = 1001;

    private ActivityHomeBinding binding;
    private ApiService apiService;
    private SessionManager sessionManager;
    private ItemAdapter adapter;

    private String currentType = null; // null = all
    private String currentCategory = null; // null = all
    private String currentSearch = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityHomeBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        sessionManager = new SessionManager(this);
        apiService = RetrofitClient.getInstance(this).getApi();

        setupRecyclerView();
        setupChipFilters();
        setupCategoryChips();
        setupSearchBar();
        setupBottomNav();

        binding.fabUpload.setOnClickListener(v ->
                startActivity(new Intent(this, UploadItemActivity.class)));

        binding.btnHomeSearch.setOnClickListener(v -> {
            binding.etHomeSearch.setVisibility(
                    binding.etHomeSearch.getVisibility() == View.VISIBLE ? View.GONE : View.VISIBLE);
            if (binding.etHomeSearch.getVisibility() == View.VISIBLE) {
                binding.etHomeSearch.requestFocus();
            }
        });

        binding.btnVoiceSearch.setOnClickListener(v -> startVoiceSearch());

        loadItems();
    }

    @Override
    protected void onResume() {
        super.onResume();
        loadItems();
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
                    loadItems();
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
                loadItems();
            }
        });
    }

    private void setupSearchBar() {
        binding.etHomeSearch.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                currentSearch = binding.etHomeSearch.getText().toString().trim();
                loadItems();
                return true;
            }
            return false;
        });
    }

    private void setupBottomNav() {
        binding.bottomNav.setOnItemSelectedListener(item -> {
            int id = item.getItemId();
            if (id == R.id.nav_home) {
                // Already on home
                return true;
            } else if (id == R.id.nav_notifications) {
                startActivity(new Intent(this, NotificationsActivity.class));
                return true;
            } else if (id == R.id.nav_profile) {
                startActivity(new Intent(this, ProfileActivity.class));
                return true;
            }
            return false;
        });
    }

    private void loadItems() {
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.tvEmptyState.setVisibility(View.GONE);

        apiService.getItems().enqueue(new Callback<List<Item>>() {
            @Override
            public void onResponse(Call<List<Item>> call, Response<List<Item>> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.swipeRefresh.setRefreshing(false);

                if (response.isSuccessful() && response.body() != null) {
                    List<Item> items = response.body();
                    // Local filtering as a fallback
                    List<Item> filtered = new ArrayList<>();
                    for (Item item : items) {
                        boolean matchType = currentType == null || currentType.equalsIgnoreCase(item.getType());
                        boolean matchCat = currentCategory == null || currentCategory.equalsIgnoreCase(item.getCategory());
                        boolean matchSearch = currentSearch.isEmpty() || 
                                (item.getTitle() != null && item.getTitle().toLowerCase().contains(currentSearch.toLowerCase()));
                        
                        if (matchType && matchCat && matchSearch) {
                            filtered.add(item);
                        }
                    }
                    adapter.setItems(filtered);
                    binding.tvEmptyState.setVisibility(filtered.isEmpty() ? View.VISIBLE : View.GONE);
                } else {
                    adapter.setItems(new ArrayList<>());
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
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

    private void startVoiceSearch() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO}, RC_AUDIO_PERM);
            return;
        }

        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            Toast.makeText(this, "Speech recognition not available on this device.",
                    Toast.LENGTH_SHORT).show();
            return;
        }

        SpeechRecognizer recognizer = SpeechRecognizer.createSpeechRecognizer(this);
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());

        recognizer.setRecognitionListener(new RecognitionListener() {
            @Override public void onReadyForSpeech(Bundle params) {
                Toast.makeText(HomeActivity.this, "Listening...", Toast.LENGTH_SHORT).show();
            }
            @Override public void onBeginningOfSpeech() {}
            @Override public void onRmsChanged(float rmsdB) {}
            @Override public void onBufferReceived(byte[] buffer) {}
            @Override public void onEndOfSpeech() {}
            @Override public void onError(int error) {
                Toast.makeText(HomeActivity.this, "Voice recognition error.", Toast.LENGTH_SHORT).show();
            }
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(
                        SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String query = matches.get(0);
                    binding.etHomeSearch.setVisibility(View.VISIBLE);
                    binding.etHomeSearch.setText(query);
                    currentSearch = query;
                    loadItems();
                }
                recognizer.destroy();
            }
            @Override public void onPartialResults(Bundle partialResults) {}
            @Override public void onEvent(int eventType, Bundle params) {}
        });

        recognizer.startListening(intent);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == RC_AUDIO_PERM && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            startVoiceSearch();
        }
    }
}
