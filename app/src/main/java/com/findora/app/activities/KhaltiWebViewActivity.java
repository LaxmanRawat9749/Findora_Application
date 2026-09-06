package com.findora.app.activities;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.activity.OnBackPressedCallback;

import com.findora.app.databinding.ActivityKhaltiWebviewBinding;

public class KhaltiWebViewActivity extends BaseActivity {

    public static final String EXTRA_URL = "extra_url";
    public static final String EXTRA_PIDX = "extra_pidx";
    public static final String EXTRA_STATUS = "extra_status";
    public static final String EXTRA_TITLE = "extra_title";

    private ActivityKhaltiWebviewBinding binding;
    private String originalUrl;
    private String pidx;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityKhaltiWebviewBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        String title = getIntent().getStringExtra(EXTRA_TITLE);
        if (title == null || title.isEmpty()) {
            title = "eSewa Checkout";
        }
        binding.toolbar.setTitle(title);

        pidx = getIntent().getStringExtra(EXTRA_PIDX);
        originalUrl = getIntent().getStringExtra(EXTRA_URL);

        binding.toolbar.setNavigationOnClickListener(v -> showCancelConfirmationDialog());

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                showCancelConfirmationDialog();
            }
        });

        if (originalUrl == null || originalUrl.isEmpty()) {
            finishWithResult("Error: Invalid URL", pidx);
            return;
        }

        setupWebView();
        binding.webview.loadUrl(originalUrl);
    }

    private void setupWebView() {
        WebSettings settings = binding.webview.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowContentAccess(true);
        settings.setAllowFileAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);

        binding.webview.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                binding.progressBar.setVisibility(View.VISIBLE);

                // Check in onPageStarted as well to intercept redirects immediately
                if (url != null && url.contains("/api/payments/callback/")) {
                    handleCallbackUrl(url);
                }
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                binding.progressBar.setVisibility(View.GONE);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String url = uri.toString();

                // 1. Intercept Findora payment callback
                if (url.contains("/api/payments/callback/")) {
                    handleCallbackUrl(url);
                    return true;
                }

                // 2. Handle eSewa custom scheme (esewa://)
                if (url.startsWith("esewa://")) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                        startActivity(intent);
                        return true;
                    } catch (ActivityNotFoundException e) {
                        return false;
                    }
                }

                // 3. Handle Android Intent scheme (intent://)
                if (url.startsWith("intent://")) {
                    try {
                        Intent intent = Intent.parseUri(url, Intent.URI_INTENT_SCHEME);
                        if (intent != null) {
                            if (getPackageManager().resolveActivity(intent, 0) != null) {
                                startActivity(intent);
                                return true;
                            }
                            String fallbackUrl = intent.getStringExtra("browser_fallback_url");
                            if (fallbackUrl != null) {
                                view.loadUrl(fallbackUrl);
                                return true;
                            }
                        }
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                    return true;
                }

                // 4. Handle Market / Play Store links
                if (url.startsWith("market://")) {
                    try {
                        Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                        startActivity(intent);
                        return true;
                    } catch (Exception ignored) {}
                }

                return false;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                super.onReceivedError(view, request, error);
                if (request.isForMainFrame()) {
                    binding.progressBar.setVisibility(View.GONE);
                }
            }
        });
    }

    private void handleCallbackUrl(String url) {
        try {
            Uri uri = Uri.parse(url);
            String callbackPidx = uri.getQueryParameter("pidx");
            String callbackStatus = uri.getQueryParameter("status");

            if (callbackPidx == null || callbackPidx.isEmpty()) {
                callbackPidx = pidx;
            }

            String finalStatus = (callbackStatus != null && !callbackStatus.isEmpty()) ? callbackStatus : "Completed";
            finishWithResult(finalStatus, callbackPidx);
        } catch (Exception e) {
            finishWithResult("Completed", pidx);
        }
    }

    private void showCancelConfirmationDialog() {
        new AlertDialog.Builder(this)
                .setTitle("Cancel Payment?")
                .setMessage("Are you sure you want to cancel the payment? Your item will not be promoted.")
                .setPositiveButton("Yes, Cancel", (dialog, which) -> finishWithResult("Canceled", pidx))
                .setNegativeButton("Continue Payment", (dialog, which) -> dialog.dismiss())
                .show();
    }

    private void finishWithResult(String status, String callbackPidx) {
        Intent resultIntent = new Intent();
        resultIntent.putExtra(EXTRA_STATUS, status != null ? status : "Canceled");
        if (callbackPidx != null) {
            resultIntent.putExtra(EXTRA_PIDX, callbackPidx);
        } else if (pidx != null) {
            resultIntent.putExtra(EXTRA_PIDX, pidx);
        }
        setResult(Activity.RESULT_OK, resultIntent);
        finish();
    }
}
