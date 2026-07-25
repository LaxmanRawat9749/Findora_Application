package com.findora.app.utils;

public class Constants {
    // API Base URL
    // For USB physical device testing on same Wi-Fi: "http://192.168.1.96:8000/api/"
    // For ADB port forwarding over USB (run: adb reverse tcp:8000 tcp:8000): "http://127.0.0.1:8000/api/"
    // For Android Emulator: "http://10.0.2.2:8000/api/"
    // ✅ Wireless debugging / Physical phone on same Wi-Fi
    //private static final String BASE_URL = "http://192.168.1.96:8000/api/";
    
    public static final String BASE_URL = "http://192.168.1.96:8000/api/";

    // Intent extras
    public static final String EXTRA_ITEM_ID      = "item_id";
    public static final String EXTRA_RECEIVER_ID  = "receiver_id";
    public static final String EXTRA_EMAIL        = "email";
    public static final String EXTRA_OTP_PURPOSE  = "otp_purpose";

    // OTP purposes
    public static final String OTP_EMAIL_VERIFY   = "email_verify";
    public static final String OTP_PASSWORD_RESET = "password_reset";

    // Chat refresh interval (milliseconds)
    public static final int CHAT_REFRESH_INTERVAL = 5000;

    // Item categories
    public static final String[] CATEGORIES = {
        "wallet", "phone", "keys", "bag",
        "id_card", "documents", "electronics", "other"
    };

    public static final String[] CATEGORY_LABELS = {
        "Wallet", "Phone", "Keys", "Bag",
        "ID Card", "Documents", "Electronics", "Other"
    };
}
