package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ConversationInitRequest {
    @SerializedName("item_id")
    private int itemId;

    public ConversationInitRequest(int itemId) {
        this.itemId = itemId;
    }

    public int getItemId() { return itemId; }
    public void setItemId(int itemId) { this.itemId = itemId; }
}
