# -*- coding: utf-8 -*-
"""生成「复习日」学习单（间隔复习节点用）。
格式遵循 sync/提示词.txt 规则 5：每词一行四层——🔊+单词+汉译+例句；不配音标、不配拆解；按批次分组。
强制附加：主动回忆自测区 + 输出倒逼区（规则 5 重启新增）。
复用 单词总表.html 的 .nav-fab 与 data-w 单播互斥播放器。
"""
import json, datetime, html

SRC = 'words_tts.json'
OUT = '今日学习单_2026-08-28.html'
BATCH = 1
DATE = '2026年8月28日'
WEEKDAY = '周五'
DAY = 2

data = json.load(open(SRC, encoding='utf-8'))
b = [w for w in data if w.get('batch') == BATCH]
b.sort(key=lambda w: w.get('root', ''))

fam_order = []
groups = {}
for w in b:
    r = w.get('root', '其他')
    if r not in groups:
        groups[r] = []
        fam_order.append(r)
    groups[r].append(w)


def esc(s):
    return html.escape(str(s), quote=True)


word_blocks = []
for r in fam_order:
    lines = []
    for w in groups[r]:
        word = esc(w['word'])
        mn = esc(w.get('meaning', ''))
        exen = esc(w.get('example_en', ''))
        exzh = esc(w.get('example_zh', ''))
        lines.append(
            '          <div class="w" data-w="%s">'
            '<button class="spk" data-w="%s" title="播放发音">\U0001F50A</button>'
            '<span class="word">%s</span>'
            '<span class="mean">%s</span>'
            '<span class="ex">例：%s %s</span>'
            '</div>' % (word, word, word, mn, exen, exzh)
        )
    word_blocks.append(
        '        <div class="root">\n'
        '          <div class="rt">词根族 %s</div>\n%s\n'
        '        </div>' % (esc(r), '\n'.join(lines))
    )
word_region_html = '\n'.join(word_blocks)

self_words = ' · '.join(esc(w['word']) for w in b)
self_ans = '｜'.join('%s %s' % (esc(w['word']), esc(w.get('meaning', ''))) for w in b)
gen_date = datetime.date.today().isoformat()

TPL = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>考研备考·第01批 间隔第1天复习（2026-08-28）</title>
<style>
* { box-sizing: border-box; }
body { font-family: system-ui, "Segoe UI", "Microsoft YaHei", sans-serif;
       background:#f6f7f9; color:#1f2937; max-width:760px; margin:0 auto;
       padding:18px 16px 80px; line-height:1.6; font-size:16px; }
