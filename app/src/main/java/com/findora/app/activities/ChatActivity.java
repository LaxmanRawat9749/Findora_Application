package com.findora.app.activities;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import com.findora.app.adapters.ChatAdapter;
import com.findora.app.cache.FindoraCache;
import com.findora.app.databinding.ActivityChatBinding;
import com.findora.app.models.ChatMessage;
import com.findora.app.network.ApiService;
import com.findora.app.network.RetrofitClient;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.models.User;
import com.findora.app.models.MessageResponse;
import com.google.android.material.bottomsheet.BottomSheetDialog;
import android.net.Uri;
import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.core.content.FileProvider;
import androidx.core.content.ContextCompat;
import android.Manifest;
import android.content.pm.PackageManager;
import java.io.File;
import android.widget.EditText;
import android.widget.ImageView;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import java.io.FileOutputStream;
import java.io.InputStream;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import androidx.exifinterface.media.ExifInterface;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import retrofit2.Call;
import retrofit2.Callback;
import retrofit2.Response;

public class ChatActivity extends BaseActivity {

    private ActivityChatBinding binding;
    private ApiService apiService;
    
    private ChatAdapter adapter;
    private int conversationId;
    private int otherUserId = -1;
    private Handler pollHandler;
    private Runnable pollRunnable;
    private ChatMessage messageToEdit;
    private boolean isUserAtBottom = true;
    private Call<List<ChatMessage>> pollCall;
    private final ExecutorService imageUploadExecutor = Executors.newSingleThreadExecutor();
    
    private Uri currentPhotoUri;
    private ActivityResultLauncher<Uri> takePictureLauncher;
    private ActivityResultLauncher<String> pickMultipleMediaLauncher;
    private ActivityResultLauncher<String[]> requestPermissionsLauncher;
    private static final java.util.concurrent.atomic.AtomicInteger tempMessageIdCounter = new java.util.concurrent.atomic.AtomicInteger(1000);
    private final java.util.concurrent.atomic.AtomicInteger activeUploadsCount = new java.util.concurrent.atomic.AtomicInteger(0);

    private boolean isInitialLoad = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityChatBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        apiService = RetrofitClient.getInstance(this).getApi();

        conversationId = getIntent().getIntExtra(Constants.EXTRA_CONVERSATION_ID, -1);
        int itemId = getIntent().getIntExtra("ITEM_ID", -1);
        int ownerId = getIntent().getIntExtra("OWNER_ID", -1);
        int finderId = getIntent().getIntExtra("FINDER_ID", -1);
        String otherUserName = getIntent().getStringExtra("other_user_name");

