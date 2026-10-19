# -*- coding: utf-8 -*-
"""生成 61天冲刺 Day1 学习单（2026-10-20 · 周二 · 第01批压缩复习 + 真题精翻启动）。

数据源：words_tts.json（batch==1，27词/5族）
运行：python -B tools/gen_day_20261020.py   （CWD = 仓库根）
"""
import json, os

data = json.load(open('words_tts.json', encoding='utf-8'))
b1 = [d for d in data if d.get('batch') == 1]
assert len(b1) == 27, f'batch1 = {len(b1)} != 27'

missing = [d['word'] for d in b1 if not os.path.exists(f"audio/{d['word']}.mp3")]
assert not missing, f'缺音频: {missing}'

FAM = {
    '-spect / -spic': ('-spect / -spic', '看（look / see）', '#0e7490'),
    '-port':          ('-port', '拿 / 运 / 带（carry）', '#7c3aed'),
    '-dict / -dic':   ('-dict / -dic', '说（say / tell）', '#d97706'),
    '-mit / -miss':   ('-mit / -miss', '送 / 派（send）', '#be123c'),
    '-struct':        ('-struct', '建造（build）', '#15803d'),
}
HOOK = {
    '-spect / -spic': 'in- 往里看 = 检查｜re- 再看重 = 尊重｜ex- 往外看 = 期待｜per- 透过看 = 视角｜pro- 往前看 = 前景',
    '-port':          'im- 运入 = 进口｜ex- 运出 = 出口｜trans- 转运 = 运输｜re- 往回带 = 报告｜sup- 在下托 = 支持',
    '-dict / -dic':   'dict- 说｜pre- 预先说 = 预测｜contra- 反着说 = 反驳｜in- 说进去 = 指示｜de- 说下去 = 奉献',
    '-mit / -miss':   'ad- 送进 = 承认｜com- 一起送 = 承诺｜per- 送过 = 允许｜sub- 送下去 = 提交｜dis- 送走 = 解散',
    '-struct':        'structure 结构｜con- 一起建 = 建造｜in- 建进去 = 指导｜de- 拆建 = 摧毁',
}

by_root = {}
for d in b1:
    by_root.setdefault(d['root'], []).append(d)
assert len(by_root) == 5, f'族数 = {len(by_root)} != 5'


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


# ---------- 单词区（复习日四层格式） ----------
word_html = []
for root, ws in by_root.items():
    name, mean_cn, color = FAM[root]
    rows = []
    for d in ws:
        ex_en = esc(d['example_en'])
        ex_zh = esc(d['example_zh'])
        rows.append(
            f'<div class="w" data-w="{d["word"]}">'
            f'<button class="spk" data-w="{d["word"]}" title="播放发音">🔊</button>'
            f'<span class="word">{d["word"]}</span>'
            f'<span class="mean">{esc(d["meaning"])}</span>'
            f'<span class="ex">例：{ex_en} {ex_zh}</span></div>'
        )
    word_html.append(
        f'<div class="root"><div class="rt" style="color:{color}">{esc(name)}'
        f'<span class="rm"> · {esc(mean_cn)}</span></div>'
        f'<div class="hook">{esc(HOOK[root])}</div>'
        + ''.join(rows) + '</div>'
    )
WORDS = '\n'.join(word_html)

# ---------- 自测答案 ----------
ans_line = ' ｜ '.join(f'{d["word"]} {d["meaning"]}' for d in b1)
test_list = ' · '.join(d['word'] for d in b1)

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>考研冲刺 Day1 · 2026-10-20 · 第01批压缩复习</title>
<style>
* {{ box-sizing:border-box; }}
body {{ font-family:system-ui,"Segoe UI","Microsoft YaHei",sans-serif;
       background:#f6f7f9; color:#1f2937; max-width:760px; margin:0 auto;
       padding:18px 16px 80px; line-height:1.6; font-size:16px; }}
