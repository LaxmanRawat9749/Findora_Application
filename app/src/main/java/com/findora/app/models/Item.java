package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

import java.io.Serializable;
import java.util.List;

public class Item implements Serializable {
    private int id;
    private int user;
    @SerializedName("user_name")
    private String userName;
    @SerializedName("user_role")
    private String userRole;
    @SerializedName("user_profile_image")
    private String userProfileImage;
    private String type; // "lost" or "found"
    private String title;
    private String description;
    private String category;
    private String status; // "pending", "approved", "resolved", "rejected"
    private String image;
    @SerializedName("image_url")
    private String imageUrl;
    private String location;
    private Double latitude;
    private Double longitude;
    private double reward;
    
    @SerializedName("is_featured")
    private boolean isFeatured;
    
    @SerializedName("featured_until")
    private String featuredUntil;

    @SerializedName("reported_at")
    private String reportedAt;
    @SerializedName("updated_at")
    private String updatedAt;
    
    @SerializedName("owner_returned_confirm")
    private boolean ownerReturnedConfirm;
    @SerializedName("finder_returned_confirm")
    private boolean finderReturnedConfirm;
    @SerializedName("resolved_at")
    private String resolvedAt;
    @SerializedName("parent_item")
    private Integer parentItem;
    @SerializedName("parent_item_title")
    private String parentItemTitle;

    private List<ItemImage> images;

    public Item() {}

    public Integer getParentItem() { return parentItem; }
    public void setParentItem(Integer parentItem) { this.parentItem = parentItem; }

    public String getParentItemTitle() { return parentItemTitle; }
    public void setParentItemTitle(String parentItemTitle) { this.parentItemTitle = parentItemTitle; }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getUser() { return user; }
    public void setUser(int user) { this.user = user; }

    public String getUserName() { return userName; }
    public void setUserName(String userName) { this.userName = userName; }

    public String getUserRole() { return userRole; }
    public void setUserRole(String userRole) { this.userRole = userRole; }
    
    public String getUserProfileImage() { return userProfileImage; }
    public void setUserProfileImage(String userProfileImage) { this.userProfileImage = userProfileImage; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getImage() { return image; }
    public void setImage(String image) { this.image = image; }

    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

    public String getLocation() { return location; }
    public void setLocation(String location) { this.location = location; }

    public Double getLatitude() { return latitude; }
    public void setLatitude(Double latitude) { this.latitude = latitude; }

    public Double getLongitude() { return longitude; }
    public void setLongitude(Double longitude) { this.longitude = longitude; }

    public double getReward() { return reward; }
    public void setReward(double reward) { this.reward = reward; }

    public boolean isFeatured() { return isFeatured; }
    public void setFeatured(boolean featured) { isFeatured = featured; }

    public String getFeaturedUntil() { return featuredUntil; }
    public void setFeaturedUntil(String featuredUntil) { this.featuredUntil = featuredUntil; }

    public String getReportedAt() { return reportedAt; }
    public void setReportedAt(String reportedAt) { this.reportedAt = reportedAt; }

    public String getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(String updatedAt) { this.updatedAt = updatedAt; }

    public boolean isOwnerReturnedConfirm() { return ownerReturnedConfirm; }
    public void setOwnerReturnedConfirm(boolean ownerReturnedConfirm) { this.ownerReturnedConfirm = ownerReturnedConfirm; }

    public boolean isFinderReturnedConfirm() { return finderReturnedConfirm; }
    public void setFinderReturnedConfirm(boolean finderReturnedConfirm) { this.finderReturnedConfirm = finderReturnedConfirm; }

    public String getResolvedAt() { return  resolvedAt; }
    public void setResolvedAt(String resolvedAt) { this.resolvedAt = resolvedAt; }

    public List<ItemImage> getImages() { return images; }
    public void setImages(List<ItemImage> images) { this.images = images; }
}
