package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class MessageResponse {
    public Boolean success;
    public String message;
    public String error;
    public String email;
    public Boolean verified;
    @SerializedName("retry_after")
    public Integer retryAfter;
    public String action;

    public MessageResponse() {}
}
