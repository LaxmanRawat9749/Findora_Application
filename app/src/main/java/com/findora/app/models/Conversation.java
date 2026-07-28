package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class Conversation {
    private int id;
    @SerializedName("item_title")
    private String itemTitle;
    @SerializedName("item_type")
    private String itemType;
    @SerializedName("other_user_id")
    private int otherUserId;
    @SerializedName("other_user_name")
    private String otherUserName;
    @SerializedName("other_user_role")
    private String otherUserRole;
    @SerializedName("other_user_profile_image")
    private String otherUserProfileImage;
    @SerializedName("last_message")
    private String lastMessage;
    @SerializedName("last_message_time")
    private String lastMessageTime;
    @SerializedName("unread_count")
    private int unreadCount;
    @SerializedName("item_image")
    private String itemImage;
    @SerializedName("is_online")
    private boolean isOnline;
    @SerializedName("created_at")
    private String createdAt;

    public Conversation() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    
    public String getItemTitle() { return itemTitle; }
    public void setItemTitle(String itemTitle) { this.itemTitle = itemTitle; }
    
    public String getItemType() { return itemType; }
    public void setItemType(String itemType) { this.itemType = itemType; }
    
    public int getOtherUserId() { return otherUserId; }
    public void setOtherUserId(int otherUserId) { this.otherUserId = otherUserId; }
    
    public String getOtherUserName() { return otherUserName; }
    public void setOtherUserName(String otherUserName) { this.otherUserName = otherUserName; }
    
    public String getOtherUserRole() { return otherUserRole; }
    public void setOtherUserRole(String otherUserRole) { this.otherUserRole = otherUserRole; }
    
    public String getOtherUserProfileImage() { return otherUserProfileImage; }
    public void setOtherUserProfileImage(String otherUserProfileImage) { this.otherUserProfileImage = otherUserProfileImage; }
    
    public String getLastMessage() { return lastMessage; }
    public void setLastMessage(String lastMessage) { this.lastMessage = lastMessage; }
    
    public String getLastMessageTime() { return lastMessageTime; }
    public void setLastMessageTime(String lastMessageTime) { this.lastMessageTime = lastMessageTime; }
    
    public int getUnreadCount() { return unreadCount; }
    public void setUnreadCount(int unreadCount) { this.unreadCount = unreadCount; }
    
    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
    
    public String getItemImage() { return itemImage; }
    public void setItemImage(String itemImage) { this.itemImage = itemImage; }
    
    public boolean isOnline() { return isOnline; }
    public void setOnline(boolean isOnline) { this.isOnline = isOnline; }
}
