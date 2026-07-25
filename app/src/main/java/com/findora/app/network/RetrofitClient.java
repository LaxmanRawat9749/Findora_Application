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

    // Volatile ensures the singleton reference is visible across threads
    private static volatile Retrofit retrofit = null;
    private static volatile Context appContext = null;

    // ─── Backwards-compatible no-ops ─────────────────────────────────────────

    public static void setToken(String token) {
        // Kept for backwards compatibility — token is now read live from SessionManager
    }

    public static void clearToken() {
        // Kept for backwards compatibility
    }

    // ─── Instance factory used by Activities ──────────────────────────────────

    /**
     * Stores the application context (safe, no memory leak) and returns a
     * RetrofitClient wrapper. Activities use this to obtain the ApiService.
     *
     * IMPORTANT: This must be called before getInstance() is used so that
     * appContext is available when the OkHttp auth interceptor runs.
     */
    public static RetrofitClient getInstance(Context context) {
        if (context != null) {
            // Set appContext BEFORE touching the singleton so the interceptor
            // always sees a non-null context when it is first built.
            appContext = context.getApplicationContext();
        }
        return new RetrofitClient();
    }

    // ─── Retrofit singleton — thread-safe double-checked locking ─────────────

    /**
     * Returns the Retrofit singleton. Thread-safe via double-checked locking
     * with a volatile field so multiple OkHttp dispatcher threads cannot race
     * to build the singleton concurrently.
     *
     * The appContext MUST have been set via getInstance(Context) before this
     * is called. If it has not been set (programming error), we fail fast with
     * a clear exception rather than silently building an unauthenticated client.
     */
    public static Retrofit getInstance() {
        if (retrofit == null) {
            synchronized (RetrofitClient.class) {
                if (retrofit == null) {
                    // Fail fast rather than silently omitting the auth header
                    if (appContext == null) {
                        throw new IllegalStateException(
                            "RetrofitClient: appContext is null. " +
                            "Call RetrofitClient.getInstance(Context) from an Activity " +
                            "before using getInstance().");
                    }

                    HttpLoggingInterceptor logging = new HttpLoggingInterceptor();
                    logging.setLevel(HttpLoggingInterceptor.Level.BODY);

                    // Capture the context in a local final variable for the lambda
                    final Context ctx = appContext;

                    OkHttpClient.Builder clientBuilder = new OkHttpClient.Builder()
                        .addInterceptor(chain -> {
                            // Read the token fresh on every request — SessionManager reads
                            // directly from SharedPreferences so it always sees the latest
                            // value, even after a token refresh by TokenAuthenticator.
                            SessionManager sessionManager = new SessionManager(ctx);
                            String token = sessionManager.getToken();

                            Request.Builder builder = chain.request().newBuilder()
                                .header("Content-Type", "application/json")
                                .header("Accept", "application/json");

                            if (token != null && !token.trim().isEmpty()) {
                                builder.header("Authorization", "Bearer " + token);
                            }

                            return chain.proceed(builder.build());
                        })
                        .addInterceptor(logging)
                        .authenticator(new TokenAuthenticator(ctx))
                        .connectTimeout(30, TimeUnit.SECONDS)
                        .readTimeout(30, TimeUnit.SECONDS)
                        .writeTimeout(30, TimeUnit.SECONDS);

                    retrofit = new Retrofit.Builder()
                        .baseUrl(BASE_URL)
                        .client(clientBuilder.build())
                        .addConverterFactory(GsonConverterFactory.create())
                        .build();
                }
            }
        }
        return retrofit;
    }

    // ─── ApiService accessor ──────────────────────────────────────────────────

    public ApiService getApi() {
        return getInstance().create(ApiService.class);
    }
}
