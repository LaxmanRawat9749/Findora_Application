package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class RateRequest {
    @SerializedName("item_id")
    private int itemId;
    private int rating;
    private String review;

    public RateRequest(int itemId, int rating, String review) {
        this.itemId = itemId;
        this.rating = rating;
        this.review = review != null ? review : "";
    }

    public int getItemId() { return itemId; }
    public void setItemId(int itemId) { this.itemId = itemId; }

    public int getRating() { return rating; }
    public void setRating(int rating) { this.rating = rating; }

    public String getReview() { return review; }
    public void setReview(String review) { this.review = review; }
}
