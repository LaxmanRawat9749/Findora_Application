package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.databinding.ItemChatReceivedBinding;
import com.findora.app.databinding.ItemChatSentBinding;
import com.findora.app.models.ChatMessage;
import java.util.ArrayList;
import java.util.List;

public class ChatAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    private static final int VIEW_TYPE_SENT = 1;
    private static final int VIEW_TYPE_RECEIVED = 2;

    private Context context;
    private List<ChatMessage> messages = new ArrayList<>();
    private int currentUserId;

    public ChatAdapter(Context context, int currentUserId) {
        this.context = context;
        this.currentUserId = currentUserId;
    }

    public void setMessages(List<ChatMessage> newMessages) {
        this.messages = newMessages != null ? newMessages : new ArrayList<>();
        notifyDataSetChanged();
    }

    public void addMessage(ChatMessage message) {
        this.messages.add(message);
        notifyItemInserted(messages.size() - 1);
    }

    @Override
    public int getItemViewType(int position) {
        ChatMessage msg = messages.get(position);
        return msg.getSender() == currentUserId ? VIEW_TYPE_SENT : VIEW_TYPE_RECEIVED;
    }

    @NonNull
    @Override
    public RecyclerView.ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        LayoutInflater inflater = LayoutInflater.from(context);
        if (viewType == VIEW_TYPE_SENT) {
            ItemChatSentBinding binding = ItemChatSentBinding.inflate(inflater, parent, false);
            return new SentViewHolder(binding);
        } else {
            ItemChatReceivedBinding binding = ItemChatReceivedBinding.inflate(inflater, parent, false);
            return new ReceivedViewHolder(binding);
        }
    }

    @Override
    public void onBindViewHolder(@NonNull RecyclerView.ViewHolder holder, int position) {
        ChatMessage msg = messages.get(position);
        if (holder instanceof SentViewHolder) {
            ((SentViewHolder) holder).bind(msg);
        } else {
            ((ReceivedViewHolder) holder).bind(msg);
        }
    }

    @Override
    public int getItemCount() {
        return messages.size();
    }

    static class SentViewHolder extends RecyclerView.ViewHolder {
        private ItemChatSentBinding binding;

        SentViewHolder(ItemChatSentBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(ChatMessage msg) {
            binding.tvMessage.setText(msg.getMessage());
            binding.tvTime.setText(formatTime(msg.getSentAt()));
        }

        private String formatTime(String timestamp) {
            if (timestamp == null) return "";
            try {
                if (timestamp.contains("T")) {
                    String timePart = timestamp.split("T")[1];
                    return timePart.substring(0, 5);
                }
            } catch (Exception e) {
                // ignore
            }
            return timestamp;
        }
    }

    static class ReceivedViewHolder extends RecyclerView.ViewHolder {
        private ItemChatReceivedBinding binding;

        ReceivedViewHolder(ItemChatReceivedBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(ChatMessage msg) {
            binding.tvMessage.setText(msg.getMessage());
            binding.tvTime.setText(formatTime(msg.getSentAt()));
        }

        private String formatTime(String timestamp) {
            if (timestamp == null) return "";
            try {
                if (timestamp.contains("T")) {
                    String timePart = timestamp.split("T")[1];
                    return timePart.substring(0, 5);
                }
            } catch (Exception e) {
                // ignore
            }
            return timestamp;
        }
    }
}
