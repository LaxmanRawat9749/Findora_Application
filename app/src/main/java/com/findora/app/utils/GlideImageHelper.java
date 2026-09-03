package com.findora.app.utils;

import android.content.Context;
import android.widget.ImageView;

import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;
import com.bumptech.glide.load.model.GlideUrl;
import com.bumptech.glide.load.model.Headers;
import com.findora.app.R;

import java.util.Collections;
import java.util.Map;

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
     * Loads a chat message image attachment.
     */
    public static void loadChatImage(Context context, String url, ImageView target) {
        if (context == null || target == null) return;
        Object model = getGlideModel(url);
        if (model == null) return;

        Glide.with(context)
                .load(model)
                .diskCacheStrategy(DiskCacheStrategy.ALL)
                .dontAnimate()
                .into(target);
    }
}
