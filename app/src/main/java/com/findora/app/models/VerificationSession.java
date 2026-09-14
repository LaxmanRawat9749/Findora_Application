package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.io.Serializable;
import java.util.List;

public class VerificationSession implements Serializable {
    private int id;
    @SerializedName("potential_match")
    private Integer potentialMatch;

    @SerializedName("lost_item")
    private int lostItem;
    @SerializedName("lost_item_title")
    private String lostItemTitle;
    @SerializedName("lost_item_category")
    private String lostItemCategory;

    @SerializedName("found_item")
    private int foundItem;
    @SerializedName("found_item_title")
    private String foundItemTitle;
    @SerializedName("found_item_category")
    private String foundItemCategory;
    @SerializedName("found_item_location")
    private String foundItemLocation;

    private int owner;
    @SerializedName("owner_username")
    private String ownerUsername;

    private int finder;
    @SerializedName("finder_username")
    private String finderUsername;

    private String status;
    @SerializedName("overall_confidence")
    private double overallConfidence;
    @SerializedName("verification_summary")
    private String verificationSummary;
    @SerializedName("is_contact_allowed")
    private boolean isContactAllowed;

    @SerializedName("questions_for_user")
    private List<VerificationQuestion> questionsForUser;

    @SerializedName("evidence_submissions")
    private List<VerificationEvidence> evidenceSubmissions;

    @SerializedName("created_at")
    private String createdAt;
    @SerializedName("verified_at")
    private String verifiedAt;

    public static class VerificationQuestion implements Serializable {
        private String key;
        private String prompt;
        @SerializedName("is_answered")
        private boolean isAnswered;
        private String category;
        private String role;

        public VerificationQuestion() {}

        public String getKey() { return key; }
        public void setKey(String key) { this.key = key; }

        public String getPrompt() { return prompt; }
        public void setPrompt(String prompt) { this.prompt = prompt; }

        public boolean isAnswered() { return isAnswered; }
        public void setAnswered(boolean answered) { isAnswered = answered; }

        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }

        public String getRole() { return role; }
        public void setRole(String role) { this.role = role; }
    }

    public VerificationSession() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public Integer getPotentialMatch() { return potentialMatch; }
    public void setPotentialMatch(Integer potentialMatch) { this.potentialMatch = potentialMatch; }

    public int getLostItem() { return lostItem; }
    public void setLostItem(int lostItem) { this.lostItem = lostItem; }

    public String getLostItemTitle() { return lostItemTitle; }
    public void setLostItemTitle(String lostItemTitle) { this.lostItemTitle = lostItemTitle; }

    public String getLostItemCategory() { return lostItemCategory; }
    public void setLostItemCategory(String lostItemCategory) { this.lostItemCategory = lostItemCategory; }

    public int getFoundItem() { return foundItem; }
    public void setFoundItem(int foundItem) { this.foundItem = foundItem; }

    public String getFoundItemTitle() { return foundItemTitle; }
    public void setFoundItemTitle(String foundItemTitle) { this.foundItemTitle = foundItemTitle; }

    public String getFoundItemCategory() { return foundItemCategory; }
    public void setFoundItemCategory(String foundItemCategory) { this.foundItemCategory = foundItemCategory; }

    public String getFoundItemLocation() { return foundItemLocation; }
    public void setFoundItemLocation(String foundItemLocation) { this.foundItemLocation = foundItemLocation; }

    public int getOwner() { return owner; }
    public void setOwner(int owner) { this.owner = owner; }

    public String getOwnerUsername() { return ownerUsername; }
    public void setOwnerUsername(String ownerUsername) { this.ownerUsername = ownerUsername; }

    public int getFinder() { return finder; }
    public void setFinder(int finder) { this.finder = finder; }

    public String getFinderUsername() { return finderUsername; }
    public void setFinderUsername(String finderUsername) { this.finderUsername = finderUsername; }

    public String getStatus() { return status != null ? status : "under_verification"; }
    public void setStatus(String status) { this.status = status; }

    public double getOverallConfidence() { return overallConfidence; }
    public void setOverallConfidence(double overallConfidence) { this.overallConfidence = overallConfidence; }
    public double getVerificationConfidence() { return overallConfidence; }

    public String getVerificationSummary() { return verificationSummary; }
    public void setVerificationSummary(String verificationSummary) { this.verificationSummary = verificationSummary; }

    public boolean isContactAllowed() { return isContactAllowed; }
    public void setContactAllowed(boolean contactAllowed) { isContactAllowed = contactAllowed; }

    public List<VerificationQuestion> getQuestionsForUser() { return questionsForUser; }
    public void setQuestionsForUser(List<VerificationQuestion> questionsForUser) { this.questionsForUser = questionsForUser; }

    public List<VerificationEvidence> getEvidenceSubmissions() { return evidenceSubmissions; }
    public void setEvidenceSubmissions(List<VerificationEvidence> evidenceSubmissions) { this.evidenceSubmissions = evidenceSubmissions; }
    public List<VerificationEvidence> getEvidences() { return evidenceSubmissions; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }

    public String getVerifiedAt() { return verifiedAt; }
    public void setVerifiedAt(String verifiedAt) { this.verifiedAt = verifiedAt; }
}
