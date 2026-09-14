package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class SubmitEvidenceRequest {
    @SerializedName("evidence_key")
    private String evidenceKey;

    @SerializedName("submitted_value")
    private String submittedValue;

    @SerializedName("evidence_type")
    private String evidenceType;

    public SubmitEvidenceRequest(String evidenceKey, String submittedValue) {
        this.evidenceKey = evidenceKey;
        this.submittedValue = submittedValue;
        this.evidenceType = "blind_qa";
    }

    public SubmitEvidenceRequest(String evidenceKey, String submittedValue, String evidenceType) {
        this.evidenceKey = evidenceKey;
        this.submittedValue = submittedValue;
        this.evidenceType = evidenceType;
    }

    public String getEvidenceKey() { return evidenceKey; }
    public void setEvidenceKey(String evidenceKey) { this.evidenceKey = evidenceKey; }

    public String getSubmittedValue() { return submittedValue; }
    public void setSubmittedValue(String submittedValue) { this.submittedValue = submittedValue; }

    public String getEvidenceType() { return evidenceType; }
    public void setEvidenceType(String evidenceType) { this.evidenceType = evidenceType; }
}
