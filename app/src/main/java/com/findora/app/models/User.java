package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class User {
    private int id;
    private String username;
    private String email;
    @SerializedName("first_name")
    private String firstName;
    @SerializedName("last_name")
    private String lastName;
    private String phone;
    private String role;
    @SerializedName("is_verified")
    private boolean isVerified;
    @SerializedName("profile_image")
    private String profileImage;
    @SerializedName("emergency_contact_name")
    private String emergencyContactName;
    @SerializedName("emergency_contact_phone")
    private String emergencyContactPhone;
    @SerializedName("total_points")
    private int totalPoints;
    @SerializedName("successful_returns")
    private int successfulReturns;
    @SerializedName("reputation_display")
    private String reputationDisplay;
    @SerializedName("primary_badge")
    private String primaryBadge;
    @SerializedName("created_at")
    private String createdAt;

    public User() {}

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getFirstName() { return firstName; }
    public void setFirstName(String firstName) { this.firstName = firstName; }

    public String getLastName() { return lastName; }
    public void setLastName(String lastName) { this.lastName = lastName; }

    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }

    public boolean isVerified() { return isVerified; }
    public void setVerified(boolean verified) { isVerified = verified; }

    public String getProfileImage() { return profileImage; }
    public void setProfileImage(String profileImage) { this.profileImage = profileImage; }

    public String getEmergencyContactName() { return emergencyContactName; }
    public void setEmergencyContactName(String emergencyContactName) { this.emergencyContactName = emergencyContactName; }

    public String getEmergencyContactPhone() { return emergencyContactPhone; }
    public void setEmergencyContactPhone(String emergencyContactPhone) { this.emergencyContactPhone = emergencyContactPhone; }

    public int getTotalPoints() { return totalPoints; }
    public void setTotalPoints(int totalPoints) { this.totalPoints = totalPoints; }

    public int getSuccessfulReturns() { return successfulReturns; }
    public void setSuccessfulReturns(int successfulReturns) { this.successfulReturns = successfulReturns; }

    public String getReputationDisplay() { return reputationDisplay != null ? reputationDisplay : "New Finder"; }
    public void setReputationDisplay(String reputationDisplay) { this.reputationDisplay = reputationDisplay; }

    public String getPrimaryBadge() { return primaryBadge; }
    public void setPrimaryBadge(String primaryBadge) { this.primaryBadge = primaryBadge; }

    public String getCreatedAt() { return createdAt; }
    public void setCreatedAt(String createdAt) { this.createdAt = createdAt; }

    public String getFullName() {
        String first = firstName != null ? firstName : "";
        String last = lastName != null ? lastName : "";
        String full = (first + " " + last).trim();
        return full.isEmpty() ? username : full;
    }
}
