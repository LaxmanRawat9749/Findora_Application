package com.findora.app.utils;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import android.util.Log;

import org.json.JSONObject;

public class SessionManager {
    private static final String TAG = "SessionManager";

    private final SharedPreferences prefs;

    private static final String PREF_NAME      = "FindoraSession";
    private static final String KEY_TOKEN      = "access_token";
    private static final String KEY_REFRESH    = "refresh_token";
    private static final String KEY_USERNAME   = "username";
    private static final String KEY_ROLE       = "role";
    private static final String KEY_NAME       = "full_name";
    private static final String KEY_EMAIL      = "email";
    private static final String KEY_USER_ID    = "user_id";
    private static final String KEY_IS_VERIFIED = "is_verified";

    public SessionManager(Context context) {
        // Always use application context to prevent memory leaks
        prefs = context.getApplicationContext()
                       .getSharedPreferences(PREF_NAME, Context.MODE_PRIVATE);
    }

    // ─── Write operations — all use commit() for synchronous, durable writes ──

    /**
     * Saves the full session atomically after a successful login.
     * Uses commit() so the data is guaranteed on disk before this method returns.
     * The caller (LoginActivity) navigates to HomeActivity only after this returns.
     */
    public void saveSession(String accessToken, String refreshToken,
                            String username, String role, String fullName,
                            String email, int userId) {
        prefs.edit()
             .putString(KEY_TOKEN, accessToken)
             .putString(KEY_REFRESH, refreshToken)
             .putString(KEY_USERNAME, username)
             .putString(KEY_ROLE, role)
             .putString(KEY_NAME, fullName)
             .putString(KEY_EMAIL, email)
             .putInt(KEY_USER_ID, userId)
             .putBoolean(KEY_IS_VERIFIED, true)
             .commit(); // synchronous — token is durable when this returns
    }

    /**
     * Updates only the access token (called by TokenAuthenticator after refresh).
     * Uses commit() so the new token is immediately readable by subsequent interceptor calls.
     */
    public void saveToken(String accessToken) {
        prefs.edit()
             .putString(KEY_TOKEN, accessToken)
             .commit(); // synchronous — essential for thread-safety with OkHttp threads
    }

    /**
     * Updates only the refresh token (called by TokenAuthenticator after a rotation).
     * Uses commit() for the same reason as saveToken().
     */
    public void saveRefreshToken(String refreshToken) {
        prefs.edit()
             .putString(KEY_REFRESH, refreshToken)
             .commit(); // synchronous
    }

    // ─── Read operations ──────────────────────────────────────────────────────

    public String getToken()        { return prefs.getString(KEY_TOKEN, ""); }
    public String getRefreshToken() { return prefs.getString(KEY_REFRESH, ""); }
    public String getUsername()     { return prefs.getString(KEY_USERNAME, ""); }
    public String getRole()         { return prefs.getString(KEY_ROLE, ""); }
    public String getFullName()     { return prefs.getString(KEY_NAME, ""); }
    public String getEmail()        { return prefs.getString(KEY_EMAIL, ""); }
    public int    getUserId()       { return prefs.getInt(KEY_USER_ID, 0); }
    public boolean isAdmin()        { return "admin".equals(getRole()); }

    // ─── Session validation ───────────────────────────────────────────────────

    /**
     * Performs real session validation. Returns true only when ALL of the
     * following conditions hold:
     *  1. Access token is present and non-empty.
     *  2. Refresh token is present and non-empty.
     *  3. User ID is positive (> 0).
     *  4. The JWT access token has not expired (checked via the "exp" claim).
     *
     * This replaces the old isLoggedIn() which only checked for a non-empty
     * token string — an unsafe check that allowed stale SharedPreferences data
     * from a previous session to bypass authentication.
     */
    public boolean isSessionValid() {
        String accessToken  = getToken();
        String refreshToken = getRefreshToken();
        int    userId       = getUserId();

        // Structural checks — must have both tokens and a valid user ID
        if (accessToken == null || accessToken.trim().isEmpty()) return false;
        if (refreshToken == null || refreshToken.trim().isEmpty()) return false;
        if (userId <= 0) return false;

        // JWT expiry check — decode payload without a library
        return !isJwtExpired(accessToken);
    }

    /**
     * Kept as an alias for isSessionValid() so all existing callers benefit
     * from the improved check without requiring changes to their call sites.
     */
    public boolean isLoggedIn() {
        return isSessionValid();
    }

    /**
     * Decodes a JWT and checks its "exp" claim against the current time.
     * Returns true if the token IS expired or cannot be decoded (fail-safe).
     */
    private boolean isJwtExpired(String jwt) {
        try {
            // JWT format: header.payload.signature — we only need the payload
            String[] parts = jwt.split("\\.");
            if (parts.length < 2) return true; // malformed token — treat as expired

            // Base64URL decode (JWT uses URL-safe Base64 without padding)
            byte[] decodedBytes = Base64.decode(parts[1], Base64.URL_SAFE | Base64.NO_PADDING);
            String payload = new String(decodedBytes, "UTF-8");

            JSONObject json = new JSONObject(payload);
            if (!json.has("exp")) return true; // no expiry claim — treat as expired

            long expSeconds = json.getLong("exp");
            long nowSeconds = System.currentTimeMillis() / 1000L;

            // Add a 30-second buffer so we proactively refresh near-expired tokens
            return nowSeconds >= (expSeconds - 30);

        } catch (Exception e) {
            Log.w(TAG, "Failed to decode JWT for expiry check — treating as expired", e);
            return true; // fail-safe: if we cannot verify, treat as expired
        }
    }

    // ─── Logout — clears ALL session data synchronously ──────────────────────

    /**
     * Clears every session key atomically and synchronously.
     * Using commit() guarantees the data is removed from disk before this
     * method returns, so pressing Back after logout never re-reads stale state.
     */
    public void logout() {
        prefs.edit()
             .remove(KEY_TOKEN)
             .remove(KEY_REFRESH)
             .remove(KEY_USERNAME)
             .remove(KEY_ROLE)
             .remove(KEY_NAME)
             .remove(KEY_EMAIL)
             .remove(KEY_USER_ID)
             .remove(KEY_IS_VERIFIED)
             .commit(); // synchronous — prefs are cleared before caller proceeds
    }
}
