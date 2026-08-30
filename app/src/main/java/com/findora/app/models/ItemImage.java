package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

import java.io.Serializable;

public class ItemImage implements Serializable {
    private int id;
    
    @SerializedName("image_url")
    private String imageUrl;
    
    @SerializedName("uploaded_at")
    private String uploadedAt;

    public ItemImage() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

    public String getUploadedAt() { return uploadedAt; }
    public void setUploadedAt(String uploadedAt) { this.uploadedAt = uploadedAt; }
}
