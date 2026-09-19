# -*- coding: utf-8 -*-
"""生成『新词日单词区小样』：内容套用第10批（8.20 Day15 昨天学的那批），
排版按《单词总表》词根块样式 + 复习日同款 🔊 发音按钮，供用户确认新词日样式。"""
import re, io

doc = open("单词总表.html", encoding="utf-8").read()
start = doc.find("id='batch-b10'")
end = doc.find("id='batch-b11'")
if end < 0:
    end = doc.find("<footer")
batch = doc[start:end]

def clean(s):
    return re.sub(r"<[^>]+>", "", s).strip()

roots = []
for r in re.findall(r"<div class='root'[^>]*>(.*?)(?=<div class='root'|$)", batch, re.S):
    rt = re.search(r"<div class='rt'[^>]*>(.*?)<span class='mean'>(.*?)</span>", r, re.S)
    hook = re.search(r"<p class='hook'>(.*?)</p>", r, re.S)
    words = []
    for w in re.findall(r"<div class='w'>(.*?)</div>", r, re.S):
        b = re.search(r"<b>([^<]+)</b>", w)
        ipa = re.search(r"<span class='ipa'>(.*?)</span>", w)
        brk = re.search(r"<span class='brk'>(.*?)</span>", w)
        ex = re.search(r"<span class='ex'>例：(.*?)</span>", w)
        # 词义 = ipa 之后、brk 之前；若 brk 缺失则到 ex 前
        core = w
        if ex: core = core[:ex.start()]
        if brk: core = core[:brk.start()]
        if ipa: core = core[ipa.end():]
        meaning = clean(core)
        words.append({
            "w": b.group(1) if b else "?",
            "ipa": clean(ipa.group(1)) if ipa else "",
            "meaning": meaning,
            "brk": clean(brk.group(1)) if brk else "",
            "ex": clean(ex.group(1)) if ex else "",
        })
    roots.append({
        "rt": clean(rt.group(1)) if rt else "?",
        "mean": clean(rt.group(2)) if rt else "?",
        "hook": clean(hook.group(1)) if hook else "?",
        "words": words,
    })

# 配色（第10批 = indigo）
C = "#4338ca"

cards = []
for ri, r in enumerate(roots):
    cards.append(f"<div class='root' style='border-left-color:{C}'>")
    cards.append(f"<div class='rt' style='color:{C}'>{r['rt']} <span class='mean'>= {r['mean']}</span></div>")
    cards.append(f"<p class='hook'>{r['hook']}</p>")
    for w in r["words"]:
        cards.append(
            f"<div class='w'><button class='spk' data-w=\"{w['w']}\" title='播放发音'>🔊</button>"
            f"<span class='wmain'><b>{w['w']}</b><span class='ipa'>{w['ipa']}</span>"
            f"<span class='mean2'>{w['meaning']}</span>"
            f"<span class='brk'>{w['brk']}</span></span>"
            f"<span class='ex'>例：{w['ex']}</span></div>"
        )
    cards.append("</div>")

