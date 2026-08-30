package com.findora.app.adapters;

import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.models.ItemImage;
import java.util.List;

public class ItemImagePagerAdapter extends RecyclerView.Adapter<ItemImagePagerAdapter.ViewHolder> {
    private final List<ItemImage> images;
    private final OnImageClickListener clickListener;

    public interface OnImageClickListener {
        void onClick(String imageUrl);
    }

    public ItemImagePagerAdapter(List<ItemImage> images, OnImageClickListener clickListener) {
        this.images = images;
        this.clickListener = clickListener;
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
        String url = images.get(position).getImageUrl();
        Glide.with(holder.imageView.getContext())
                .load(url)
                .thumbnail(0.25f)
                .diskCacheStrategy(com.bumptech.glide.load.engine.DiskCacheStrategy.ALL)
                .placeholder(R.color.light_purple)
                .into(holder.imageView);

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
        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            imageView = (ImageView) itemView;
        }
    }
}
