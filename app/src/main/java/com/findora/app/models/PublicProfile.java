package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class PublicProfile {
    private int id;
    private String username;
    @SerializedName("first_name")
    private String firstName;
    @SerializedName("last_name")
    private String lastName;
    private String role;
    @SerializedName("profile_image")
    private String profileImage;
    @SerializedName("created_at")
    private String createdAt;
    
    @SerializedName("lost_reports")
    private int lostReports;
    @SerializedName("found_reports")
    private int foundReports;
    @SerializedName("recovered_items")
    private int recoveredItems;

    public PublicProfile() {}

    public int getId() { return id; }
    public String getUsername() { return username; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getRole() { return role; }
    public String getProfileImage() { return profileImage; }
    public String getCreatedAt() { return createdAt; }
    public int getLostReports() { return lostReports; }
    public int getFoundReports() { return foundReports; }
    public int getRecoveredItems() { return recoveredItems; }
    
    public String getFullName() {
        String first = firstName != null ? firstName : "";
        String last = lastName != null ? lastName : "";
        String full = (first + " " + last).trim();
        return full.isEmpty() ? username : full;
    }
}
