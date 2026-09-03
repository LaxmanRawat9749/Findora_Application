package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class UserBadge {
    private int id;
    @SerializedName("badge_key")
    private String badgeKey;
    private String name;
    private String description;
    @SerializedName("required_returns")
    private int requiredReturns;
    private String icon;
    @SerializedName("is_earned")
    private boolean isEarned;
    @SerializedName("current_progress")
    private int currentProgress;
    @SerializedName("progress_text")
    private String progressText;
    @SerializedName("progress_percent")
    private int progressPercent;
    @SerializedName("earned_at")
    private String earnedAt;

    public UserBadge() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getBadgeKey() { return badgeKey; }
    public void setBadgeKey(String badgeKey) { this.badgeKey = badgeKey; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public int getRequiredReturns() { return requiredReturns; }
    public void setRequiredReturns(int requiredReturns) { this.requiredReturns = requiredReturns; }

    public String getIcon() { return icon != null ? icon : ""; }
    public void setIcon(String icon) { this.icon = icon; }

    public int getIconDrawableRes() {
        if (badgeKey != null) {
            switch (badgeKey.toLowerCase()) {
                case "first_return":
                case "seedling":
                    return com.findora.app.R.drawable.ic_eco;
                case "reliable_finder":
                case "bronze":
                    return com.findora.app.R.drawable.ic_handshake;
                case "trusted_finder":
                case "silver":
                    return com.findora.app.R.drawable.ic_verified;
                case "hero_finder":
                case "gold":
                    return com.findora.app.R.drawable.ic_trophy;
                case "legendary_finder":
                case "master":
                case "crown":
                    return com.findora.app.R.drawable.ic_crown;
            }
        }
        return com.findora.app.R.drawable.ic_military_tech;
    }

    public boolean isEarned() { return isEarned; }
    public void setEarned(boolean earned) { isEarned = earned; }

    public int getCurrentProgress() { return currentProgress; }
    public void setCurrentProgress(int currentProgress) { this.currentProgress = currentProgress; }

    public String getProgressText() { return progressText; }
    public void setProgressText(String progressText) { this.progressText = progressText; }

    public int getProgressPercent() { return progressPercent; }
    public void setProgressPercent(int progressPercent) { this.progressPercent = progressPercent; }

    public String getEarnedAt() { return earnedAt; }
    public void setEarnedAt(String earnedAt) { this.earnedAt = earnedAt; }
}
