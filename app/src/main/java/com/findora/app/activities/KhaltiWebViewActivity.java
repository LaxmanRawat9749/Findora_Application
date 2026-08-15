package com.findora.app.activities;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import com.findora.app.databinding.ActivityKhaltiWebviewBinding;

public class KhaltiWebViewActivity extends BaseActivity {

    public static final String EXTRA_URL = "extra_url";
    public static final String EXTRA_PIDX = "extra_pidx";
    public static final String EXTRA_STATUS = "extra_status";

    private ActivityKhaltiWebviewBinding binding;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        binding = ActivityKhaltiWebviewBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        binding.toolbar.setNavigationOnClickListener(v -> finishWithResult("User canceled", null));

        String url = getIntent().getStringExtra(EXTRA_URL);
        if (url == null || url.isEmpty()) {
            finishWithResult("Error: Invalid URL", null);
            return;
        }

        setupWebView();
        binding.webview.loadUrl(url);
    }

    private void setupWebView() {
        binding.webview.getSettings().setJavaScriptEnabled(true);
        binding.webview.getSettings().setDomStorageEnabled(true);

        binding.webview.setWebViewClient(new WebViewClient() {
            @Override
            public void onPageStarted(WebView view, String url, Bitmap favicon) {
                super.onPageStarted(view, url, favicon);
                binding.progressBar.setVisibility(View.VISIBLE);
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
                
                // Intercept the return_url we configured on the backend
                if (url.startsWith("findorapp://payment/callback")) {
                    String pidx = uri.getQueryParameter("pidx");
                    String status = uri.getQueryParameter("status");
                    
                    finishWithResult(status, pidx);
                    return true;
                }
                
                return false;
            }
        });
    }
    
    private void finishWithResult(String status, String pidx) {
        Intent resultIntent = new Intent();
        resultIntent.putExtra(EXTRA_STATUS, status != null ? status : "User canceled");
        if (pidx != null) {
            resultIntent.putExtra(EXTRA_PIDX, pidx);
        }
        setResult(Activity.RESULT_OK, resultIntent);
        finish();
    }
}
