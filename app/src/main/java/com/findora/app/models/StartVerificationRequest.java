package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class StartVerificationRequest {
    @SerializedName("potential_match_id")
    private Integer potentialMatchId;

    @SerializedName("lost_item_id")
    private Integer lostItemId;

    @SerializedName("found_item_id")
    private Integer foundItemId;

    public StartVerificationRequest() {}

    public StartVerificationRequest(int potentialMatchId) {
        this.potentialMatchId = potentialMatchId;
    }

    public StartVerificationRequest(int lostItemId, int foundItemId) {
        this.lostItemId = lostItemId;
        this.foundItemId = foundItemId;
    }

    public StartVerificationRequest(int lostItemId, int foundItemId, int potentialMatchId) {
        this.lostItemId = lostItemId;
        this.foundItemId = foundItemId;
        this.potentialMatchId = potentialMatchId;
    }

    public Integer getPotentialMatchId() { return potentialMatchId; }
    public void setPotentialMatchId(Integer potentialMatchId) { this.potentialMatchId = potentialMatchId; }

    public Integer getLostItemId() { return lostItemId; }
    public void setLostItemId(Integer lostItemId) { this.lostItemId = lostItemId; }

    public Integer getFoundItemId() { return foundItemId; }
    public void setFoundItemId(Integer foundItemId) { this.foundItemId = foundItemId; }
}
