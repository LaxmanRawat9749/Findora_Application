package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ChangeUsernameResponse {
    @SerializedName("message")
    private String message;
    
    @SerializedName("username")
    private String username;

    public String getMessage() {
        return message;
    }

    public String getUsername() {
        return username;
    }
}
