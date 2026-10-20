# -*- coding: utf-8 -*-
"""
生成考研单词卡 App 图标（PWA + Android APK 共用）
输出：
  icons/icon-192.png          普通图标
  icons/icon-512.png          普通图标
  icons/icon-maskable-192.png  Android 自适应图标（含安全边距）
  icons/icon-maskable-512.png
  icons/apple-touch-icon.png  iOS 主屏图标 180x180
  icons/favicon-32.png
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icons")
os.makedirs(OUT, exist_ok=True)

BG_TOP = (24, 95, 165)      # #185FA5 主题蓝
BG_BOT = (12, 62, 112)
GLYPH = (255, 255, 255)

FONT_REG = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_ALT = r"C:\Windows\Fonts\simhei.ttf"


def font(size):
    for p in (FONT_REG, FONT_ALT):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def vertical_gradient(w, h):
    img = Image.new("RGB", (w, h), BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=c)
    return img


def make_icon(size, maskable=False):
    """maskable=True 时图形缩到安全区（中心 80%），四周留白由系统裁切"""
    img = vertical_gradient(size, size).convert("RGBA")
    d = ImageDraw.Draw(img)

    # 圆角方块背景（非 maskable 时才有圆角；maskable 要满幅）
    if not maskable:
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1],
                                               radius=int(size * 0.22), fill=255)
        img.putalpha(mask)
        d = ImageDraw.Draw(img)

    # 内层半透明白色卡片，模拟卡片感
    inset = int(size * (0.26 if maskable else 0.20))
    card_alpha = 34
    ov = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rounded_rectangle([inset, inset, size - inset, size - inset],
                         radius=int(size * 0.12), fill=(255, 255, 255, card_alpha))
    img = Image.alpha_composite(img, ov)
    d = ImageDraw.Draw(img)

    # 主字「研」
    fs = int(size * (0.40 if maskable else 0.46))
    f = font(fs)
    text = "研"
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) / 2 - bbox[0]
    y = (size - th) / 2 - bbox[1] - size * 0.02
    d.text((x, y), text, font=f, fill=GLYPH)

    # 副字「词」小一号，贴右下
    fs2 = int(size * (0.26 if maskable else 0.30))
    f2 = font(fs2)
    bbox2 = d.textbbox((0, 0), "词", font=f2)
    tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    x2 = size - tw2 - size * (0.16 if maskable else 0.12) - bbox2[0]
    y2 = size - th2 - size * (0.13 if maskable else 0.10) - bbox2[1]
    d.text((x2, y2), "词", font=f2, fill=(255, 255, 255, 205))

    return img


def save(img, name, size):
    p = os.path.join(OUT, name)
    img.convert("RGB").save(p, "PNG", optimize=True)
    print("生成", name, size, str(os.path.getsize(p)) + "B")


if __name__ == "__main__":
    save(make_icon(192), "icon-192.png", 192)
    save(make_icon(512), "icon-512.png", 512)
    save(make_icon(192, True), "icon-maskable-192.png", 192)
    save(make_icon(512, True), "icon-maskable-512.png", 512)
    save(make_icon(180), "apple-touch-icon.png", 180)
    save(make_icon(32), "favicon-32.png", 32)
    print("图标目录:", OUT)
