/* 考研单词卡 Service Worker
 * 作用：把页面壳和「缓存过的整批音频」留在本地，之后断网也能刷词+听音。
 *
 * 设计要点（2026-10-20 实测后调整）：
 *  1) 音频来自 https://clementbarnes.github.io（跨源），不能只判同源，
 *     要按 pathname 是否含 /kaoyan-study/audio/ 来识别。
 *  2) 音频走 cache-first —— 单词音频是不可变资源，缓存命中就秒回。
 *  3) 页面壳走 stale-while-revalidate —— 秒开，同时后台拉新版。
 *  4) 缓存分两个：ky-shell-v2（壳）与 ky-audio-v1（音频），互不驱逐。
 */
var SHELL_CACHE = 'ky-shell-v2';
var AUDIO_CACHE = 'ky-audio-v1';

var SHELL = ['./', './index.html', './单词卡.html', './manifest.webmanifest'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(SHELL_CACHE)
      .then(function (c) { return c.addAll(SHELL).catch(function () {}); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        /* 音频缓存必须保留，只清理旧版壳缓存和其他 ky-* */
        if (k === AUDIO_CACHE) return null;
        if (k === SHELL_CACHE) return null;
        if (k.indexOf('ky-') === 0 || k.indexOf('kaoyan') === 0) return caches.delete(k);
        return null;
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function isAudio(url) {
  return /\.mp3(\?|$)/.test(url.pathname) || /\/kaoyan-study\/audio\//.test(url.pathname);
}

function isShell(url) {
  return /\/([^\/]*(单词卡|index|manifest|sw)[^\/]*)$/.test(url.pathname);
}

self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;

  var url;
  try { url = new URL(req.url); } catch (err) { return; }

  /* ---- 音频：cache-first ---- */
  if (isAudio(url)) {
    e.respondWith(
      caches.open(AUDIO_CACHE).then(function (c) {
        return c.match(req, { ignoreVary: true }).then(function (hit) {
          if (hit) return hit;
          return fetch(req).then(function (res) {
            /* 跨源 no-cors 是 opaque 响应（status 0），同样可以存 */
            if (res && (res.status === 200 || res.type === 'opaque')) {
              var copy = res.clone();
              c.put(req, copy).catch(function () {});
            }
            return res;
          }).catch(function () {
            /* 离线且未缓存：返回空响应，让页面走 onerror 提示而不是整页崩 */
            return new Response('', { status: 504, statusText: 'offline' });
          });
        });
      })
    );
    return;
  }

  /* ---- 页面壳：stale-while-revalidate ---- */
  if (isShell(url) || req.mode === 'navigate') {
    e.respondWith(
      caches.open(SHELL_CACHE).then(function (c) {
        return c.match(req).then(function (hit) {
          var net = fetch(req).then(function (res) {
            if (res && res.status === 200 && res.type === 'basic') {
              var copy = res.clone();
              c.put(req, copy).catch(function () {});
            }
            return res;
          }).catch(function () {
            return hit || new Response('离线且未缓存，请联网打开一次', {
              status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' }
            });
          });
          return hit || net;
        });
      })
    );
  }
});