h1 {{ font-size:22px; margin:0 0 2px; }}
.meta {{ color:#6b7280; font-size:13px; margin:0 0 12px; }}
.focus {{ background:#ecfdf5; border:1px solid #6ee7b7; border-left:5px solid #059669;
         border-radius:8px; padding:10px 13px; font-size:14px; color:#065f46; margin:0 0 14px; }}
.milestone {{ background:#fff7ed; border:1px solid #fed7aa; border-radius:8px;
             padding:10px 13px; font-size:13.5px; color:#9a3412; margin:0 0 18px; }}
h3 {{ font-size:17px; margin:24px 0 8px; padding-bottom:6px; border-bottom:2px solid #e5e7eb; }}
.sub {{ color:#6b7280; font-size:13.5px; margin:0 0 10px; }}
.tc {{ display:inline-block; background:#111827; color:#fff; border-radius:5px;
      padding:1px 8px; font-size:12px; margin-left:6px; vertical-align:middle; font-weight:600; }}
.gotopaper {{ display:inline-flex; align-items:center; gap:7px; background:#185FA5; color:#fff;
      border:none; border-radius:9px; padding:11px 18px; font-size:15px; font-weight:700;
      cursor:pointer; margin:4px 0 2px; text-decoration:none; box-shadow:0 2px 6px rgba(24,95,165,.28); }}
.gotopaper:active {{ transform:scale(.97); }}
.gotopaper.ghost {{ background:#fff; color:#185FA5; border:1.5px solid #185FA5; box-shadow:none; font-weight:600; }}
.jumpbox {{ background:#E6F1FB; border:1px solid #85B7EB; border-left:5px solid #185FA5;
      border-radius:8px; padding:12px 14px; margin:10px 0 14px; font-size:14px; color:#0C447C; }}
.jumpbox .jt {{ font-weight:700; font-size:14.5px; color:#185FA5; margin-bottom:4px; }}
.root {{ margin:14px 0; }}
.rt {{ font-weight:700; font-size:15px; margin-bottom:3px; }}
.rm {{ font-weight:400; font-size:13px; color:#6b7280; }}
.hook {{ font-size:12.5px; color:#6b7280; background:#f9fafb; border-left:3px solid #e5e7eb;
        padding:5px 10px; margin:0 0 4px; border-radius:0 4px 4px 0; }}
.w {{ display:flex; align-items:baseline; flex-wrap:wrap; gap:4px 8px; padding:8px 0;
     border-bottom:1px dashed #eef0f2; font-size:15px; }}
.w:last-child {{ border-bottom:none; }}
.spk {{ flex:0 0 auto; width:38px; height:38px; border:none; border-radius:50%;
       background:#085041; color:#fff; font-size:16px; cursor:pointer; align-self:center; }}
.spk:active {{ transform:scale(.94); }}
.spk.on {{ background:#d97706; }}
.word {{ font-weight:700; color:#111827; font-size:16px; }}
.mean {{ color:#374151; }}
.ex {{ flex-basis:100%; color:#6b7280; font-size:13px; padding-left:46px; }}
.batchPlay {{ margin:6px 0 4px; border:none; border-radius:7px; padding:9px 16px;
             font-size:13px; font-weight:600; color:#fff; background:#0e7490; cursor:pointer; }}
.batchPlay:active {{ transform:scale(.97); }}
.tip {{ background:#eef2ff; border:1px solid #c7d2fe; border-radius:8px; padding:10px 13px;
       font-size:13.5px; color:#3730a3; margin:10px 0; }}
.warn {{ background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:10px 13px;
        font-size:13.5px; color:#991b1b; margin:10px 0; }}
.ok {{ background:#ecfdf5; border:1px solid #6ee7b7; border-radius:8px; padding:10px 13px;
      font-size:13.5px; color:#065f46; margin:10px 0; }}
.ans {{ background:#f9fafb; border:1px solid #e5e7eb; border-radius:8px; padding:8px 12px;
       font-size:13px; color:#374151; }}
.ans summary {{ cursor:pointer; font-weight:600; color:#111827; }}
.sent {{ background:#fff7ed; border-left:3px solid #f59e0b; padding:8px 11px; margin:10px 0;
        border-radius:4px; font-size:13.5px; color:#9a3412; }}
.sent b {{ color:#7c2d12; }}
.sent .cn {{ display:block; color:#065f46; margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; margin:10px 0; font-size:13.5px; }}
th, td {{ border:1px solid #e5e7eb; padding:7px 8px; text-align:left; vertical-align:top; }}
th {{ background:#f9fafb; font-weight:600; color:#111827; }}
.write {{ background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:10px 12px;min-height:84px;
        font-size:14px;color:#374151;line-height:1.8; }}
.timer {{ display:inline-flex; align-items:center; gap:6px; background:#111827; color:#fff;
        border:none; border-radius:7px; padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer; }}
.timer.run {{ background:#b91c1c; }}
.night {{ background:#f3f4f6; border-radius:8px; padding:11px 14px; font-size:13.5px; margin:18px 0; }}
footer {{ margin-top:30px; font-size:12px; color:#9ca3af; border-top:1px solid #e5e7eb; padding-top:12px; }}
@media(min-width:768px){{
  body {{ font-size:17px; padding:26px 22px 90px; }}
  .w {{ font-size:16px; }} .word {{ font-size:17px; }}
}}
</style>
<style>
  .nav-fab{{position:fixed;right:18px;bottom:18px;z-index:9999;display:flex;gap:10px;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
  .nav-fab a{{display:inline-flex;align-items:center;gap:6px;padding:10px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;box-shadow:0 4px 14px rgba(0,0,0,.22)}}
  .nav-fab a:active{{transform:scale(.96)}}
  .nav-fab .back-home{{background:#2C2C2A;color:#fff}}
  @media(max-width:600px){{.nav-fab{{right:12px;bottom:12px;gap:8px}}.nav-fab a{{padding:9px 13px;font-size:13px}}}}
</style>
</head>
<body>
<div class="nav-fab"><a href="index.html" class="back-home" title="返回考研备考中心首页">← 目录</a></div>

<h1>DAY 1 · 2026年10月20日 · 周二 · 61天冲刺启动</h1>
<p class="meta">2027级 MBA 备考 · 生产式学习（主动回忆自测 + 遗忘曲线间隔复习 + 输出倒逼）· 距初试 <b>61天</b></p>

<div class="focus">🎯 今日主线：<b>第01批 27 词压缩复习</b>（25min）＋ <b>长难句拆解 2 句</b>（20min）＋ <b>真题阅读精翻启动 · 2010 Text 1</b>（60min）＋ <b>作文模板背诵</b>（30min）＋ 管综数/逻手感维持（30min）</div>
<a class="gotopaper" href="papers/2010/2010_eng2_T1_精翻.html">📖 打开今日精翻材料：2010 Text 1（原文 20 句 + 中译折叠 + 21–25 题）→</a>

<div class="milestone">📍 <b>三级重启 · 第一天</b>。今天是 61 天冲刺的起点，也是<b>压缩复习流</b>的起点——不再每周推一批新词，改为<b>每日 1 批</b>。01–11 批 385 词要在 61 天内过 2 轮。明天（10/21）进第 02 批，今天先把第 01 批焊死。<br>
⚠️ <b>公考已让路</b>：今年国考无岗，公考改为等山西省考（2027-03-14 笔试），与考研<strong>彻底不冲突</strong>。这 61 天<strong>公考一分时间都不给</strong>，全部压给英语二。</div>

<h3>1. 单词区 · 第01批 27 词（复习日四层格式）<span class="tc">25 min</span></h3>
<p class="sub"><b>复习日不配音标、不配拆解</b>——目标是「看词 → 瞬间反应义」，不是重学一遍。先点下面的▶ 联播本批建立印象，再逐词自测。</p>
<button class="batchPlay" id="seqAll">▶ 联播本批（27词·顺序）</button>
<div class="batch">
{WORDS}
</div>

<h3>★ 主动回忆自测（强制环节）<span class="tc">10 min</span></h3>
<p class="sub">被动听看<b>不算学会</b>。先<b>遮住下面的答案</b>，两种方式逼自己输出：</p>
<div class="tip">① <b>听音写词</b>——点 🔊 听发音，默写拼写<br>② <b>遮义回想</b>——看单词，默写中文义<br><b>过关线：正确率 ≥ 90%（27 词错 ≤ 2）</b>。不达标 → 明天（10/21）不推第 02 批，本批重测一轮。</div>
<details class="ans"><summary>点开看自测清单与答案（自测完再对）</summary>
  <p><b>清单：</b>{test_list}</p>
  <p><b>答案：</b>{ans_line}</p>
</details>

<h3>2. 长难句拆解 · 2 句<span class="tc">20 min</span></h3>
<p class="sub">★ 新规则：<b>句子一律从当天真题里挑</b>，不重听基础课。下面 2 句用本批词仿写，先按真题标准拆，<b>下周同一结构再上真句</b>。</p>

<div class="sent">
<b>句 1 · 倒装 + 主语后置</b><br>
<span style="color:#0c447c;font-family:Georgia,serif">Only when the report was submitted did the structure of the argument become clear.</span>
<span class="cn">拆：Only when 引导的状语从句前置 → 主句倒装（助动词 did 提到主语前）。主干 = did the structure become clear。译：只有当报告被提交时，这个论证的结构才变得清晰。</span>
<br><b style="color:#7c2d12">考点</b>：Only when / Not until 置于句首必倒装，这是 2015–2021 高频句式，看到就条件反射。
</div>

<div class="sent">
<b>句 2 · 分词作状语 + 插入语</b><br>
<span style="color:#0c447c;font-family:Georgia,serif">The policy, contrary to public expectation, was opposed by those who respect the old structure.</span>
<span class="cn">拆：逗号后 contrary to public expectation 为<b>插入语</b>（可删）；those who respect the old structure 是 who 引导的定语从句作后置定语。主干 = The policy was opposed by those...。译：该政策与公众预期相反，遭到了那些尊重旧结构的人的反对。</span>
<br><b style="color:#7c2d12">考点</b>：插入语<b>读的时候直接跳过</b>，别在括号里死磕。主干找完再回头补。
</div>

<div class="warn">📌 <b>读法铁律</b>：<b>先找主干（主+谓+宾）→ 再挂修饰 → 最后才处理插入语和从句</b>。任何句子 3 遍内拆不开就别硬拆，标记下来放错题本。明天起从真题原文里挑真句练。</div>

<h3>3. 真题阅读精翻启动 · 2010 Text 1<span class="tc">60 min</span></h3>
<div class="jumpbox">
<div class="jt">▶ 精翻材料在这里，点开就能做</div>
<div style="margin-bottom:9px">全部内容已备好：<b>原文按句分行（20 句 / 469 词，每句编号）</b>＋<b>每段中译折叠</b>＋21–25 题全选项＋3 个长难句拆解＋错项归因参考＋9 个高频生词＋<b>18 分钟倒计时器</b>。</div>
<a class="gotopaper" href="papers/2010/2010_eng2_T1_精翻.html">📖 打开 2010 Text 1 精翻页 →</a>
<a class="gotopaper ghost" href="papers/2010/Text1_原文与题目.txt" target="_blank">📄 纯文本版（可打印）</a>
</div>
<p class="sub">阶段一主打<b>慢</b>——宁可一天 1 篇错得多，也不要一天 3 篇全是猜的。今天只做 1 篇，流程一步不许省。<b>建议先在本页做词汇与长难句，最后打开精翻页连续做完阅读部分。</b></p>
<button class="timer" id="t1">⏱ 开始计时 · 限时 18 分钟</button>
<table>
<tr><th style="width:22px">#</th><th>步骤</th><th>动作</th><th style="width:60px">用时</th></tr>
<tr><td>1</td><td>限时做题</td><td>18 分钟内做完 4 题，<b>不查词典、不回读</b></td><td>18′</td></tr>
<tr><td>2</td><td>对答案</td><td>记下错题数，<b>不纠结为什么不选它</b></td><td>2′</td></tr>
<tr><td>3</td><td><b>逐句英译中</b></td><td>全文一句一句拆，句子结构写出来，中文写出来。<b>全篇都要做</b></td><td>25′</td></tr>
<tr><td>4</td><td><b>选项归因</b></td><td>每个错项都要归到一类：<b>主旨混淆 / 过度推断 / 细节拼凑 / 无中生有</b></td><td>10′</td></tr>
<tr><td>5</td><td>抄生词</td><td>本篇生词抄进错题本，<b>不超过 20 个</b></td><td>5′</td></tr>
</table>
<div class="warn">⚠️ <b>本篇过关线：单题 ≤ 20 分钟、正确率 ≥ 50%</b>。正确率低于 50% 不是坏事——阶段一就是慢，通过率低才正常。<b>低于 50% 就把这篇在 11/26 前刷第二遍</b>，别急着往下推。</div>

<h3>4. 作文模板背诵<span class="tc">30 min</span></h3>
<p class="sub">今天<b>只背结构，不写整篇</b>。英语二作文 25 分是纯模板分，晚背一天就少一分。</p>

<div class="ok">
<b>小作文 · 书信（万能三段）</b><br>
<b>① 开头（2 句）</b>：I am writing to <i>purpose</i>. / I am writing to <b>你</b> in order to <i>purpose</i>.<br>
<b>② 正文（3 句）</b>：To begin with, <i>原因1</i>. What is more, <i>原因2</i>. <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Finally, I would like to <i>建议/请求</i>.<br>
<b>③ 结尾（1 句）</b>：Looking forward to your early reply.<br>
<b>万能动词</b>：suggest / recommend / advise / appreciate / devote / attach / solve<br>
<b>万能形容词</b>：grateful / convenient / beneficial / urgent / significant<br>
<b style="color:#991b1b">避雷</b>：别用复杂句。阅卷老师看的是<b>踩点</b>（有没有写到该写的点），不是句式多漂亮。
</div>

<div class="ok">
<b>大作文 · 图表（万能三段）</b><br>
<b>① 描述（2 句）</b>：As is vividly shown in the chart, <i>图表描述</i>. <br>
<b>② 分析（3 句）</b>：This phenomenon mainly results from <i>原因1</i>. <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Additionally, <i>原因2</i> should not be ignored.<br>
<b>③ 结论（2 句）</b>：In conclusion, it is high time that we <i>采取行动</i>.<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Only in this way can we <i>美好结果</i>.<br>
<b>万能动词</b>：account for / contribute to / result from / attribute to / witness / soar / decline<br>
<b>万能形容词</b>：considerable / dramatic / remarkable / gradual / decline / tendency<br>
<b style="color:#991b1b">避雷</b>：别写议论文体！必须「<b>图表描述 → 原因分析 → 结论建议</b>」三段齐，缺一段结构分就没了。
</div>

<div class="night">
<b>⑤ 输出倒逼 · micro-writing（10 min）</b><br>
用今天第 01 批的词，写 <b>3–5 句</b>你工作里的真实场景（写材料、开会、下乡，随便写）。<br>
示例骨架：<i>The structure of the report...</i> / <i>We should respect...</i> / <i>I expect...</i> / <i>submit...</i><br>
<div class="write" contenteditable="true">点这里开始写……</div>
</div>

<h3>6. 管综手感维持<span class="tc">30 min</span></h3>
<p class="sub">今天只做<b>数学</b>（明天逻辑，后天写作，轮替）。<b>不碰新难题</b>——管综 180 是地板分，保住就行。</p>
<div class="tip">✅ 回忆默写公式：<b>数列 / 排列组合 / 概率 / 函数</b>四大块公式，各写一遍<br>✅ 做 <b>5 道真题</b>（限时 8 分钟），错的重做一遍<br>❌ 不做模拟整套、不做偏题怪题</div>

<div class="night">
<b>今日自检（打勾才算完成）</b>
<div style="margin-top:8px">□ 联播第 01 批 + 逐词自测 <b>≥ 90%</b>（27 词错 ≤ 2）<br>
□ 长难句 2 句拆完，能口述主干<br>
□ 2010 T1 精翻：18′ 做完 + 逐句英译中 + 选项归因 + 抄生词<br>
□ 作文模板能<b>默写</b>三段开头和结尾（不是看着念）<br>
□ micro-writing 3–5 句写完<br>
□ 管综公式回忆 + 5 道真题</div>
</div>

<h3>明日预告 · 10/21 周三</h3>
<div class="sub">第 01 批间隔第 <b>1</b> 天回看（启用日 +1）+ <b>第 02 批</b>（26 词）压缩复习 + 长难句 2 句 + 阅读精翻 2010 T2 + 作文默写小作文一篇。</div>

<footer>
本页为个人备考资料，请勿外传。· 生成于 2026-10-20 · 元宝
</footer>

<script>
let cur=null, batchPlaying=false, seq=[];
const spks=[...document.querySelectorAll('.spk')];
spks.forEach(b=>b.addEventListener('click',e=>{{e.stopPropagation();
  if(cur){{cur.pause();cur=null;}}
  spks.forEach(x=>x.classList.remove('on'));
  b.classList.add('on');
  const a=new Audio('audio/'+b.dataset.w+'.mp3');a.play();
  b.classList.remove('on');
}}));
document.getElementById('seqAll').addEventListener('click',function(){{
  if(batchPlaying){{batchPlaying=false;this.textContent='▶ 联播本批（27词·顺序）';seq=[];return;}}
  batchPlaying=true;this.textContent='⏸ 停止联播';
  seq=spks.map(b=>b.dataset.w);playNext();
}});
function playNext(){{
  if(!batchPlaying||!seq.length){{batchPlaying=false;
    const b=document.getElementById('seqAll');
    if(b)b.textContent='▶ 联播本批（27词·顺序）';return;}}
  const w=seq.shift();
  const a=new Audio('audio/'+w+'.mp3');
  a.onended=playNext; a.play();
}}
const t1=document.getElementById('t1');let sec=1080,timer=null;
t1.addEventListener('click',function(){{
  if(timer){{clearInterval(timer);timer=null;t1.classList.remove('run');t1.textContent='⏱ 已用 '+(1080-sec)+' 秒 · 点此重开';return;}}
  t1.classList.add('run');t1.textContent='⏱ 计时中…';
  timer=setInterval(()=>{{sec--;
    if(sec<=0){{clearInterval(timer);timer=null;t1.classList.remove('run');
      t1.textContent='⏱ 时间到· 停笔对答案';return;}}
    const m=Math.floor(sec/60),s=sec%60;
    t1.textContent='⏱ '+m+':'+String(s).padStart(2,'0');
  }},1000);
}});
</script>
</body>
</html>'''

out = '今日学习单_2026-10-20.html'
open(out, 'w', encoding='utf-8').write(HTML)
print(f'OK -> {out}  ({len(HTML)} bytes, 27词/5族, 音频全在)')