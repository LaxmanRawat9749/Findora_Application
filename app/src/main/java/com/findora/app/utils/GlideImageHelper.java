package com.findora.app.utils;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.net.Uri;
import android.widget.ImageView;
import android.widget.Toast;

import androidx.core.content.FileProvider;

import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;
import com.bumptech.glide.load.model.GlideUrl;
import com.bumptech.glide.load.model.Headers;
import com.findora.app.R;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Collections;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Centralized Glide helper for smart memory and persistent disk caching.
 *
 * Automatically handles Backblaze B2 presigned URLs:
 * Strips dynamic query parameters (signature, expires, credentials) from the Glide
 * cache key so the same media file is cached stably on disk without redundant re-downloads.
 */
public final class GlideImageHelper {

    private GlideImageHelper() {}

    /**
     * Converts a raw image URL into a cache-optimized Glide model.
     * Preserves the full URL with query parameters for the HTTP request, but
     * returns the base path as the disk cache key.
     */
    public static Object getGlideModel(String url) {
        if (url == null || url.trim().isEmpty()) {
            return null;
        }
        url = url.trim();
        if (url.startsWith("http://") || url.startsWith("https://")) {
            final String rawUrl = url;
            int qIndex = rawUrl.indexOf('?');
            final String cleanKey = (qIndex != -1) ? rawUrl.substring(0, qIndex) : rawUrl;

            return new GlideUrl(rawUrl, new Headers() {
                @Override
                public Map<String, String> getHeaders() {
                    return Collections.emptyMap();
                }
            }) {
                @Override
                public String getCacheKey() {
                    return cleanKey;
                }
            };
        }
        if (url.startsWith("content://") || url.startsWith("file://")) {
            return android.net.Uri.parse(url);
        }
        return url;
    }

    /**
     * Loads an item image thumbnail for list / grid feeds with DiskCacheStrategy.ALL.
     */
    public static void loadItemThumbnail(Context context, String url, ImageView target) {
        if (context == null || target == null) return;
        Object model = getGlideModel(url);
        if (model == null) {
            target.setImageResource(R.drawable.ic_image);
            return;
        }

        android.graphics.drawable.Drawable currentDrawable = target.getDrawable();
        com.bumptech.glide.RequestBuilder<android.graphics.drawable.Drawable> builder = Glide.with(context)
                .load(model)
                .thumbnail(0.25f)
                .diskCacheStrategy(DiskCacheStrategy.ALL)
                .centerCrop()
                .dontAnimate()
                .error(R.drawable.ic_image);

        if (currentDrawable != null) {
            builder = builder.placeholder(currentDrawable);
        }

        builder.into(target);
    }

    /**
     * Loads a high-resolution item detail image.
     */
    public static void loadItemDetail(Context context, String url, ImageView target) {
        if (context == null || target == null) return;
        Object model = getGlideModel(url);
        if (model == null) {
            target.setImageResource(R.drawable.ic_image);
            return;
        }

        android.graphics.drawable.Drawable currentDrawable = target.getDrawable();
        com.bumptech.glide.RequestBuilder<android.graphics.drawable.Drawable> builder = Glide.with(context)
                .load(model)
                .thumbnail(
                        Glide.with(context)
                                .load(model)
                                .thumbnail(0.25f)
                                .diskCacheStrategy(DiskCacheStrategy.ALL)
                                .centerCrop()
                                .dontAnimate()
                )
                .diskCacheStrategy(DiskCacheStrategy.ALL)
                .centerCrop()
                .dontAnimate()
                .error(R.drawable.ic_image);

        if (currentDrawable != null) {
            builder = builder.placeholder(currentDrawable);
        }

        builder.into(target);
    }

    /**
     * Loads a circular user avatar with fallback to ic_person.
     */
    public static void loadAvatar(Context context, String url, ImageView target) {
        loadAvatar(context, url, target, false);
    }

    /**
     * Loads a circular user avatar with optional cache invalidation.
     */
    public static void loadAvatar(Context context, String url, ImageView target, boolean invalidateCache) {
        if (context == null || target == null) return;
        Object model = getGlideModel(url);
        if (model == null) {
            target.setImageResource(R.drawable.ic_person);
            return;
        }

        android.graphics.drawable.Drawable currentDrawable = target.getDrawable();
        com.bumptech.glide.RequestBuilder<android.graphics.drawable.Drawable> builder = Glide.with(context)
                .load(model)
                .circleCrop()
                .dontAnimate()
                .error(R.drawable.ic_person);

        if (invalidateCache) {
            builder = builder.signature(new com.bumptech.glide.signature.ObjectKey(System.currentTimeMillis()))
                    .diskCacheStrategy(DiskCacheStrategy.NONE)
                    .skipMemoryCache(true);
        } else {
            builder = builder.diskCacheStrategy(DiskCacheStrategy.ALL);
        }

        if (currentDrawable != null) {
            builder = builder.placeholder(currentDrawable);
        }

        builder.into(target);
    }

