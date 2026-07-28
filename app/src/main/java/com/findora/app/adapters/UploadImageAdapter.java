package com.findora.app.adapters;

import android.net.Uri;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ImageView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import java.util.List;

public class UploadImageAdapter extends RecyclerView.Adapter<UploadImageAdapter.ViewHolder> {

    private final List<Uri> imageUris;
    private final OnImageRemoveListener removeListener;

    public interface OnImageRemoveListener {
        void onRemove(int position);
    }

    public UploadImageAdapter(List<Uri> imageUris, OnImageRemoveListener removeListener) {
        this.imageUris = imageUris;
        this.removeListener = removeListener;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_upload_image, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        Uri uri = imageUris.get(position);
        Glide.with(holder.ivPreview.getContext())
                .load(uri)
                .into(holder.ivPreview);

        holder.ivRemove.setOnClickListener(v -> {
            if (removeListener != null) {
                removeListener.onRemove(holder.getAdapterPosition());
            }
        });
    }

    @Override
    public int getItemCount() {
        return imageUris.size();
    }

    public static class ViewHolder extends RecyclerView.ViewHolder {
        ImageView ivPreview;
        ImageView ivRemove;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            ivPreview = itemView.findViewById(R.id.ivPreview);
            ivRemove = itemView.findViewById(R.id.ivRemove);
        }
    }
}
