package com.findora.app.network;

import android.content.Context;
import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;
import java.util.concurrent.TimeUnit;

public class RetrofitClient {
    public static final String BASE_URL = Constants.BASE_URL;
    private static Retrofit retrofit = null;
    private static Context appContext = null;

    public static void setToken(String token) {
        // Kept for backwards compatibility
    }

    public static void clearToken() {
        // Kept for backwards compatibility
    }

    public static RetrofitClient getInstance(Context context) {
        if (context != null) {
            appContext = context.getApplicationContext();
        }
        return new RetrofitClient();
    }

    public static Retrofit getInstance() {
        if (retrofit == null) {
            HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
            logging.setLevel(HttpLoggingInterceptor.Level.BODY);

            OkHttpClient.Builder clientBuilder = new OkHttpClient.Builder()
                .addInterceptor(chain -> {
                    Request.Builder builder = chain.request().newBuilder()
                        .header("Content-Type", "application/json")
                        .header("Accept", "application/json");

                    if (appContext != null) {
                        SessionManager sessionManager = new SessionManager(appContext);
                        String token = sessionManager.getToken();
                        if (token != null && !token.trim().isEmpty()) {
                            builder.header("Authorization", "Bearer " + token);
                        }
                    }
                    return chain.proceed(builder.build());
                })
                .addInterceptor(logging)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS);

            if (appContext != null) {
                clientBuilder.authenticator(new TokenAuthenticator(appContext));
            }

            OkHttpClient client = clientBuilder.build();

            retrofit = new Retrofit.Builder()
                .baseUrl(BASE_URL)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build();
        }
        return retrofit;
    }

    public ApiService getApi() {
        return getInstance().create(ApiService.class);
    }
}