        if (conversationId == -1) {
            Toast.makeText(this, "Error: Invalid chat context.", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        if (otherUserName != null) {
            binding.tvChatName.setText(otherUserName);
            binding.toolbar.setTitle(""); // Clear default title to prevent overlap
        } else {
            binding.toolbar.setTitle("");
        }

        binding.toolbar.setNavigationOnClickListener(v -> finish());

        binding.toolbar.inflateMenu(R.menu.menu_chat);
        binding.toolbar.setOnMenuItemClickListener(item -> {
            if (item.getItemId() == R.id.action_view_profile) {
                openUserProfile(baseSessionManager.getUserId());
                return true;
            }
            return false;
        });

        adapter = new ChatAdapter(this, baseSessionManager.getUserId(), 
            msg -> showMessageOptions(msg),
            userId -> openUserProfile(userId));
        LinearLayoutManager layoutManager = new LinearLayoutManager(this);
        layoutManager.setStackFromEnd(true);
        binding.rvMessages.setLayoutManager(layoutManager);

        androidx.recyclerview.widget.RecyclerView.ItemAnimator animator = binding.rvMessages.getItemAnimator();
        if (animator instanceof androidx.recyclerview.widget.SimpleItemAnimator) {
            ((androidx.recyclerview.widget.SimpleItemAnimator) animator).setSupportsChangeAnimations(false);
        }

        binding.rvMessages.setAdapter(adapter);

        binding.rvMessages.addOnScrollListener(new androidx.recyclerview.widget.RecyclerView.OnScrollListener() {
            @Override
            public void onScrolled(@androidx.annotation.NonNull androidx.recyclerview.widget.RecyclerView recyclerView, int dx, int dy) {
                super.onScrolled(recyclerView, dx, dy);
                LinearLayoutManager layoutManager = (LinearLayoutManager) recyclerView.getLayoutManager();
                if (layoutManager != null) {
                    int lastVisible = layoutManager.findLastCompletelyVisibleItemPosition();
                    int totalCount = layoutManager.getItemCount();
                    isUserAtBottom = (lastVisible >= totalCount - 2);
                }
            }
        });

        setupLaunchers();
        binding.btnAttachment.setOnClickListener(v -> showImagePickerDialog());
        binding.btnSend.setOnClickListener(v -> sendMessage());

        loadChatProfile();

        // ─── Cache-First: Display cached messages immediately (0ms delay) ─────
        List<ChatMessage> cachedMessages = FindoraCache.getInstance(this).getCachedMessages(conversationId);
        if (cachedMessages != null && !cachedMessages.isEmpty()) {
            adapter.setMessages(cachedMessages);
            binding.progressBar.setVisibility(View.GONE);
            binding.tvEmptyState.setVisibility(View.GONE);
            binding.rvMessages.scrollToPosition(cachedMessages.size() - 1);
            isInitialLoad = false;
        }

        // Initialize polling Handler & Runnable
        pollHandler = new Handler(Looper.getMainLooper());
        pollRunnable = new Runnable() {
            @Override
            public void run() {
                loadMessages();
                if (pollHandler != null) {
                    pollHandler.postDelayed(this, Constants.CHAT_REFRESH_INTERVAL);
                }
            }
        };

        loadMessages();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (pollHandler != null && pollRunnable != null) {
            pollHandler.removeCallbacks(pollRunnable);
            pollHandler.postDelayed(pollRunnable, Constants.CHAT_REFRESH_INTERVAL);
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (pollHandler != null && pollRunnable != null) {
            pollHandler.removeCallbacks(pollRunnable);
        }
        if (pollCall != null) {
            pollCall.cancel();
            pollCall = null;
        }
    }

    private void loadMessages() {
        if (pollCall != null && !pollCall.isExecuted() && !pollCall.isCanceled()) {
            return; // Skip if a request is already in-flight
        }

        if (isInitialLoad && adapter.getItemCount() == 0) {
            binding.progressBar.setVisibility(View.VISIBLE);
        }
        pollCall = apiService.getMessages(conversationId);
        pollCall.enqueue(new Callback<List<ChatMessage>>() {
            @Override
            public void onResponse(Call<List<ChatMessage>> call, Response<List<ChatMessage>> response) {
                if (isInitialLoad) {
                    isInitialLoad = false;
                    binding.progressBar.setVisibility(View.GONE);
                }
                if (response.isSuccessful() && response.body() != null) {
                    List<ChatMessage> messages = response.body();
                    FindoraCache.getInstance(ChatActivity.this).saveMessages(conversationId, messages);
                    int previousCount = adapter.getItemCount();
                    adapter.setMessages(messages);
                    binding.tvEmptyState.setVisibility(messages.isEmpty() ? View.VISIBLE : View.GONE);
                    if (!messages.isEmpty()) {
                        if (previousCount == 0 || (isUserAtBottom && messages.size() > previousCount)) {
                            binding.rvMessages.scrollToPosition(messages.size() - 1);
                        }
                    }
                }
            }

            @Override
            public void onFailure(Call<List<ChatMessage>> call, Throwable t) {
                if (isInitialLoad) {
                    isInitialLoad = false;
                    binding.progressBar.setVisibility(View.GONE);
                }
                // Silently ignore background polling errors
            }
        });
    }

    private void sendMessage() {
        String text = binding.etMessage.getText().toString().trim();
        if (text.isEmpty()) return;

        binding.etMessage.setText("");

        if (messageToEdit != null) {
            // Edit existing message
            if ("image".equals(messageToEdit.getMessageType())) {
                messageToEdit.setCaption(text);
            } else {
                messageToEdit.setMessage(text);
            }
            apiService.editMessage(messageToEdit.getId(), messageToEdit).enqueue(new Callback<ChatMessage>() {
                @Override
                public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                    if (response.isSuccessful()) {
                        messageToEdit = null;
                        binding.etMessage.setHint("Type a message...");
                        loadMessages(); // Refresh UI
                    } else {
                        Toast.makeText(ChatActivity.this, "Failed to edit message.", Toast.LENGTH_SHORT).show();
                    }
                }
                @Override
                public void onFailure(Call<ChatMessage> call, Throwable t) {
                    Toast.makeText(ChatActivity.this, "Network error", Toast.LENGTH_SHORT).show();
                }
            });
            return;
        }

        ChatMessage msg = new ChatMessage(conversationId, text);
        apiService.sendMessage(msg).enqueue(new Callback<ChatMessage>() {
            @Override
            public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                if (response.isSuccessful() && response.body() != null) {
                    ChatMessage sent = response.body();
                    FindoraCache.getInstance(ChatActivity.this).addSentMessage(conversationId, sent);
                    adapter.addMessage(sent);
                    binding.rvMessages.scrollToPosition(adapter.getItemCount() - 1);
                    binding.tvEmptyState.setVisibility(View.GONE);
                } else {
                    Toast.makeText(ChatActivity.this,
                            "Failed to send message.", Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onFailure(Call<ChatMessage> call, Throwable t) {
                Toast.makeText(ChatActivity.this,
                        "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void setupLaunchers() {
        takePictureLauncher = registerForActivityResult(
            new ActivityResultContracts.TakePicture(),
            success -> {
                if (success && currentPhotoUri != null) {
                    showImagesPreviewDialog(java.util.Collections.singletonList(currentPhotoUri));
                }
            }
        );

        pickMultipleMediaLauncher = registerForActivityResult(
            new ActivityResultContracts.GetMultipleContents(),
            uris -> {
                if (uris != null && !uris.isEmpty()) {
                    showImagesPreviewDialog(new java.util.ArrayList<>(uris));
                }
            }
        );

        requestPermissionsLauncher = registerForActivityResult(
            new ActivityResultContracts.RequestMultiplePermissions(),
            result -> {
                Boolean cameraGranted = result.getOrDefault(Manifest.permission.CAMERA, false);
                if (cameraGranted != null && cameraGranted) {
                    launchCamera();
                } else {
                    Toast.makeText(this, "Camera permission required.", Toast.LENGTH_SHORT).show();
                }
            }
        );
    }

    private void showImagePickerDialog() {
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

        bottomSheetView.findViewById(R.id.btnCancel).setOnClickListener(v -> {
            dialog.dismiss();
            messageToEdit = null;
        });
        dialog.show();
    }

    private void launchCamera() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestPermissionsLauncher.launch(new String[]{Manifest.permission.CAMERA});
            return;
        }
        try {
            File photoFile = File.createTempFile("JPEG_" + System.currentTimeMillis() + "_", ".jpg", getExternalCacheDir());
            currentPhotoUri = FileProvider.getUriForFile(this, getApplicationContext().getPackageName() + ".fileprovider", photoFile);
            takePictureLauncher.launch(currentPhotoUri);
        } catch (Exception e) {
            Toast.makeText(this, "Failed to launch camera", Toast.LENGTH_SHORT).show();
        }
    }

    private void launchGallery() {
        pickMultipleMediaLauncher.launch("image/*");
    }

    private void showImagesPreviewDialog(List<Uri> initialUris) {
        if (initialUris == null || initialUris.isEmpty()) return;
        final List<Uri> uris = new java.util.ArrayList<>(initialUris);

        BottomSheetDialog dialog = new BottomSheetDialog(this);
        View view = getLayoutInflater().inflate(R.layout.dialog_image_preview, null);
        dialog.setContentView(view);

        android.widget.TextView tvTitle = view.findViewById(R.id.tvPreviewTitle);
        ImageView ivPreview = view.findViewById(R.id.ivPreview);
        androidx.recyclerview.widget.RecyclerView rvThumbnails = view.findViewById(R.id.rvThumbnails);
        EditText etCaption = view.findViewById(R.id.etCaption);
        com.google.android.material.button.MaterialButton btnCancel = view.findViewById(R.id.btnCancel);
        com.google.android.material.button.MaterialButton btnSend = view.findViewById(R.id.btnSend);

        final com.findora.app.adapters.ChatImagePreviewAdapter[] adapterRef = new com.findora.app.adapters.ChatImagePreviewAdapter[1];

        Runnable updateUiState = () -> {
            if (uris.isEmpty()) {
                dialog.dismiss();
                messageToEdit = null;
                return;
            }
            if (uris.size() == 1) {
                if (tvTitle != null) {
                    tvTitle.setText(messageToEdit != null ? "Edit Image" : "Preview Image");
                }
                rvThumbnails.setVisibility(View.GONE);
            } else {
                if (tvTitle != null) {
                    tvTitle.setText("Preview Images (" + uris.size() + ")");
                }
                rvThumbnails.setVisibility(View.VISIBLE);
            }
        };

        Glide.with(this).load(uris.get(0)).into(ivPreview);

        if (messageToEdit != null && "image".equals(messageToEdit.getMessageType())) {
            etCaption.setText(messageToEdit.getCaption() != null ? messageToEdit.getCaption() : "");
        }

        rvThumbnails.setLayoutManager(new LinearLayoutManager(this, LinearLayoutManager.HORIZONTAL, false));
        adapterRef[0] = new com.findora.app.adapters.ChatImagePreviewAdapter(uris,
            (uri, position) -> Glide.with(this).load(uri).into(ivPreview),
            position -> {
                if (position >= 0 && position < uris.size()) {
                    uris.remove(position);
                    adapterRef[0].notifyItemRemoved(position);
                    int currentSel = adapterRef[0].getSelectedPosition();
                    if (currentSel >= uris.size()) {
                        currentSel = Math.max(0, uris.size() - 1);
                        adapterRef[0].setSelectedPosition(currentSel);
                    }
                    if (!uris.isEmpty()) {
                        Glide.with(this).load(uris.get(currentSel)).into(ivPreview);
                    }
                    updateUiState.run();
                }
            }
        );
        rvThumbnails.setAdapter(adapterRef[0]);
        updateUiState.run();

        btnCancel.setOnClickListener(v -> {
            dialog.dismiss();
            messageToEdit = null;
        });

        btnSend.setOnClickListener(v -> {
            btnSend.setEnabled(false);
            btnCancel.setEnabled(false);
            dialog.dismiss();
            String caption = etCaption.getText().toString().trim();
            if (messageToEdit != null) {
                if (!uris.isEmpty()) {
                    updateImageMessage(uris.get(0), caption);
                }
            } else {
                sendImageMessages(uris, caption);
            }
        });

        dialog.show();
    }

    private void updateImageMessage(Uri uri, String caption) {
        if (messageToEdit == null) return;
        final int editMsgId = messageToEdit.getId();
        binding.progressBar.setVisibility(View.VISIBLE);
        binding.btnSend.setEnabled(false);
        binding.btnAttachment.setEnabled(false);

        imageUploadExecutor.execute(() -> {
            File file = compressImage(uri);
            if (file == null) {
                runOnUiThread(() -> {
                    binding.progressBar.setVisibility(View.GONE);
                    binding.btnSend.setEnabled(true);
                    binding.btnAttachment.setEnabled(true);
                    Toast.makeText(ChatActivity.this, "Failed to process image.", Toast.LENGTH_SHORT).show();
                });
                return;
            }

            RequestBody captionBody = RequestBody.create(MediaType.parse("text/plain"), caption != null ? caption : "");
            RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), file);
            MultipartBody.Part imagePart = MultipartBody.Part.createFormData("image", file.getName(), requestFile);

            apiService.editImageMessage(editMsgId, captionBody, imagePart).enqueue(new Callback<ChatMessage>() {
                @Override
                public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                    if (file.exists()) {
                        //noinspection ResultOfMethodCallIgnored
                        file.delete();
                    }
                    binding.progressBar.setVisibility(View.GONE);
                    binding.btnSend.setEnabled(true);
                    binding.btnAttachment.setEnabled(true);
                    if (response.isSuccessful() && response.body() != null) {
                        messageToEdit = null;
                        ChatMessage updated = response.body();
                        FindoraCache.getInstance(ChatActivity.this).updateMessage(conversationId, updated);
                        adapter.replaceMessage(editMsgId, updated);
                    } else {
                        Toast.makeText(ChatActivity.this, "Failed to update image.", Toast.LENGTH_SHORT).show();
                    }
                }

                @Override
                public void onFailure(Call<ChatMessage> call, Throwable t) {
                    if (file.exists()) {
                        //noinspection ResultOfMethodCallIgnored
                        file.delete();
                    }
                    binding.progressBar.setVisibility(View.GONE);
                    binding.btnSend.setEnabled(true);
                    binding.btnAttachment.setEnabled(true);
                    Toast.makeText(ChatActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
                }
            });
        });
    }

    private void sendImageMessages(List<Uri> uris, String caption) {
        if (uris == null || uris.isEmpty()) return;

        final List<Uri> imagesToSend = new java.util.ArrayList<>(uris);
        final int totalCount = imagesToSend.size();
        final String timeStamp = new java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", java.util.Locale.US).format(new java.util.Date());

        // 1. Instantly display optimistic preview message in chat list for each image
        final List<Integer> tempIds = new java.util.ArrayList<>();
        for (int i = 0; i < totalCount; i++) {
            Uri uri = imagesToSend.get(i);
            int tempId = -(1000000 + tempMessageIdCounter.incrementAndGet());
            tempIds.add(tempId);

            ChatMessage localMsg = new ChatMessage();
            localMsg.setId(tempId);
            localMsg.setConversation(conversationId);
            localMsg.setSender(baseSessionManager.getUserId());
            localMsg.setMessageType("image");
            localMsg.setImageUrl(uri.toString());
            localMsg.setCaption(i == 0 ? caption : "");
            localMsg.setSentAt(timeStamp);

            adapter.addMessage(localMsg);
        }

        binding.rvMessages.scrollToPosition(adapter.getItemCount() - 1);
        binding.tvEmptyState.setVisibility(View.GONE);

        // 2. Track pending upload count and show progress indicator
        activeUploadsCount.addAndGet(totalCount);
        binding.progressBar.setVisibility(View.VISIBLE);

        // 3. Perform compression and multipart upload sequentially in background thread
        for (int i = 0; i < totalCount; i++) {
            final int index = i;
            final Uri uri = imagesToSend.get(index);
            final int tempId = tempIds.get(index);
            final String itemCaption = (index == 0) ? caption : "";

            imageUploadExecutor.execute(() -> {
                File file = compressImage(uri);
                if (file == null) {
                    runOnUiThread(() -> {
                        adapter.removeTemporaryMessage(tempId);
                        int remaining = activeUploadsCount.decrementAndGet();
                        if (remaining <= 0) {
                            binding.progressBar.setVisibility(View.GONE);
                        }
                        String errMsg = totalCount > 1 ? "Failed to process image (" + (index + 1) + "/" + totalCount + ")" : "Failed to process image.";
                        Toast.makeText(ChatActivity.this, errMsg, Toast.LENGTH_SHORT).show();
                    });
                    return;
                }

                RequestBody convBody = RequestBody.create(MediaType.parse("text/plain"), String.valueOf(conversationId));
                RequestBody typeBody = RequestBody.create(MediaType.parse("text/plain"), "image");
                RequestBody captionBody = RequestBody.create(MediaType.parse("text/plain"), itemCaption != null ? itemCaption : "");

                RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), file);
                MultipartBody.Part imagePart = MultipartBody.Part.createFormData("image", file.getName(), requestFile);

                apiService.sendImageMessage(convBody, typeBody, captionBody, imagePart).enqueue(new Callback<ChatMessage>() {
                    @Override
                    public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                        if (file.exists()) {
                            //noinspection ResultOfMethodCallIgnored
                            file.delete();
                        }

                        int remaining = activeUploadsCount.decrementAndGet();
                        if (remaining <= 0) {
                            binding.progressBar.setVisibility(View.GONE);
                        }

                        if (response.isSuccessful() && response.body() != null) {
                            ChatMessage sent = response.body();
                            FindoraCache.getInstance(ChatActivity.this).addSentMessage(conversationId, sent);
                            adapter.replaceMessage(tempId, sent);
                            if (isUserAtBottom) {
                                binding.rvMessages.scrollToPosition(adapter.getItemCount() - 1);
                            }
                        } else {
                            adapter.removeTemporaryMessage(tempId);
                            String errMsg = totalCount > 1 ? "Failed to send image (" + (index + 1) + "/" + totalCount + ")" : "Failed to send image.";
                            Toast.makeText(ChatActivity.this, errMsg, Toast.LENGTH_SHORT).show();
                        }
                    }

                    @Override
                    public void onFailure(Call<ChatMessage> call, Throwable t) {
                        if (file.exists()) {
                            //noinspection ResultOfMethodCallIgnored
                            file.delete();
                        }

                        int remaining = activeUploadsCount.decrementAndGet();
                        if (remaining <= 0) {
                            binding.progressBar.setVisibility(View.GONE);
                        }

                        adapter.removeTemporaryMessage(tempId);
                        String errMsg = totalCount > 1 ? "Failed to send image (" + (index + 1) + "/" + totalCount + "): Network error" : "Network error: " + t.getMessage();
                        Toast.makeText(ChatActivity.this, errMsg, Toast.LENGTH_SHORT).show();
                    }
                });
            });
        }
    }

