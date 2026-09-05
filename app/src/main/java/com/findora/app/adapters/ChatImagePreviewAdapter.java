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

public class ChatImagePreviewAdapter extends RecyclerView.Adapter<ChatImagePreviewAdapter.ViewHolder> {

    private final List<Uri> imageUris;
    private int selectedPosition = 0;
    private final OnImageClickListener clickListener;
    private final OnImageRemoveListener removeListener;

    public interface OnImageClickListener {
        void onImageClick(Uri uri, int position);
    }

    public interface OnImageRemoveListener {
        void onImageRemove(int position);
    }

    public ChatImagePreviewAdapter(List<Uri> imageUris, OnImageClickListener clickListener, OnImageRemoveListener removeListener) {
        this.imageUris = imageUris;
        this.clickListener = clickListener;
        this.removeListener = removeListener;
    }

    public void setSelectedPosition(int position) {
        int previous = this.selectedPosition;
        this.selectedPosition = position;
        if (previous >= 0 && previous < imageUris.size()) {
            notifyItemChanged(previous);
        }
        if (position >= 0 && position < imageUris.size()) {
            notifyItemChanged(position);
        }
    }

    public int getSelectedPosition() {
        return selectedPosition;
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
                .centerCrop()
                .into(holder.ivPreview);

        holder.itemView.setAlpha(position == selectedPosition ? 1.0f : 0.6f);

        holder.itemView.setOnClickListener(v -> {
            int currentPos = holder.getBindingAdapterPosition();
            if (currentPos != RecyclerView.NO_POSITION) {
                setSelectedPosition(currentPos);
                if (clickListener != null) {
                    clickListener.onImageClick(imageUris.get(currentPos), currentPos);
                }
            }
        });

        holder.ivRemove.setOnClickListener(v -> {
            int currentPos = holder.getBindingAdapterPosition();
            if (currentPos != RecyclerView.NO_POSITION && removeListener != null) {
                removeListener.onImageRemove(currentPos);
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
