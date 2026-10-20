package com.clementbarnes.kaoyan;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.webkit.JsResult;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * 考研单词卡 App 壳
 *
 * 设计要点：
 * 1. 资源全部打包在 assets 内，零网络权限，完全离线。
 * 2. 不用 file:// 加载（file:// 是 opaque origin，官方不推荐，且 API 30+ 需强开
 *    setAllowFileAccess），改用虚拟域名 https://appassets.androidplatform.net/
 *    —— 即官方 WebViewAssetLoader 的做法，这里用原生 API 自实现以免引入依赖。
 *    origin 固定后 localStorage 写入稳定，学习进度不会丢。
 * 3. 支持 Range 请求，音频可正常播放与拖动。
 */
public class MainActivity extends Activity {

    /** 虚拟域名，与官方 WebViewAssetLoader 默认值一致 */
    private static final String HOST = "appassets.androidplatform.net";
    private static final String HOME = "https://" + HOST + "/www/index.html";
    /** 兜底入口：万一某些机型不触发 shouldInterceptRequest，回退到 file:// 保证能用 */
    private static final String FALLBACK = "file:///android_asset/www/index.html";

    private WebView web;
    private boolean fellBack = false;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        web = new WebView(this);
        setContentView(web);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);              // localStorage：学习进度靠它
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        // 页面版式按固定字号设计；跟随系统字体放大会把卡片撑破
        s.setTextZoom(100);
        // 走虚拟 https 域名后不再需要 file:// 访问，关掉以缩小攻击面
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);

        // 页面底部有 alert 引导文案，需提供 WebChromeClient 才不会静默丢弃
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onJsAlert(WebView view, String url, String message, final JsResult result) {
                new AlertDialog.Builder(MainActivity.this)
                        .setMessage(message)
                        .setPositiveButton("知道了", new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(DialogInterface d, int w) {
                                result.confirm();
                            }
                        })
                        .setCancelable(false)
                        .show();
                return true;
            }
        });

        web.setWebViewClient(new WebViewClient() {
            /* API 24+ 实际只会调用这个重载；旧重载保留仅为低版本兜底 */
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return handleNav(request == null ? null : request.getUrl());
            }

            @SuppressWarnings("deprecation")
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleNav(url == null ? null : Uri.parse(url));
            }

            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                if (request == null) return null;
                return serve(request.getUrl(), request.getRequestHeaders());
            }

            @SuppressWarnings("deprecation")
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, String url) {
                return serve(url == null ? null : Uri.parse(url), null);
            }

            /* 主框架加载失败（拦截器未生效 / 虚拟域名解析失败）→ 自动退回 file:// */
            @Override
            public void onReceivedError(WebView view, WebResourceRequest request,
                                        android.webkit.WebResourceError error) {
                if (request != null && request.isForMainFrame()) fallback(view);
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request,
                                            WebResourceResponse errorResponse) {
                if (request != null && request.isForMainFrame()) fallback(view);
            }
        });

        if (savedInstanceState == null) {
            web.loadUrl(HOME);
        } else {
            web.restoreState(savedInstanceState);
        }
    }

    /** 只放行内部导航；其余交给系统浏览器 */
    private boolean handleNav(Uri uri) {
        if (uri == null) return true;
        if (HOST.equals(uri.getHost())) return false;                 // 虚拟域名内部资源
        String s = uri.toString();
        if (s.startsWith("file:///android_asset/")) return false;      // 兜底模式下的内部资源
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (Exception ignored) {
            // 没有可处理的 App，忽略，避免崩溃
        }
        return true;
    }

    /** 主框架加载失败时退回 file://，并临时放开文件访问（file:// 必需） */
    private void fallback(WebView view) {
        if (fellBack || view == null) return;
        fellBack = true;
        try {
            view.getSettings().setAllowFileAccess(true);
        } catch (Exception ignored) { }
        view.loadUrl(FALLBACK);
    }

    /** 把虚拟域名请求映射到 assets 目录并返回内容（含 Range 支持） */
    private WebResourceResponse serve(Uri uri, Map<String, String> reqHeaders) {
        if (uri == null || !HOST.equals(uri.getHost())) return null;

        String path = uri.getPath();
        if (path == null) path = "/";
        while (path.startsWith("/")) path = path.substring(1);
        if (path.isEmpty()) path = "www/index.html";

        // 防目录穿越
        if (path.contains("..")) return forbidden();

        String assetPath = path;
        InputStream raw;
        try {
            raw = getAssets().open(assetPath);
        } catch (IOException e) {
            return notFound();
        }

        byte[] data;
        try {
            data = readAll(raw);
        } catch (IOException e) {
            return notFound();
        } finally {
            try { raw.close(); } catch (IOException ignored) { }
        }

        String mime = mimeOf(assetPath);
        Map<String, String> headers = new HashMap<String, String>();
        headers.put("Accept-Ranges", "bytes");
        headers.put("Cache-Control", "no-cache");

        // 音频拖动会发 Range 请求，必须回 206，否则部分机型直接播不出声
        String range = null;
        if (reqHeaders != null) range = reqHeaders.get("Range");
        int total = data.length;

        if (range != null && range.startsWith("bytes=")) {
            long[] span = parseRange(range, total);
            if (span != null) {
                int start = (int) span[0];
                int end = (int) span[1];
                int len = end - start + 1;
                byte[] slice = new byte[len];
                System.arraycopy(data, start, slice, 0, len);
                headers.put("Content-Range", "bytes " + start + "-" + end + "/" + total);
                headers.put("Content-Length", String.valueOf(len));
                return new WebResourceResponse(mime, null, 206, "Partial Content", headers,
                        new java.io.ByteArrayInputStream(slice));
            }
        }

        headers.put("Content-Length", String.valueOf(total));
        return new WebResourceResponse(mime, encodingOf(mime), 200, "OK", headers,
                new java.io.ByteArrayInputStream(data));
    }

    /** 解析 bytes=a-b / bytes=a- / bytes=-n，返回 [start, end]；不合法返回 null */
    private long[] parseRange(String header, int total) {
        try {
            String spec = header.substring(6).trim();
            if (spec.indexOf(',') >= 0) spec = spec.substring(0, spec.indexOf(',')).trim();
            int dash = spec.indexOf('-');
            if (dash < 0) return null;

            long start;
            long end;
            String a = spec.substring(0, dash).trim();
            String b = spec.substring(dash + 1).trim();

            if (a.isEmpty()) {                 // bytes=-n 取末尾 n 字节
                if (b.isEmpty()) return null;
                long n = Long.parseLong(b);
                if (n <= 0) return null;
                start = Math.max(0, total - n);
                end = total - 1L;
            } else {
                start = Long.parseLong(a);
                end = b.isEmpty() ? total - 1L : Long.parseLong(b);
            }

            if (start < 0 || start >= total) return null;
            if (end >= total) end = total - 1L;
            if (end < start) return null;
            return new long[]{start, end};
        } catch (NumberFormatException e) {
            return null;
        }
    }

    private static byte[] readAll(InputStream in) throws IOException {
        java.io.ByteArrayOutputStream bos = new java.io.ByteArrayOutputStream(Math.max(1024, in.available()));
        byte[] buf = new byte[16384];
        int n;
        while ((n = in.read(buf)) > 0) bos.write(buf, 0, n);
        return bos.toByteArray();
    }

    private static String mimeOf(String p) {
        String s = p.toLowerCase();
        if (s.endsWith(".html") || s.endsWith(".htm")) return "text/html";
        if (s.endsWith(".js")) return "application/javascript";
        if (s.endsWith(".css")) return "text/css";
        if (s.endsWith(".json")) return "application/json";
        if (s.endsWith(".webmanifest")) return "application/manifest+json";
        if (s.endsWith(".png")) return "image/png";
        if (s.endsWith(".jpg") || s.endsWith(".jpeg")) return "image/jpeg";
        if (s.endsWith(".gif")) return "image/gif";
        if (s.endsWith(".svg")) return "image/svg+xml";
        if (s.endsWith(".mp3")) return "audio/mpeg";
        if (s.endsWith(".wav")) return "audio/wav";
        if (s.endsWith(".woff")) return "font/woff";
        if (s.endsWith(".woff2")) return "font/woff2";
        if (s.endsWith(".ttf")) return "font/ttf";
        if (s.endsWith(".ico")) return "image/x-icon";
        return "application/octet-stream";
    }

    private static String encodingOf(String mime) {
        if (mime.startsWith("text/") || mime.endsWith("javascript")
                || mime.endsWith("json") || mime.endsWith("svg+xml")) {
            return "utf-8";
        }
        return null;   // 二进制不声明编码
    }

    private static WebResourceResponse notFound() {
        return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found",
                new HashMap<String, String>(), new java.io.ByteArrayInputStream(new byte[0]));
    }

    private static WebResourceResponse forbidden() {
        return new WebResourceResponse("text/plain", "utf-8", 403, "Forbidden",
                new HashMap<String, String>(), new java.io.ByteArrayInputStream(new byte[0]));
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
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

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.setWebChromeClient(null);
            web.setWebViewClient(null);
            web.stopLoading();
            web.loadUrl("about:blank");
            web.removeAllViews();
            web.destroy();
            web = null;
        }
        super.onDestroy();
    }
}
