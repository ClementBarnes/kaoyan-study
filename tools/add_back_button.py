# -*- coding: utf-8 -*-
"""为考研站所有 HTML 页面注入统一导航浮窗（右下角双按钮）：
- 子页面：← 目录（站内返回 index.html / ../index.html）+ 🏠 主页（返回个人门户 href="/"）
- 导航页 index.html：仅 🏠 主页（它自己就是目录）
返回门户一律绝对路径 href="/"（https://ClementBarnes.github.io/，见《考研对话交接提示词》契约）。
幂等：先彻底清除所有 nav-fab/back-home/go-home 痕迹，再注入唯一一份。
运行：python -B tools/add_back_button.py
"""
import os, re

dirs = [
    r"C:\Users\cyql0\WorkBuddy\2026-08-04-00-52-59\online",
    r"C:\Users\cyql0\WorkBuddy\2026-08-04-00-52-59",
]
# 部署目录集合（os.walk 根目录时禁止递归进 online/，避免二次处理覆盖）
skip_roots = {os.path.normpath(x) for x in dirs}

new_style = """<style>
  .nav-fab{position:fixed;right:18px;bottom:18px;z-index:9999;display:flex;gap:10px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
  .nav-fab a{display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;box-shadow:0 4px 14px rgba(0,0,0,.22)}
  .nav-fab a:active{transform:scale(.96)}
  .nav-fab .back-home{background:#2C2C2A;color:#fff}
  .nav-fab .go-home{background:#085041;color:#fff}
  @media(max-width:600px){.nav-fab{right:12px;bottom:12px;gap:8px}.nav-fab a{padding:9px 13px;font-size:13px}}
</style>
"""

def sanitize(content):
    """彻底清除所有导航浮窗痕迹，返回干净的 HTML（不注入）。"""
    # 1) 删除完整 nav-fab 样式块
    content = re.sub(r'<style>\s*\.nav-fab.*?</style>', '', content, flags=re.S)
    # 2) 删除旧 back-home/go-home 独立样式块（以 .back-home 或 .go-home 开头的 style 块）
    content = re.sub(r'<style>\s*\.(?:back-home|go-home).*?</style>', '', content, flags=re.S)
    # 3) 删除散落在主样式里的旧规则（负向后顾：排除 .nav-fab 前缀后的 .back-home/.go-home）
    content = re.sub(r'(?<!\.nav-fab )\.go-home[^{}]*\{[^{}]*\}', '', content)
    content = re.sub(r'(?<!\.nav-fab )\.back-home[^{}]*\{[^{}]*\}', '', content)
    content = re.sub(r'@media\(max-width:600px\)\{[^{}]*\.(?:back-home|go-home)[^{}]*\{[^{}]*\}[^{}]*\}', '', content)
    # 4) 删除导航浮窗按钮容器与旧单按钮
    content = re.sub(r'\s*<div class="nav-fab">.*?</div>', '', content, flags=re.S)
    content = re.sub(r'\s*<a href="(?:\.\./)?index\.html" class="back-home"[^>]*>.*?</a>', '', content, flags=re.S)
    content = re.sub(r'\s*<a href="/" class="go-home"[^>]*>.*?</a>', '', content, flags=re.S)
    # 5) 清理空 style 块与残留空 media query
    content = re.sub(r'@media\(max-width:600px\)\{\}', '', content)
    content = re.sub(r'<style>\s*</style>', '', content)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content

for d in dirs:
    for root, subdirs, files in os.walk(d):
        if '.git' in root:
            continue
        # 递归进根目录时，跳过其他部署目录（避免 online/ 被二次处理）
        subdirs[:] = [s for s in subdirs
                      if os.path.normpath(os.path.join(root, s)) not in skip_roots]
        for fn in sorted(files):
            if not fn.lower().endswith('.html'):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, d)
            is_nav = (rel.lower() == 'index.html')          # 目录根下的 index.html = 导航页
            is_sub = (os.path.dirname(rel) != '')           # 在子目录里（如 sync/）

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            orig = content
            content = sanitize(content)

            # 注入新样式（放在 </head> 前）
            if '</head>' in content:
                content = content.replace('</head>', new_style + '</head>', 1)

            # 注入按钮（放在 <body> 后）
            if '<body' in content:
                if is_nav:
                    btn = '\n<div class="nav-fab"><a href="/" class="go-home" title="返回个人主页">🏠 主页</a></div>\n'
                else:
                    back = '../index.html' if is_sub else 'index.html'
                    btn = (f'\n<div class="nav-fab"><a href="{back}" class="back-home" title="返回考研备考中心首页">← 目录</a>'
                           f'<a href="/" class="go-home" title="返回个人主页">🏠 主页</a></div>\n')
                content = re.sub(r'<body[^>]*>', lambda m: m.group(0) + btn, content, count=1)

            if content != orig:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print('updated:', rel)
            else:
                print('ok     :', rel)

print('DONE')
