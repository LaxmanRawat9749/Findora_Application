package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class Notification {
    private int id;
    private int user;
    private String type;
    private String message;
    @SerializedName("is_read")
    private boolean isRead;
    @SerializedName("related_item")
    private Integer relatedItem;
    @SerializedName("created_at")
    private String createdAt;

    public Notification() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getUser() { return user; }
    public void setUser(int user) { this.user = user; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public boolean isRead() { return isRead; }
    public void setRead(boolean read) { isRead = read; }

    public Integer getRelatedItem() { return relatedItem; }
    public void setRelatedItem(Integer relatedItem) { this.relatedItem = relatedItem; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}