    private File compressImage(Uri uri) {
        if (uri == null) return null;
        try {
            // 1. Read EXIF orientation first
            int orientation = androidx.exifinterface.media.ExifInterface.ORIENTATION_NORMAL;
            try (InputStream exifStream = getContentResolver().openInputStream(uri)) {
                if (exifStream != null) {
                    androidx.exifinterface.media.ExifInterface exif = new androidx.exifinterface.media.ExifInterface(exifStream);
                    orientation = exif.getAttributeInt(androidx.exifinterface.media.ExifInterface.TAG_ORIENTATION, androidx.exifinterface.media.ExifInterface.ORIENTATION_NORMAL);
                }
            } catch (Exception ignored) {}

            // 2. Decode bounds only to compute optimal sampleSize (prevent OOM)
            BitmapFactory.Options boundsOptions = new BitmapFactory.Options();
            boundsOptions.inJustDecodeBounds = true;
            try (InputStream boundsStream = getContentResolver().openInputStream(uri)) {
                if (boundsStream == null) return null;
                BitmapFactory.decodeStream(boundsStream, null, boundsOptions);
            }

            int origWidth = boundsOptions.outWidth;
            int origHeight = boundsOptions.outHeight;
            if (origWidth <= 0 || origHeight <= 0) return null;

            int maxDimension = 1280;
            int sampleSize = 1;
            while (origWidth / (sampleSize * 2) >= maxDimension || origHeight / (sampleSize * 2) >= maxDimension) {
                sampleSize *= 2;
            }

            // 3. Decode bitmap with calculated sampleSize
            BitmapFactory.Options decodeOptions = new BitmapFactory.Options();
            decodeOptions.inSampleSize = sampleSize;
            decodeOptions.inJustDecodeBounds = false;
            decodeOptions.inPreferredConfig = Bitmap.Config.ARGB_8888;

            Bitmap sampledBitmap = null;
            try (InputStream decodeStream = getContentResolver().openInputStream(uri)) {
                if (decodeStream == null) return null;
                sampledBitmap = BitmapFactory.decodeStream(decodeStream, null, decodeOptions);
            }

            if (sampledBitmap == null) return null;

            // 4. Calculate scaling & rotation matrix
            int curWidth = sampledBitmap.getWidth();
            int curHeight = sampledBitmap.getHeight();

            float scale = Math.min(1.0f, Math.min((float) maxDimension / curWidth, (float) maxDimension / curHeight));
            Matrix matrix = new Matrix();
            if (scale < 1.0f) {
                matrix.postScale(scale, scale);
            }

            switch (orientation) {
                case androidx.exifinterface.media.ExifInterface.ORIENTATION_ROTATE_90:
                    matrix.postRotate(90);
                    break;
                case androidx.exifinterface.media.ExifInterface.ORIENTATION_ROTATE_180:
                    matrix.postRotate(180);
                    break;
                case androidx.exifinterface.media.ExifInterface.ORIENTATION_ROTATE_270:
                    matrix.postRotate(270);
                    break;
                case androidx.exifinterface.media.ExifInterface.ORIENTATION_FLIP_HORIZONTAL:
                    matrix.postScale(-1, 1);
                    break;
                case androidx.exifinterface.media.ExifInterface.ORIENTATION_FLIP_VERTICAL:
                    matrix.postScale(1, -1);
                    break;
                default:
                    break;
            }

            Bitmap finalBitmap;
            if (!matrix.isIdentity()) {
                finalBitmap = Bitmap.createBitmap(sampledBitmap, 0, 0, curWidth, curHeight, matrix, true);
                if (finalBitmap != sampledBitmap) {
                    sampledBitmap.recycle();
                }
            } else {
                finalBitmap = sampledBitmap;
            }

            // 5. Compress to temporary cache file as JPEG quality 80 with guaranteed unique filename
            File tempFile = File.createTempFile("chat_upload_" + System.currentTimeMillis() + "_", ".jpg", getCacheDir());
            try (FileOutputStream out = new FileOutputStream(tempFile)) {
                finalBitmap.compress(Bitmap.CompressFormat.JPEG, 80, out);
                out.flush();
            }
            finalBitmap.recycle();

            return tempFile;
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        }
    }

