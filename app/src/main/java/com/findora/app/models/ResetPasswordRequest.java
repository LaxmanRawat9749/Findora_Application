package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class ResetPasswordRequest {
    private String email;
    private String otp;
    @SerializedName("new_password")
    private String newPassword;
    @SerializedName("confirm_password")
    private String confirmPassword;

    public ResetPasswordRequest(String email, String otp, String newPassword) {
        this.email = email;
        this.otp = otp;
        this.newPassword = newPassword;
        this.confirmPassword = newPassword;
    }

    public ResetPasswordRequest(String email, String otp, String newPassword, String confirmPassword) {
        this.email = email;
        this.otp = otp;
        this.newPassword = newPassword;
        this.confirmPassword = confirmPassword;
    }

    public String getEmail() { return email; }
    public String getOtp() { return otp; }
    public String getNewPassword() { return newPassword; }
    public String getConfirmPassword() { return confirmPassword; }
}
