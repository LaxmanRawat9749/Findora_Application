package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ChangeUsernameRequest {
    @SerializedName("new_username")
    private String newUsername;
    
    @SerializedName("confirm_username")
    private String confirmUsername;

    public ChangeUsernameRequest(String newUsername, String confirmUsername) {
        this.newUsername = newUsername;
        this.confirmUsername = confirmUsername;
    }

    public String getNewUsername() {
        return newUsername;
    }

    public String getConfirmUsername() {
        return confirmUsername;
    }
}
