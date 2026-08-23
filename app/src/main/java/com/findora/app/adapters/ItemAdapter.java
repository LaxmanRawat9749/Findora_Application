package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import com.bumptech.glide.Glide;
import com.findora.app.R;
import com.findora.app.databinding.ItemCardBinding;
import com.findora.app.models.Item;
import com.findora.app.utils.DateUtils;
import java.util.ArrayList;
import java.util.List;

public class ItemAdapter extends RecyclerView.Adapter<ItemAdapter.ItemViewHolder> {

    public interface OnItemClickListener {
        void onItemClick(Item item);
    }

    private Context context;
    private List<Item> items = new ArrayList<>();
    private OnItemClickListener listener;
    private boolean isMyReportsStyle;

    public ItemAdapter(Context context, OnItemClickListener listener) {
        this.context = context;
        this.isMyReportsStyle = false;
        this.listener = listener;
    }

    public ItemAdapter(Context context, boolean isMyReportsStyle, OnItemClickListener listener) {
        this.context = context;
        this.isMyReportsStyle = isMyReportsStyle;
        this.listener = listener;
    }

    public void setItems(List<Item> newItems) {
        this.items = newItems != null ? newItems : new ArrayList<>();
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ItemViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemCardBinding binding = ItemCardBinding.inflate(LayoutInflater.from(context), parent, false);
        return new ItemViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ItemViewHolder holder, int position) {
        Item item = items.get(position);
        holder.bind(item);
    }

    @Override
    public int getItemCount() {
        return items.size();
    }

    class ItemViewHolder extends RecyclerView.ViewHolder {
        private ItemCardBinding binding;

        public ItemViewHolder(ItemCardBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        public void bind(Item item) {
            binding.tvTitle.setText(item.getTitle());
            binding.tvCategory.setText(item.getCategory() != null ? item.getCategory().replace('_', ' ') : "");

            boolean isResolved = "resolved".equalsIgnoreCase(item.getStatus()) || item.isFinderReturnedConfirm();
            boolean isPendingReturn = item.isOwnerReturnedConfirm() && !item.isFinderReturnedConfirm() && !isResolved;
            boolean isLost = "lost".equalsIgnoreCase(item.getType());

            if (isResolved) {
                binding.tvTypeBadge.setText("RECOVERED");
                binding.tvTypeBadge.setBackgroundColor(ContextCompat.getColor(context, R.color.light_green));
                binding.tvTypeBadge.setTextColor(ContextCompat.getColor(context, R.color.success_green));

                String dateStr = item.getResolvedAt() != null && !item.getResolvedAt().isEmpty() 
                        ? item.getResolvedAt() : item.getUpdatedAt();
                if (dateStr != null && !dateStr.isEmpty()) {
                    binding.tvDate.setVisibility(View.VISIBLE);
                    binding.tvDate.setText("Returned: " + DateUtils.formatNotificationTime(dateStr));
                } else {
                    binding.tvDate.setVisibility(View.GONE);
                }
            } else if (isPendingReturn) {
                binding.tvTypeBadge.setText("RETURN PENDING");
                binding.tvTypeBadge.setBackgroundColor(ContextCompat.getColor(context, R.color.light_warning));
                binding.tvTypeBadge.setTextColor(ContextCompat.getColor(context, R.color.warning_orange));

                if (item.getReportedAt() != null && !item.getReportedAt().isEmpty()) {
                    binding.tvDate.setVisibility(View.VISIBLE);
                    binding.tvDate.setText((isLost ? "Reported: " : "Found: ") + DateUtils.formatNotificationTime(item.getReportedAt()));
                } else {
                    binding.tvDate.setVisibility(View.GONE);
                }
            } else {
                binding.tvTypeBadge.setText(isLost ? "LOST" : "FOUND");
                binding.tvTypeBadge.setBackgroundColor(ContextCompat.getColor(context, isLost ? R.color.light_red : R.color.light_purple));
                binding.tvTypeBadge.setTextColor(ContextCompat.getColor(context, isLost ? R.color.error_red : R.color.primary_purple));

                if (item.getReportedAt() != null && !item.getReportedAt().isEmpty()) {
                    binding.tvDate.setVisibility(View.VISIBLE);
                    binding.tvDate.setText((isLost ? "Reported: " : "Found: ") + DateUtils.formatNotificationTime(item.getReportedAt()));
                } else {
                    binding.tvDate.setVisibility(View.GONE);
                }
            }

            if (item.getLocation() != null && !item.getLocation().isEmpty()) {
                binding.layoutLocation.setVisibility(View.VISIBLE);
                binding.tvLocation.setText(item.getLocation());
            } else {
                binding.layoutLocation.setVisibility(View.GONE);
            }

            if (item.getReward() > 0) {
                binding.layoutReward.setVisibility(View.VISIBLE);
                binding.tvReward.setText("Rs. " + (int) item.getReward());
            } else {
                binding.layoutReward.setVisibility(View.GONE);
            }

            String imageUrl = null;
            if (item.getImages() != null && !item.getImages().isEmpty()) {
                imageUrl = item.getImages().get(0).getImageUrl();
            } else if (item.getImageUrl() != null) {
                imageUrl = item.getImageUrl();
            } else if (item.getImage() != null) {
                imageUrl = item.getImage();
            }

            if (imageUrl != null && !imageUrl.isEmpty()) {
                binding.ivItemImage.setVisibility(View.VISIBLE);
                binding.layoutIconPlaceholder.setVisibility(View.GONE);
                Glide.with(context)
                        .load(imageUrl)
                        .centerCrop()
                        .into(binding.ivItemImage);
            } else {
                binding.ivItemImage.setVisibility(View.GONE);
                binding.layoutIconPlaceholder.setVisibility(View.VISIBLE);
            }

            itemView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onItemClick(item);
                }
            });
        }
    }
}
