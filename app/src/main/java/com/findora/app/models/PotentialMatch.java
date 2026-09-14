package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.io.Serializable;
import java.util.List;

public class PotentialMatch implements Serializable {
    private int id;
    @SerializedName("lost_item")
    private int lostItem;
    @SerializedName("lost_item_title")
    private String lostItemTitle;
    @SerializedName("lost_item_category")
    private String lostItemCategory;
    @SerializedName("lost_item_image")
    private String lostItemImage;

    @SerializedName("found_item")
    private int foundItem;
    @SerializedName("found_item_title")
    private String foundItemTitle;
    @SerializedName("found_item_category")
    private String foundItemCategory;
    @SerializedName("found_item_image")
    private String foundItemImage;
    @SerializedName("found_item_location")
    private String foundItemLocation;

    @SerializedName("owner_username")
    private String ownerUsername;
    @SerializedName("finder_username")
    private String finderUsername;

    @SerializedName("similarity_score")
    private double similarityScore;
    @SerializedName("confidence_level")
    private String confidenceLevel;
    @SerializedName("match_reasons")
    private List<String> matchReasons;
    @SerializedName("evidence_strength")
    private String evidenceStrength;
    private String status;

    @SerializedName("verification_request_id")
    private Integer verificationRequestId;

    @SerializedName("created_at")
    private String createdAt;

    public PotentialMatch() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getLostItem() { return lostItem; }
    public void setLostItem(int lostItem) { this.lostItem = lostItem; }

    public String getLostItemTitle() { return lostItemTitle; }
    public void setLostItemTitle(String lostItemTitle) { this.lostItemTitle = lostItemTitle; }

    public String getLostItemCategory() { return lostItemCategory; }
    public void setLostItemCategory(String lostItemCategory) { this.lostItemCategory = lostItemCategory; }

    public String getLostItemImage() { return lostItemImage; }
    public void setLostItemImage(String lostItemImage) { this.lostItemImage = lostItemImage; }

    public int getFoundItem() { return foundItem; }
    public void setFoundItem(int foundItem) { this.foundItem = foundItem; }

    public String getFoundItemTitle() { return foundItemTitle; }
    public void setFoundItemTitle(String foundItemTitle) { this.foundItemTitle = foundItemTitle; }

    public String getFoundItemCategory() { return foundItemCategory; }
    public void setFoundItemCategory(String foundItemCategory) { this.foundItemCategory = foundItemCategory; }

    public String getFoundItemImage() { return foundItemImage; }
    public void setFoundItemImage(String foundItemImage) { this.foundItemImage = foundItemImage; }

    public String getFoundItemLocation() { return foundItemLocation; }
    public void setFoundItemLocation(String foundItemLocation) { this.foundItemLocation = foundItemLocation; }

    public String getOwnerUsername() { return ownerUsername; }
    public void setOwnerUsername(String ownerUsername) { this.ownerUsername = ownerUsername; }

    public String getFinderUsername() { return finderUsername; }
    public void setFinderUsername(String finderUsername) { this.finderUsername = finderUsername; }

    public double getSimilarityScore() { return similarityScore; }
    public void setSimilarityScore(double similarityScore) { this.similarityScore = similarityScore; }
    public double getMatchScore() { return similarityScore; }

    public String getConfidenceLevel() { return confidenceLevel != null ? confidenceLevel : "medium"; }
    public void setConfidenceLevel(String confidenceLevel) { this.confidenceLevel = confidenceLevel; }

    public List<String> getMatchReasons() { return matchReasons; }
    public void setMatchReasons(List<String> matchReasons) { this.matchReasons = matchReasons; }

    public String getEvidenceStrength() { return evidenceStrength; }
    public void setEvidenceStrength(String evidenceStrength) { this.evidenceStrength = evidenceStrength; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public Integer getVerificationRequestId() { return verificationRequestId; }
    public void setVerificationRequestId(Integer verificationRequestId) { this.verificationRequestId = verificationRequestId; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}
