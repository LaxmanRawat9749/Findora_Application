package com.findora.app.adapters;

import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.models.ItemImage;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Objects;

public class ItemImagePagerAdapter extends RecyclerView.Adapter<ItemImagePagerAdapter.ViewHolder> {
    private final List<ItemImage> images = new ArrayList<>();
    private final OnImageClickListener clickListener;

    public interface OnImageClickListener {
        void onClick(String imageUrl);
    }

    public ItemImagePagerAdapter(List<ItemImage> initialImages, OnImageClickListener clickListener) {
        if (initialImages != null) {
            this.images.addAll(initialImages);
        }
        this.clickListener = clickListener;
        setHasStableIds(true);
    }

    public void setImages(List<ItemImage> newImages) {
        if (newImages == null) {
            newImages = Collections.emptyList();
        }

        // Compare current list with new list to avoid unnecessary adapter invalidation & image flashing
        if (this.images.size() == newImages.size()) {
            boolean isIdentical = true;
            for (int i = 0; i < this.images.size(); i++) {
                String oldUrl = this.images.get(i) != null ? this.images.get(i).getImageUrl() : null;
                String newUrl = newImages.get(i) != null ? newImages.get(i).getImageUrl() : null;
                if (!Objects.equals(oldUrl, newUrl)) {
                    isIdentical = false;
                    break;
                }
            }
            if (isIdentical) {
                return; // Nothing changed, keep existing rendered images completely stable without flicker
            }
        }

        this.images.clear();
        this.images.addAll(newImages);
        notifyDataSetChanged();
    }

    @Override
    public long getItemId(int position) {
        if (position >= 0 && position < images.size() && images.get(position) != null) {
            ItemImage img = images.get(position);
            if (img.getId() > 0) {
                return img.getId();
            }
            String url = img.getImageUrl();
            if (url != null) {
                return url.hashCode();
            }
        }
        return position;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ImageView imageView = new ImageView(parent.getContext());
        imageView.setLayoutParams(new ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
        imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
        return new ViewHolder(imageView);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        if (position < 0 || position >= images.size() || images.get(position) == null) return;
        String url = images.get(position).getImageUrl();

        // Avoid re-triggering Glide if this viewholder is already displaying this exact image URL
        if (url != null && url.equals(holder.boundUrl) && holder.imageView.getDrawable() != null) {
            return;
        }
        holder.boundUrl = url;

        com.findora.app.utils.GlideImageHelper.loadItemDetail(holder.imageView.getContext(), url, holder.imageView);

        holder.imageView.setOnClickListener(v -> {
            if (clickListener != null) clickListener.onClick(url);
        });
    }

    @Override
    public int getItemCount() {
        return images.size();
    }

    public static class ViewHolder extends RecyclerView.ViewHolder {
        ImageView imageView;
        String boundUrl;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            imageView = (ImageView) itemView;
        }
    }
}