    private void loadChatProfile() {
        apiService.getChatProfile(conversationId).enqueue(new Callback<User>() {
            @Override
            public void onResponse(Call<User> call, Response<User> response) {
                if (response.isSuccessful() && response.body() != null) {
                    User otherUser = response.body();
                    otherUserId = otherUser.getId();
                    binding.tvChatName.setText(otherUser.getFirstName() != null && !otherUser.getFirstName().isEmpty() ? 
                        otherUser.getFirstName() + " " + otherUser.getLastName() : otherUser.getUsername());
                    
                    String roleText = otherUser.getRole();
                    if (roleText != null) {
                        roleText = roleText.substring(0, 1).toUpperCase() + roleText.substring(1).toLowerCase();
                    }
                    binding.tvChatRole.setText(roleText);
                    
                    if (otherUser.getProfileImage() != null && !otherUser.getProfileImage().isEmpty()) {
                        binding.ivChatAvatar.setImageTintList(null);
                        com.findora.app.utils.GlideImageHelper.loadAvatar(ChatActivity.this, otherUser.getProfileImage(), binding.ivChatAvatar);
                    } else {
                        binding.ivChatAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                                getResources().getColor(R.color.text_gray, null)));
                        binding.ivChatAvatar.setImageResource(R.drawable.ic_person);
                    }
                    
                    binding.ivChatAvatar.setOnClickListener(v -> openUserProfile(otherUser.getId()));
                    binding.tvChatName.setOnClickListener(v -> openUserProfile(otherUser.getId()));
                }
            }
            @Override
            public void onFailure(Call<User> call, Throwable t) {}
        });
    }

    private void openUserProfile(int userId) {
        if (userId == -1) return;
        Intent intent;
        if (userId == baseSessionManager.getUserId()) {
            intent = new Intent(this, ProfileActivity.class);
        } else {
            intent = new Intent(this, UserProfileActivity.class);
            intent.putExtra(UserProfileActivity.EXTRA_USER_ID, userId);
        }
        startActivity(intent);
    }

    private void showMessageOptions(ChatMessage message) {
        if (message == null) return;
        BottomSheetDialog dialog = new BottomSheetDialog(this);
        View bottomSheetView = getLayoutInflater().inflate(R.layout.layout_chat_bottom_sheet, null);
        dialog.setContentView(bottomSheetView);

        View btnCopy = bottomSheetView.findViewById(R.id.btnCopy);
        View btnDeleteMe = bottomSheetView.findViewById(R.id.btnDeleteMe);
        View btnDeleteEveryone = bottomSheetView.findViewById(R.id.btnDeleteEveryone);

        if (message.isDeletedForEveryone()) {
            btnCopy.setVisibility(View.GONE);
            btnDeleteEveryone.setVisibility(View.GONE);
        } else {
            btnCopy.setVisibility(View.VISIBLE);
            btnCopy.setOnClickListener(v -> {
                dialog.dismiss();
                String textToCopy = "image".equals(message.getMessageType()) ? message.getCaption() : message.getMessage();
                if (textToCopy == null) textToCopy = "";
                ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
                ClipData clip = ClipData.newPlainText("Message", textToCopy);
                if (clipboard != null) clipboard.setPrimaryClip(clip);
                Toast.makeText(this, "Message copied", Toast.LENGTH_SHORT).show();
            });

            if (message.getSender() == baseSessionManager.getUserId()) {
                btnDeleteEveryone.setVisibility(View.VISIBLE);
                btnDeleteEveryone.setOnClickListener(v -> {
                    dialog.dismiss();
                    showDeleteConfirmationDialog(message.getId(), true);
                });
            } else {
                btnDeleteEveryone.setVisibility(View.GONE);
            }
        }

        btnDeleteMe.setOnClickListener(v -> {
            dialog.dismiss();
            showDeleteConfirmationDialog(message.getId(), false);
        });

        dialog.show();
    }

    private void showDeleteConfirmationDialog(int messageId, boolean forEveryone) {
        new com.google.android.material.dialog.MaterialAlertDialogBuilder(this)
                .setTitle("Delete Message")
                .setMessage("Are you sure you want to delete this message?")
                .setNegativeButton("Cancel", (dialog, which) -> dialog.dismiss())
                .setPositiveButton("Delete", (dialog, which) -> {
                    dialog.dismiss();
                    deleteMessage(messageId, forEveryone);
                })
                .show();
    }

    private void deleteMessage(int messageId, boolean forEveryone) {
        apiService.deleteMessage(messageId, forEveryone).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                if (response.isSuccessful()) {
                    FindoraCache.getInstance(ChatActivity.this).deleteMessage(conversationId, messageId, forEveryone);
                    if (forEveryone) {
                        adapter.markMessageDeleted(messageId);
                    } else {
                        adapter.removeMessage(messageId);
                    }
                    Toast.makeText(ChatActivity.this, "Message deleted", Toast.LENGTH_SHORT).show();
                } else {
                    String errorMsg = "Failed to delete message.";
                    try {
                        if (response.errorBody() != null) {
                            String errStr = response.errorBody().string();
                            org.json.JSONObject obj = new org.json.JSONObject(errStr);
                            if (obj.has("error")) {
                                errorMsg = obj.getString("error");
                            } else if (obj.has("message")) {
                                errorMsg = obj.getString("message");
                            }
                        }
                    } catch (Exception ignored) {}
                    Toast.makeText(ChatActivity.this, errorMsg, Toast.LENGTH_SHORT).show();
                }
            }
            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                Toast.makeText(ChatActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }



    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (pollHandler != null && pollRunnable != null) {
            pollHandler.removeCallbacks(pollRunnable);
            pollHandler = null;
        }
        if (pollCall != null) {
            pollCall.cancel();
            pollCall = null;
        }
        imageUploadExecutor.shutdown();
    }
}
