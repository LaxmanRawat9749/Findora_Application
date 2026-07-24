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
        this.notifications = newNotifications != null ? newNotifications : new ArrayList<>();
        notifyDataSetChanged();
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
            binding.tvTitle.setText(notification.getType() != null ?
                    notification.getType().replace('_', ' ').toUpperCase() : "Notification");
            binding.tvMessage.setText(notification.getMessage());

            String time = notification.getCreatedAt();
            if (time != null && time.contains("T")) {
                String datePart = time.split("T")[0];
                binding.tvTime.setText(datePart);
            } else {
                binding.tvTime.setText(time != null ? time : "");
            }

            if (!notification.isRead()) {
                binding.getRoot().setBackgroundColor(
                        ContextCompat.getColor(context, R.color.light_purple));
            } else {
                binding.getRoot().setBackgroundColor(
                        ContextCompat.getColor(context, android.R.color.white));
            }

            itemView.setOnClickListener(v -> {
                if (listener != null) {
                    listener.onNotificationClick(notification);
                }
            });
        }
    }
}
