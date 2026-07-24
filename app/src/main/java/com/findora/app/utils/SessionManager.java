package com.findora.app.utils;

import android.content.Context;
import android.content.SharedPreferences;

public class SessionManager {
    private SharedPreferences prefs;
    private SharedPreferences.Editor editor;
    private static final String PREF_NAME       = "FindoraSession";
    private static final String KEY_TOKEN        = "access_token";
    private static final String KEY_REFRESH      = "refresh_token";
    private static final String KEY_USERNAME     = "username";
    private static final String KEY_ROLE         = "role";
    private static final String KEY_NAME         = "full_name";
    private static final String KEY_EMAIL        = "email";
    private static final String KEY_USER_ID      = "user_id";
    private static final String KEY_IS_VERIFIED  = "is_verified";

    public SessionManager(Context context) {
        prefs  = context.getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
        editor = prefs.edit();
    }

    public void saveSession(String accessToken, String refreshToken,
                            String username, String role, String fullName,
                            String email, int userId) {
        editor.putString(KEY_TOKEN, accessToken);
        editor.putString(KEY_REFRESH, refreshToken);
        editor.putString(KEY_USERNAME, username);
        editor.putString(KEY_ROLE, role);
        editor.putString(KEY_NAME, fullName);
        editor.putString(KEY_EMAIL, email);
        editor.putInt(KEY_USER_ID, userId);
        editor.putBoolean(KEY_IS_VERIFIED, true);
        editor.apply();
    }

    public void saveToken(String accessToken) {
        editor.putString(KEY_TOKEN, accessToken);
        editor.apply();
    }

    public void saveRefreshToken(String refreshToken) {
        editor.putString(KEY_REFRESH, refreshToken);
        editor.apply();
    }

    public String getToken()       { return prefs.getString(KEY_TOKEN, ""); }
    public String getRefreshToken(){ return prefs.getString(KEY_REFRESH, ""); }
    public String getUsername()    { return prefs.getString(KEY_USERNAME, ""); }
    public String getRole()        { return prefs.getString(KEY_ROLE, ""); }
    public String getFullName()    { return prefs.getString(KEY_NAME, ""); }
    public String getEmail()       { return prefs.getString(KEY_EMAIL, ""); }
    public int    getUserId()      { return prefs.getInt(KEY_USER_ID, 0); }
    public boolean isLoggedIn()    { return !getToken().isEmpty(); }
    public boolean isAdmin()       { return "admin".equals(getRole()); }

    public void logout() {
        editor.clear();
        editor.apply();
    }
}
