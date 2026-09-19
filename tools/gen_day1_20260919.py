# -*- coding: utf-8 -*-
"""生成二次重启 Day1 学习单（2026-09-19 · 重学第01批 27 词 · 本地版）。

数据源：words_tts.json（batch==1）；词根族与拆解沿用 8-27 重启已验证数据。
运行：python -B tools/gen_day1_20260919.py  （CWD = 仓库根）
"""
import json, os, sys

data = json.load(open('words_tts.json', encoding='utf-8'))
b1 = [d for d in data if d.get('batch') == 1]
assert len(b1) == 27, f'batch1 words = {len(b1)} != 27'

brk = {
 'inspect':'in-(往里) + spect(看) → 往里看 = 检查',
 'respect':'re-(再/回) + spect(看) → 看重 = 尊重',
 'expect':'ex-(出/外) + spect(看) → 往外看 = 期待',
 'aspect':'a-(朝向) + spect(看) → 看向的一面 = 方面',
 'prospect':'pro-(前) + spect(看) → 向前看 = 前景',
 'perspective':'per-(透过) + spect(看) + -ive → 透过的看法 = 视角',
 'import':'im-(入) + port(运) → 运入 = 进口',
 'export':'ex-(出) + port(运) → 运出 = 出口',
 'transport':'trans-(跨) + port(运) → 转运 = 运输',
 'report':'re-(回) + port(带) → 带回 = 报告',
 'support':'sup-(下) + port(托) → 在下面托 = 支持',
 'portable':'port(带) + -able → 可带的 = 便携',
 'dictate':'dict(说) + -ate → 口述 / 命令',
 'predict':'pre-(前) + dict(说) → 预先说 = 预测',
 'contradict':'contra-(反) + dict(说) → 反着说 = 反驳',
 'indicate':'in-(入) + dic(说) + -ate → 说进去 = 指示/表明',
 'dedicate':'de-(向下/加强) + dic(说) + -ate → 说下去(献) = 奉献/致力于',
 'admit':'ad-(向) + mit(送) → 送进 = 承认',
 'commit':'com-(一起) + mit(送) → 一起送 = 承诺/犯',
 'permit':'per-(通过) + mit(送) → 送过 = 允许',
 'submit':'sub-(下) + mit(送) → 送下 = 提交',
 'mission':'miss(派) + -ion → 被派的 = 任务',
 'dismiss':'dis-(离) + miss(送) → 送走 = 解散/解雇',
 'structure':'struct(建) + -ure → 结构/建筑物',
 'construct':'con-(一起) + struct(建) → 一起建 = 建造',
 'instruct':'in-(入) + struct(建) → 建入(灌输) = 指导',
 'destroy':'de-(毁) + stroy(struct变体) → 拆毁 = 摧毁',
}
fam = [
 ('-spect / -spic','看（look / see）','#0e7490','都和"看/视野"有关：in-往里看=检查，re-再看重=尊重，ex-往外看=期待，per-透过看=视角，pro-往前看=前景'),
 ('-port','拿/运/带（carry）','#7c3aed','拿/运/带：im-运入=进口，ex-运出=出口，trans-转运=运输，re-往回带=报告，sup-在下托=支持，portable 可携带'),
 ('-dict / -dic','说（say / tell）','#d97706','说：dict-说，pre-预先说=预言，contra-反着说=反驳，in-说进去=指，de-说下去=奉献'),
 ('-mit / -miss','送/派（send）','#be123c','送/派：ad-送进=承认，com-一起送=承诺，per-送过=允许，sub-送下去=提交，mission 任务，dis-送走=解散'),
 ('-struct','建造（build）','#15803d','建造：structure 结构，con-一起建=建造，in-建进去=指导，de-拆建=摧毁'),
]
# 音频存在性校验（本地版硬要求）
missing = [d['word'] for d in b1 if not os.path.exists(f"audio/{d['word']}.mp3")]
assert not missing, f'缺音频: {missing}'

words_by_root = {}
for d in b1:
    words_by_root.setdefault(d['root'], []).append(d)
roots_in_data = list(words_by_root)
assert len(roots_in_data) == 5, f'族数 = {len(roots_in_data)} != 5'

