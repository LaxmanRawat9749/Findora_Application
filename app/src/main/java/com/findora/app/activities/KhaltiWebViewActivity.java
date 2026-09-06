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
    public static final String EXTRA_FORM_URL = "extra_form_url";
    public static final String EXTRA_POST_DATA = "extra_post_data";
    public static final String EXTRA_FORM_HTML = "extra_form_html";

    private ActivityKhaltiWebviewBinding binding;
    private String originalUrl;
    private String formUrl;
    private String postData;
    private String formHtml;
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
        formUrl = getIntent().getStringExtra(EXTRA_FORM_URL);
        postData = getIntent().getStringExtra(EXTRA_POST_DATA);
        formHtml = getIntent().getStringExtra(EXTRA_FORM_HTML);

        binding.toolbar.setNavigationOnClickListener(v -> showCancelConfirmationDialog());

        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override
            public void handleOnBackPressed() {
                showCancelConfirmationDialog();
            }
        });

        setupWebView();

        if (formHtml != null && !formHtml.isEmpty()) {
            binding.webview.loadDataWithBaseURL("https://rc-epay.esewa.com.np", formHtml, "text/html", "UTF-8", null);
        } else if (formUrl != null && !formUrl.isEmpty() && postData != null && !postData.isEmpty()) {
            String generatedHtml = buildAutoSubmittingFormHtml(formUrl, postData);
            binding.webview.loadDataWithBaseURL("https://rc-epay.esewa.com.np", generatedHtml, "text/html", "UTF-8", null);
        } else if (originalUrl != null && !originalUrl.isEmpty()) {
            binding.webview.loadUrl(originalUrl);
        } else {
            finishWithResult("Error: Invalid URL", pidx);
        }
    }

    private String buildAutoSubmittingFormHtml(String actionUrl, String postData) {
        StringBuilder inputs = new StringBuilder();
        if (postData != null && !postData.isEmpty()) {
            String[] pairs = postData.split("&");
            for (String pair : pairs) {
                int idx = pair.indexOf("=");
                if (idx > 0) {
                    try {
                        String key = java.net.URLDecoder.decode(pair.substring(0, idx), "UTF-8");
                        String val = java.net.URLDecoder.decode(pair.substring(idx + 1), "UTF-8");
                        inputs.append("<input type=\"hidden\" name=\"")
                              .append(escapeHtml(key))
                              .append("\" value=\"")
                              .append(escapeHtml(val))
                              .append("\">\n");
                    } catch (Exception ignored) {}
                }
            }
        }

        return "<!DOCTYPE html>\n" +
                "<html>\n" +
                "<head>\n" +
                "    <meta charset=\"UTF-8\">\n" +
                "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n" +
                "    <title>Connecting to eSewa...</title>\n" +
                "    <style>\n" +
                "        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background-color: #F8F9FD; color: #1A1A2E; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; text-align: center; }\n" +
                "        .card { background: #FFFFFF; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); padding: 32px; max-width: 380px; width: 100%; }\n" +
                "        .spinner { border: 4px solid #E9ECEF; border-top: 4px solid #60BB46; border-radius: 50%; width: 44px; height: 44px; animation: spin 1s linear infinite; margin: 0 auto 20px; }\n" +
                "        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }\n" +
                "        h2 { font-size: 18px; margin: 0 0 8px; color: #1A1A2E; }\n" +
                "        p { font-size: 14px; color: #6C757D; margin: 0 0 20px; }\n" +
                "        .btn { background-color: #60BB46; color: white; border: none; padding: 12px 24px; font-size: 15px; font-weight: 600; border-radius: 10px; width: 100%; cursor: pointer; }\n" +
                "    </style>\n" +
                "</head>\n" +
                "<body onload=\"document.getElementById('esewaForm').submit();\">\n" +
                "    <div class=\"card\">\n" +
                "        <div class=\"spinner\"></div>\n" +
                "        <h2>Redirecting to eSewa</h2>\n" +
                "        <p>Connecting securely to eSewa payment gateway...</p>\n" +
                "        <form id=\"esewaForm\" method=\"POST\" action=\"" + escapeHtml(actionUrl) + "\">\n" +
                inputs.toString() +
                "            <noscript><button type=\"submit\" class=\"btn\">Click here to continue to eSewa</button></noscript>\n" +
                "        </form>\n" +
                "    </div>\n" +
                "</body>\n" +
                "</html>";
    }

    private String escapeHtml(String text) {
        if (text == null) return "";
        return text.replace("&", "&amp;")
                   .replace("\"", "&quot;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;");
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
