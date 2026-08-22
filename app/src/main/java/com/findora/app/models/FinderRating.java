package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class FinderRating {
    private int id;
    private int owner;
    @SerializedName("owner_name")
    private String ownerName;
    private int finder;
    @SerializedName("finder_name")
    private String finderName;
    private int item;
    @SerializedName("item_title")
    private String itemTitle;
    private int rating;
    private String review;
    @SerializedName("created_at")
    private String createdAt;

    public FinderRating() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getOwner() { return owner; }
    public void setOwner(int owner) { this.owner = owner; }

    public String getOwnerName() { return ownerName; }
    public void setOwnerName(String ownerName) { this.ownerName = ownerName; }

    public int getFinder() { return finder; }
    public void setFinder(int finder) { this.finder = finder; }

    public String getFinderName() { return finderName; }
    public void setFinderName(String finderName) { this.finderName = finderName; }

    public int getItem() { return item; }
    public void setItem(int item) { this.item = item; }

    public String getItemTitle() { return itemTitle; }
    public void setItemTitle(String itemTitle) { this.itemTitle = itemTitle; }

    public int getRating() { return rating; }
    public void setRating(int rating) { this.rating = rating; }

    public String getReview() { return review; }
    public void setReview(String review) { this.review = review; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}
