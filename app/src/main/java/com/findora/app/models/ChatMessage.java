package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ChatMessage {
    private int id;
    private int sender;
    private int receiver;
    private int item;
    @SerializedName("sender_name")
    private String senderName;
    @SerializedName("sender_role")
    private String senderRole;
    private String message;
    @SerializedName("is_read")
    private boolean isRead;
    @SerializedName("sent_at")
    private String sentAt;

    public ChatMessage() {}

    public ChatMessage(int receiver, int item, String message) {
        this.receiver = receiver;
        this.item = item;
        this.message = message;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getSender() { return sender; }
    public void setSender(int sender) { this.sender = sender; }

    public int getReceiver() { return receiver; }
    public void setReceiver(int receiver) { this.receiver = receiver; }

    public int getItem() { return item; }
    public void setItem(int item) { this.item = item; }

    public String getSenderName() { return senderName; }
    public void setSenderName(String senderName) { this.senderName = senderName; }

    public String getSenderRole() { return senderRole; }
    public void setSenderRole(String senderRole) { this.senderRole = senderRole; }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public boolean isRead() { return isRead; }
    public void setRead(boolean read) { isRead = read; }

    public String getSentAt() { return sentAt; }
    public void setSentAt(String sentAt) { this.sentAt = sentAt; }
}
