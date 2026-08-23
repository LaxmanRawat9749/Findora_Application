package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.util.ArrayList;
import java.util.List;

public class PublicProfile {
    private int id;
    private String username;
    @SerializedName("first_name")
    private String firstName;
    @SerializedName("last_name")
    private String lastName;
    private String role;
    @SerializedName("profile_image")
    private String profileImage;
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("lost_reports")
    private int lostReports;
    @SerializedName("found_reports")
    private int foundReports;
    @SerializedName("recovered_items")
    private int recoveredItems;
    @SerializedName("items_recovered")
    private int itemsRecovered;

    @SerializedName("total_points")
    private int totalPoints;
    @SerializedName("successful_returns")
    private int successfulReturns;
    @SerializedName("average_rating")
    private double averageRating;
    @SerializedName("rating_count")
    private int ratingCount;
    @SerializedName("reputation_display")
    private String reputationDisplay;
    @SerializedName("primary_badge")
    private String primaryBadge;
    private List<UserBadge> badges;

    public PublicProfile() {
        this.badges = new ArrayList<>();
    }

    public int getId() { return id; }
    public String getUsername() { return username; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getRole() { return role; }
    public String getProfileImage() { return profileImage; }
    public String getCreatedAt() { return createdAt; }
    public int getLostReports() { return lostReports; }
    public int getFoundReports() { return foundReports; }
    public int getRecoveredItems() { return recoveredItems > 0 ? recoveredItems : itemsRecovered; }
    public int getItemsRecovered() { return itemsRecovered > 0 ? itemsRecovered : (recoveredItems > 0 ? recoveredItems : successfulReturns); }

    public int getTotalPoints() { return totalPoints; }
    public int getSuccessfulReturns() { return successfulReturns; }
    public double getAverageRating() { return averageRating; }
    public int getRatingCount() { return ratingCount; }

    public String getReputationDisplay() {
        if (reputationDisplay != null && !reputationDisplay.isEmpty()) {
            return reputationDisplay;
        }
        return ratingCount > 0 ? String.format("%.1f", averageRating) : "New Finder";
    }

    public String getPrimaryBadge() { return primaryBadge; }
    public List<UserBadge> getBadges() { return badges != null ? badges : new ArrayList<>(); }
    
    public String getFullName() {
        String first = firstName != null ? firstName : "";
        String last = lastName != null ? lastName : "";
        String full = (first + " " + last).trim();
        return full.isEmpty() ? username : full;
    }
}
