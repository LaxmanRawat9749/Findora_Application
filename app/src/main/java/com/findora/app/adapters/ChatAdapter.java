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

    public interface OnMessageActionListener {
        void onCopy(ChatMessage message);
        void onEdit(ChatMessage message);
        void onDelete(ChatMessage message);
    }

    private Context context;
    private List<ChatMessage> messages = new ArrayList<>();
    private int currentUserId;
    private OnMessageLongClickListener longClickListener;
    private OnProfileClickListener profileClickListener;
    private OnMessageActionListener actionListener;

    public ChatAdapter(Context context, int currentUserId, OnMessageLongClickListener listener, OnProfileClickListener profileClickListener) {
        this(context, currentUserId, listener, profileClickListener, null);
    }

    public ChatAdapter(Context context, int currentUserId, OnMessageLongClickListener listener, OnProfileClickListener profileClickListener, OnMessageActionListener actionListener) {
        this.context = context;
        this.currentUserId = currentUserId;
        this.longClickListener = listener;
        this.profileClickListener = profileClickListener;
        this.actionListener = actionListener;
    }

    public void setMessages(List<ChatMessage> newMessages) {
        if (newMessages == null) newMessages = new ArrayList<>();

        // Preserve any in-flight temporary messages (id < 0) that are still uploading/sending
        List<ChatMessage> pendingTempMessages = new ArrayList<>();
        for (ChatMessage m : this.messages) {
            if (m != null && m.getId() < 0) {
                pendingTempMessages.add(m);
            }
        }

        List<ChatMessage> combinedList = new ArrayList<>(newMessages);
        if (!pendingTempMessages.isEmpty()) {
            for (ChatMessage tempMsg : pendingTempMessages) {
                combinedList.add(tempMsg);
            }
        }

        DiffUtil.DiffResult diffResult = DiffUtil.calculateDiff(new ChatDiffCallback(this.messages, combinedList));
        this.messages.clear();
        this.messages.addAll(combinedList);
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
            ChatMessage oldMsg = oldList.get(oldItemPosition);
            ChatMessage newMsg = newList.get(newItemPosition);
            if (oldMsg == null || newMsg == null) return false;
            return oldMsg.getId() == newMsg.getId();
        }
        
        @Override
        public boolean areContentsTheSame(int oldItemPosition, int newItemPosition) {
            ChatMessage oldMsg = oldList.get(oldItemPosition);
            ChatMessage newMsg = newList.get(newItemPosition);
            if (oldMsg == null || newMsg == null) return false;
            
            String oldMessage = oldMsg.getMessage() != null ? oldMsg.getMessage() : "";
            String newMessage = newMsg.getMessage() != null ? newMsg.getMessage() : "";
            String oldCaption = oldMsg.getCaption() != null ? oldMsg.getCaption() : "";
            String newCaption = newMsg.getCaption() != null ? newMsg.getCaption() : "";
            String oldImg = oldMsg.getImageUrl() != null ? oldMsg.getImageUrl() : "";
            String newImg = newMsg.getImageUrl() != null ? newMsg.getImageUrl() : "";
            String oldSenderImg = oldMsg.getSenderProfileImage() != null ? oldMsg.getSenderProfileImage() : "";
            String newSenderImg = newMsg.getSenderProfileImage() != null ? newMsg.getSenderProfileImage() : "";
            
            return oldMessage.equals(newMessage) &&
                   oldCaption.equals(newCaption) &&
                   oldImg.equals(newImg) &&
                   oldSenderImg.equals(newSenderImg) &&
                   oldMsg.isDeletedForEveryone() == newMsg.isDeletedForEveryone() &&
                   oldMsg.isEdited() == newMsg.isEdited();
        }
    }

    public void addMessage(ChatMessage message) {
        if (message == null) return;
        for (ChatMessage m : this.messages) {
            if (m.getId() == message.getId()) {
                return; // Already present in list
            }
        }
        this.messages.add(message);
        notifyItemInserted(this.messages.size() - 1);
    }

    public void replaceMessage(int oldMessageId, ChatMessage newMessage) {
        if (newMessage == null) return;
        int oldIndex = -1;
        int existingNewIndex = -1;
        for (int i = 0; i < this.messages.size(); i++) {
            ChatMessage msg = this.messages.get(i);
            if (msg != null) {
                if (msg.getId() == oldMessageId) {
                    oldIndex = i;
                } else if (msg.getId() == newMessage.getId()) {
                    existingNewIndex = i;
                }
            }
        }
        if (oldIndex != -1) {
            if (existingNewIndex != -1) {
                // Server confirmed message was already delivered via polling; remove temp placeholder
                this.messages.remove(oldIndex);
                notifyItemRemoved(oldIndex);
            } else {
                this.messages.set(oldIndex, newMessage);
                notifyItemChanged(oldIndex);
            }
            return;
        }
        if (existingNewIndex == -1) {
            addMessage(newMessage);
        }
    }

    public void removeTemporaryMessage(int tempId) {
        for (int i = 0; i < this.messages.size(); i++) {
            ChatMessage msg = this.messages.get(i);
            if (msg != null && msg.getId() == tempId) {
                this.messages.remove(i);
                notifyItemRemoved(i);
                break;
            }
        }
    }

    public void markMessageDeleted(int messageId) {
        for (int i = 0; i < this.messages.size(); i++) {
            ChatMessage msg = this.messages.get(i);
            if (msg != null && msg.getId() == messageId) {
                msg.setDeletedForEveryone(true);
                if ("image".equals(msg.getMessageType())) {
                    msg.setMessage("This image was deleted");
                    msg.setImageUrl(null);
                    msg.setCaption("");
                } else {
                    msg.setMessage("This message was deleted");
                }
                notifyItemChanged(i);
                break;
            }
        }
    }

    public void removeMessage(int messageId) {
        for (int i = 0; i < this.messages.size(); i++) {
            ChatMessage msg = this.messages.get(i);
            if (msg != null && msg.getId() == messageId) {
                this.messages.remove(i);
                notifyItemRemoved(i);
                break;
            }
        }
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
            ((SentViewHolder) holder).bind(msg, longClickListener, profileClickListener, actionListener);
        } else {
            ((ReceivedViewHolder) holder).bind(msg, longClickListener, profileClickListener, actionListener);
        }
    }

    @Override
    public void onViewRecycled(@NonNull RecyclerView.ViewHolder holder) {
        super.onViewRecycled(holder);
        if (holder instanceof SentViewHolder) {
            ((SentViewHolder) holder).cleanup();
        } else if (holder instanceof ReceivedViewHolder) {
            ((ReceivedViewHolder) holder).cleanup();
        }
    }

    @Override
    public int getItemCount() {
        return messages.size();
    }

    static class SentViewHolder extends RecyclerView.ViewHolder {
        private ItemChatSentBinding binding;
        private boolean isMenuOpen = false;
        private androidx.appcompat.widget.PopupMenu currentPopup = null;

        SentViewHolder(ItemChatSentBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void cleanup() {
            if (currentPopup != null) {
                currentPopup.dismiss();
                currentPopup = null;
            }
            isMenuOpen = false;
            binding.btnMoreOptions.setVisibility(android.view.View.GONE);
        }

        void bind(ChatMessage msg, OnMessageLongClickListener listener, OnProfileClickListener profileClickListener, OnMessageActionListener actionListener) {
            boolean isDeleted = msg.isDeletedForEveryone();

            if (isDeleted) {
                binding.btnMoreOptions.setVisibility(android.view.View.GONE);
                binding.btnMoreOptions.setOnClickListener(null);
                binding.btnMoreOptions.setOnHoverListener(null);
                binding.getRoot().setOnHoverListener(null);
                binding.layoutBubble.setOnHoverListener(null);

                binding.layoutImageContainer.setVisibility(android.view.View.GONE);
                binding.ivMessageImage.setOnClickListener(null);
                binding.ivMessageImage.setOnLongClickListener(null);

                binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                String deletedText = "image".equals(msg.getMessageType()) ? "This image was deleted" : "This message was deleted";
                if (msg.getMessage() != null && !msg.getMessage().trim().isEmpty()) {
                    deletedText = msg.getMessage();
                }
                binding.tvMessage.setText(deletedText);
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.ITALIC);
                binding.tvMessage.setTextColor(android.graphics.Color.parseColor("#CCCCCC"));
                binding.tvEdited.setVisibility(android.view.View.GONE);
                binding.getRoot().setOnLongClickListener(null);
            } else if ("image".equals(msg.getMessageType()) && msg.getImageUrl() != null) {
                setupHoverAndMenu(msg, actionListener);

                binding.layoutImageContainer.setVisibility(android.view.View.VISIBLE);
                com.findora.app.utils.GlideImageHelper.loadChatImage(binding.getRoot().getContext(), msg.getImageUrl(), binding.ivMessageImage);
                
                // Show in-bubble upload spinner if the message is in-flight (temp negative ID)
                if (msg.getId() < 0) {
                    binding.pbImageUpload.setVisibility(android.view.View.VISIBLE);
                } else {
                    binding.pbImageUpload.setVisibility(android.view.View.GONE);
                }

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
            } else {
                setupHoverAndMenu(msg, actionListener);

                binding.layoutImageContainer.setVisibility(android.view.View.GONE);
                binding.ivMessageImage.setOnClickListener(null);
                binding.ivMessageImage.setOnLongClickListener(null);

                binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                binding.tvMessage.setText(msg.getMessage());
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.NORMAL);
                binding.tvMessage.setTextColor(android.graphics.Color.WHITE);
                binding.tvEdited.setVisibility(msg.isEdited() ? android.view.View.VISIBLE : android.view.View.GONE);

                binding.getRoot().setOnLongClickListener(v -> {
                    if (listener != null) listener.onMessageLongClick(msg);
                    return true;
                });
            }

            binding.tvTime.setText(formatTime(msg.getSentAt()));
            
            binding.ivAvatar.setOnClickListener(v -> {
                if (profileClickListener != null) {
                    profileClickListener.onProfileClick(msg.getSender());
                }
            });
            
            if (msg.getSenderProfileImage() != null && !msg.getSenderProfileImage().trim().isEmpty()) {
                binding.ivAvatar.setImageTintList(null);
                com.findora.app.utils.GlideImageHelper.loadAvatar(binding.getRoot().getContext(), msg.getSenderProfileImage(), binding.ivAvatar);
            } else {
                binding.ivAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                        binding.getRoot().getContext().getResources().getColor(com.findora.app.R.color.primary_purple, null)));
                binding.ivAvatar.setImageResource(com.findora.app.R.drawable.ic_person);
            }
        }

        private void setupHoverAndMenu(ChatMessage msg, OnMessageActionListener actionListener) {
            binding.btnMoreOptions.setVisibility(isMenuOpen ? android.view.View.VISIBLE : android.view.View.GONE);

            android.view.View.OnHoverListener hoverListener = (v, event) -> {
                int action = event.getAction();
                if (action == android.view.MotionEvent.ACTION_HOVER_ENTER || action == android.view.MotionEvent.ACTION_HOVER_MOVE) {
                    if (!msg.isDeletedForEveryone()) {
                        binding.btnMoreOptions.setVisibility(android.view.View.VISIBLE);
                    }
                } else if (action == android.view.MotionEvent.ACTION_HOVER_EXIT) {
                    if (!isMenuOpen) {
                        binding.btnMoreOptions.setVisibility(android.view.View.GONE);
                    }
                }
                return false;
            };

            binding.getRoot().setOnHoverListener(hoverListener);
            binding.layoutBubble.setOnHoverListener(hoverListener);
            binding.btnMoreOptions.setOnHoverListener(hoverListener);

            binding.btnMoreOptions.setOnClickListener(v -> {
                if (currentPopup != null) {
                    currentPopup.dismiss();
                }
                androidx.appcompat.widget.PopupMenu popup = new androidx.appcompat.widget.PopupMenu(v.getContext(), v);
                popup.getMenuInflater().inflate(com.findora.app.R.menu.menu_chat_message_sent, popup.getMenu());

                isMenuOpen = true;
                currentPopup = popup;
                binding.btnMoreOptions.setVisibility(android.view.View.VISIBLE);

                popup.setOnMenuItemClickListener(item -> {
                    int itemId = item.getItemId();
                    if (itemId == com.findora.app.R.id.action_copy) {
                        if (actionListener != null) actionListener.onCopy(msg);
                        return true;
                    } else if (itemId == com.findora.app.R.id.action_edit) {
                        if (actionListener != null) actionListener.onEdit(msg);
                        return true;
                    } else if (itemId == com.findora.app.R.id.action_delete) {
                        if (actionListener != null) actionListener.onDelete(msg);
                        return true;
                    }
                    return false;
                });

                popup.setOnDismissListener(p -> {
                    isMenuOpen = false;
                    currentPopup = null;
                    binding.btnMoreOptions.setVisibility(android.view.View.GONE);
                });

                popup.show();
            });
        }

        private String formatTime(String timestamp) {
            return com.findora.app.utils.DateUtils.formatChatTime(timestamp);
        }
    }

    static class ReceivedViewHolder extends RecyclerView.ViewHolder {
        private ItemChatReceivedBinding binding;
        private boolean isMenuOpen = false;
        private androidx.appcompat.widget.PopupMenu currentPopup = null;

        ReceivedViewHolder(ItemChatReceivedBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }

        void cleanup() {
            if (currentPopup != null) {
                currentPopup.dismiss();
                currentPopup = null;
            }
            isMenuOpen = false;
            binding.btnMoreOptions.setVisibility(android.view.View.GONE);
        }

        void bind(ChatMessage msg, OnMessageLongClickListener longClickListener, OnProfileClickListener profileClickListener, OnMessageActionListener actionListener) {
            boolean isDeleted = msg.isDeletedForEveryone();

            if (isDeleted) {
                binding.btnMoreOptions.setVisibility(android.view.View.GONE);
                binding.btnMoreOptions.setOnClickListener(null);
                binding.btnMoreOptions.setOnHoverListener(null);
                binding.getRoot().setOnHoverListener(null);
                binding.layoutBubble.setOnHoverListener(null);

                binding.ivMessageImage.setVisibility(android.view.View.GONE);
                binding.ivMessageImage.setOnClickListener(null);
                binding.ivMessageImage.setOnLongClickListener(null);

                binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                String deletedText = "image".equals(msg.getMessageType()) ? "This image was deleted" : "This message was deleted";
                if (msg.getMessage() != null && !msg.getMessage().trim().isEmpty()) {
                    deletedText = msg.getMessage();
                }
                binding.tvMessage.setText(deletedText);
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.ITALIC);
                binding.tvMessage.setTextColor(android.graphics.Color.GRAY);
                binding.tvEdited.setVisibility(android.view.View.GONE);
                binding.getRoot().setOnLongClickListener(null);
            } else if ("image".equals(msg.getMessageType()) && msg.getImageUrl() != null) {
                setupHoverAndMenu(msg, actionListener);

                binding.ivMessageImage.setVisibility(android.view.View.VISIBLE);
                com.findora.app.utils.GlideImageHelper.loadChatImage(binding.getRoot().getContext(), msg.getImageUrl(), binding.ivMessageImage);
                
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
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.NORMAL);
                binding.tvMessage.setTextColor(binding.getRoot().getContext().getResources().getColor(com.findora.app.R.color.text_dark, null));
                binding.tvEdited.setVisibility(msg.isEdited() ? android.view.View.VISIBLE : android.view.View.GONE);

                binding.getRoot().setOnLongClickListener(v -> {
                    if (longClickListener != null) longClickListener.onMessageLongClick(msg);
                    return true;
                });

                binding.ivMessageImage.setOnLongClickListener(v -> {
                    if (longClickListener != null) longClickListener.onMessageLongClick(msg);
                    return true;
                });
            } else {
                setupHoverAndMenu(msg, actionListener);

                binding.ivMessageImage.setVisibility(android.view.View.GONE);
                binding.ivMessageImage.setOnClickListener(null);
                binding.ivMessageImage.setOnLongClickListener(null);

                binding.tvMessage.setVisibility(android.view.View.VISIBLE);
                binding.tvMessage.setText(msg.getMessage());
                binding.tvMessage.setTypeface(null, android.graphics.Typeface.NORMAL);
                binding.tvMessage.setTextColor(binding.getRoot().getContext().getResources().getColor(com.findora.app.R.color.text_dark, null));
                binding.tvEdited.setVisibility(msg.isEdited() ? android.view.View.VISIBLE : android.view.View.GONE);

                binding.getRoot().setOnLongClickListener(v -> {
                    if (longClickListener != null) longClickListener.onMessageLongClick(msg);
                    return true;
                });
            }

            binding.tvTime.setText(formatTime(msg.getSentAt()));
            
            binding.ivAvatar.setOnClickListener(v -> {
                if (profileClickListener != null) {
                    profileClickListener.onProfileClick(msg.getSender());
                }
            });
            
            if (msg.getSenderProfileImage() != null && !msg.getSenderProfileImage().trim().isEmpty()) {
                binding.ivAvatar.setImageTintList(null);
                com.findora.app.utils.GlideImageHelper.loadAvatar(binding.getRoot().getContext(), msg.getSenderProfileImage(), binding.ivAvatar);
            } else {
                binding.ivAvatar.setImageTintList(android.content.res.ColorStateList.valueOf(
                        binding.getRoot().getContext().getResources().getColor(com.findora.app.R.color.primary_purple, null)));
                binding.ivAvatar.setImageResource(com.findora.app.R.drawable.ic_person);
            }
        }

        private void setupHoverAndMenu(ChatMessage msg, OnMessageActionListener actionListener) {
            binding.btnMoreOptions.setVisibility(isMenuOpen ? android.view.View.VISIBLE : android.view.View.GONE);

            android.view.View.OnHoverListener hoverListener = (v, event) -> {
                int action = event.getAction();
                if (action == android.view.MotionEvent.ACTION_HOVER_ENTER || action == android.view.MotionEvent.ACTION_HOVER_MOVE) {
                    if (!msg.isDeletedForEveryone()) {
                        binding.btnMoreOptions.setVisibility(android.view.View.VISIBLE);
                    }
                } else if (action == android.view.MotionEvent.ACTION_HOVER_EXIT) {
                    if (!isMenuOpen) {
                        binding.btnMoreOptions.setVisibility(android.view.View.GONE);
                    }
                }
                return false;
            };

            binding.getRoot().setOnHoverListener(hoverListener);
            binding.layoutBubble.setOnHoverListener(hoverListener);
            binding.btnMoreOptions.setOnHoverListener(hoverListener);

            binding.btnMoreOptions.setOnClickListener(v -> {
                if (currentPopup != null) {
                    currentPopup.dismiss();
                }
                androidx.appcompat.widget.PopupMenu popup = new androidx.appcompat.widget.PopupMenu(v.getContext(), v);
                popup.getMenuInflater().inflate(com.findora.app.R.menu.menu_chat_message_received, popup.getMenu());

                isMenuOpen = true;
                currentPopup = popup;
                binding.btnMoreOptions.setVisibility(android.view.View.VISIBLE);

                popup.setOnMenuItemClickListener(item -> {
                    if (item.getItemId() == com.findora.app.R.id.action_copy) {
                        if (actionListener != null) actionListener.onCopy(msg);
                        return true;
                    }
                    return false;
                });

                popup.setOnDismissListener(p -> {
                    isMenuOpen = false;
                    currentPopup = null;
                    binding.btnMoreOptions.setVisibility(android.view.View.GONE);
                });

                popup.show();
            });
        }

        private String formatTime(String timestamp) {
            return com.findora.app.utils.DateUtils.formatChatTime(timestamp);
        }
    }
}
