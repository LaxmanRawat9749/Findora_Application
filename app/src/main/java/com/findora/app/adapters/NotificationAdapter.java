package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.R;
import com.findora.app.databinding.ItemNotificationBinding;
import com.findora.app.models.Notification;
import java.util.ArrayList;
import java.util.List;

public class NotificationAdapter extends RecyclerView.Adapter<NotificationAdapter.NotificationViewHolder> {

    public interface OnNotificationClickListener {
        void onNotificationClick(Notification notification);
    }

    private Context context;
    private List<Notification> notifications = new ArrayList<>();
    private OnNotificationClickListener listener;

    public NotificationAdapter(Context context, OnNotificationClickListener listener) {
        this.context = context;
        this.listener = listener;
    }

    public void setNotifications(List<Notification> newNotifications) {
        List<Notification> safeList = newNotifications != null ? new ArrayList<>(newNotifications) : new ArrayList<>();
        androidx.recyclerview.widget.DiffUtil.DiffResult diffResult = androidx.recyclerview.widget.DiffUtil.calculateDiff(
            new androidx.recyclerview.widget.DiffUtil.Callback() {
                @Override
                public int getOldListSize() { return notifications.size(); }
                @Override
                public int getNewListSize() { return safeList.size(); }
                @Override
                public boolean areItemsTheSame(int oldItemPosition, int newItemPosition) {
                    return notifications.get(oldItemPosition).getId() == safeList.get(newItemPosition).getId();
                }
                @Override
                public boolean areContentsTheSame(int oldItemPosition, int newItemPosition) {
                    Notification oldN = notifications.get(oldItemPosition);
                    Notification newN = safeList.get(newItemPosition);
                    return oldN.getId() == newN.getId()
                            && oldN.isRead() == newN.isRead()
                            && String.valueOf(oldN.getMessage()).equals(String.valueOf(newN.getMessage()));
                }
            }
        );
        this.notifications.clear();
        this.notifications.addAll(safeList);
        diffResult.dispatchUpdatesTo(this);
    }

    @NonNull
    @Override
    public NotificationViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemNotificationBinding binding = ItemNotificationBinding.inflate(
                LayoutInflater.from(context), parent, false);
        return new NotificationViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull NotificationViewHolder holder, int position) {
        Notification notification = notifications.get(position);
        holder.bind(notification);
    }

    @Override
    public int getItemCount() {
        return notifications.size();
    }

    class NotificationViewHolder extends RecyclerView.ViewHolder {
        private ItemNotificationBinding binding;

        NotificationViewHolder(ItemNotificationBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(Notification notification) {
            String type = notification.getType() != null ? notification.getType().trim() : "";
            String msg = notification.getMessage() != null ? notification.getMessage() : "";
            String title;
            if (isReturnNotification(type, msg)) {
                title = "RETURN UPDATE";
            } else if ("message".equalsIgnoreCase(type)) {
                title = "NEW MESSAGE";
            } else if ("rating".equalsIgnoreCase(type) || msg.toLowerCase().contains("rate your finder")) {
                title = "RATING";
            } else if ("badge".equalsIgnoreCase(type)) {
                title = "BADGE UNLOCKED";
            } else if ("reputation".equalsIgnoreCase(type)) {
                title = "POINTS & REPUTATION";
            } else if ("approved".equalsIgnoreCase(type)) {
                title = "REPORT APPROVED";
            } else if ("rejected".equalsIgnoreCase(type)) {
                title = "REPORT REJECTED";
            } else if ("match".equalsIgnoreCase(type)) {
                title = "MATCH FOUND";
            } else if (!type.isEmpty()) {
                title = type.replace('_', ' ').toUpperCase();
            } else {
                title = "NOTIFICATION";
            }
            binding.tvTitle.setText(title);
            binding.tvMessage.setText(notification.getMessage());

            String time = notification.getCreatedAt();
            binding.tvTime.setText(com.findora.app.utils.DateUtils.formatNotificationTime(time));

            if (!notification.isRead()) {
                binding.cardNotification.setCardBackgroundColor(
                        ContextCompat.getColor(context, R.color.surface_02));
                binding.vUnreadIndicator.setVisibility(android.view.View.VISIBLE);
                binding.tvTitle.setTypeface(null, android.graphics.Typeface.BOLD);
                binding.tvTitle.setTextColor(ContextCompat.getColor(context, R.color.text_dark));
            } else {
                binding.cardNotification.setCardBackgroundColor(
                        ContextCompat.getColor(context, R.color.card_background));
                binding.vUnreadIndicator.setVisibility(android.view.View.GONE);
                binding.tvTitle.setTypeface(null, android.graphics.Typeface.NORMAL);
                binding.tvTitle.setTextColor(ContextCompat.getColor(context, R.color.text_gray));
            }

            itemView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onNotificationClick(notification);
                }
            });
        }

        private boolean isReturnNotification(String type, String message) {
            if ("claim".equalsIgnoreCase(type)) return true;
            if (message == null) return false;
            String lower = message.toLowerCase();
            return (lower.contains("marked") && lower.contains("returned"))
                    || lower.contains("confirmed the return")
                    || lower.contains("return confirmation")
                    || lower.contains("item is now resolved");
        }
    }
}
