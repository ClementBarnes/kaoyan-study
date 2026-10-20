# -*- coding: utf-8 -*-
"""
精确模拟 APK 内的运行环境：
  自签证书 + 本地 HTTPS 服务，域名 appassets.androidplatform.net 指向 127.0.0.1
  这样浏览器 origin 与 APK 里 WebView 的 origin 完全一致，
  可验证：localStorage、相对路径音频、安装横幅隐藏、缓存按钮隐藏。

输出探测结果到 DOM，供 dump-dom 抓取。
"""
import http.server
import ssl
import os
import re
import subprocess
import socketserver
import threading

ROOT = r"C:\tmp\apkcheck"          # 含 www/ 子目录，精确对应 assets/ 结构
WWW = os.path.join(ROOT, "www")
CERT = r"C:\tmp\apkcheck\cert.pem"
KEY = r"C:\tmp\apkcheck\key.pem"
PORT = 8443
HOST = "appassets.androidplatform.net"


def make_cert():
    if os.path.exists(CERT) and os.path.exists(KEY):
        return
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", KEY, "-out", CERT, "-days", "1",
        "-subj", "/CN=" + HOST,
        "-addext", "subjectAltName=DNS:" + HOST
    ], check=True, capture_output=True)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def log_message(self, *a):
        pass

    def do_GET(self):
        # 支持 Range，模拟 APK 里 serve() 的行为
        path = self.translate_path(self.path)
        if not os.path.isfile(path):
            self.send_error(404)
            return
        rng = self.headers.get("Range")
        size = os.path.getsize(path)
        ctype = self.guess_type(path)
        if rng and rng.startswith("bytes="):
            spec = rng[6:].split(",")[0].strip()
            a, _, b = spec.partition("-")
            start = int(a) if a else max(0, size - int(b))
            end = int(b) if (b and a) else size - 1
            end = min(end, size - 1)
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
            self.send_header("Content-Length", str(length))
            self.end_headers()
            with open(path, "rb") as f:
                f.seek(start)
                self.wfile.write(f.read(length))
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        with open(path, "rb") as f:
            self.wfile.write(f.read())


def main():
    make_cert()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)

    httpd = socketserver.TCPServer(("127.0.0.1", PORT), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    print("HTTPS 已启动: https://%s:%d/" % (HOST, PORT))

    # 探针页：写入真实 APK 页面，附加检测脚本
    with open(os.path.join(WWW, "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    probe = """
<div id="__out" style="position:fixed;bottom:0;left:0;font-size:10px">RUN</div>
<script>
(function(){
  var r=[];
  function t(n,fn){ try{ r.push(n+'='+fn()); }catch(e){ r.push(n+'=THROW('+(e&&e.name)+')'); } }
  t('origin', function(){ return location.origin; });
  t('ls.write', function(){ localStorage.setItem('__p','1'); return 'ok'; });
  t('ls.read', function(){ return localStorage.getItem('__p'); });
  t('word', function(){ return (document.getElementById('word')||{}).textContent; });
  t('root', function(){ return (document.getElementById('rootline')||{}).textContent; });
  t('stat', function(){ return (document.getElementById('stat')||{}).textContent; });
  t('instbarShown', function(){
     var b=document.getElementById('instbar');
     return b ? getComputedStyle(b).display : 'no-node';
  });
  t('dlboxShown', function(){
     var d=document.querySelector('.dlbox');
     return d ? getComputedStyle(d).display : 'no-node';
  });
  var a=new Audio('audio/inspect.mp3');
  var done=false;
  a.addEventListener('canplaythrough',function(){
    if(done) return; done=true;
    r.push('audio=ok('+(Math.round(a.duration*10)/10)+'s)');
    document.getElementById('__out').textContent='RESULT '+r.join(' | ');
  });
  a.addEventListener('error',function(){
    if(done) return; done=true;
    r.push('audio=ERROR');
    document.getElementById('__out').textContent='RESULT '+r.join(' | ');
  });
  setTimeout(function(){
    if(!done){ done=true; r.push('audio=TIMEOUT');
      document.getElementById('__out').textContent='RESULT '+r.join(' | '); }
  }, 8000);
  a.load();
})();
</script>
"""
    with open(os.path.join(WWW, "__apk_probe.html"), "w", encoding="utf-8") as f:
        f.write(html.replace("</body>", probe + "</body>"))

    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    # 与 APK 内部入口完全一致：/www/index.html 同目录
    url = "https://%s:%d/www/__apk_probe.html" % (HOST, PORT)
    p = subprocess.run([
        edge, "--headless=new", "--disable-gpu", "--no-sandbox",
        "--ignore-certificate-errors",
        "--host-resolver-rules=MAP %s 127.0.0.1" % HOST,
        "--user-data-dir=C:\\tmp\\apkcheck\\prof2",
        "--autoplay-policy=no-user-gesture-required",
        "--virtual-time-budget=12000", "--dump-dom", url
    ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)

    dom = p.stdout or ""
    m = re.search(r'id="__out"[^>]*>([^<]*)<', dom)
    print("探测结果:", m.group(1) if m else "(未捕获)")
    httpd.shutdown()


if __name__ == "__main__":
    main()
