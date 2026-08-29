package com.findora.app.network;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkCapabilities;
import android.util.Log;

import com.findora.app.utils.Constants;
import com.findora.app.utils.SessionManager;

import java.io.IOException;
import java.net.ConnectException;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.util.concurrent.TimeUnit;

import okhttp3.ConnectionPool;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.logging.HttpLoggingInterceptor;
import retrofit2.Retrofit;
import retrofit2.converter.gson.GsonConverterFactory;

public class RetrofitClient {

    private static final String TAG = "RetrofitClient";
    public static final String BASE_URL = Constants.BASE_URL;

    // Volatile ensures the singleton reference is visible across threads.
    private static volatile Retrofit retrofit = null;

    // appContext is set once from the first Activity call and never changes
    // after that (Application context is process-scoped and stable).
    // Using a separate lock object avoids holding the class-level monitor
    // longer than necessary.
    private static final Object CONTEXT_LOCK = new Object();
    private static volatile Context appContext = null;

    private static volatile ApiService apiService = null;

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
     * Thread-safety: appContext is set under CONTEXT_LOCK before the Retrofit
     * singleton is touched. This eliminates the TOCTOU race where appContext
     * could be reassigned between the outer retrofit==null check and the
     * synchronized block in getInstance().
     */
    public static RetrofitClient getInstance(Context context) {
        if (context != null) {
            synchronized (CONTEXT_LOCK) {
                // Only update if not already set — Application context is stable;
                // we only need it once. Subsequent calls from different activities
                // all resolve to the same Application context anyway.
                if (appContext == null) {
                    appContext = context.getApplicationContext();
                }
            }
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
                    // Capture appContext inside the synchronized block so the
                    // lambda closure always holds the exact context that was
                    // valid at construction time — no TOCTOU window.
                    final Context ctx;
                    synchronized (CONTEXT_LOCK) {
                        ctx = appContext;
                    }

                    if (ctx == null) {
                        throw new IllegalStateException(
                            "RetrofitClient: appContext is null. " +
                            "Call RetrofitClient.getInstance(Context) from an Activity " +
                            "before using getInstance().");
                    }

                    // ── OkHttp body-level logging interceptor ─────────────
                    HttpLoggingInterceptor logging = new HttpLoggingInterceptor(
                        message -> Log.d("OkHttp", message)
                    );
                    logging.setLevel(HttpLoggingInterceptor.Level.BODY);
                    logging.redactHeader("Authorization");

                    // ── Auth header interceptor ───────────────────────────
                    okhttp3.Interceptor authInterceptor = chain -> {
                        SessionManager sessionManager = new SessionManager(ctx);
                        String token = sessionManager.getToken();

                        if (token != null && !token.trim().isEmpty()) {
                            sessionManager.updateLastActivity();
                        }

                        Request.Builder builder = chain.request().newBuilder()
                            .header("Content-Type", "application/json")
                            .header("Accept", "application/json");

                        if (token != null && !token.trim().isEmpty()) {
                            builder.header("Authorization", "Bearer " + token);
                        }

                        return chain.proceed(builder.build());
                    };

                    // ── Network diagnostics interceptor ───────────────────
                    okhttp3.Interceptor networkLogger = chain -> {
                        Request request = chain.request();
                        long startMs = System.currentTimeMillis();
                        String endpoint = request.url().encodedPath();

                        Log.d(TAG, "→ " + request.method() + " " + endpoint);

                        try {
                            Response response = chain.proceed(request);
                            long elapsedMs = System.currentTimeMillis() - startMs;
                            Log.d(TAG, "← " + request.method() + " " + endpoint
                                    + " HTTP " + response.code()
                                    + " (" + elapsedMs + " ms)");
                            return response;
                        } catch (ConnectException e) {
                            long elapsedMs = System.currentTimeMillis() - startMs;
                            Log.e(TAG, "✗ ConnectException on " + endpoint
                                    + " after " + elapsedMs + " ms: "
                                    + e.getMessage());
                            throw e;
                        } catch (SocketTimeoutException e) {
                            long elapsedMs = System.currentTimeMillis() - startMs;
                            Log.e(TAG, "✗ SocketTimeoutException on " + endpoint
                                    + " after " + elapsedMs + " ms: "
                                    + e.getMessage());
                            throw e;
                        } catch (UnknownHostException e) {
                            long elapsedMs = System.currentTimeMillis() - startMs;
                            Log.e(TAG, "✗ UnknownHostException on " + endpoint
                                    + " after " + elapsedMs + " ms: "
                                    + e.getMessage());
                            throw e;
                        } catch (IOException e) {
                            long elapsedMs = System.currentTimeMillis() - startMs;
                            Log.e(TAG, "✗ IOException (" + e.getClass().getSimpleName()
                                    + ") on " + endpoint
                                    + " after " + elapsedMs + " ms: "
                                    + e.getMessage(), e);
                            throw e;
                        }
                    };

                    ConnectionPool connectionPool = new ConnectionPool(
                            5,
                            30,
                            TimeUnit.SECONDS
                    );

                    okhttp3.Dispatcher dispatcher = new okhttp3.Dispatcher();
                    dispatcher.setMaxRequests(32);
                    dispatcher.setMaxRequestsPerHost(10);

                    okhttp3.Cache cache = null;
                    try {
                        java.io.File cacheDir = new java.io.File(ctx.getCacheDir(), "http_cache");
                        cache = new okhttp3.Cache(cacheDir, 10 * 1024 * 1024);
                    } catch (Exception ignored) {}

                    OkHttpClient.Builder clientBuilder = new OkHttpClient.Builder()
                        .addInterceptor(authInterceptor)
                        .addInterceptor(networkLogger)
                        .addInterceptor(logging)
                        .authenticator(new TokenAuthenticator(ctx))
                        .connectionPool(connectionPool)
                        .dispatcher(dispatcher)
                        .connectTimeout(15, TimeUnit.SECONDS)
                        .readTimeout(20, TimeUnit.SECONDS)
                        .writeTimeout(20, TimeUnit.SECONDS);

                    if (cache != null) {
                        clientBuilder.cache(cache);
                    }

                    OkHttpClient client = clientBuilder.build();

                    retrofit = new Retrofit.Builder()
                        .baseUrl(BASE_URL)
                        .client(client)
                        .addConverterFactory(GsonConverterFactory.create())
                        .build();
                }
            }
        }
        return retrofit;
    }

    // ─── Connectivity helper (static, usable by Activities) ──────────────────

    public static boolean isNetworkAvailable(Context context) {
        ConnectivityManager cm =
            (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm == null) return false;
        android.net.Network network = cm.getActiveNetwork();
        if (network == null) return false;
        NetworkCapabilities caps = cm.getNetworkCapabilities(network);
        return caps != null
            && (caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
             || caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)
             || caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET));
    }

    // ─── ApiService accessor ──────────────────────────────────────────────────

    public ApiService getApi() {
        if (apiService == null) {
            synchronized (RetrofitClient.class) {
                if (apiService == null) {
                    apiService = getInstance().create(ApiService.class);
                }
            }
        }
        return apiService;
    }
}
