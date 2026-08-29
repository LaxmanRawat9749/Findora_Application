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
import java.util.List;
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
    
    private Uri currentPhotoUri;
    private ActivityResultLauncher<Uri> takePictureLauncher;
    private ActivityResultLauncher<String> pickMediaLauncher;
    private ActivityResultLauncher<String[]> requestPermissionsLauncher;

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
                if (otherUserId != -1) {
                    openUserProfile(otherUserId);
                } else {
                    Toast.makeText(this, "Profile not loaded yet.", Toast.LENGTH_SHORT).show();
                }
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
                    adapter.addMessage(response.body());
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
                    showImagePreviewDialog(currentPhotoUri);
                }
            }
        );

        pickMediaLauncher = registerForActivityResult(
            new ActivityResultContracts.GetContent(),
            uri -> {
                if (uri != null) {
                    showImagePreviewDialog(uri);
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
        pickMediaLauncher.launch("image/*");
    }

    private void showImagePreviewDialog(Uri uri) {
        BottomSheetDialog dialog = new BottomSheetDialog(this);
        View view = getLayoutInflater().inflate(R.layout.dialog_image_preview, null);
        dialog.setContentView(view);
        
        ImageView ivPreview = view.findViewById(R.id.ivPreview);
        EditText etCaption = view.findViewById(R.id.etCaption);
        
        Glide.with(this).load(uri).into(ivPreview);
        
        if (messageToEdit != null && "image".equals(messageToEdit.getMessageType())) {
            etCaption.setText(messageToEdit.getCaption() != null ? messageToEdit.getCaption() : "");
        }
        
        view.findViewById(R.id.btnCancel).setOnClickListener(v -> {
            dialog.dismiss();
            messageToEdit = null;
        });
        view.findViewById(R.id.btnSend).setOnClickListener(v -> {
            dialog.dismiss();
            if (messageToEdit != null) {
                updateImageMessage(uri, etCaption.getText().toString().trim());
            } else {
                sendImageMessage(uri, etCaption.getText().toString().trim());
            }
        });
        
        dialog.show();
    }

    private void updateImageMessage(Uri uri, String caption) {
        File file = compressImage(uri);
        if (file == null) {
            Toast.makeText(this, "Failed to process image.", Toast.LENGTH_SHORT).show();
            return;
        }

        binding.progressBar.setVisibility(View.VISIBLE);
        binding.btnSend.setEnabled(false);
        binding.btnAttachment.setEnabled(false);

        RequestBody captionBody = RequestBody.create(MediaType.parse("text/plain"), caption);
        RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), file);
        MultipartBody.Part imagePart = MultipartBody.Part.createFormData("image", file.getName(), requestFile);

        apiService.editImageMessage(messageToEdit.getId(), captionBody, imagePart).enqueue(new Callback<ChatMessage>() {
            @Override
            public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSend.setEnabled(true);
                binding.btnAttachment.setEnabled(true);
                if (response.isSuccessful()) {
                    messageToEdit = null;
                    loadMessages(); // Refresh UI
                } else {
                    Toast.makeText(ChatActivity.this, "Failed to update image.", Toast.LENGTH_SHORT).show();
                }
            }
            @Override
            public void onFailure(Call<ChatMessage> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSend.setEnabled(true);
                binding.btnAttachment.setEnabled(true);
                Toast.makeText(ChatActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void sendImageMessage(Uri uri, String caption) {
        File file = compressImage(uri);
        if (file == null) {
            Toast.makeText(this, "Failed to process image.", Toast.LENGTH_SHORT).show();
            return;
        }

        binding.progressBar.setVisibility(View.VISIBLE);
        binding.btnSend.setEnabled(false);
        binding.btnAttachment.setEnabled(false);

        RequestBody convBody = RequestBody.create(MediaType.parse("text/plain"), String.valueOf(conversationId));
        RequestBody typeBody = RequestBody.create(MediaType.parse("text/plain"), "image");
        RequestBody captionBody = RequestBody.create(MediaType.parse("text/plain"), caption);
        
        RequestBody requestFile = RequestBody.create(MediaType.parse("image/jpeg"), file);
        MultipartBody.Part imagePart = MultipartBody.Part.createFormData("image", file.getName(), requestFile);

        apiService.sendImageMessage(convBody, typeBody, captionBody, imagePart).enqueue(new Callback<ChatMessage>() {
            @Override
            public void onResponse(Call<ChatMessage> call, Response<ChatMessage> response) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSend.setEnabled(true);
                binding.btnAttachment.setEnabled(true);
                if (response.isSuccessful() && response.body() != null) {
                    adapter.addMessage(response.body());
                    binding.rvMessages.scrollToPosition(adapter.getItemCount() - 1);
                    binding.tvEmptyState.setVisibility(View.GONE);
                } else {
                    Toast.makeText(ChatActivity.this, "Failed to send image.", Toast.LENGTH_SHORT).show();
                }
            }
            @Override
            public void onFailure(Call<ChatMessage> call, Throwable t) {
                binding.progressBar.setVisibility(View.GONE);
                binding.btnSend.setEnabled(true);
                binding.btnAttachment.setEnabled(true);
                Toast.makeText(ChatActivity.this, "Network error: " + t.getMessage(), Toast.LENGTH_SHORT).show();
            }
        });
    }

    private File compressImage(Uri uri) {
        try {
            InputStream inputStream = getContentResolver().openInputStream(uri);
            Bitmap bitmap = BitmapFactory.decodeStream(inputStream);
            if (inputStream != null) inputStream.close();
            
            if (bitmap == null) return null;

            int maxWidth = 1080;
            int maxHeight = (int) ((float) bitmap.getHeight() / bitmap.getWidth() * maxWidth);
            Bitmap scaledBitmap = Bitmap.createScaledBitmap(bitmap, maxWidth, maxHeight, true);

            File tempFile = new File(getCacheDir(), "chat_upload_" + System.currentTimeMillis() + ".jpg");
            FileOutputStream out = new FileOutputStream(tempFile);
            scaledBitmap.compress(Bitmap.CompressFormat.JPEG, 80, out);
            out.flush();
            out.close();
            
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
                        Glide.with(ChatActivity.this)
                                .load(otherUser.getProfileImage())
                                .diskCacheStrategy(com.bumptech.glide.load.engine.DiskCacheStrategy.ALL)
                                .circleCrop()
                                .placeholder(R.drawable.ic_person)
                                .error(R.drawable.ic_person)
                                .into(binding.ivChatAvatar);
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
        BottomSheetDialog dialog = new BottomSheetDialog(this);
        View bottomSheetView = getLayoutInflater().inflate(R.layout.layout_chat_bottom_sheet, null);
        dialog.setContentView(bottomSheetView);



        bottomSheetView.findViewById(R.id.btnCopy).setOnClickListener(v -> {
            dialog.dismiss();
            String textToCopy = "image".equals(message.getMessageType()) ? message.getCaption() : message.getMessage();
            if (textToCopy == null) textToCopy = "";
            ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip = ClipData.newPlainText("Message", textToCopy);
            if (clipboard != null) clipboard.setPrimaryClip(clip);
            Toast.makeText(this, "Message copied", Toast.LENGTH_SHORT).show();
        });

        bottomSheetView.findViewById(R.id.btnDeleteMe).setOnClickListener(v -> {
            dialog.dismiss();
            deleteMessage(message.getId(), false);
        });
        
        View btnDeleteEveryone = bottomSheetView.findViewById(R.id.btnDeleteEveryone);
        if (message.getSender() == baseSessionManager.getUserId()) {
            btnDeleteEveryone.setVisibility(View.VISIBLE);
            btnDeleteEveryone.setOnClickListener(v -> {
                dialog.dismiss();
                deleteMessage(message.getId(), true);
            });
        } else {
            btnDeleteEveryone.setVisibility(View.GONE);
        }

        dialog.show();
    }

    private void deleteMessage(int messageId, boolean forEveryone) {
        apiService.deleteMessage(messageId, forEveryone).enqueue(new Callback<MessageResponse>() {
            @Override
            public void onResponse(Call<MessageResponse> call, Response<MessageResponse> response) {
                if (response.isSuccessful()) {
                    loadMessages(); // Refresh UI
                } else {
                    Toast.makeText(ChatActivity.this, "Failed to delete message", Toast.LENGTH_SHORT).show();
                }
            }
            @Override
            public void onFailure(Call<MessageResponse> call, Throwable t) {
                Toast.makeText(ChatActivity.this, "Network error", Toast.LENGTH_SHORT).show();
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
    }
}
