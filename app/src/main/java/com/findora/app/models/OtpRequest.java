package com.findora.app.models;

public class OtpRequest {
    private String email;
    private String otp;
    private String purpose;

    public OtpRequest(String email, String otp, String purpose) {
        this.email = email;
        this.otp = otp;
        this.purpose = purpose;
    }

    public OtpRequest(String email, String purpose) {
        this.email = email;
        this.purpose = purpose;
    }

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getOtp() { return otp; }
    public void setOtp(String otp) { this.otp = otp; }

    public String getPurpose() { return purpose; }
    public void setPurpose(String purpose) { this.purpose = purpose; }
}
