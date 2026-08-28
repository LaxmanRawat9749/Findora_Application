package com.findora.app.adapters;

import android.content.Context;
import android.content.Intent;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import com.findora.app.activities.ChatActivity;
import com.findora.app.databinding.ItemConversationBinding;
import com.findora.app.models.Conversation;
import com.findora.app.utils.Constants;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.ArrayList;
import java.util.List;
import java.util.List;

public class ConversationAdapter extends RecyclerView.Adapter<ConversationAdapter.ViewHolder> {

    public interface OnProfileClickListener {
        void onProfileClick(int userId);
    }

    private final Context context;
    private List<Conversation> conversations = new ArrayList<>();
    private final OnProfileClickListener profileClickListener;

    public ConversationAdapter(Context context, OnProfileClickListener profileClickListener) {
        this.context = context;
        this.profileClickListener = profileClickListener;
    }

    public void setConversations(List<Conversation> conversations) {
        this.conversations = conversations != null ? conversations : new ArrayList<>();
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemConversationBinding binding = ItemConversationBinding.inflate(LayoutInflater.from(context), parent, false);
        return new ViewHolder(binding);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        holder.bind(conversations.get(position));
    }

    @Override
    public int getItemCount() {
        return conversations.size();
    }

    class ViewHolder extends RecyclerView.ViewHolder {
        private final ItemConversationBinding binding;

        public ViewHolder(ItemConversationBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        public void bind(Conversation conversation) {
            String name = conversation.getOtherUserName() != null ? conversation.getOtherUserName() : "User";
            binding.tvUsername.setText(name);
            
            if (conversation.getOtherUserProfileImage() != null && !conversation.getOtherUserProfileImage().isEmpty()) {
                binding.ivAvatar.setImageTintList(null);
                com.bumptech.glide.Glide.with(context)
                        .load(conversation.getOtherUserProfileImage())
                        .circleCrop()
                        .placeholder(com.findora.app.R.drawable.ic_person)
                        .error(com.findora.app.R.drawable.ic_person)
                        .into(binding.ivAvatar);
            } else {
                binding.ivAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                        context.getResources().getColor(com.findora.app.R.color.primary_purple, null)));
                binding.ivAvatar.setImageResource(com.findora.app.R.drawable.ic_person);
            }
            
            View.OnClickListener profileClickListenerView = v -> {
                if (profileClickListener != null) {
                    profileClickListener.onProfileClick(conversation.getOtherUserId());
                }
            };
            binding.ivAvatar.setOnClickListener(profileClickListenerView);
            binding.tvUsername.setOnClickListener(profileClickListenerView);
            
            if (conversation.isOnline()) {
                binding.vOnlineIndicator.setVisibility(View.VISIBLE);
            } else {
                binding.vOnlineIndicator.setVisibility(View.GONE);
            }
            
            if (conversation.getItemImage() != null && !conversation.getItemImage().isEmpty()) {
                binding.ivItemThumbnail.setImageTintList(null);
                com.bumptech.glide.Glide.with(context)
                        .load(conversation.getItemImage())
                        .centerCrop()
                        .placeholder(com.findora.app.R.drawable.ic_image)
                        .error(com.findora.app.R.drawable.ic_image)
                        .into(binding.ivItemThumbnail);
            } else {
                binding.ivItemThumbnail.setImageTintList(android.content.res.ColorStateList.valueOf(context.getResources().getColor(com.findora.app.R.color.text_gray, null)));
                binding.ivItemThumbnail.setImageResource(com.findora.app.R.drawable.ic_image);
            }
            
            String title = conversation.getItemTitle() != null ? conversation.getItemTitle() : "Unknown Item";
            binding.tvItemTitle.setText("Re: " + title);

            binding.tvLastMessage.setText(conversation.getLastMessage());
            binding.tvTime.setText(formatTime(conversation.getLastMessageTime()));

            if (conversation.getUnreadCount() > 0) {
                binding.tvUnreadBadge.setVisibility(View.VISIBLE);
                binding.tvUnreadBadge.setText(String.valueOf(conversation.getUnreadCount()));
                binding.tvLastMessage.setTypeface(null, android.graphics.Typeface.BOLD);
                binding.tvLastMessage.setTextColor(context.getResources().getColor(com.findora.app.R.color.text_dark, null));
            } else {
                binding.tvUnreadBadge.setVisibility(View.GONE);
                binding.tvLastMessage.setTypeface(null, android.graphics.Typeface.NORMAL);
                binding.tvLastMessage.setTextColor(context.getResources().getColor(com.findora.app.R.color.text_gray, null));
            }

            itemView.setOnClickListener(v -> {
                android.util.Log.e("ChatBug", "Opening Chat from Conversation List (Notification Chat)! " +
                        "conversation_id=" + conversation.getId() + 
                        ", item_title=" + conversation.getItemTitle());
                Intent intent = new Intent(context, ChatActivity.class);
                intent.putExtra(Constants.EXTRA_CONVERSATION_ID, conversation.getId());
                intent.putExtra("other_user_name", name);
                context.startActivity(intent);
            });
        }
        
        private String formatTime(String timeStr) {
            return com.findora.app.utils.DateUtils.formatConversationTime(timeStr);
        }
    }
}
