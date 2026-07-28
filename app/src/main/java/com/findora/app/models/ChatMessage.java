package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ChatMessage {
    private int id;
    private int sender;
    private int conversation;
    @SerializedName("sender_name")
    private String senderName;
    @SerializedName("sender_role")
    private String senderRole;
    @SerializedName("sender_profile_image")
    private String senderProfileImage;
    private String message;
    @SerializedName("is_edited")
    private boolean isEdited;
    @SerializedName("deleted_for_everyone")
    private boolean deletedForEveryone;
    @SerializedName("is_read")
    private boolean isRead;
    @SerializedName("sent_at")
    private String sentAt;

    @SerializedName("message_type")
    private String messageType;
    @SerializedName("image_url")
    private String imageUrl;
    private String caption;

    public ChatMessage() {}

    public ChatMessage(int conversation, String message) {
        this.conversation = conversation;
        this.message = message;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getSender() { return sender; }
    public void setSender(int sender) { this.sender = sender; }

    public int getConversation() { return conversation; }
    public void setConversation(int conversation) { this.conversation = conversation; }

    public String getSenderName() { return senderName; }
    public void setSenderName(String senderName) { this.senderName = senderName; }

    public String getSenderRole() { return senderRole; }
    public void setSenderRole(String senderRole) { this.senderRole = senderRole; }
    
    public String getSenderProfileImage() { return senderProfileImage; }
    public void setSenderProfileImage(String senderProfileImage) { this.senderProfileImage = senderProfileImage; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public boolean isRead() { return isRead; }
    public void setRead(boolean read) { isRead = read; }

    public boolean isEdited() { return isEdited; }
    public void setEdited(boolean edited) { isEdited = edited; }

    public boolean isDeletedForEveryone() { return deletedForEveryone; }
    public void setDeletedForEveryone(boolean deletedForEveryone) { this.deletedForEveryone = deletedForEveryone; }

    public String getSentAt() { return sentAt; }
    public void setSentAt(String sentAt) { this.sentAt = sentAt; }

    public String getMessageType() { return messageType; }
    public void setMessageType(String messageType) { this.messageType = messageType; }

    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

    public String getCaption() { return caption; }
    public void setCaption(String caption) { this.caption = caption; }
}
