package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import com.findora.app.databinding.ActivityProfileBinding;
import com.findora.app.models.ChangePasswordRequest;
import com.findora.app.models.ChangeUsernameRequest;
import com.findora.app.models.ChangeUsernameResponse;
import com.findora.app.models.MessageResponse;
import com.findora.app.models.RefreshRequest;
import com.findora.app.models.User;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.SessionManager;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

import android.Manifest;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.provider.MediaStore;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;
import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;
import com.google.android.material.bottomsheet.BottomSheetDialog;
import com.yalantis.ucrop.UCrop;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import com.findora.app.R;


public class ProfileActivity extends BaseActivity {

    private ActivityProfileBinding binding;
    private ApiService apiService;
    
    private boolean isPasswordFormVisible = false;
    private boolean isUsernameFormVisible = false;

    private Uri currentPhotoUri;
    private BottomSheetDialog bottomSheetDialog;

    private final ActivityResultLauncher<String> requestCameraPermissionLauncher =
            registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
                if (isGranted) {
                    launchCamera();
                } else {
                    if (!shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)) {
                        showSettingsDialog();
                    } else {
                        Toast.makeText(this, "Camera permission denied", Toast.LENGTH_SHORT).show();
                    }
                }
            });

    private final ActivityResultLauncher<Uri> takePictureLauncher =
            registerForActivityResult(new ActivityResultContracts.TakePicture(), success -> {
                if (success && currentPhotoUri != null) {
                    startCrop(currentPhotoUri);
                }
            });

    private final ActivityResultLauncher<String> pickImageLauncher =
            registerForActivityResult(new ActivityResultContracts.GetContent(), uri -> {
                if (uri != null) {
                    startCrop(uri);
                }
            });
            
    private final ActivityResultLauncher<Intent> cropImageLauncher = 
            registerForActivityResult(new ActivityResultContracts.StartActivityForResult(), result -> {
                if (result.getResultCode() == RESULT_OK && result.getData() != null) {
                    Uri resultUri = UCrop.getOutput(result.getData());
                    if (resultUri != null) {
                        uploadProfilePicture(resultUri);
                    }
                } else if (result.getResultCode() == UCrop.RESULT_ERROR) {
                    Throwable cropError = UCrop.getError(result.getData());
                    Toast.makeText(this, "Crop error: " + (cropError != null ? cropError.getMessage() : "Unknown"), Toast.LENGTH_SHORT).show();
                }
            });

    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityProfileBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService     = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        // Do NOT pre-populate UI from SharedPreferences cache here.
        // The cache belongs to the previously authenticated user — showing it
        // before the API confirms the current session is what caused another
        // user's name/email to be displayed to a new unauthenticated user.
        // The API call below is authoritative; cached data is only a fallback.
        binding.tvFullName.setText("");
        binding.tvEmail.setText("");
        binding.tvRole.setText("");

        // Load fresh profile from API — UI is populated only when this returns
        loadProfile();

        // Change username toggle
        binding.btnToggleChangeUsername.setOnClickListener(v -> {
            isUsernameFormVisible = !isUsernameFormVisible;
            binding.layoutChangeUsernameForm.setVisibility(
                    isUsernameFormVisible ? View.VISIBLE : View.GONE);
            binding.btnToggleChangeUsername.setText(isUsernameFormVisible ? "Hide" : "Show");
        });

        // Update username
        binding.btnUpdateUsername.setOnClickListener(v -> attemptChangeUsername());

        // Change password toggle
        binding.btnToggleChangePassword.setOnClickListener(v -> {
            isPasswordFormVisible = !isPasswordFormVisible;
            binding.layoutChangePasswordForm.setVisibility(
                    isPasswordFormVisible ? View.VISIBLE : View.GONE);
            binding.btnToggleChangePassword.setText(isPasswordFormVisible ? "Hide" : "Show");
        });

        // Update password
        binding.btnUpdatePassword.setOnClickListener(v -> attemptChangePassword());
        binding.btnLogout.setOnClickListener(v -> logout());

        binding.btnMyReports.setOnClickListener(v -> {
            Intent intent = new Intent(this, MyReportsActivity.class);
            startActivity(intent);
        });

        // Setup Theme Toggle
        int currentTheme = baseSessionManager.getThemeMode();
        if (currentTheme == androidx.appcompat.app.AppCompatDelegate.MODE_NIGHT_NO) {
            binding.rbThemeLight.setChecked(true);
        } else {
            binding.rbThemeDark.setChecked(true);
        }

        binding.rgTheme.setOnCheckedChangeListener((group, checkedId) -> {
            int newTheme = (checkedId == R.id.rbThemeLight) 
                    ? androidx.appcompat.app.AppCompatDelegate.MODE_NIGHT_NO 
                    : androidx.appcompat.app.AppCompatDelegate.MODE_NIGHT_YES;
            baseSessionManager.setThemeMode(newTheme);
            androidx.appcompat.app.AppCompatDelegate.setDefaultNightMode(newTheme);
        });

        binding.btnEditProfilePicture.setOnClickListener(v -> showProfilePictureOptions());

        // Setup Badge Adapter
        badgeAdapter = new com.findora.app.adapters.BadgeAdapter(this);
        binding.rvProfileBadges.setLayoutManager(new androidx.recyclerview.widget.LinearLayoutManager(this));
        binding.rvProfileBadges.setAdapter(badgeAdapter);

        // View Point History Click
        binding.btnViewPointHistory.setOnClickListener(v -> {
            Intent intent = new Intent(ProfileActivity.this, PointHistoryActivity.class);
            startActivity(intent);
        });

        // Finder Activity Stat Item Clicks -> Opens MyReportsActivity with filter
        binding.btnSuccessfulReturnsActivity.setOnClickListener(v -> openMyReportsWithFilter("successful_returns"));
        binding.btnLostReportsActivity.setOnClickListener(v -> openMyReportsWithFilter("lost"));
        binding.btnFoundReportsActivity.setOnClickListener(v -> openMyReportsWithFilter("found"));
        binding.btnItemsRecoveredActivity.setOnClickListener(v -> openMyReportsWithFilter("successful_returns"));

    }

    @Override
    protected void onResume() {
        super.onResume();
        loadProfile();
    }

    private void openMyReportsWithFilter(String filterType) {
        Intent intent = new Intent(ProfileActivity.this, MyReportsActivity.class);
        if (filterType != null) {
            intent.putExtra(MyReportsActivity.EXTRA_FILTER_TYPE, filterType);
        }
        startActivity(intent);
    }

    private com.findora.app.adapters.BadgeAdapter badgeAdapter;

    private void loadProfile() {
        apiService.getProfile().enqueue(new Callback<User>() {
            @Override
            public void onResponse(Call<User> call, Response<User> response) {
                if (response.isSuccessful() && response.body() != null) {
                    User user = response.body();
                    binding.tvFullName.setText(user.getFullName());
                    binding.tvEmail.setText(user.getEmail());
                    binding.tvRole.setText("Role: " + capitalize(user.getRole()));
                    if (user.getUsername() != null) {
                        binding.etCurrentUsername.setText(user.getUsername());
                        baseSessionManager.saveUsername(user.getUsername());
                    }
                    if (user.getProfileImage() != null && !user.getProfileImage().isEmpty()) {
                        baseSessionManager.saveProfileImage(user.getProfileImage());
                        Glide.with(ProfileActivity.this)
                                .load(user.getProfileImage())
                                .circleCrop()
                                .placeholder(R.drawable.ic_person)
                                .error(R.drawable.ic_person)
                                .diskCacheStrategy(DiskCacheStrategy.ALL)
                                .into(binding.ivProfilePicture);
                    } else {
                        baseSessionManager.saveProfileImage("");
                        binding.ivProfilePicture.setImageResource(R.drawable.ic_person);
                    }

                    // Load Finder Reputation, Activity & Badges ONLY if user is a Finder
                    if ("finder".equalsIgnoreCase(user.getRole())) {
                        binding.cvReputationSection.setVisibility(View.VISIBLE);
                        binding.cvActivitySection.setVisibility(View.VISIBLE);
                        binding.cvBadgesSection.setVisibility(View.VISIBLE);

                        binding.tvLostReportsCount.setText(String.valueOf(user.getLostReports()));
                        binding.tvFoundReportsCount.setText(String.valueOf(user.getFoundReports()));
                        binding.tvItemsRecoveredCount.setText(String.valueOf(user.getItemsRecovered()));

                        loadReputation();
                    } else {
                        binding.cvReputationSection.setVisibility(View.GONE);
                        binding.cvActivitySection.setVisibility(View.GONE);
                        binding.cvBadgesSection.setVisibility(View.GONE);
                    }
                } else {
                    // Unexpected server error — fall back to cache as last resort
                    showCachedProfile();
                }
            }

            @Override
            public void onFailure(Call<User> call, Throwable t) {
                // Network unavailable — fall back to cached data so the user
                // is not left with a blank profile screen when offline.
                showCachedProfile();
            }
        });
    }

    private void loadReputation() {
        apiService.getReputation().enqueue(new Callback<com.findora.app.models.FinderReputation>() {
            @Override
            public void onResponse(Call<com.findora.app.models.FinderReputation> call, Response<com.findora.app.models.FinderReputation> response) {
                if (response.isSuccessful() && response.body() != null) {
                    com.findora.app.models.FinderReputation rep = response.body();
                    binding.tvReputationScore.setText("⭐ " + rep.getReputationDisplay());
                    binding.tvPointsScore.setText("🏆 " + rep.getTotalPoints() + " Pts");
                    binding.tvReturnsScore.setText("🤝 " + rep.getSuccessfulReturns());

                    binding.tvLostReportsCount.setText(String.valueOf(rep.getLostReports()));
                    binding.tvFoundReportsCount.setText(String.valueOf(rep.getFoundReports()));
                    binding.tvItemsRecoveredCount.setText(String.valueOf(rep.getItemsRecovered()));

                    String badgeName = rep.getPrimaryBadge();
                    binding.tvPrimaryBadge.setText(badgeName != null ? "🏅 " + badgeName : "🏅 Starting Out");

                    if (badgeAdapter != null && rep.getBadgeProgress() != null) {
                        badgeAdapter.setBadges(rep.getBadgeProgress());
                    }
                }
            }

            @Override
            public void onFailure(Call<com.findora.app.models.FinderReputation> call, Throwable t) {
                // Non-critical
            }
        });
    }


    /**
     * Shows cached session data as a fallback when the API is unavailable.
     * This is only called after the API attempt fails — never before it.
     */
    private void showCachedProfile() {
        String cachedName = baseSessionManager.getFullName();
        String cachedEmail = baseSessionManager.getEmail();
        String cachedRole = baseSessionManager.getRole();
        String cachedUsername = baseSessionManager.getUsername();

        if (!cachedName.isEmpty()) binding.tvFullName.setText(cachedName);
        if (!cachedEmail.isEmpty()) binding.tvEmail.setText(cachedEmail);
        if (!cachedRole.isEmpty()) binding.tvRole.setText("Role: " + capitalize(cachedRole));
        if (!cachedUsername.isEmpty()) binding.etCurrentUsername.setText(cachedUsername);
        
        String cachedImage = baseSessionManager.getProfileImage();
        if (cachedImage != null && !cachedImage.isEmpty()) {
            Glide.with(this).load(cachedImage).circleCrop().placeholder(R.drawable.ic_person).error(R.drawable.ic_person).into(binding.ivProfilePicture);
        } else {
            binding.ivProfilePicture.setImageResource(R.drawable.ic_person);
        }
    }

    private void attemptChangeUsername() {
        String currentUsername = binding.etCurrentUsername.getText().toString().trim();
        String newUsername = binding.etNewUsername.getText().toString().trim();
        String confirmUsername = binding.etConfirmUsername.getText().toString().trim();

        if (newUsername.isEmpty() || confirmUsername.isEmpty()) {
            showUsernameError("All fields are required.");
            return;
        }

        if (newUsername.equals(currentUsername)) {
            showUsernameError("No changes were made.");
            return;
        }

        if (newUsername.length() < 3 || newUsername.length() > 30) {
            showUsernameError("Username must be 3-30 characters.");
            return;
        }

        if (!newUsername.matches("^[a-zA-Z0-9_.]+$")) {
            showUsernameError("Only letters, numbers, underscores, and periods are allowed.");
            return;
        }

        if (!newUsername.equals(confirmUsername)) {
            showUsernameError("Usernames do not match.");
            return;
        }

        ChangeUsernameRequest request = new ChangeUsernameRequest(newUsername, confirmUsername);
        apiService.changeUsername(request).enqueue(new Callback<ChangeUsernameResponse>() {
            @Override
            public void onResponse(Call<ChangeUsernameResponse> call, Response<ChangeUsernameResponse> response) {
                if (response.isSuccessful() && response.body() != null) {
                    Toast.makeText(ProfileActivity.this, "Username updated successfully!", Toast.LENGTH_LONG).show();
                    String updatedUsername = response.body().getUsername();
                    if (updatedUsername != null) {
                        baseSessionManager.saveUsername(updatedUsername);
                        binding.etCurrentUsername.setText(updatedUsername);
                    }
                    binding.etNewUsername.setText("");
                    binding.etConfirmUsername.setText("");
                    binding.tvChangeUsernameError.setVisibility(View.GONE);
                    // Hide form
                    isUsernameFormVisible = false;
                    binding.layoutChangeUsernameForm.setVisibility(View.GONE);
                    binding.btnToggleChangeUsername.setText("Show");
                    // Refresh profile
                    loadProfile();
                } else {
                    showUsernameError("Failed to update username. It may already exist.");
                }
            }

            @Override
            public void onFailure(Call<ChangeUsernameResponse> call, Throwable t) {
                showUsernameError("Network error: " + t.getMessage());
            }
        });
    }

    private void showUsernameError(String message) {
        binding.tvChangeUsernameError.setText(message);
        binding.tvChangeUsernameError.setVisibility(View.VISIBLE);
    }

    private void attemptChangePassword() {
        String currentPass = binding.etCurrentPassword.getText().toString().trim();
        String newPass = binding.etNewPassword.getText().toString().trim();
        String confirmPass = binding.etConfirmPassword.getText().toString().trim();

        if (currentPass.isEmpty() || newPass.isEmpty() || confirmPass.isEmpty()) {
            showPasswordError("All fields are required.");
            return;
        }

        if (newPass.length() < 8) {
            showPasswordError("New password must be at least 8 characters.");
            return;
        }

        if (!newPass.equals(confirmPass)) {
            showPasswordError("New passwords do not match.");
            return;
        }

        ChangePasswordRequest request = new ChangePasswordRequest(currentPass, newPass);
        apiService.changePassword(request).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                if (response.isSuccessful()) {
                    Toast.makeText(ProfileActivity.this,
                            "Password updated successfully!", Toast.LENGTH_LONG).show();
                    binding.etCurrentPassword.setText("");
                    binding.etNewPassword.setText("");
                    binding.etConfirmPassword.setText("");
                    binding.tvChangePasswordError.setVisibility(View.GONE);
                } else {
                    showPasswordError("Failed. Current password may be incorrect.");
                }
            }

            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                showPasswordError("Network error: " + t.getMessage());
            }
        });
    }

    private void logout() {
        baseSessionManager.logout();
        Toast.makeText(this, "Logged out successfully", Toast.LENGTH_SHORT).show();
        Intent intent = new Intent(this, LoginActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(intent);
        finish();
    }

    private void showPasswordError(String message) {
        binding.tvChangePasswordError.setText(message);
        binding.tvChangePasswordError.setVisibility(View.VISIBLE);
    }

    private String capitalize(String s) {
        if (s == null || s.isEmpty()) return "";
        return s.substring(0, 1).toUpperCase() + s.substring(1);
    }

    private void showProfilePictureOptions() {
        bottomSheetDialog = new BottomSheetDialog(this);
        View view = getLayoutInflater().inflate(R.layout.bottom_sheet_profile_picture, null);
        bottomSheetDialog.setContentView(view);
        
        view.findViewById(R.id.btnTakePhoto).setOnClickListener(v -> {
            bottomSheetDialog.dismiss();
            launchCamera();
        });
        
        view.findViewById(R.id.btnChooseGallery).setOnClickListener(v -> {
            bottomSheetDialog.dismiss();
            launchGallery();
        });
        
        view.findViewById(R.id.btnRemovePhoto).setOnClickListener(v -> {
            bottomSheetDialog.dismiss();
            removeProfilePicture();
        });
        
        bottomSheetDialog.show();
    }
    
    private void launchCamera() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA);
            return;
        }
        try {
            File photoFile = File.createTempFile("profile_", ".jpg", getExternalCacheDir());
            currentPhotoUri = FileProvider.getUriForFile(this, getApplicationContext().getPackageName() + ".fileprovider", photoFile);
            takePictureLauncher.launch(currentPhotoUri);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to launch camera", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void launchGallery() {
        pickImageLauncher.launch("image/*");
    }

    private void showSettingsDialog() {
        new com.google.android.material.dialog.MaterialAlertDialogBuilder(this)
            .setTitle("Camera Permission Required")
            .setMessage("This app needs camera access to take profile pictures. Please enable it in app settings.")
            .setPositiveButton("Settings", (dialog, which) -> {
                Intent intent = new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                Uri uri = Uri.fromParts("package", getPackageName(), null);
                intent.setData(uri);
                startActivity(intent);
            })
            .setNegativeButton("Cancel", null)
            .show();
    }
    
    private void startCrop(Uri sourceUri) {
        String destinationFileName = "cropped_" + System.currentTimeMillis() + ".jpg";
        Uri destinationUri = Uri.fromFile(new File(getCacheDir(), destinationFileName));
        
        UCrop.Options options = new UCrop.Options();
        options.setCircleDimmedLayer(true);
        options.setShowCropGrid(false);
        options.setToolbarTitle("Crop Profile Picture");
        options.setToolbarColor(ContextCompat.getColor(this, R.color.primary_purple));
        options.setStatusBarColor(ContextCompat.getColor(this, R.color.primary_purple));
        options.setActiveControlsWidgetColor(ContextCompat.getColor(this, R.color.primary_purple));
        
        Intent intent = UCrop.of(sourceUri, destinationUri)
                .withAspectRatio(1, 1)
                .withMaxResultSize(1000, 1000)
                .withOptions(options)
                .getIntent(this);
        cropImageLauncher.launch(intent);
    }
    
    private void uploadProfilePicture(Uri uri) {
        try {
            InputStream inputStream = getContentResolver().openInputStream(uri);
            File tempFile = new File(getCacheDir(), "upload_profile.jpg");
            FileOutputStream out = new FileOutputStream(tempFile);
            byte[] buf = new byte[1024];
            int len;
            while ((len = inputStream.read(buf)) > 0) {
                out.write(buf, 0, len);
            }
            out.close();
            inputStream.close();
            
            RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), tempFile);
            MultipartBody.Part body = MultipartBody.Part.createFormData("profileImage", tempFile.getName(), requestFile);
            
            apiService.updateProfileImage(body).enqueue(new Callback<User>() {
                @Override
                public void onResponse(Call<User> call, Response<User> response) {
                    if (response.isSuccessful() && response.body() != null) {
                        Toast.makeText(ProfileActivity.this, "Profile picture updated", Toast.LENGTH_SHORT).show();
                        baseSessionManager.saveProfileImage(response.body().getProfileImage());
                        loadProfile();
                    } else {
                        Toast.makeText(ProfileActivity.this, "Failed to update profile picture", Toast.LENGTH_SHORT).show();
                    }
                }
                
                @Override
                public void onFailure(Call<User> call, Throwable t) {
                    Toast.makeText(ProfileActivity.this, "Network error", Toast.LENGTH_SHORT).show();
                }
            });
        } catch (Exception e) {
            Toast.makeText(this, "Error processing image", Toast.LENGTH_SHORT).show();
        }
    }
    
    private void removeProfilePicture() {
        apiService.deleteProfileImage().enqueue(new Callback<User>() {
            @Override
            public void onResponse(Call<User> call, Response<User> response) {
                if (response.isSuccessful() && response.body() != null) {
                    Toast.makeText(ProfileActivity.this, "Profile picture removed", Toast.LENGTH_SHORT).show();
                    baseSessionManager.saveProfileImage("");
                    loadProfile();
                } else {
                    Toast.makeText(ProfileActivity.this, "Failed to remove profile picture", Toast.LENGTH_SHORT).show();
                }
            }
            
            @Override
            public void onFailure(Call<User> call, Throwable t) {
                Toast.makeText(ProfileActivity.this, "Network error", Toast.LENGTH_SHORT).show();
            }
        });
    }

}
