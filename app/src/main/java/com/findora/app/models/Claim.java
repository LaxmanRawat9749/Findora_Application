package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class Claim {
    private int id;
    private int item;
    private int claimant;
    @SerializedName("claimant_name")
    private String claimantName;
    private String status;
    @SerializedName("proof_description")
    private String proofDescription;
    @SerializedName("claimed_at")
    private String claimedAt;

    public Claim() {}

    public Claim(int item, String proofDescription) {
        this.item = item;
        this.proofDescription = proofDescription;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public int getItem() { return item; }
    public void setItem(int item) { this.item = item; }

    public int getClaimant() { return claimant; }
    public void setClaimant(int claimant) { this.claimant = claimant; }

    public String getClaimantName() { return claimantName; }
    public void setClaimantName(String claimantName) { this.claimantName = claimantName; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getProofDescription() { return proofDescription; }
    public void setProofDescription(String proofDescription) { this.proofDescription = proofDescription; }

    public String getClaimedAt() { return claimedAt; }
    public void setClaimedAt(String claimedAt) { this.claimedAt = claimedAt; }
}
