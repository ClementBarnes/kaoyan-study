package com.clementbarnes.kaoyan;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.ViewGroup;
import android.widget.TextView;
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
    /** 页面基地址：相对路径（audio/x.mp3、icons/x.png）都会解析到这里，由拦截器读 assets */
    private static final String BASE_URL = "https://" + HOST + "/www/";

    private WebView web;

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

        // 音频桥：详见 AudioBridge，不依赖任何 URL 协议
        web.addJavascriptInterface(new AudioBridge(), "NativeAudio");

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
        });

        if (savedInstanceState == null) {
            loadApp();
        } else {
            web.restoreState(savedInstanceState);
        }
    }

    /**
     * 音频通道：完全不走网络、不走 file:// 协议。
     * JS 通过 NativeAudio.getAudio(词) 拿到 base64，前端转成 Blob URL 播放。
     * 这样即使某些 ROM 的 shouldInterceptRequest 不生效，发音也照样能响。
     */
    private class AudioBridge {
        @android.webkit.JavascriptInterface
        public boolean available() {
            return true;
        }

        /** 只接受字母词条，杜绝任意路径读取 */
        @android.webkit.JavascriptInterface
        public String getAudio(String word) {
            if (word == null) return "";
            String w = word.trim().toLowerCase();
            if (w.length() == 0 || w.length() > 40) return "";
            for (int i = 0; i < w.length(); i++) {
                char c = w.charAt(i);
                boolean ok = (c >= 'a' && c <= 'z') || c == '-' || c == ' ' || c == '\'';
                if (!ok) return "";
            }
            try {
                byte[] data = readAll(getAssets().open("www/audio/" + w + ".mp3"));
                return android.util.Base64.encodeToString(data, android.util.Base64.NO_WRAP);
            } catch (Throwable t) {
                return "";
            }
        }
    }

    /**
     * 直接由 Java 把 index.html 读成字符串再交给 WebView。
     * 不依赖 WebView 自己对 file:///android_asset/ 的路径解析，
     * 避免个别 ROM（如 vivo OriginOS）解析失败导致 ERR_FILE_NOT_FOUND。
     * baseUrl 仍用虚拟域名，保证 origin 固定、相对路径与 localStorage 正常。
     */
    private void loadApp() {
        String html;
        try {
            html = readAsset("www/index.html");
        } catch (Throwable t) {
            showDiagnostics(t);
            return;
        }
        web.loadDataWithBaseURL(BASE_URL, html, "text/html", "utf-8", null);
    }

    private String readAsset(String path) throws IOException {
        InputStream in = getAssets().open(path);
        try {
            byte[] data = readAll(in);
            return new String(data, "UTF-8");
        } finally {
            try { in.close(); } catch (IOException ignored) { }
        }
    }

    /** 读不到资源时，把 assets 实际结构显示出来，便于定位 */
    private void showDiagnostics(Throwable t) {
        StringBuilder sb = new StringBuilder();
        sb.append("页面资源读取失败\n\n");
        sb.append(t.toString()).append("\n\n");

        sb.append("assets 根目录：\n");
        try {
            for (String s : getAssets().list("")) sb.append("  ").append(s).append("\n");
        } catch (Throwable e) {
            sb.append("  读取失败 ").append(e).append("\n");
        }

        sb.append("\nassets/www 目录：\n");
        try {
            String[] list = getAssets().list("www");
            if (list == null || list.length == 0) {
                sb.append("  （空）\n");
            } else {
                int n = 0;
                for (String s : list) {
                    if (n++ >= 30) { sb.append("  …\n"); break; }
                    sb.append("  ").append(s).append("\n");
                }
            }
        } catch (Throwable e) {
            sb.append("  读取失败 ").append(e).append("\n");
        }

        TextView tv = new TextView(this);
        tv.setText(sb.toString());
        tv.setTextSize(12f);
        tv.setPadding(36, 80, 36, 36);
        tv.setTextIsSelectable(true);
        setContentView(tv);
    }

    /** 只放行内部导航；其余交给系统浏览器 */
    private boolean handleNav(Uri uri) {
        if (uri == null) return true;
        if (HOST.equals(uri.getHost())) return false;                 // 虚拟域名内部资源
        String s = uri.toString();
        if (s.startsWith("file:///android_asset/")) return false;      // 内部资源
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (Exception ignored) {
            // 没有可处理的 App，忽略，避免崩溃
        }
        return true;
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
