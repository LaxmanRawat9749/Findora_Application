package com.findora.app.models;

import com.google.gson.annotations.SerializedName;

public class RegisterRequest {
    private String username;
    private String email;
    private String password;
    @SerializedName("confirm_password")
    private String confirmPassword;
    @SerializedName("first_name")
    private String firstName;
    @SerializedName("last_name")
    private String lastName;
    private String phone;
    private String role;

    public RegisterRequest(String username, String email, String password, String confirmPassword,
                           String firstName, String lastName, String phone) {
        this(username, email, password, confirmPassword, firstName, lastName, phone, "user");
    }

    public RegisterRequest(String username, String email, String password, String confirmPassword,
                           String firstName, String lastName, String phone, String role) {
        this.username = username;
        this.email = email;
        this.password = password;
        this.confirmPassword = confirmPassword;
        this.firstName = firstName;
        this.lastName = lastName;
        this.phone = phone;
        this.role = role;
    }

    public String getUsername() { return username; }
    public String getEmail() { return email; }
    public String getPassword() { return password; }
    public String getConfirmPassword() { return confirmPassword; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
    public String getPhone() { return phone; }
    public String getRole() { return role; }
}
