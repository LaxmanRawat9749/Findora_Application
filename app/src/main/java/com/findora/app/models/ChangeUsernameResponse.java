package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ChangeUsernameResponse {
    @SerializedName("message")
    private String message;
    
    @SerializedName("username")
    private String username;

    @SerializedName("user")
    private User user;

    @SerializedName("access")
    private String access;

    @SerializedName("refresh")
    private String refresh;

    public String getMessage() {
        return message;
    }

    public String getUsername() {
        if (username != null && !username.isEmpty()) {
            return username;
        }
        if (user != null && user.getUsername() != null && !user.getUsername().isEmpty()) {
            return user.getUsername();
        }
        return null;
    }

    public User getUser() {
        return user;
    }

    public String getAccess() {
        return access;
    }

    public String getRefresh() {
        return refresh;
    }
}
