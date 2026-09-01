package com.findora.app.activities;

import android.Manifest;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import com.findora.app.utils.SessionManager;
import android.os.Environment;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Toast;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.core.content.FileProvider;
import androidx.exifinterface.media.ExifInterface;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.R;
import com.findora.app.adapters.UploadImageAdapter;
import com.findora.app.databinding.ActivityUploadItemBinding;
import com.findora.app.models.Item;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.google.android.material.bottomsheet.BottomSheetDialog;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class UploadItemActivity extends BaseActivity {
    

    private ActivityUploadItemBinding binding;
    private ApiService apiService;

    private List<Uri> selectedImages = new ArrayList<>();
    private UploadImageAdapter imageAdapter;
    private Uri currentPhotoUri;

    private ActivityResultLauncher<String[]> requestPermissionsLauncher;
    private ActivityResultLauncher<Uri> takePictureLauncher;
    private ActivityResultLauncher<String> pickMultipleMediaLauncher;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityUploadItemBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        // Setup category spinner
        ArrayAdapter<String> categoryAdapter = new ArrayAdapter<>(
                this, android.R.layout.simple_spinner_item, Constants.CATEGORY_LABELS);
        categoryAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        binding.spinnerCategory.setAdapter(categoryAdapter);

        // Adjust Report Type and Reward field based on role
        String role = new SessionManager(this).getRole();
        if ("owner".equalsIgnoreCase(role)) {
            binding.rbLost.setChecked(true);
            binding.rbFound.setVisibility(View.GONE);
            binding.rbFound.setEnabled(false);
            binding.rbLost.setVisibility(View.VISIBLE);
            binding.rbLost.setEnabled(true);
            binding.tilReward.setVisibility(View.VISIBLE);
            updateImageLabels(true);
        } else if ("finder".equalsIgnoreCase(role)) {
            binding.rbFound.setChecked(true);
            binding.rbLost.setVisibility(View.GONE);
            binding.rbLost.setEnabled(false);
            binding.rbFound.setVisibility(View.VISIBLE);
            binding.rbFound.setEnabled(true);
            binding.tilReward.setVisibility(View.GONE);
            binding.etReward.setText("");
            updateImageLabels(false);
        } else {
            // Fallback for admin or unassigned role
            updateRewardVisibility(binding.rbLost.isChecked());
            updateImageLabels(binding.rbLost.isChecked());
            binding.rgType.setOnCheckedChangeListener((group, checkedId) -> {
                boolean isLost = checkedId == R.id.rbLost;
                updateRewardVisibility(isLost);
                updateImageLabels(isLost);
            });
        }

        // Auto-fill and lock Title & Category if reporting against an Owner's Lost Item
        if (getIntent() != null && (getIntent().hasExtra("extra_lost_item_id") || getIntent().hasExtra(Constants.EXTRA_ITEM_ID))) {
            linkedLostItemId = getIntent().getIntExtra("extra_lost_item_id", getIntent().getIntExtra(Constants.EXTRA_ITEM_ID, 0));
            String linkedLostItemTitle = getIntent().getStringExtra("extra_lost_item_title");
            String linkedLostItemCategory = getIntent().getStringExtra("extra_lost_item_category");

            if (linkedLostItemTitle != null && !linkedLostItemTitle.isEmpty()) {
                binding.etTitle.setText(linkedLostItemTitle);
                binding.etTitle.setEnabled(false);
                binding.etTitle.setFocusable(false);
            }
            if (linkedLostItemCategory != null && !linkedLostItemCategory.isEmpty()) {
                for (int i = 0; i < Constants.CATEGORIES.length; i++) {
                    if (Constants.CATEGORIES[i].equalsIgnoreCase(linkedLostItemCategory)) {
                        binding.spinnerCategory.setSelection(i);
                        break;
                    }
                }
                binding.spinnerCategory.setEnabled(false);
            }
            binding.rbFound.setChecked(true);
            binding.rbLost.setVisibility(View.GONE);
            binding.rbFound.setVisibility(View.VISIBLE);
            binding.tilReward.setVisibility(View.GONE);
            updateImageLabels(false);
        }

        // Setup image recycler view
        imageAdapter = new UploadImageAdapter(selectedImages, position -> {
            selectedImages.remove(position);
            imageAdapter.notifyItemRemoved(position);
            updateImageVisibility();
        });
        binding.rvImages.setLayoutManager(new LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false));
        binding.rvImages.setAdapter(imageAdapter);

        binding.cardAddPhoto.setOnClickListener(v -> showImagePickerDialog());
        binding.btnSubmit.setOnClickListener(v -> submitReport());

        setupLaunchers();
    }

    private int linkedLostItemId = 0;

    private boolean isLostReport() {
        String role = new SessionManager(this).getRole();
        if ("owner".equalsIgnoreCase(role)) return true;
        if ("finder".equalsIgnoreCase(role)) return false;
        return binding.rbLost.isChecked();
    }

    private void updateImageLabels(boolean isLost) {
        if (isLost) {
            binding.tvImagesHeader.setText("Item Photo (Optional)");
            binding.tvImagesSubheader.setText("Upload a photo of the item (optional) or describe it below.");
            binding.tvAddPhotoLabel.setText("Add Photo");
        } else {
            binding.tvImagesHeader.setText("Item Photo (Required)");
            binding.tvImagesSubheader.setText("Upload 1 photo of the found item to help identification.");
            binding.tvAddPhotoLabel.setText("Add Photo");
        }
    }

    private void updateRewardVisibility(boolean isLost) {
        if (isLost) {
            binding.tilReward.setVisibility(View.VISIBLE);
        } else {
            binding.tilReward.setVisibility(View.GONE);
            binding.etReward.setText("");
        }
    }

    private void updateImageVisibility() {
        binding.rvImages.setVisibility(selectedImages.isEmpty() ? View.GONE : View.VISIBLE);
    }

    private void setupLaunchers() {
        requestPermissionsLauncher = registerForActivityResult(new ActivityResultContracts.RequestMultiplePermissions(), result -> {
            boolean allGranted = true;
            for (Boolean granted : result.values()) {
                if (!granted) allGranted = false;
            }
            if (allGranted) {
                launchCamera();
            } else {
                if (!shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)) {
                    showSettingsDialog();
                } else {
                    Toast.makeText(this, "Camera permission denied", Toast.LENGTH_SHORT).show();
                }
            }
        });

        takePictureLauncher = registerForActivityResult(new ActivityResultContracts.TakePicture(), success -> {
            if (success && currentPhotoUri != null) {
                addImage(currentPhotoUri);
            }
        });

        pickMultipleMediaLauncher = registerForActivityResult(new ActivityResultContracts.GetMultipleContents(), uris -> {
            if (uris != null && !uris.isEmpty()) {
                if (selectedImages.size() >= 1 || uris.size() > 1) {
                    Toast.makeText(this, "Only one photo can be uploaded.", Toast.LENGTH_SHORT).show();
                    if (selectedImages.isEmpty()) {
                        addImage(uris.get(0));
                    }
                    return;
                }
                for (Uri uri : uris) {
                    addImage(uri);
                }
            }
        });
    }

    private void addImage(Uri uri) {
        if (selectedImages.size() >= 1) {
            Toast.makeText(this, "Only one photo can be uploaded.", Toast.LENGTH_SHORT).show();
            return;
        }
        selectedImages.add(uri);
        imageAdapter.notifyItemInserted(selectedImages.size() - 1);
        updateImageVisibility();
    }

    private void showImagePickerDialog() {
        if (selectedImages.size() >= 1) {
            Toast.makeText(this, "Only one photo can be uploaded.", Toast.LENGTH_SHORT).show();
            return;
        }

        BottomSheetDialog dialog = new BottomSheetDialog(this);
        View bottomSheetView = getLayoutInflater().inflate(R.layout.layout_image_picker_bottom_sheet, null);
        dialog.setContentView(bottomSheetView);

        bottomSheetView.findViewById(R.id.btnCamera).setOnClickListener(v -> {
            dialog.dismiss();
            launchCamera();
        });

        bottomSheetView.findViewById(R.id.btnGallery).setOnClickListener(v -> {
            dialog.dismiss();
            launchGallery();
        });

        bottomSheetView.findViewById(R.id.btnCancel).setOnClickListener(v -> dialog.dismiss());

        dialog.show();
    }

    private void launchCamera() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissionsLauncher.launch(new String[]{Manifest.permission.CAMERA});
            return;
        }
        try {
            File cacheDir = getExternalCacheDir() != null ? getExternalCacheDir() : getCacheDir();
            File photoFile = File.createTempFile("JPEG_" + System.currentTimeMillis() + "_", ".jpg", cacheDir);
            currentPhotoUri = FileProvider.getUriForFile(this, getApplicationContext().getPackageName() + ".fileprovider", photoFile);
            takePictureLauncher.launch(currentPhotoUri);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to launch camera", Toast.LENGTH_SHORT).show();
        }
    }

    private void launchGallery() {
        pickMultipleMediaLauncher.launch("image/*");
    }

    private void showSettingsDialog() {
        new com.google.android.material.dialog.MaterialAlertDialogBuilder(this)
            .setTitle("Camera Permission Required")
            .setMessage("This app needs camera access to take item photos. Please enable it in app settings.")
            .setPositiveButton("Settings", (dialog, which) -> {
                Intent intent = new Intent(android.provider.Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                Uri uri = Uri.fromParts("package", getPackageName(), null);
                intent.setData(uri);
                startActivity(intent);
            })
            .setNegativeButton("Cancel", null)
            .show();
    }

    private void submitReport() {
        String role = new SessionManager(this).getRole();
        String type;
        if ("owner".equalsIgnoreCase(role)) {
            type = "lost";
        } else if ("finder".equalsIgnoreCase(role)) {
            type = "found";
        } else {
            type = binding.rbLost.isChecked() ? "lost" : "found";
        }
        String title = binding.etTitle.getText().toString().trim();
        String location = binding.etLocation.getText().toString().trim();
        String rewardStr = binding.etReward.getText().toString().trim();
        String description = binding.etDescription.getText().toString().trim();
        int categoryIdx = binding.spinnerCategory.getSelectedItemPosition();
        String category = Constants.CATEGORIES[categoryIdx];

        if (title.isEmpty() || description.isEmpty()) {
            Toast.makeText(this, "Title and description are required.", Toast.LENGTH_SHORT).show();
            return;
        }
        
        // For finder reports, exactly 1 image is required; for owner/lost reports, photo is optional (0 or 1)
        if (!"lost".equalsIgnoreCase(type) && selectedImages.isEmpty()) {
            Toast.makeText(this, "Please upload 1 photo of the found item.", Toast.LENGTH_SHORT).show();
            return;
        }

        if (selectedImages.size() > 1) {
            Toast.makeText(this, "Only one photo can be uploaded.", Toast.LENGTH_SHORT).show();
            return;
        }

        setLoading(true);

        Map<String, RequestBody> partMap = new HashMap<>();
        partMap.put("type", RequestBody.create(MediaType.parse("text/plain"), type));
        partMap.put("title", RequestBody.create(MediaType.parse("text/plain"), title));
        partMap.put("description", RequestBody.create(MediaType.parse("text/plain"), description));
        partMap.put("category", RequestBody.create(MediaType.parse("text/plain"), category));
        partMap.put("location", RequestBody.create(MediaType.parse("text/plain"), location));
        if (linkedLostItemId > 0) {
            partMap.put("parent_item", RequestBody.create(MediaType.parse("text/plain"), String.valueOf(linkedLostItemId)));
        }
        if (!"finder".equalsIgnoreCase(role) && !"found".equalsIgnoreCase(type) && !rewardStr.isEmpty()) {
            partMap.put("reward", RequestBody.create(MediaType.parse("text/plain"), rewardStr));
        }

        List<MultipartBody.Part> imageParts = new ArrayList<>();
        for (int i = 0; i < selectedImages.size(); i++) {
            File file = compressImage(selectedImages.get(i));
            if (file != null) {
                RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), file);
                MultipartBody.Part body = MultipartBody.Part.createFormData("images", file.getName(), requestFile);
                imageParts.add(body);
            } else {
                setLoading(false);
                Toast.makeText(this, "Failed to process selected image. Please re-select the photo.", Toast.LENGTH_SHORT).show();
                return;
            }
        }

        apiService.reportItemWithImages(partMap, imageParts).enqueue(new Callback<Item>() {
            @Override
            public void onResponse(Call<Item> call, Response<Item> response) {
                setLoading(false);
                if (response.isSuccessful()) {
                    if (response.body() != null) {
                        com.findora.app.cache.FindoraCache.getInstance(UploadItemActivity.this).updateOrInsertItem(response.body());
                    }
                    Toast.makeText(UploadItemActivity.this, "Item reported successfully!", Toast.LENGTH_LONG).show();
                    finish();
                } else {
                    Toast.makeText(UploadItemActivity.this, "Failed to submit report.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<Item> call, Throwable t) {
                setLoading(false);
                Toast.makeText(UploadItemActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private File compressImage(Uri uri) {
        try {
            // First decode with inJustDecodeBounds to check dimensions
            BitmapFactory.Options options = new BitmapFactory.Options();
            options.inJustDecodeBounds = true;
            InputStream boundsInput = getContentResolver().openInputStream(uri);
            if (boundsInput == null) return null;
            BitmapFactory.decodeStream(boundsInput, null, options);
            boundsInput.close();

            int rawWidth = options.outWidth;
            int rawHeight = options.outHeight;
            if (rawWidth <= 0 || rawHeight <= 0) {
                return null;
            }

            int inSampleSize = 1;
            int maxDim = Math.max(rawWidth, rawHeight);
            while (maxDim / inSampleSize > 1920) {
                inSampleSize *= 2;
            }

            // Decode actual bitmap with sample size and memory efficient config
            BitmapFactory.Options decodeOptions = new BitmapFactory.Options();
            decodeOptions.inSampleSize = inSampleSize;
            decodeOptions.inPreferredConfig = Bitmap.Config.RGB_565;

            InputStream input = getContentResolver().openInputStream(uri);
            if (input == null) return null;
            Bitmap bitmap = BitmapFactory.decodeStream(input, null, decodeOptions);
            input.close();

            if (bitmap == null) return null;

            // Handle rotation safely
            int orientation = ExifInterface.ORIENTATION_NORMAL;
            try {
                InputStream exifInput = getContentResolver().openInputStream(uri);
                if (exifInput != null) {
                    ExifInterface exif = new ExifInterface(exifInput);
                    orientation = exif.getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL);
                    exifInput.close();
                }
            } catch (Throwable ignored) {}

            Matrix matrix = new Matrix();
            if (orientation == ExifInterface.ORIENTATION_ROTATE_90) matrix.postRotate(90);
            else if (orientation == ExifInterface.ORIENTATION_ROTATE_180) matrix.postRotate(180);
            else if (orientation == ExifInterface.ORIENTATION_ROTATE_270) matrix.postRotate(270);

            if (orientation != ExifInterface.ORIENTATION_NORMAL && orientation != ExifInterface.ORIENTATION_UNDEFINED) {
                Bitmap rotated = Bitmap.createBitmap(bitmap, 0, 0, bitmap.getWidth(), bitmap.getHeight(), matrix, true);
                if (rotated != bitmap) {
                    bitmap.recycle();
                    bitmap = rotated;
                }
            }

            // Final resize if still above 1920 after rotation/sampling
            int curMax = Math.max(bitmap.getWidth(), bitmap.getHeight());
            if (curMax > 1920) {
                float scale = 1920f / curMax;
                Bitmap scaled = Bitmap.createScaledBitmap(bitmap, (int)(bitmap.getWidth() * scale), (int)(bitmap.getHeight() * scale), true);
                if (scaled != bitmap) {
                    bitmap.recycle();
                    bitmap = scaled;
                }
            }

            File cacheDir = getExternalCacheDir() != null ? getExternalCacheDir() : getCacheDir();
            File file = new File(cacheDir, "compressed_" + System.currentTimeMillis() + ".jpg");
            FileOutputStream fos = new FileOutputStream(file);
            bitmap.compress(Bitmap.CompressFormat.JPEG, 85, fos);
            fos.flush();
            fos.close();
            bitmap.recycle();
            return file;
        } catch (Throwable t) {
            t.printStackTrace();
        }
        return null;
    }

    private void setLoading(boolean loading) {
        binding.progressBar.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnSubmit.setEnabled(!loading);
        binding.cardAddPhoto.setEnabled(!loading);
    }
}