h1 { font-size:22px; margin:0 0 2px; }
.meta { color:#6b7280; font-size:13px; margin:0 0 12px; }
.focus { background:#ecfdf5; border:1px solid #6ee7b7; border-left:5px solid #059669;
         border-radius:8px; padding:9px 13px; font-size:14px; color:#065f46; margin:0 0 14px; }
.milestone { background:#fff7ed; border:1px solid #fed7aa; border-radius:8px;
             padding:9px 13px; font-size:13.5px; color:#9a3412; margin:0 0 18px; }
h3 { font-size:17px; margin:22px 0 8px; }
.sub { color:#6b7280; font-size:13.5px; margin:0 0 10px; }
.batch { border:1px solid #e5e7eb; border-radius:10px; padding:10px 14px; background:#fff; margin:12px 0; }
.root { margin:12px 0; }
.rt { font-weight:700; font-size:15px; color:#0e7490; margin-bottom:4px; }
.w { display:flex; align-items:baseline; flex-wrap:wrap; gap:4px 8px; padding:7px 0;
     border-bottom:1px dashed #eef0f2; font-size:15px; }
.w:last-child { border-bottom:none; }
.spk { flex:0 0 auto; width:38px; height:38px; border:none; border-radius:50%;
       background:#085041; color:#fff; font-size:16px; cursor:pointer; }
.spk:active { transform:scale(.94); }
.spk.on { background:#d97706; }
.word { font-weight:700; color:#111827; font-size:16px; }
.mean { color:#374151; }
.ex { flex-basis:100%; color:#6b7280; font-size:13px; padding-left:46px; }
.batchPlay { margin:6px 0 2px; border:none; border-radius:7px; padding:7px 14px;
             font-size:13px; font-weight:600; color:#fff; background:#0e7490; cursor:pointer; }
.tip { background:#eef2ff; border:1px solid #c7d2fe; border-radius:8px; padding:10px 13px;
       font-size:13.5px; color:#3730a3; margin:10px 0; }
.ans { background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:8px 12px;
       font-size:13px; color:#374151; }
.ans summary { cursor:pointer; font-weight:600; color:#111827; }
.sent { background:#fff7ed; border-left:3px solid #f59e0b; padding:6px 11px; margin:8px 0;
        border-radius:4px; font-size:13.5px; color:#9a3412; }
.night { background:#f3f4f6; border-radius:8px; padding:10px 14px; font-size:13.5px; margin:18px 0; }
footer { margin-top:30px; font-size:12px; color:#9ca3af; border-top:1px solid #e5e7eb; padding-top:12px; }
@media(min-width:768px){
  body { font-size:17px; padding:26px 22px 90px; }
  .w { font-size:16px; }
  .word { font-size:17px; }
}
</style>
<style>
  .nav-fab{position:fixed;right:18px;bottom:18px;z-index:9999;display:flex;gap:10px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
  .nav-fab a{display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;box-shadow:0 4px 14px rgba(0,0,0,.22)}
  .nav-fab a:active{transform:scale(.96)}
  .nav-fab .back-home{background:#2C2C2A;color:#fff}
  .nav-fab .go-home{background:#085041;color:#fff}
  @media(max-width:600px){.nav-fab{right:12px;bottom:12px;gap:8px}.nav-fab a{padding:9px 13px;font-size:13px}}
</style>
</head>
<body>
<div class="nav-fab"><a href="index.html" class="back-home" title="返回考研备考中心首页">\u2190 目录</a><a href="/" class="go-home" title="返回个人主页">\U0001F3E0 主页</a></div>

<h1>DAY __DAY__ · __DATE__ · __WEEKDAY__ · 累计学习第 __DAY__ 天（★重启·新阶段）· \U0001F501 复习日（第01批 间隔第1天）</h1>
<p class="meta">2027级 MBA 备考 · 生产式学习（主动回忆自测 + 遗忘曲线间隔复习 + 输出倒逼）</p>
<div class="focus">\U0001F501 复习日：第01批 27 词（5 族·看/拿运带/说/送派/建造）间隔第 1 天回看 ＋ 主动回忆自测(≥90%过关) ＋ micro-writing 输出 ＋ 综合数学轻维持</div>
<div class="milestone">\U0001F4CD ★ 重启里程碑（回顾）：从 Day1(8.27) 重新夯实地基，词根 01–11 批（385 词/74 族）全部保留复用、状态降级为「待重学/待巩固」。今天是第 01 批启用后的<b>间隔第 1 天</b>，只回看、不学新词——把地基砸实。</div>

<h3>1. 复习日单词区 · 第01批 27 词（四层格式：\U0001F50A+单词+汉译+例句）</h3>
<p class="sub">不配音标、不配拆解，纯「看词→反应义→听音确认」的提取练习。先点 🔊 听，遮住汉译自己说；卡壳的词标星，结束后回听 1 遍。</p>
<button class="batchPlay" id="seqAll">\u25B6 联播本批（27词·顺序）</button>
<div class="batch">
__WORD_REGION__
</div>

<h3>★ 主动回忆自测（强制环节）· 30 min · 本批正确率 ≥ 90% 才过关</h3>
<p class="sub">被动听看不算学会。先<b>遮住下面「答案」</b>，两种方式逼自己输出：① <b>听音写词</b>——点 🔊 听发音，默写拼写；② <b>遮义回想</b>——看单词，默写中文义。27 词错 ≤ 2 个（约93%）即过关，否则本批次日重测（重启后「扎实」的硬门槛）。</p>
<div class="tip">\U0001F4DD 自测清单（先别看右侧答案）：<b>__SELF_WORDS__</b></div>
<details class="ans"><summary>点开看答案（自测完再对）</summary>
  <p>__SELF_ANS__</p>
</details>

<h3>★ 输出倒逼（强制环节）· 25 min · 用本批词写 micro-writing</h3>
<p class="sub">学完不「用」一次等于没学。从本批挑 <b>至少 8 个词</b>，写一段 <b>80–120 字</b>小短文（主题任意：学习/工作/生活皆可），或口述 30 秒小故事。写作日(管综)也用这些词练论证段，双重固化。</p>
<div class="sent">✍️ 示例框架：用 <i>inspect / expect / aspect / support / construct / structure / contradict / perspective</i> 写「我对重启备考的看法」——先列骨架，再成段。</div>
<div class="ans"><b>提交方式</b>：把写好的短文发回对话，我按「用词准确 + 搭配自然 + 逻辑通顺」三档反馈；或口述录音自行核对。</div>

<div class="night">
<b>晚间复盘（10 min）</b>：① 回看自测错词，卡壳的再听 1 遍 🔊（尤其 -dict/-dic 族 dict=说 的派生、contradict 的「反着说=反驳」逻辑）；② 把自测错词 + micro-writing 过一遍；③ 默念明日开场：「本批自测过关 + 首轮间隔复习做完，才解锁第 02 批（缓加新）」。<br>
<b>明日（8.29 周六）</b>：第01批 间隔第 2 天复习（同格式）。若本批自测 ≥90% 且首轮(第1/2天)间隔复习完成，可评估解锁第 02 批。
</div>

<footer>数据来源：words_tts.json（单一事实源）· 第01批 27 词 / 5 词根族 · 音频 audio/&lt;词&gt;.mp3 · 复习日四层格式（规则 5）· 生成于 __GEN_DATE__</footer>
<script>
const player = new Audio(); player.preload = 'none';
let curBtn = null, queue = null, qIdx = 0, playingBatch = false;
function highlight(btn, on){ if(btn) btn.classList.toggle('on', on); }
function sel(w){ return document.querySelector('.spk[data-w="' + CSS.escape(w) + '"]'); }
function playWord(w, btn){
  if(curBtn === btn && !player.paused){ player.pause(); highlight(curBtn,false); curBtn=null; return; }
  if(curBtn) highlight(curBtn,false);
  player.src = 'audio/' + encodeURIComponent(w) + '.mp3';
  player.currentTime = 0; player.play();
  curBtn = btn; highlight(btn, true);
}
document.querySelectorAll('.spk').forEach(b => b.addEventListener('click', () => playWord(b.dataset.w, b)));
document.getElementById('seqAll').addEventListener('click', () => {
  if(playingBatch){ player.pause(); playingBatch=false; qIdx=0; if(curBtn) highlight(curBtn,false); return; }
  const ws = Array.from(document.querySelectorAll('.spk')).map(x => x.dataset.w);
  queue = ws; qIdx = 0; playingBatch = true;
  playWord(queue[qIdx], sel(queue[qIdx]));
});
player.addEventListener('ended', () => {
  if(curBtn) highlight(curBtn, false);
  if(playingBatch && qIdx < queue.length - 1){ qIdx++; const w = queue[qIdx]; playWord(w, sel(w)); }
  else { playingBatch = false; qIdx = 0; }
});
</script>
</body></html>'''

html_doc = (TPL
            .replace('__DAY__', str(DAY))
            .replace('__DATE__', DATE)
            .replace('__WEEKDAY__', WEEKDAY)
            .replace('__WORD_REGION__', word_region_html)
            .replace('__SELF_WORDS__', self_words)
            .replace('__SELF_ANS__', self_ans)
            .replace('__GEN_DATE__', gen_date))

with open(OUT, 'w', encoding='utf-8') as f:
    f.write(html_doc)

print('written:', OUT)
print('batch1 words:', len(b))
print('data-w buttons:', html_doc.count('class="spk"'))
print('self_test present:', '主动回忆自测' in html_doc, '| output present:', '输出倒逼' in html_doc)
print('leftover ipa in word lines:', 'class="ipa"' in html_doc)
print('any unresolved token:', '__' in html_doc)