    /**
     * Loads a chat message image attachment preserving aspect ratio without cropping.
     */
    public static void loadChatImage(Context context, String url, ImageView target) {
        if (context == null || target == null) return;
        Object model = getGlideModel(url);
        if (model == null) return;

        android.graphics.drawable.Drawable currentDrawable = target.getDrawable();
        com.bumptech.glide.RequestBuilder<android.graphics.drawable.Drawable> builder = Glide.with(context)
                .load(model)
                .diskCacheStrategy(DiskCacheStrategy.ALL)
                .dontAnimate()
                .fitCenter();

        if (currentDrawable != null) {
            builder = builder.placeholder(currentDrawable);
        }

        builder.into(target);
    }

    /**
     * Loads a full-screen image for ZoomableImageView without cropping or distortion.
     */
    public static void loadFullScreenImage(Context context, String url, ImageView target) {
        if (context == null || target == null) return;
        Object model = getGlideModel(url);
        if (model == null) {
            target.setImageResource(R.drawable.ic_image);
            return;
        }

        Glide.with(context)
                .load(model)
                .diskCacheStrategy(DiskCacheStrategy.ALL)
                .dontAnimate()
                .error(R.drawable.ic_image)
                .into(target);
    }

    private static final ExecutorService CLIPBOARD_EXECUTOR = Executors.newSingleThreadExecutor();

    /**
     * Retrieves cached image file and copies it as a content URI to Android Clipboard.
     * Also supports copying the optional caption.
     */
    public static void copyImageToClipboard(Context context, String imageUrl, String caption) {
        if (context == null) return;
        if (imageUrl == null || imageUrl.trim().isEmpty()) {
            if (caption != null && !caption.trim().isEmpty()) {
                ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                if (clipboard != null) {
                    ClipData clip = ClipData.newPlainText("Caption", caption);
                    clipboard.setPrimaryClip(clip);
                    Toast.makeText(context, "Caption copied", Toast.LENGTH_SHORT).show();
                }
            } else {
                Toast.makeText(context, "No image to copy", Toast.LENGTH_SHORT).show();
            }
            return;
        }

        Toast.makeText(context, "Copying image...", Toast.LENGTH_SHORT).show();

        CLIPBOARD_EXECUTOR.execute(() -> {
            try {
                Object model = getGlideModel(imageUrl);
                File srcFile = Glide.with(context.getApplicationContext())
                        .asFile()
                        .load(model)
                        .submit()
                        .get();

                if (srcFile == null || !srcFile.exists()) {
                    throw new Exception("Source image file not found");
                }

                File copyDir = new File(context.getCacheDir(), "copied_images");
                if (!copyDir.exists()) {
                    //noinspection ResultOfMethodCallIgnored
                    copyDir.mkdirs();
                }

                File destFile = new File(copyDir, "chat_img_" + System.currentTimeMillis() + ".jpg");
                try (InputStream in = new FileInputStream(srcFile);
                     OutputStream out = new FileOutputStream(destFile)) {
                    byte[] buffer = new byte[8192];
                    int len;
                    while ((len = in.read(buffer)) > 0) {
                        out.write(buffer, 0, len);
                    }
                    out.flush();
                }

                Uri contentUri = FileProvider.getUriForFile(
                        context,
                        context.getPackageName() + ".fileprovider",
                        destFile
                );

                android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                mainHandler.post(() -> {
                    try {
                        ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                        if (clipboard != null) {
                            ClipData clip = ClipData.newUri(context.getContentResolver(), "Chat Image", contentUri);
                            if (caption != null && !caption.trim().isEmpty()) {
                                clip.addItem(new ClipData.Item(caption));
                            }
                            clipboard.setPrimaryClip(clip);
                            Toast.makeText(context, "Image copied to clipboard", Toast.LENGTH_SHORT).show();
                        }
                    } catch (Exception e) {
                        Toast.makeText(context, "Failed to copy image to clipboard", Toast.LENGTH_SHORT).show();
                    }
                });
            } catch (Exception e) {
                e.printStackTrace();
                android.os.Handler mainHandler = new android.os.Handler(android.os.Looper.getMainLooper());
                mainHandler.post(() -> {
                    if (caption != null && !caption.trim().isEmpty()) {
                        ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                        if (clipboard != null) {
                            ClipData clip = ClipData.newPlainText("Caption", caption);
                            clipboard.setPrimaryClip(clip);
                            Toast.makeText(context, "Caption copied", Toast.LENGTH_SHORT).show();
                        }
                    } else {
                        Toast.makeText(context, "Failed to copy image", Toast.LENGTH_SHORT).show();
                    }
                });
            }
        });
    }
}
