package com.findora.app.adapters;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.DiffUtil;
import com.findora.app.databinding.ItemChatReceivedBinding;
import com.findora.app.databinding.ItemChatSentBinding;
import com.findora.app.models.ChatMessage;
import com.bumptech.glide.Glide;
import com.bumptech.glide.load.engine.DiskCacheStrategy;
import java.util.ArrayList;
import java.util.List;

public class ChatAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder> {

    private static final int VIEW_TYPE_SENT = 1;
    private static final int VIEW_TYPE_RECEIVED = 2;

    public interface OnMessageLongClickListener {
        void onMessageLongClick(ChatMessage message);
    }
    
    public interface OnProfileClickListener {
        void onProfileClick(int userId);
    }

    private Context context;
    private List<ChatMessage> messages = new ArrayList<>();
    private int currentUserId;
    private OnMessageLongClickListener longClickListener;
    private OnProfileClickListener profileClickListener;

    public ChatAdapter(Context context, int currentUserId, OnMessageLongClickListener listener, OnProfileClickListener profileClickListener) {
        this.context = context;
        this.currentUserId = currentUserId;
        this.longClickListener = listener;
        this.profileClickListener = profileClickListener;
    }

    public void setMessages(List<ChatMessage> newMessages) {
        if (newMessages == null) newMessages = new ArrayList<>();
        DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new ChatDiffCallback(this.messages, newMessages));
        this.messages.clear();
        this.messages.addAll(newMessages);
        diffResult.dispatchUpdatesTo(this);
    }
    
    private static class ChatDiffCallback extends DiffUtil.Callback {
        private final List<ChatMessage> oldList;
        private final List<ChatMessage> newList;
        
        ChatDiffCallback(List<ChatMessage> oldList, List<ChatMessage> newList) {
            this.oldList = oldList;
            this.newList = newList;
        }
        
        @Override
        public int getOldListSize() { return oldList.size(); }
        
        @Override
        public int getNewListSize() { return newList.size(); }
        
        @Override
        public boolean areItemsTheSame(int oldItemPosition, int newItemPosition) {
            return oldList.get(oldItemPosition).getId() == newList.get(newItemPosition).getId();
        }
        
        @Override
        public boolean areContentsTheSame(int oldItemPosition, int newItemPosition) {
            ChatMessage oldMsg = oldList.get(oldItemPosition);
            ChatMessage newMsg = newList.get(newItemPosition);
            
            String oldMessage = oldMsg.getMessage() != null ? oldMsg.getMessage() : "";
            String newMessage = newMsg.getMessage() != null ? newMsg.getMessage() : "";
            String oldCaption = oldMsg.getCaption() != null ? oldMsg.getCaption() : "";
            String newCaption = newMsg.getCaption() != null ? newMsg.getCaption() : "";
            
            return oldMessage.equals(newMessage) &&
                   oldCaption.equals(newCaption) &&
                   oldMsg.isDeletedForEveryone() == newMsg.isDeletedForEveryone() &&
                   oldMsg.isEdited() == newMsg.isEdited();
        }
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
            ((SentViewHolder) holder).bind(msg, longClickListener, profileClickListener);
        } else {
            ((ReceivedViewHolder) holder).bind(msg, profileClickListener);
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

        void bind(ChatMessage msg, OnMessageLongClickListener listener, OnProfileClickListener profileClickListener) {
            if ("image".equals(msg.getMessageType()) && msg.getImageUrl() != null) {
                binding.ivMessageImage.setVisibility(android.view.View.VISIBLE);
                Glide.with(binding.getRoot().getContext())
                        .load(msg.getImageUrl())
                        .diskCacheStrategy(DiskCacheStrategy.ALL)
                        .dontAnimate()
                        .into(binding.ivMessageImage);
                
                binding.ivMessageImage.setOnClickListener(v -> {
                    android.content.Intent intent = new android.content.Intent(binding.getRoot().getContext(), com.findora.app.activities.FullScreenImageActivity.class);
                    intent.putExtra("image_url", msg.getImageUrl());
                    binding.getRoot().getContext().startActivity(intent);
                });

                if (msg.getCaption() != null && !msg.getCaption().trim().isEmpty()) {
                    binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                    binding.tvMessage.setText(msg.getCaption());
                } else {
                    binding.tvMessage.setVisibility(android.view.View.GONE);
                }
            } else {
                binding.ivMessageImage.setVisibility(android.view.View.GONE);
                binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                binding.tvMessage.setText(msg.getMessage());
            }

            binding.tvTime.setText(formatTime(msg.getSentAt()));
            
            binding.ivAvatar.setOnClickListener(v -> {
                if (profileClickListener != null) {
                    profileClickListener.onProfileClick(msg.getSender());
                }
            });
            
            if (msg.isDeletedForEveryone()) {
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.ITALIC);
                binding.tvMessage.setTextColor(android.graphics.Color.GRAY);
                binding.tvEdited.setVisibility(android.view.View.GONE);
                binding.getRoot().setOnLongClickListener(null);
                binding.ivMessageImage.setVisibility(android.view.View.GONE);
            } else {
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.NORMAL);
                binding.tvMessage.setTextColor(android.graphics.Color.WHITE);
                binding.tvEdited.setVisibility(msg.isEdited() ? android.view.View.VISIBLE : android.view.View.GONE);
                
                binding.getRoot().setOnLongClickListener(v -> {
                    if (listener != null) listener.onMessageLongClick(msg);
                    return true;
                });
                
                binding.ivMessageImage.setOnLongClickListener(v -> {
                    if (listener != null) listener.onMessageLongClick(msg);
                    return true;
                });
            }
            
            if (msg.getSenderProfileImage() != null && !msg.getSenderProfileImage().isEmpty()) {
                binding.ivAvatar.setImageTintList(null);
                Glide.with(binding.getRoot().getContext())
                        .load(msg.getSenderProfileImage())
                        .circleCrop()
                        .dontAnimate()
                        .placeholder(com.findora.app.R.drawable.ic_person)
                        .error(com.findora.app.R.drawable.ic_person)
                        .into(binding.ivAvatar);
            } else {
                binding.ivAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                        binding.getRoot().getContext().getResources().getColor(com.findora.app.R.color.primary_purple, null)));
                binding.ivAvatar.setImageResource(com.findora.app.R.drawable.ic_person);
            }
        }

        private String formatTime(String timestamp) {
            return com.findora.app.utils.DateUtils.formatChatTime(timestamp);
        }
    }

    static class ReceivedViewHolder extends RecyclerView.ViewHolder {
        private ItemChatReceivedBinding binding;

        ReceivedViewHolder(ItemChatReceivedBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void bind(ChatMessage msg, OnProfileClickListener profileClickListener) {
            if ("image".equals(msg.getMessageType()) && msg.getImageUrl() != null) {
                binding.ivMessageImage.setVisibility(android.view.View.VISIBLE);
                Glide.with(binding.getRoot().getContext())
                        .load(msg.getImageUrl())
                        .diskCacheStrategy(DiskCacheStrategy.ALL)
                        .dontAnimate()
                        .into(binding.ivMessageImage);
                
                binding.ivMessageImage.setOnClickListener(v -> {
                    android.content.Intent intent = new android.content.Intent(binding.getRoot().getContext(), com.findora.app.activities.FullScreenImageActivity.class);
                    intent.putExtra("image_url", msg.getImageUrl());
                    binding.getRoot().getContext().startActivity(intent);
                });

                if (msg.getCaption() != null && !msg.getCaption().trim().isEmpty()) {
                    binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                    binding.tvMessage.setText(msg.getCaption());
                } else {
                    binding.tvMessage.setVisibility(android.view.View.GONE);
                }
            } else {
                binding.ivMessageImage.setVisibility(android.view.View.GONE);
                binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                binding.tvMessage.setText(msg.getMessage());
            }

            binding.tvTime.setText(formatTime(msg.getSentAt()));
            
            binding.ivAvatar.setOnClickListener(v -> {
                if (profileClickListener != null) {
                    profileClickListener.onProfileClick(msg.getSender());
                }
            });
            
            if (msg.isDeletedForEveryone()) {
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.ITALIC);
                binding.tvMessage.setTextColor(android.graphics.Color.GRAY);
                binding.tvEdited.setVisibility(android.view.View.GONE);
                binding.ivMessageImage.setVisibility(android.view.View.GONE);
            } else {
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.NORMAL);
                // Keep the default text color for received messages (usually dark)
                binding.tvEdited.setVisibility(msg.isEdited() ? android.view.View.VISIBLE : android.view.View.GONE);
            }
            
            if (msg.getSenderProfileImage() != null && !msg.getSenderProfileImage().isEmpty()) {
                binding.ivAvatar.setImageTintList(null);
                Glide.with(binding.getRoot().getContext())
                        .load(msg.getSenderProfileImage())
                        .circleCrop()
                        .dontAnimate()
                        .placeholder(com.findora.app.R.drawable.ic_person)
                        .error(com.findora.app.R.drawable.ic_person)
                        .into(binding.ivAvatar);
            } else {
                binding.ivAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                        binding.getRoot().getContext().getResources().getColor(com.findora.app.R.color.primary_purple, null)));
                binding.ivAvatar.setImageResource(com.findora.app.R.drawable.ic_person);
            }
        }

        private String formatTime(String timestamp) {
            return com.findora.app.utils.DateUtils.formatChatTime(timestamp);
        }
    }
}
