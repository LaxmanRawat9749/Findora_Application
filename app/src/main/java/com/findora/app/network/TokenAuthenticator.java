package com.findora.app.network;

import android.content.Context;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;

import com.findora.app.models.RefreshRequest;
import com.findora.app.models.TokenResponse;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;

import okhttp3.Authenticator;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.Route;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

import java.io.IOException;

public class TokenAuthenticator implements Authenticator {

    private static final String TAG = "TokenAuthenticator";

    // Class-level lock: prevents multiple OkHttp dispatcher threads from
    // simultaneously attempting to refresh the token when they all receive
    // a 401. Without this, the first thread refreshes successfully, but
    // subsequent threads use the now-invalidated old refresh token, causing
    // all concurrent requests to fail permanently.
    private static final Object REFRESH_LOCK = new Object();

    private final Context context;

    public TokenAuthenticator(Context context) {
        this.context = context.getApplicationContext();
    }

    @Nullable
    @Override
    public Request authenticate(@Nullable Route route, @NonNull Response response)
            throws IOException {

        // Stop after 2 attempts (the original request + one retry)
        // to prevent an infinite 401 retry loop.
        if (responseCount(response) >= 2) {
            Log.w(TAG, "Refresh already attempted — giving up to prevent infinite loop");
            return null;
        }

        synchronized (REFRESH_LOCK) {
            // Re-check the token AFTER acquiring the lock.
            // Another thread may have already refreshed it while we were waiting.
            SessionManager sessionManager = new SessionManager(context);
            String currentAccessToken = sessionManager.getToken();

            // If the token in SharedPreferences no longer matches the token
            // that triggered the 401, a concurrent thread already refreshed it.
            // Retry the request with the new token without hitting the server again.
            String failedRequestToken = response.request().header("Authorization");
            if (failedRequestToken != null
                    && currentAccessToken != null
                    && !currentAccessToken.trim().isEmpty()
                    && !failedRequestToken.equals("Bearer " + currentAccessToken)) {
                Log.d(TAG, "Token was already refreshed by another thread — retrying with new token");
                return response.request().newBuilder()
                        .header("Authorization", "Bearer " + currentAccessToken)
                        .build();
            }

            // Attempt the token refresh
            String refreshToken = sessionManager.getRefreshToken();
            if (refreshToken == null || refreshToken.trim().isEmpty()) {
                Log.w(TAG, "No refresh token available — clearing session");
                sessionManager.logout();
                return null;
            }

            try {
                // Use a dedicated Retrofit instance with no auth interceptor/authenticator
                // to avoid recursive authentication loops during the refresh call itself.
                Retrofit refreshRetrofit = new Retrofit.Builder()
                        .baseUrl(Constants.BASE_URL)
                        .addConverterFactory(GsonConverterFactory.create())
                        .build();

                ApiService refreshService = refreshRetrofit.create(ApiService.class);
                retrofit2.Response<TokenResponse> refreshResponse =
                        refreshService.refreshToken(new RefreshRequest(refreshToken)).execute();

                if (refreshResponse.isSuccessful() && refreshResponse.body() != null) {
                    TokenResponse tokenBody = refreshResponse.body();

                    if (tokenBody.access != null && !tokenBody.access.isEmpty()) {
                        // Persist the new token synchronously (commit()) so the
                        // auth interceptor immediately reads the new value on retry.
                        sessionManager.saveToken(tokenBody.access);

                        if (tokenBody.refresh != null && !tokenBody.refresh.isEmpty()) {
                            sessionManager.saveRefreshToken(tokenBody.refresh);
                        }

                        Log.d(TAG, "Token refreshed successfully — retrying original request");
                        return response.request().newBuilder()
                                .header("Authorization", "Bearer " + tokenBody.access)
                                .build();
                    }
                }

                // Refresh failed (bad response or empty body) — session is invalid
                Log.w(TAG, "Token refresh failed (HTTP " + refreshResponse.code()
                        + ") — clearing session");
                sessionManager.logout();
                return null;

            } catch (IOException e) {
                // Network error during refresh — do NOT log out; the user may just
                // be temporarily offline. Return null so the current request fails
                // gracefully. The next request will try to refresh again.
                Log.w(TAG, "Network error during token refresh — will retry on next request", e);
                return null;
            }
        }
    }

    private int responseCount(Response response) {
        int count = 1;
        while ((response = response.priorResponse()) != null) {
            count++;
        }
        return count;
    }
}
