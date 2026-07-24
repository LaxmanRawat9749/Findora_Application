package com.findora.app.network;

import android.content.Context;
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
    private final Context context;

    public TokenAuthenticator(Context context) {
        this.context = context.getApplicationContext();
    }

    @Nullable
    @Override
    public Request authenticate(@Nullable Route route, @NonNull Response response) throws IOException {
        if (responseCount(response) >= 2) {
            return null;
        }

        SessionManager sessionManager = new SessionManager(context);
        String refreshToken = sessionManager.getRefreshToken();

        if (refreshToken == null || refreshToken.trim().isEmpty()) {
            return null;
        }

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
                sessionManager.saveToken(tokenBody.access);
                if (tokenBody.refresh != null && !tokenBody.refresh.isEmpty()) {
                    sessionManager.saveRefreshToken(tokenBody.refresh);
                }

                return response.request().newBuilder()
                        .header("Authorization", "Bearer " + tokenBody.access)
                        .build();
            }
        }

        sessionManager.logout();
        return null;
    }

    private int responseCount(Response response) {
        int count = 1;
        while ((response = response.priorResponse()) != null) {
            count++;
        }
        return count;
    }
}
