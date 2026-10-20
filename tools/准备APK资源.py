# -*- coding: utf-8 -*-
"""
准备 APK 打包资源：把单词卡 + 音频 + 图标整理到 android/app/src/main/assets/www/
同时生成 Android 各密度启动图标（mipmap-*）
"""
import os
import shutil
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "android", "app", "src", "main")
ASSETS = os.path.join(APP, "assets", "www")
RES = os.path.join(APP, "res")

BG_TOP = (24, 95, 165)
BG_BOT = (12, 62, 112)
FONT_REG = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_ALT = r"C:\Windows\Fonts\simhei.ttf"

# 音频 385 个，共 ~19MB，全量打进 APK，保证离线可听
AUDIO_DIRS = [os.path.join(ROOT, "audio")]


def font(size):
    for p in (FONT_REG, FONT_ALT):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def grad(w, h):
    img = Image.new("RGB", (w, h), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)],
               fill=tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3)))
    return img


def make(size, pad_ratio=0.0, bg=True, glyph_ratio=0.40, sub_ratio=0.26):
    """pad_ratio>0 时四周留白（自适应图标前景用）"""
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = int(size * (1 - pad_ratio * 2))
    if bg:
        b = grad(inner, inner).convert("RGBA")
        d0 = ImageDraw.Draw(b)
        d0.rounded_rectangle([0, 0, inner - 1, inner - 1],
                             radius=int(inner * 0.18), fill=None)
        canvas.paste(b, ((size - inner) // 2, (size - inner) // 2), b)
    d = ImageDraw.Draw(canvas)

    off = (size - inner) // 2
    # 卡片质感
    ci = int(inner * 0.26)
    ov = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(
        [off + ci, off + ci, off + inner - ci, off + inner - ci],
        radius=int(inner * 0.12), fill=(255, 255, 255, 30))
    canvas = Image.alpha_composite(canvas, ov)
    d = ImageDraw.Draw(canvas)

    f = font(int(inner * glyph_ratio))
    bb = d.textbbox((0, 0), "研", font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((size - tw) / 2 - bb[0], (size - th) / 2 - bb[1] - inner * 0.02),
           "研", font=f, fill=(255, 255, 255, 255))

    f2 = font(int(inner * sub_ratio))
    bb2 = d.textbbox((0, 0), "词", font=f2)
    tw2, th2 = bb2[2] - bb2[0], bb2[3] - bb2[1]
    d.text((size - tw2 - inner * 0.12 - bb2[0],
            size - th2 - inner * 0.10 - bb2[1]),
           "词", font=f2, fill=(255, 255, 255, 205))
    return canvas


DENSITIES = {
    "mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192
}
FG_DENSITIES = {
    "mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432
}


def build_icons():
    for dens, sz in DENSITIES.items():
        d = os.path.join(RES, "mipmap-" + dens)
        os.makedirs(d, exist_ok=True)
        ic = make(sz, bg=True)
        ic.save(os.path.join(d, "ic_launcher.png"), "PNG", optimize=True)
        ic.save(os.path.join(d, "ic_launcher_round.png"), "PNG", optimize=True)
        # 圆形裁切
        circ = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        ImageDraw.Draw(circ).ellipse([0, 0, sz - 1, sz - 1], fill=(255, 255, 255, 255))
        circ.putalpha(Image.composite(circ.getchannel("A"),
                                       Image.new("L", (sz, sz), 0),
                                       circ.getchannel("A")))
        rc = Image.new("RGBA", (sz, sz), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rc)
        rd.ellipse([0, 0, sz - 1, sz - 1], fill=(255, 255, 255, 255))
        rounded = Image.composite(ic, Image.new("RGBA", (sz, sz), (0, 0, 0, 0)), rc.getchannel("A"))
        rounded.save(os.path.join(d, "ic_launcher_round.png"), "PNG", optimize=True)

    for dens, sz in FG_DENSITIES.items():
        d = os.path.join(RES, "mipmap-" + dens)
        os.makedirs(d, exist_ok=True)
        # 自适应图标前景：安全区为中间 66%，图形缩到 ~55%
        fg = make(sz, pad_ratio=0.22, bg=False, glyph_ratio=0.30, sub_ratio=0.20)
        fg.save(os.path.join(d, "ic_launcher_foreground.png"), "PNG", optimize=True)
    print("启动图标生成完毕")


def copy_www():
    if os.path.isdir(ASSETS):
        shutil.rmtree(ASSETS)
    os.makedirs(ASSETS)

    # 单词卡主页面
    shutil.copy2(os.path.join(ROOT, "单词卡.html"),
                 os.path.join(ASSETS, "index.html"))

    # manifest（APK 内不需要，但页面引用了，避免 404 报错）
    shutil.copy2(os.path.join(ROOT, "manifest.webmanifest"),
                 os.path.join(ASSETS, "manifest.webmanifest"))

    # 图标
    shutil.copytree(os.path.join(ROOT, "icons"),
                    os.path.join(ASSETS, "icons"),
                    dirs_exist_ok=True)

    # 音频：全量
    n = 0
    total = 0
    for src in AUDIO_DIRS:
        if not os.path.isdir(src):
            continue
        dst = os.path.join(ASSETS, "audio")
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            if f.lower().endswith(".mp3"):
                shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
                n += 1
                total += os.path.getsize(os.path.join(dst, f))
    print("音频复制: %d 个, %.1f MB" % (n, total / 1048576))

    # 打包进 APK 后音频要改成相对路径
    p = os.path.join(ASSETS, "index.html")
    with open(p, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("var AUDIO_MODE = 'gh';", "var AUDIO_MODE = 'rel';")

    # APK 内本身就是 app，不再显示安装引导。
    # 走虚拟 https 域名（appassets.androidplatform.net），原 file:// 判断已不适用
    old_guard = "if(standalone || localStorage.getItem('instDismissed')==='1') return;"
    new_guard = ("if(standalone || location.hostname==='appassets.androidplatform.net' "
                 "|| location.protocol.indexOf('file')===0 "
                 "|| localStorage.getItem('instDismissed')==='1') return;")
    assert old_guard in html, "安装横幅守卫锚点未找到，页面结构可能已变"
    html = html.replace(old_guard, new_guard)

    # APK 内 385 个音频已全部内置，「缓存本批音频」按钮点了只会失败，直接隐藏
    assert "</style>" in html, "样式块锚点未找到"
    html = html.replace("</style>", ".dlbox{display:none!important}</style>", 1)

    # APK 内资源本地化，Service Worker 无意义且 sw.js 未打包，会持续 404
    sw_reg = "navigator.serviceWorker.register('sw.js').catch(function(){});"
    assert sw_reg in html, "Service Worker 注册锚点未找到"
    html = html.replace(sw_reg, "/* APK: 本地资源，无需 Service Worker */")

    with open(p, "w", encoding="utf-8") as f:
        f.write(html)
    print("APK 版 index.html 已切换为本地音频模式 + 隐藏安装引导/缓存按钮 + 关闭 SW 注册")
    return n


if __name__ == "__main__":
    build_icons()
    copy_www()
    # 体积统计
    tot = 0
    for dp, dn, fn in os.walk(ASSETS):
        for f in fn:
            tot += os.path.getsize(os.path.join(dp, f))
    print("assets 总体积: %.1f MB" % (tot / 1048576))
