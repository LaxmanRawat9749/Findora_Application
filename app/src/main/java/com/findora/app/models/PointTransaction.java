package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class PointTransaction {
    private int id;
    private int points;
    @SerializedName("transaction_type")
    private String transactionType;
    private String description;
    @SerializedName("related_item")
    private Integer relatedItem;
    @SerializedName("related_item_title")
    private String relatedItemTitle;
    @SerializedName("created_at")
    private String createdAt;

    public PointTransaction() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getPoints() { return points; }
    public void setPoints(int points) { this.points = points; }

    public String getTransactionType() { return transactionType; }
    public void setTransactionType(String transactionType) { this.transactionType = transactionType; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public Integer getRelatedItem() { return relatedItem; }
    public void setRelatedItem(Integer relatedItem) { this.relatedItem = relatedItem; }

    public String getRelatedItemTitle() { return relatedItemTitle; }
    public void setRelatedItemTitle(String relatedItemTitle) { this.relatedItemTitle = relatedItemTitle; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }

    public String getFormattedPoints() {
        return (points > 0 ? "+" : "") + points;
    }
}
