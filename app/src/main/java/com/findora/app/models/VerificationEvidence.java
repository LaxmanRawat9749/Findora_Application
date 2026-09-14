package com.findora.app.models;

import com.google.gson.annotations.SerializedName;
import java.io.Serializable;

public class VerificationEvidence implements Serializable {
    private int id;
    @SerializedName("verification_request")
    private int verificationRequest;
    @SerializedName("submitted_by")
    private int submittedBy;
    @SerializedName("submitted_by_username")
    private String submittedByUsername;
    @SerializedName("submitted_by_role")
    private String submittedByRole;
    @SerializedName("evidence_type")
    private String evidenceType;
    @SerializedName("evidence_key")
    private String evidenceKey;
    @SerializedName("submitted_value")
    private String submittedValue;
    @SerializedName("submitted_image")
    private String submittedImage;
    @SerializedName("image_url")
    private String imageUrl;
    @SerializedName("is_blind")
    private boolean isBlind;
    @SerializedName("match_result")
    private String matchResult;
    @SerializedName("discriminative_weight")
    private double discriminativeWeight;
    @SerializedName("created_at")
    private String createdAt;

    public VerificationEvidence() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getVerificationRequest() { return verificationRequest; }
    public void setVerificationRequest(int verificationRequest) { this.verificationRequest = verificationRequest; }

    public int getSubmittedBy() { return submittedBy; }
    public void setSubmittedBy(int submittedBy) { this.submittedBy = submittedBy; }

    public String getSubmittedByUsername() { return submittedByUsername; }
    public void setSubmittedByUsername(String submittedByUsername) { this.submittedByUsername = submittedByUsername; }

    public String getSubmittedByRole() { return submittedByRole; }
    public void setSubmittedByRole(String submittedByRole) { this.submittedByRole = submittedByRole; }

    public String getEvidenceType() { return evidenceType; }
    public void setEvidenceType(String evidenceType) { this.evidenceType = evidenceType; }

    public String getEvidenceKey() { return evidenceKey; }
    public void setEvidenceKey(String evidenceKey) { this.evidenceKey = evidenceKey; }

    public String getSubmittedValue() { return submittedValue; }
    public void setSubmittedValue(String submittedValue) { this.submittedValue = submittedValue; }

    public String getSubmittedImage() { return submittedImage; }
    public void setSubmittedImage(String submittedImage) { this.submittedImage = submittedImage; }

    public String getImageUrl() { return imageUrl; }
    public void setImageUrl(String imageUrl) { this.imageUrl = imageUrl; }

    public boolean isBlind() { return isBlind; }
    public void setBlind(boolean blind) { isBlind = blind; }

    public String getMatchResult() { return matchResult; }
    public void setMatchResult(String matchResult) { this.matchResult = matchResult; }

    public double getDiscriminativeWeight() { return discriminativeWeight; }
    public void setDiscriminativeWeight(double discriminativeWeight) { this.discriminativeWeight = discriminativeWeight; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }
}
