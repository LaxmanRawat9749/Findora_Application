package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.io.Serializable;
import java.util.List;

public class MatchedItem implements Serializable {
    private int id;
    
    @SerializedName("lost_item")
    private Item lostItem;
    
    @SerializedName("found_item")
    private Item foundItem;
    
    @SerializedName("match_score")
    private int matchScore;
    
    @SerializedName("matched_reasons")
    private List<String> matchedReasons;
    
    private String status;
    
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("updated_at")
    private String updatedAt;

    public MatchedItem() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public Item getLostItem() { return lostItem; }
    public void setLostItem(Item lostItem) { this.lostItem = lostItem; }

    public Item getFoundItem() { return foundItem; }
    public void setFoundItem(Item foundItem) { this.foundItem = foundItem; }

    public int getMatchScore() { return matchScore; }
    public void setMatchScore(int matchScore) { this.matchScore = matchScore; }

    public List<String> getMatchedReasons() { return matchedReasons; }
    public void setMatchedReasons(List<String> matchedReasons) { this.matchedReasons = matchedReasons; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }

    public String getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(String updatedAt) { this.updatedAt = updatedAt; }
}
