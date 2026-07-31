package com.findora.app.activities;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Bundle;
import com.findora.app.utils.SessionManager;
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
import com.findora.app.adapters.ItemAdapter;
import com.findora.app.databinding.ActivitySearchBinding;
import com.findora.app.models.Item;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class SearchActivity extends AppCompatActivity {
    private SessionManager sessionManager;

    private ActivitySearchBinding binding;
    private ApiService apiService;
    private ItemAdapter adapter;

    private final ActivityResultLauncher<Intent> voiceSearchLauncher = 
            registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    ArrayList<String> matches = result.getData().getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
                    if (matches != null && !matches.isEmpty()) {
                        String query = matches.get(0);
                        binding.etSearchQuery.setText(query);
                        performSearch(query);
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
        binding = ActivitySearchBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        this.sessionManager = new SessionManager(this);
        if (!sessionManager.checkAndRequireSession(this)) return;

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        adapter = new ItemAdapter(this, item -> {
            Intent intent = new Intent(SearchActivity.this, ItemDetailActivity.class);
            intent.putExtra(Constants.EXTRA_ITEM_ID, item.getId());
            startActivity(intent);
        });
        binding.rvSearchItems.setLayoutManager(new LinearLayoutManager(this));
        binding.rvSearchItems.setAdapter(adapter);

        binding.etSearchQuery.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_SEARCH) {
                performSearch(binding.etSearchQuery.getText().toString().trim());
                return true;
            }
            return false;
        });

        binding.btnVoiceSearch.setOnClickListener(v -> startVoiceSearch());

        // Focus the search input
        binding.etSearchQuery.requestFocus();
    }

    private void performSearch(String query) {
        if (query.isEmpty()) {
            Toast.makeText(this, "Please enter a search query.", Toast.LENGTH_SHORT).show();
            return;
        }

        binding.progressBar.setVisibility(View.VISIBLE);
        binding.tvEmptyState.setVisibility(View.GONE);

        apiService.searchItems(query).enqueue(new Callback<List<Item>>() {
            @Override
            public void onResponse(Call<List<Item>> call, Response<List<Item>> response) {
                binding.progressBar.setVisibility(View.GONE);
                if (response.isSuccessful() && response.body() != null) {
                    List<Item> results = response.body();
                    adapter.setItems(results);
                    binding.tvEmptyState.setVisibility(results.isEmpty() ? View.VISIBLE : View.GONE);
                    if (results.isEmpty()) {
                        binding.tvEmptyState.setText("No items found for \"" + query + "\"");
                    }
                } else {
                    adapter.setItems(new ArrayList<>());
                    binding.tvEmptyState.setVisibility(View.VISIBLE);
                    binding.tvEmptyState.setText("Search failed. Please try again.");
                }
            }

            @Override
            public void onFailure(Call<List<Item>> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                Toast.makeText(SearchActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
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
