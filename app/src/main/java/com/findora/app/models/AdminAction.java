package com.findora.app.models;

public class AdminAction {
    private String action; // "approve" or "reject"

    public AdminAction(String action) {
        this.action = action;
    }

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }
}
