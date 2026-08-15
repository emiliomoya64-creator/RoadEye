package com.roadeye.app;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
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
        "http://192.168.10.21:8000/";

    private WebView webView;
    private LinearLayout errorPanel;
    private boolean cameraFullscreen = false;


    @Override
    protected void onCreate(
        Bundle savedInstanceState
    ) {
        super.onCreate(savedInstanceState);

        setContentView(
            R.layout.activity_main
        );

        configureSystemBars();

        webView = findViewById(
            R.id.roadeyeWebView
        );

        errorPanel = findViewById(
            R.id.errorPanel
        );

        Button retryButton = findViewById(
            R.id.retryButton
        );

        Button cameraFullscreenButton = findViewById(
            R.id.cameraFullscreenButton
        );

        configureWebView();

        retryButton.setOnClickListener(
            view -> loadRoadEye()
        );

        cameraFullscreenButton.setOnClickListener(
            view -> toggleCameraFullscreen(
                cameraFullscreenButton
            )
        );

        loadRoadEye();
    }


    private void configureSystemBars() {

        getWindow().setStatusBarColor(
            Color.BLACK
        );

        getWindow().setNavigationBarColor(
            Color.BLACK
        );

        if (
            android.os.Build.VERSION.SDK_INT
            >= android.os.Build.VERSION_CODES.R
        ) {

            WindowInsetsController controller =
                getWindow().getInsetsController();

            if (controller != null) {

                controller.setSystemBarsAppearance(
                    0,
                    WindowInsetsController
                        .APPEARANCE_LIGHT_STATUS_BARS
                );
            }
        }
    }


    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {

        WebSettings settings =
            webView.getSettings();

        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);

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

        settings.setSupportZoom(
            false
        );

        settings.setBuiltInZoomControls(
            false
        );

        settings.setDisplayZoomControls(
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


    private void toggleCameraFullscreen(
        Button button
    ) {
        if (cameraFullscreen) {
            exitCameraFullscreen(
                button
            );
        } else {
            enterCameraFullscreen(
                button
            );
        }
    }


    private void enterCameraFullscreen(
        Button button
    ) {
        cameraFullscreen = true;

        setRequestedOrientation(
            ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        );

        hideSystemBars();

        webView.evaluateJavascript(
            """
            (() => {
                const video =
                    document.getElementById('videoStream');

                if (!video) {
                    return;
                }

                document.body.dataset.roadeyeFullscreen =
                    '1';

                const style =
                    document.createElement('style');

                style.id =
                    'roadeye-app-fullscreen-style';

                style.textContent = `
                    html,
                    body {
                        margin: 0 !important;
                        padding: 0 !important;
                        width: 100% !important;
                        height: 100% !important;
                        overflow: hidden !important;
                        background: #000 !important;
                    }

                    body > * {
                        display: none !important;
                    }

                    main.dashboard {
                        display: block !important;
                    }

                    .dashboard > * {
                        display: none !important;
                    }

                    .dashboard > .camera-panel {
                        display: block !important;
                    }

                    .camera-panel,
                    .video-frame,
                    #videoStream {
                        display: block !important;
                    }

                    .dashboard {
                        position: fixed !important;
                        inset: 0 !important;
                        width: 100vw !important;
                        height: 100vh !important;
                        margin: 0 !important;
                        padding: 0 !important;
                    }

                    .camera-panel {
                        position: fixed !important;
                        inset: 0 !important;
                        width: 100vw !important;
                        height: 100vh !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        border: 0 !important;
                        border-radius: 0 !important;
                        background: #000 !important;
                    }

                    .camera-panel .panel-heading {
                        display: none !important;
                    }

                    .video-frame {
                        position: fixed !important;
                        inset: 0 !important;
                        width: 100vw !important;
                        height: 100vh !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        border: 0 !important;
                        border-radius: 0 !important;
                        background: #000 !important;
                    }

                    #videoStream {
                        position: fixed !important;
                        inset: 0 !important;
                        width: 100vw !important;
                        height: 100vh !important;
                        object-fit: contain !important;
                        background: #000 !important;
                    }
                `;

                const previous =
                    document.getElementById(
                        'roadeye-app-fullscreen-style'
                    );

                if (previous) {
                    previous.remove();
                }

                document.head.appendChild(
                    style
                );
            })();
            """,
            null
        );

        button.setText(
            "Salir"
        );
    }


    private void exitCameraFullscreen(
        Button button
    ) {
        cameraFullscreen = false;

        webView.evaluateJavascript(
            """
            (() => {
                const style =
                    document.getElementById(
                        'roadeye-app-fullscreen-style'
                    );

                if (style) {
                    style.remove();
                }

                delete document.body.dataset
                    .roadeyeFullscreen;
            })();
            """,
            null
        );

        showSystemBars();

        setRequestedOrientation(
            ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        );

        button.setText(
            "Cámara"
        );
    }


    private void hideSystemBars() {

        getWindow().getDecorView()
            .setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
            );

        if (
            android.os.Build.VERSION.SDK_INT
            >= android.os.Build.VERSION_CODES.R
        ) {
            WindowInsetsController controller =
                getWindow().getInsetsController();

            if (controller != null) {
                controller.hide(
                    WindowInsets.Type.statusBars()
                    | WindowInsets.Type.navigationBars()
                );

                controller.setSystemBarsBehavior(
                    WindowInsetsController
                        .BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                );
            }
        }
    }


    private void showSystemBars() {
        if (
            android.os.Build.VERSION.SDK_INT
            >= android.os.Build.VERSION_CODES.R
        ) {
            WindowInsetsController controller =
                getWindow().getInsetsController();

            if (controller != null) {
                controller.show(
                    WindowInsets.Type.systemBars()
                );
            }
        } else {
            getWindow().getDecorView()
                .setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_VISIBLE
                );
        }
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

        if (cameraFullscreen) {

            Button button = findViewById(
                R.id.cameraFullscreenButton
            );

            exitCameraFullscreen(
                button
            );

            return;
        }

        if (
            webView != null
            && webView.canGoBack()
        ) {
            webView.goBack();

        } else {
            super.onBackPressed();
        }
    }


    @Override
    protected void onDestroy() {

        if (webView != null) {

            webView.stopLoading();

            webView.loadUrl(
                "about:blank"
            );

            webView.destroy();
        }

        super.onDestroy();
    }
}
