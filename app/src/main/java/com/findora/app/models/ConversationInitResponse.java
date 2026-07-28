package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ConversationInitResponse {
    @SerializedName("conversation_id")
    private int conversationId;

    public ConversationInitResponse() {}

    public int getConversationId() { return conversationId; }
    public void setConversationId(int conversationId) { this.conversationId = conversationId; }
}
