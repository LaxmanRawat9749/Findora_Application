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
    @SerializedName("lost_reports_count")
    private Integer lostReportsCount;

    @SerializedName("found_reports")
    private int foundReports;
    @SerializedName("found_reports_count")
    private Integer foundReportsCount;

    @SerializedName("recovered_items")
    private int recoveredItems;
    @SerializedName("items_recovered")
    private int itemsRecovered;
    @SerializedName("recovered_items_count")
    private Integer recoveredItemsCount;

    @SerializedName("total_points")
    private int totalPoints;
    @SerializedName("successful_returns")
    private int successfulReturns;
    @SerializedName("successful_returns_count")
    private Integer successfulReturnsCount;
    @SerializedName("average_rating")
    private double averageRating;
    @SerializedName("rating_count")
    private int ratingCount;
    @SerializedName("reputation_display")
    private String reputationDisplay;
    @SerializedName("is_trusted_finder")
    private boolean isTrustedFinder;
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

    public int getLostReports() {
        return lostReportsCount != null ? lostReportsCount : lostReports;
    }
    public int getFoundReports() {
        return foundReportsCount != null ? foundReportsCount : foundReports;
    }
    public int getRecoveredItems() {
        return recoveredItemsCount != null ? recoveredItemsCount : (itemsRecovered > 0 ? itemsRecovered : recoveredItems);
    }
    public int getItemsRecovered() {
        return recoveredItemsCount != null ? recoveredItemsCount : (itemsRecovered > 0 ? itemsRecovered : recoveredItems);
    }

    public int getTotalPoints() { return totalPoints; }
    public int getSuccessfulReturns() {
        return successfulReturnsCount != null ? successfulReturnsCount : successfulReturns;
    }
    public double getAverageRating() { return averageRating; }
    public int getRatingCount() { return ratingCount; }

    public String getReputationDisplay() {
        if (reputationDisplay != null && !reputationDisplay.isEmpty()) {
            return reputationDisplay;
        }
        return ratingCount > 0 ? String.format("%.1f", averageRating) : "New Finder";
    }

    public boolean isTrustedFinder() { return isTrustedFinder; }
    public void setTrustedFinder(boolean trustedFinder) { isTrustedFinder = trustedFinder; }

    public String getPrimaryBadge() { return primaryBadge; }
    public List<UserBadge> getBadges() { return badges != null ? badges : new ArrayList<>(); }
    
    public String getFullName() {
        String first = firstName != null ? firstName : "";
        String last = lastName != null ? lastName : "";
        String full = (first + " " + last).trim();
        return full.isEmpty() ? username : full;
    }
}
