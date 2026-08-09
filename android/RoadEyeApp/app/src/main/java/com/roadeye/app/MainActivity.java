package com.roadeye.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;

public class MainActivity extends Activity {

    private static final String ROAD_EYE_URL =
        "http://roadeye.local:8000/";

    private WebView webView;
    private LinearLayout errorPanel;

    @Override
    protected void onCreate(
        Bundle savedInstanceState
    ) {
        super.onCreate(savedInstanceState);

        setContentView(
            R.layout.activity_main
        );

        webView = findViewById(
            R.id.roadeyeWebView
        );

        errorPanel = findViewById(
            R.id.errorPanel
        );

        Button retryButton = findViewById(
            R.id.retryButton
        );

        configureWebView();

        retryButton.setOnClickListener(
            view -> loadRoadEye()
        );

        loadRoadEye();
    }


    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {

        WebSettings settings =
            webView.getSettings();

        settings.setJavaScriptEnabled(
            true
        );

        settings.setDomStorageEnabled(
            true
        );

        settings.setMediaPlaybackRequiresUserGesture(
            false
        );

        settings.setLoadsImagesAutomatically(
            true
        );

        settings.setUseWideViewPort(
            true
        );

        settings.setLoadWithOverviewMode(
            true
        );

        settings.setBuiltInZoomControls(
            false
        );

        settings.setDisplayZoomControls(
            false
        );

        settings.setSupportZoom(
            false
        );

        settings.setMixedContentMode(
            WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        );

        webView.setBackgroundColor(
            Color.BLACK
        );

        webView.setWebChromeClient(
            new WebChromeClient()
        );

        webView.setWebViewClient(
            new WebViewClient() {

                @Override
                public boolean shouldOverrideUrlLoading(
                    WebView view,
                    WebResourceRequest request
                ) {

                    Uri uri =
                        request.getUrl();

                    String host =
                        uri.getHost();

                    if (
                        host != null
                        && (
                            host.equals(
                                "roadeye.local"
                            )
                            || host.startsWith(
                                "192.168."
                            )
                            || host.startsWith(
                                "10."
                            )
                        )
                    ) {
                        return false;
                    }

                    return true;
                }


                @Override
                public void onPageFinished(
                    WebView view,
                    String url
                ) {
                    super.onPageFinished(
                        view,
                        url
                    );

                    errorPanel.setVisibility(
                        View.GONE
                    );

                    webView.setVisibility(
                        View.VISIBLE
                    );
                }


                @Override
                public void onReceivedError(
                    WebView view,
                    WebResourceRequest request,
                    WebResourceError error
                ) {

                    super.onReceivedError(
                        view,
                        request,
                        error
                    );

                    if (
                        request.isForMainFrame()
                    ) {
                        showConnectionError();
                    }
                }
            }
        );
    }


    private void loadRoadEye() {

        errorPanel.setVisibility(
            View.GONE
        );

        webView.setVisibility(
            View.VISIBLE
        );

        webView.loadUrl(
            ROAD_EYE_URL
        );
    }


    private void showConnectionError() {

        webView.setVisibility(
            View.GONE
        );

        errorPanel.setVisibility(
            View.VISIBLE
        );
    }


    @Override
    public void onBackPressed() {

        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }


    @Override
    protected void onDestroy() {

        if (webView != null) {

            webView.loadUrl(
                "about:blank"
            );

            webView.stopLoading();

            webView.destroy();
        }

        super.onDestroy();
    }
}