def root_block(idx, root, mean_cn, color, hook):
    ws = words_by_root[root]
    L = [f'      <div class="root" style="border-left-color:{color}">']
    L.append(f'        <div class="rt" style="color:{color}">词根 {idx} {root} <span class="mean">= = {mean_cn}</span> <button class="seqFamily" data-fam="{idx}">▶ 本族</button></div>')
    L.append(f'        <p class="hook">钩子：{hook}</p>')
    for d in ws:
        w, ipa, mn = d['word'], d['ipa'], d['meaning']
        exen, exzh, b = d['example_en'], d['example_zh'], brk[w]
        L.append(f'        <div class="w"><button class="spk" data-w="{w}" data-fam="{idx}" title="播放发音">🔊</button><span class="wmain"><b>{w}</b><span class="ipa">{ipa}</span><span class="mean2">{mn}</span><span class="brk">（{b}）</span></span><span class="ex">例：{exen} {exzh}</span></div>')
    L.append('      </div>')
    return '\n'.join(L)

blocks = '\n'.join(root_block(i + 1, *f) for i, f in enumerate(fam))
all_words = ' · '.join(d['word'] for d in b1)
answers = '｜'.join(f"{d['word']} {d['meaning'].split('.')[0].split('，')[0].split(' / ')[0]}" for d in b1)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>今日学习单 · 2026-09-19（Day1 · 重学第01批）</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif; background:#f4f6fb; color:#1f2937; line-height:1.7; padding:20px; }}
  .wrap {{ max-width:820px; margin:0 auto; background:#fff; border-radius:16px; box-shadow:0 4px 24px rgba(0,0,0,.06); overflow:hidden; }}
  .head {{ background:linear-gradient(135deg,#7c3aed,#4c1d95); color:#fff; padding:22px 26px; }}
  .head .day {{ font-size:13px; opacity:.85; letter-spacing:1px; }}
  .head h1 {{ font-size:21px; margin-top:4px; }}
  .head .focus {{ margin-top:10px; display:inline-block; background:rgba(255,255,255,.18); padding:5px 13px; border-radius:999px; font-size:13px; }}
  .body {{ padding:20px 26px 28px; }}
  h3 {{ font-size:16.5px; margin:22px 0 10px; color:#111827; }}
  .sub {{ font-size:13.5px; color:#6b7280; margin-bottom:10px; }}
  .tip {{ background:#f5f3ff; border:1px solid #ddd6fe; border-radius:10px; padding:12px 14px; font-size:14px; color:#5b21b6; margin-bottom:14px; }}
  .week {{ background:#ecfdf5; border:1px solid #a7f3d0; border-radius:10px; padding:12px 14px; font-size:13.5px; color:#065f46; margin-bottom:14px; }}
  .root {{ border:1px solid #e5e7eb; border-left:6px solid #999; border-radius:8px; padding:12px 16px; margin:14px 0; background:#fff; }}
  .rt {{ font-weight:700; font-size:15.5px; margin-bottom:2px; }}
  .mean {{ font-weight:400; color:#374151; }}
  .hook {{ background:#fff7ed; border-left:3px solid #f59e0b; padding:6px 11px; margin:8px 0; border-radius:4px; font-size:13.5px; color:#9a3412; }}
  .w {{ padding:7px 0; border-bottom:1px dashed #eef0f2; font-size:14px; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .w:last-child {{ border-bottom:none; }}
  .w b {{ color:#111827; font-size:14.5px; }}
  .ipa {{ color:#6b7280; font-style:italic; margin:0 4px; font-size:12.5px; }}
  .mean2 {{ color:#374151; }}
  .brk {{ color:#b45309; font-size:13px; }}
  .ex {{ display:block; width:100%; color:#6b7280; margin-top:2px; font-size:12.5px; padding-left:40px; }}
  .spk {{ width:30px; height:30px; border:1px solid #bbf7d0; background:#f0fdf4; border-radius:50%; cursor:pointer; font-size:14px; line-height:1; flex-shrink:0; transition:transform .12s; }}
  .spk:hover {{ background:#dcfce7; }}
  .spk:active {{ transform:scale(.9); }}
  .wmain {{ display:flex; align-items:baseline; gap:6px; flex-wrap:wrap; flex:1; min-width:0; }}
  .ans {{ background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:8px 12px; font-size:13.5px; margin:10px 0; }}
  .ans summary {{ cursor:pointer; font-weight:600; color:#111827; }}
  .sent {{ background:#fff7ed; border-left:3px solid #f59e0b; padding:6px 11px; margin:8px 0; border-radius:4px; font-size:13.5px; color:#9a3412; }}
  .seqBtn,.seqFamily {{ border:none; border-radius:999px; padding:6px 14px; font-size:13px; font-weight:600; cursor:pointer; color:#fff; }}
  .seqBtn {{ background:#7c3aed; }}
  .seqFamily {{ background:#0e7490; font-size:12px; padding:4px 11px; }}
  .on {{ box-shadow:0 0 0 3px rgba(250,204,21,.55); }}
  .nav-fab{{position:fixed;right:18px;bottom:18px;z-index:9999;display:flex;gap:10px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
  .nav-fab a{{display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;box-shadow:0 4px 14px rgba(0,0,0,.22)}}
  .nav-fab a:active{{transform:scale(.96)}}
  .nav-fab .back-home{{background:#2C2C2A;color:#fff}}
  @media(max-width:600px){{.nav-fab{{right:12px;bottom:12px;gap:8px}}.nav-fab a{{padding:9px 13px;font-size:13px}}}}
  @media(min-width:768px){{ body{{padding:28px}} .spk{{width:34px;height:34px}} }}
</style>
</head>
<body>
<div class="nav-fab"><a href="index.html" class="back-home" title="返回考研备考中心目录">← 目录</a></div>

<div class="wrap">
  <div class="head">
    <div class="day">DAY 1 · 2026年9月19日 · 周六 · 累计学习第 1 天（★二次重启 · 本地版）· 🆕 重学第01批</div>
    <h1>今日学习单</h1>
    <div class="focus">重学词根第 01 批 27 词（5 族·看/拿运带/说/送派/建造）＋ 听书联播 ＋ 主动回忆自测(≥90%过关) ＋ micro-writing 输出</div>
  </div>
  <div class="body">

    <div class="week">
      📌 <b>二次重启 · Day1</b>（首学日，预算可放宽至 1.5h；日常考研 ≤1h，公考主线不动）。固定节奏：<b>每周一批、周一启用</b>（第02批 = 9-21 周一）；周日晚自测 &lt;90% → 下周一滞留重学本批；连续 2 周不过关 → 过关线降 85%。三机制强制：自测 / 间隔复习（1/2/4/7/15/30 天）/ 输出倒逼。<br>
      💻 <b>本地学习版</b>：全部内容在本机 D:\\githubprogram\\kaoyan-study，桌面快捷方式直达、无需网络；不再发布 GitHub Pages。
    </div>

    <h3>1. 单词阅读（先听后背）· 15 min</h3>
    <p class="sub">开《<a href="单词总表.html">单词总表</a>》→ 找到第 01 批 → 点「▶ 联播本批」连续听一遍（单词×2 → 词义 → 例句 → 翻译）。先建立听觉印象，再进入精学。这是新词日强制第一环节。</p>

    <h3>2. 新词精学 · 重学第 01 批 27 词（六层格式）· 45 min</h3>
    <p class="sub">每词六要素：🔊 发音 / 单词 / 音标 / 词义 / <b>结构拆解</b>（辅助记忆）/ 例句（英+中，与音频逐字一致）。先听 → 跟读 → 闭眼回忆词义 → 用例句造一句。<b>这是重学不是初学</b>：目标不是"认得"，而是"瞬间反应 + 会用"。</p>
    <div class="tip purple" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">🎧 <b>连续播放</b>：<button id="seqAll" class="seqBtn">▶ 词根联播（按词根顺序·27词）</button> 每个词根块标题后有「▶ 本族」按钮可单族连播；再点一次即停。</div>

{blocks}

    <h3>★ 主动回忆自测（强制环节）· 20 min · 本批正确率 ≥ 90% 才过关</h3>
    <p class="sub">被动听看不算学会。先<b>遮住答案</b>，两种方式逼自己输出：① <b>听音写词</b>——点 🔊 听发音，默写拼写；② <b>遮义回想</b>——看单词，默写中文义 + 例句关键词。27 词错 ≤ 2 个即过关；<b>明晚（9-20 周日）自测不过关 → 9-21 不启用第02批、本批滞留重学</b>。</p>
    <div class="tip purple">📝 自测清单（先别看右侧答案）：<b>{all_words}</b></div>
    <details class="ans"><summary>点开看答案（自测完再对）</summary>
      <p>{answers}</p>
    </details>

    <h3>★ 输出倒逼（强制环节）· 15 min · 用本批词写 micro-writing</h3>
    <p class="sub">学完不"用"一次等于没学。从本批挑 <b>至少 6 个词</b>，写一段 <b>80–120 字</b>小短文（主题任意：学习/工作/生活），或口述 30 秒小故事。以后写作日(管综)也用新词练论证段，双重固化。</p>
    <div class="sent">✍️ 示例框架：用 <i>inspect / expect / aspect / support / construct / perspective</i> 写"我对二次重启备考的看法"——先列骨架，再成段。</div>
    <div class="ans"><b>提交方式</b>：把短文发回对话，按"用词准确 + 搭配自然 + 逻辑通顺"三档反馈；口述可录音自行核对。</div>

    <div class="week" style="margin-top:18px">🌙 <b>晚间回顾</b>：① 回顾第 01 批 27 词，卡壳的再听 1 遍 🔊（尤其 -dict/-dic 族 dict=说 的派生、contradict "反着说=反驳"）；② 自测错词 + micro-writing 过一遍；③ 明日（9-20 周日）= 第01批间隔第1天复习 + 周日晚自测；<b>9-21（周一）启用第 02 批</b>（每周一批节奏）。</div>

  </div>
</div>
<script>
const player = new Audio(); player.preload = 'none';
let curBtn = null, queue = null, qIdx = 0, seqMode = null, seqBtnEl = null;
function playWord(w, btn){{
  if(curBtn === btn && !player.paused){{ player.pause(); curBtn.classList.remove('on'); curBtn = null; return; }}
  if(curBtn) curBtn.classList.remove('on');
  player.src = 'audio/' + encodeURIComponent(w) + '.mp3';
  player.currentTime = 0; player.play();
  curBtn = btn; btn.classList.add('on');
}}
function startSeq(ws, mode, btnEl){{
  if(seqMode === mode){{ player.pause(); seqMode = null; qIdx = 0; if(curBtn) curBtn.classList.remove('on'); if(seqBtnEl) seqBtnEl.classList.remove('on'); seqBtnEl = null; return; }}
  if(seqBtnEl) seqBtnEl.classList.remove('on');
  queue = ws; qIdx = 0; seqMode = mode; seqBtnEl = btnEl; btnEl.classList.add('on');
  const b = document.querySelector('.spk[data-w="' + CSS.escape(ws[0]) + '"]');
  playWord(ws[0], b);
}}
document.querySelectorAll('.spk').forEach(b => b.addEventListener('click', () => {{
  if(seqMode){{ seqMode = null; queue = null; if(seqBtnEl) seqBtnEl.classList.remove('on'); seqBtnEl = null; }}
  playWord(b.dataset.w, b);
}}));
document.getElementById('seqAll').addEventListener('click', function(){{
  const ws = Array.from(document.querySelectorAll('.spk')).map(x => x.dataset.w);
  startSeq(ws, 'all', this);
}});
document.querySelectorAll('.seqFamily').forEach(b => b.addEventListener('click', function(){{
  const ws = Array.from(document.querySelectorAll('.spk[data-fam="' + this.dataset.fam + '"]')).map(x => x.dataset.w);
  startSeq(ws, 'fam' + this.dataset.fam, this);
}}));
player.addEventListener('ended', () => {{
  if(curBtn) curBtn.classList.remove('on');
  if(seqMode && queue && qIdx < queue.length - 1){{
    qIdx++; const b = document.querySelector('.spk[data-w="' + CSS.escape(queue[qIdx]) + '"]');
    playWord(queue[qIdx], b);
  }} else {{ seqMode = null; if(seqBtnEl) seqBtnEl.classList.remove('on'); seqBtnEl = null; }}
}});
</script>
</body>
</html>
'''

open('今日学习单_2026-09-19.html', 'w', encoding='utf-8').write(html)
print('written 今日学习单_2026-09-19.html')
print('words:', len(b1), '| spk btns:', html.count('class="spk"'), '| family btns:', html.count('seqFamily" data-fam'))
print('self_test:', '主动回忆自测' in html, '| output:', '输出倒逼' in html, '| seqAll:', 'id="seqAll"' in html)
