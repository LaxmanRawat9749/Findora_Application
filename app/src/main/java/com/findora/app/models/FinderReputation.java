package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.util.ArrayList;
import java.util.List;

public class FinderReputation {
    @SerializedName("total_points")
    private int totalPoints;
    @SerializedName("successful_returns")
    private int successfulReturns;
    @SerializedName("rating_count")
    private int ratingCount;
    @SerializedName("rating_sum")
    private int ratingSum;
    @SerializedName("average_rating")
    private double averageRating;
    @SerializedName("reputation_display")
    private String reputationDisplay;
    @SerializedName("primary_badge")
    private String primaryBadge;
    private List<UserBadge> badges;
    @SerializedName("badge_progress")
    private List<UserBadge> badgeProgress;
    @SerializedName("updated_at")
    private String updatedAt;

    public FinderReputation() {
        this.badges = new ArrayList<>();
        this.badgeProgress = new ArrayList<>();
    }

    public int getTotalPoints() { return totalPoints; }
    public void setTotalPoints(int totalPoints) { this.totalPoints = totalPoints; }

    public int getSuccessfulReturns() { return successfulReturns; }
    public void setSuccessfulReturns(int successfulReturns) { this.successfulReturns = successfulReturns; }

    public int getRatingCount() { return ratingCount; }
    public void setRatingCount(int ratingCount) { this.ratingCount = ratingCount; }

    public int getRatingSum() { return ratingSum; }
    public void setRatingSum(int ratingSum) { this.ratingSum = ratingSum; }

    public double getAverageRating() { return averageRating; }
    public void setAverageRating(double averageRating) { this.averageRating = averageRating; }

    public String getReputationDisplay() {
        if (reputationDisplay != null && !reputationDisplay.isEmpty()) {
            return reputationDisplay;
        }
        return ratingCount > 0 ? String.format("%.1f", averageRating) : "New Finder";
    }
    public void setReputationDisplay(String reputationDisplay) { this.reputationDisplay = reputationDisplay; }

    public String getPrimaryBadge() { return primaryBadge; }
    public void setPrimaryBadge(String primaryBadge) { this.primaryBadge = primaryBadge; }

    public List<UserBadge> getBadges() { return badges != null ? badges : new ArrayList<>(); }
    public void setBadges(List<UserBadge> badges) { this.badges = badges; }

    public List<UserBadge> getBadgeProgress() { return badgeProgress != null ? badgeProgress : new ArrayList<>(); }
    public void setBadgeProgress(List<UserBadge> badgeProgress) { this.badgeProgress = badgeProgress; }

    public String getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(String updatedAt) { this.updatedAt = updatedAt; }
}
