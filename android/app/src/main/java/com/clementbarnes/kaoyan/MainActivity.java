package com.clementbarnes.kaoyan;

import android.annotation.SuppressLint;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;

/**
 * 考研单词卡 App 壳
 * - 全部资源打包在 assets 内，离线可用
 * - 不需要任何网络权限
 * - 外链（真題精翻等）交给系统浏览器打开
 */
public class MainActivity extends Activity {

    private WebView web;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);          // localStorage：学习进度靠它
        s.setDatabaseEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        // 让页面能自适应刘海屏
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            s.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url != null && url.startsWith("file:///android_asset/")) {
                    return false;   // 本地资源内部跳转，放行
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                } catch (Exception ignored) { }
                return true;
            }
        });

        if (savedInstanceState == null) {
            web.loadUrl("file:///android_asset/www/index.html");
        } else {
            web.restoreState(savedInstanceState);
        }
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (web != null) web.saveState(outState);
    }
}