page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>新词日单词区小样 · 第10批</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:#f4f6fb; color:#1f2937; line-height:1.7; padding:20px; }
  .wrap { max-width:820px; margin:0 auto; background:#fff; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,.06); overflow:hidden; }
  .head { background:linear-gradient(135deg,#7c3aed,#4c1d95); color:#fff; padding:22px 26px; }
  .head .day { font-size:13px; opacity:.85; letter-spacing:1px; }
  .head h1 { font-size:21px; margin-top:4px; }
  .head .focus { margin-top:10px; display:inline-block; background:rgba(255,255,255,.18); padding:5px 13px; border-radius:999px; font-size:13px; }
  .body { padding:20px 26px 28px; }
  .tip { background:#f5f3ff; border:1px solid #ddd6fe; border-radius:10px; padding:12px 14px; font-size:14px; color:#5b21b6; margin-bottom:14px; }
  .root { border:1px solid #e5e7eb; border-left:6px solid #999; border-radius:8px; padding:12px 16px; margin:14px 0; background:#fff; }
  .rt { font-weight:700; font-size:15.5px; margin-bottom:2px; }
  .mean { font-weight:400; color:#374151; }
  .hook { background:#fff7ed; border-left:3px solid #f59e0b; padding:6px 11px; margin:8px 0; border-radius:4px; font-size:13.5px; color:#9a3412; }
  .w { padding:7px 0; border-bottom:1px dashed #eef0f2; font-size:14px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
  .w:last-child { border-bottom:none; }
  .w b { color:#111827; font-size:14.5px; }
  .ipa { color:#6b7280; font-style:italic; margin:0 4px; font-size:12.5px; }
  .mean2 { color:#374151; }
  .brk { color:#b45309; font-size:13px; }
  .ex { display:block; width:100%; color:#6b7280; margin-top:2px; font-size:12.5px; padding-left:40px; }
  .spk { width:30px; height:30px; border:1px solid #bbf7d0; background:#f0fdf4; border-radius:50%; cursor:pointer; font-size:14px; line-height:1; flex-shrink:0; transition:transform .12s; }
  .spk:hover { background:#dcfce7; }
  .spk:active { transform:scale(.9); }
  .spk.playing { background:#4ade80; }
  .wmain { display:flex; align-items:baseline; gap:6px; flex-wrap:wrap; flex:1; min-width:0; }
</style><style>
  .back-home{position:fixed;right:18px;bottom:18px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:10px 16px;background:#2C2C2A;color:#fff;font-size:14px;font-weight:600;text-decoration:none;border-radius:999px;box-shadow:0 4px 14px rgba(0,0,0,.22);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
  .back-home:active{transform:scale(.96)}
  @media(max-width:600px){.back-home{padding:9px 13px;font-size:13px;right:12px;bottom:12px}}
</style>
</head>
<body>
<a href="index.html" class="back-home" title="返回备考中心首页">← 目录</a>

<div class="wrap">
  <div class="head">
    <div class="day">小样 · 新词日单词区排版（内容套用 8.20 第10批）</div>
    <h1>新词日单词区 · 样式预览</h1>
    <div class="focus">排版：词根块（词根+含义+钩子）→ 每词一行「🔊 + 单词 + 音标 + 词义 + 拆解 + 例句」</div>
  </div>
  <div class="body">

    <div class="tip">💡 这就是新词日单词区的<b>排版方案</b>：沿用《单词总表》的词根块结构（左色条 + 词根含义 + 记忆钩子），每词一行六要素——🔊发音按钮 / 单词 / 音标 / 词义 / <b>结构拆解（与总表同款，辅助记忆）</b> / 例句（英+中，与音频逐字一致）。点击 🔊 试听。下面内容直接套用了昨天（8.20 · 第10批）的 20 词，只为看排版效果。</div>

""" + "\n".join(cards) + """

    <div class="tip">📌 <b>与本批配套的「单词阅读」环节不变</b>：正式背单词前，先开《单词总表.html》点本批「▶ 联播本批」听一遍建立印象，再回到学习单用本排版逐词精学。发音按钮点按即听，单播互斥、从头重播。</div>

  </div>
</div>
<script>
(function(){
  var cur = null, curBtn = null;
  var btns = document.querySelectorAll('.spk');
  btns.forEach(function(btn){
    btn.addEventListener('click', function(){
      var w = btn.getAttribute('data-w');
      if (cur) { cur.pause(); if (curBtn) curBtn.classList.remove('playing'); }
      cur = new Audio('audio/' + w + '.mp3');
      curBtn = btn;
      cur.currentTime = 0;
      btn.classList.add('playing');
      cur.play().catch(function(){ btn.classList.remove('playing'); });
      cur.addEventListener('ended', function(){ btn.classList.remove('playing'); cur = null; curBtn = null; });
    });
  });
})();
</script>
</body>
</html>
"""

with io.open("新词日单词区小样.html", "w", encoding="utf-8") as f:
    f.write(page)
print("OK: 新词日单词区小样.html bytes=", len(page.encode("utf-8")))
print("词根块:", len(roots), "| 单词总数:", sum(len(r["words"]) for r in roots))
