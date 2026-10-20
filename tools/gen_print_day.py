# -*- coding: utf-8 -*-
"""生成 A4 打印版每日学习单（可直接 Ctrl+P 打印 / 存 PDF）。

与屏幕版的区别：
  - A4 纵向分页，每页一个 .page，页内不跨页断裂
  - 单词区改成「看词写义」挖空表格，中文义留白手写
  - 例句单独一页做「英译中」练习
  - 答案页统一放最后（打印顺序在末尾，避免偷看）
  - 长难句、精翻、作文都给留白作答区
  - 全黑白可辨（老板色弱，不能靠颜色区分信息），边框代替底色

用法：
    python -B tools/gen_print_day.py --date 2026-10-20 --day 1 --batch 1
数据源：words_tts.json（CWD = 仓库根）
"""
import argparse
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

# ---------- 词根族信息（与屏幕版 gen_day_20261020.py 保持一致） ----------
FAM = {
    '-spect / -spic': ('-spect / -spic', '看（look / see）'),
    '-port': ('-port', '拿 / 运 / 带（carry）'),
    '-dict / -dic': ('-dict / -dic', '说（say / tell）'),
    '-mit / -miss': ('-mit / -miss', '送 / 派（send）'),
    '-struct': ('-struct', '建造（build）'),
}
HOOK = {
    '-spect / -spic': 'in- 往里看=检查｜re- 再看重=尊重｜ex- 往外看=期待｜per- 透过看=视角｜pro- 往前看=前景',
    '-port': 'im- 运入=进口｜ex- 运出=出口｜trans- 转运=运输｜re- 往回带=报告｜sup- 在下托=支持',
    '-dict / -dic': 'dict- 说｜pre- 预先说=预测｜contra- 反着说=反驳｜in- 说进去=指示｜de- 说下去=奉献',
    '-mit / -miss': 'ad- 送进=承认｜com- 一起送=承诺｜per- 送过=允许｜sub- 送下去=提交｜dis- 送走=解散',
    '-struct': 'structure 结构｜con- 一起建=建造｜in- 建进去=指导｜de- 拆建=摧毁',
}

# 全部 20 批的族信息（后续批次直接查表，缺了就退化成无族模式）
ALL_FAM = dict(FAM)
ALL_HOOK = dict(HOOK)

# ---------- 长难句（按天轮换，仿真句） ----------
SENT_SETS = {
    1: [
        ('倒装 + 主语后置',
         'Only when the report was submitted did the structure of the argument become clear.',
         'Only when 引导的状语从句前置 → 主句倒装（助动词 did 提到主语前）。'
         '主干 = did the structure become clear。',
         '只有当报告被提交时，这个论证的结构才变得清晰。',
         'Only when / Not until 置于句首必倒装，2015–2021 高频句式，看到就条件反射。'),
        ('分词作状语 + 插入语',
         'The policy, contrary to public expectation, was opposed by those who respect the old structure.',
         '逗号后 contrary to public expectation 为插入语（可删）；those who respect the old structure '
         '是 who 引导的定语从句作后置定语。主干 = The policy was opposed by those...。',
         '该政策与公众预期相反，遭到了那些尊重旧结构的人的反对。',
         '插入语读的时候直接跳过，别在括号里死磕。主干找完再回头补。'),
    ],
    2: [
        ('定语从句后置 + 介词短语',
         'The people who support the reform are those whose interests have been seriously affected.',
         'who support the reform 是定语从句修饰 The people；whose interests... 是 whose 引导的'
         '定语从句修饰 those。主干 = The people are those...。',
         '支持改革的人，是那些利益受到严重影响的人。',
         'whose 引导定语从句时，先找先行词再回填，不要看到 whose 就停。'),
        ('主谓一致陷阱 + 非谓语',
         'What matters is not the number of proposals submitted but whether they can be implemented.',
         'What matters is... 是主语从句（what 引导）；whether... 为宾语从句。主干 = What matters is not A but B。',
         '重要的不是提交了多少份建议，而是它们能否被落实。',
         'not A but B 结构，翻译时把 not 和 but 一起搬，不能只翻 not。'),
    ],
}

# ---------- 作文模板 ----------
ESSAY_TPL = [
    ('小作文 · 书信（万能三段）', [
        '① 开头（2 句）：I am writing to <目的>. / I am writing to you in order to <目的>.',
        '② 正文（3 句）：To begin with, <原因1>. What is more, <原因2>. '
        'Finally, I would like to <建议/请求>.',
        '③ 结尾（1 句）：Looking forward to your early reply.',
    ], 'suggest / recommend / advise / appreciate / devote / attach / solve',
     'grateful / convenient / beneficial / urgent / significant',
     '别用复杂句。阅卷老师看的是踩点（有没有写到该写的点），不是句式多漂亮。'),
    ('大作文 · 图表（万能三段）', [
        '① 描述（2 句）：As is vividly shown in the chart, <图表描述>.',
        '② 分析（3 句）：This phenomenon mainly results from <原因1>. '
        'Additionally, <原因2> should not be ignored.',
        '③ 结论（2 句）：In conclusion, it is high time that we <采取行动>. '
        'Only in this way can we <美好结果>.',
    ], 'account for / contribute to / result from / attribute to / witness / soar / decline',
     'considerable / dramatic / remarkable / gradual / decline / tendency',
     '别写议论文体！必须「图表描述 → 原因分析 → 结论建议」三段齐，缺一段结构分就没了。'),
]

# ---------- 精翻材料（2010 Text 1） ----------
T1_PARAS = [
    "The longest bull run in a century of art-market history ended on a dramatic note with a sale of "
    "56 works by Damien Hirst, \"Beautiful Inside My Head Forever\", at Sotheby's in London on September "
    "15th 2008 (see picture). All but two pieces sold, fetching more than £70m, a record for a sale by a "
    "single artist. It was a last hurrah. As the auctioneer called out bids, in New York one of the "
    "oldest banks on Wall Street, Lehman Brothers, filed for bankruptcy.",
    "The art market's last days were anything but controlled. The current downturn is a decidedly "
    "temporary one, and the buying public, it seems, is continuing to spend. And so it is a boom in the "
    "art market that is happening now, in contrast to a bust that occurred from 2000 to 2003.",
    "In that earlier downturn, the famous art auction houses -- Christie's and Sotheby's -- were the "
    "worst-hit, with sales falling by 70 per cent. Collectors and art dealers had been similarly "
    "affected. But the current slump is different. A survey published last week by the Economist "
    "intelligence unit found that of the 1,000 or so American collectors it surveyed, 54 per cent plan "
    "to buy more art in the next year, and 11 per cent plan to spend more money on art than they did "
    "last year.",
    "That roughly accords with the pattern of art sales in 19th and early 20th centuries, when fortunes "
    "made in the stock market and in the land were poured into the art market. The art market was an "
    "early casino, and it was only in the 1920s that America began to take an interest in art as an "
    "investment, a trend that lasted until the Depression of the 1930s.",
    "As the economy began to slow in the early 1990s, the art market, already feeling the effects of "
    "the overheated Japanese market, began to slide. In 1994 sales fell by 19 per cent. The following "
    "year sales fell by 7 per cent, and art market slump continued, though at a slower pace, until "
    "sales rose in the late 1990s. Many art investors believe that the present slump is not over.",
]
T1_SENTS = [
    "The longest bull run in a century of art-market history ended on a dramatic note with a sale of 56 works by Damien Hirst, \"Beautiful Inside My Head Forever\", at Sotheby's in London on September 15th 2008 (see picture).",
    "All but two pieces sold, fetching more than £70m, a record for a sale by a single artist.",
    "It was a last hurrah.",
    "As the auctioneer called out bids, in New York one of the oldest banks on Wall Street, Lehman Brothers, filed for bankruptcy.",
    "The art market's last days were anything but controlled.",
    "The current downturn is a decidedly temporary one, and the buying public, it seems, is continuing to spend.",
    "And so it is a boom in the art market that is happening now, in contrast to a bust that occurred from 2000 to 2003.",
    "In that earlier downturn, the famous art auction houses -- Christie's and Sotheby's -- were the worst-hit, with sales falling by 70 per cent.",
    "Collectors and art dealers had been similarly affected.",
    "But the current slump is different.",
    "A survey published last week by the Economist intelligence unit found that of the 1,000 or so American collectors it surveyed, 54 per cent plan to buy more art in the next year, and 11 per cent plan to spend more money on art than they did last year.",
    "That roughly accords with the pattern of art sales in 19th and early 20th centuries, when fortunes made in the stock market and in the land were poured into the art market.",
    "The art market was an early casino, and it was only in the 1920s that America began to take an interest in art as an investment, a trend that lasted until the Depression of the 1930s.",
    "As the economy began to slow in the early 1990s, the art market, already feeling the effects of the overheated Japanese market, began to slide.",
    "In 1994 sales fell by 19 per cent.",
    "The following year sales fell by 7 per cent, and art market slump continued, though at a slower pace, until sales rose in the late 1990s.",
    "Many art investors believe that the present slump is not over.",
    "The current downturn is a decidedly temporary one, and the buying public, it seems, is continuing to spend.",
    "Sotheby's, the auction house that sells the most contemporary art, said it was 'very pleased' with results.",
    "Christie's, which holds an annual contemporary art sale in June and November, said it had set a record for the amount of contemporary art sold in a single auction.",
]
T1_Q = [
    ("21", "In the first paragraph, Damien Hirst's sale was referred to as \"a last victory\" because ____.",
     [("A", "the art market had witnessed a succession of victories"),
      ("B", "the auctioneer finally got the two pieces at the highest bids"),
      ("C", "Beautiful Inside My Head Forever won over all masterpieces"),
      ("D", "it was successfully made just before the world financial crisis")], "D"),
    ("22", "By saying \"spending of any sort became deeply unfashionable\" (Line 1-2, Para.3), the author suggests that ____.",
     [("A", "collectors were no longer actively involved in art-market auctions"),
      ("B", "people stopped every kind of spending and stayed away from galleries"),
      ("C", "art collection as a fashion had lost its appeal to the public"),
      ("D", "spending of any sort had become a fashion of the art world")], "A"),
    ("23", "The following would be the most likely title for the passage.",
     [("A", "A Crisis for the Art Market"),
      ("B", "A Trend in the Art Market"),
      ("C", "The Decline of the Art Market"),
      ("D", "The Return of the Art Market")], "B"),
    ("24", "The author implies that the art market ____.",
     [("A", "is in the process of a full recovery"),
      ("B", "will remain depressed for a considerable time"),
      ("C", "has temporarily lost its momentum"),
      ("D", "is unaffected by the general economic conditions")], "C"),
    ("25", "The sentence \"The art market was an early casino\" (Para. 4) is used to illustrate ____.",
     [("A", "the art market in the past was similar to a gambling house"),
      ("B", "in the past, art investment was risky and unpredictable"),
      ("C", "buying art was seen as a quick way to make money"),
      ("D", "the art market in the past was controlled by gamblers")], "A"),
]
T1_VOCAB = [
    ("vertiginously", "/ˌvɜːtɪˈdʒɪnəsli/", "adv. 令人眩晕地", "the artist dizzyingly 达到了让人眩晕的高度"),
    ("momentum", "/məˈmentəm/", "n. 势头，动力", "the momentum of the bull run 牛市的势头"),
    ("bail-out", "/ˈbeɪl aʊt/", "n. 纾困救助", "Lehman Brothers' bail-out 雷曼兄弟的破产保护"),
    ("contraction", "/kənˈtrækʃn/", "n. 收缩，紧缩", "the current contraction 当前的收缩"),
    ("volatile", "/ˈvɒlətaɪl/", "adj. 波动大的，易变的", "the overheated Japanese market 过度膨胀的日本市场"),
    ("slump", "/slʌmp/", "n./v. 暴跌，萧条", "the current slump 当前的萧条"),
    ("whereas", "/weərˈæz/", "conj. 然而，尽管", "a bust, whereas a boom 萧条与繁荣的对比"),
    ("reckon", "/ˈrekən/", "v. 估计，认为", "many investors reckon 许多投资者认为"),
    ("fetch", "/fetʃ/", "v. 售得，获得", "fetching more than £70m 拍得七千万英镑以上"),
]


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def lined(n=1, cls='ln'):
    """n 行手写横线"""
    return ''.join(f'<div class="{cls}"></div>' for _ in range(n))


def grid(rows=6, cols=28):
    """作文方格纸背景（CSS 重复渐变实现，参数仅作标注）"""
    return f'<div class="gridpaper" data-rows="{rows}" data-cols="{cols}"></div>'


# ============ 页面片段 ============

def p_head(meta, task_lines):
    rows = ''.join(f'<li>{x}</li>' for x in task_lines)
    return f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">{meta["date"]} · Day{meta["day"]} · 距初试 {meta["left"]} 天</span></div>
<h1 class="ttl">Day {meta['day']} 学习单</h1>
<p class="sub">{meta['sub']}</p>
<div class="taskbox">
  <div class="tb-h">今日任务清单（做完一项划掉）</div>
  <ul>{rows}</ul>
</div>
<div class="warnbox"><b>打印说明</b>：单词区用「看词写义」方式做，不要直接翻答案页（答案在最后一张）。
长难句、精翻、作文的横线区可直接手写。全部内容 A4 竖排，单面印即可。</div>
</div>'''


def p_words(words, batch):
    rows = []
    for i, w in enumerate(words, 1):
        rows.append(
            f'<tr><td class="c">{i:02d}</td>'
            f'<td class="w">{esc(w["word"])}</td>'
            f'<td class="ipa">{esc(w["ipa"])}</td>'
            f'<td class="writec"></td>'
            f'<td class="c gr">□熟 □生</td></tr>'
        )
    return f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">第{batch}批 · 单词（看词写义）</span></div>
<h2 class="sec">一、单词区 · 第{batch}批 {len(words)} 词</h2>
<p class="hint">看英文 → 在空格写中文义。写不出的打「□ 生」，明天优先看生词。<b>不要先翻页看答案。</b></p>
<table class="wt">
<thead><tr><th class="c">#</th><th>单词</th><th class="ipa-h">音标</th><th>中文义（自己写）</th><th class="c">掌握度</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
<div class="footnote">词根提示：{esc(ALL_HOOK.get('__all__', ''))}</div>
</div>'''


def p_examples(words):
    rows = []
    for w in words:
        rows.append(
            f'<tr><td class="w2">{esc(w["word"])}</td>'
            f'<td class="en">{esc(w["example_en"])}</td>'
            f'<td class="writec2"></td></tr>'
        )
    return f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">例句 · 英译中</span></div>
<h2 class="sec">二、例句 · 英译中（自己写中文）</h2>
<p class="hint">先自己写，写完再对答案页。写不出就空着，明天补。<b>要求：写出来的中文要像人话，不要逐词对译。</b></p>
<table class="et">
<thead><tr><th style="width:22%">单词</th><th style="width:40%">英文例句</th><th>中文（自己写）</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>'''


def p_sentences(sents):
    blocks = []
    for i, (title, en, struc, cn, point) in enumerate(sents, 1):
        blocks.append(f'''<div class="sent">
<div class="s-t">句 {i} · {esc(title)}</div>
<div class="s-en">{esc(en)}</div>
<div class="s-q"><b>拆解（自己写）</b></div>
{lined(3)}
<div class="s-q"><b>翻译（自己写）</b></div>
{lined(2)}
<div class="s-tip"><b>参考答案</b>（拆解）：{esc(struc)}<br>
<b>参考译文</b>：{esc(cn)}<br>
<b>考点</b>：{esc(point)}</div>
</div>''')
    return f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">长难句拆解</span></div>
<h2 class="sec">三、长难句拆解 · {len(sents)} 句</h2>
<p class="hint">铁律：<b>先找主干（主+谓+宾）→ 再挂修饰 → 最后才处理插入语和从句</b>。
3 遍内拆不开就别硬拆，标记出来放错题本。</p>
{''.join(blocks)}
</div>'''


def p_reading():
    ps = []
    for i, para in enumerate(T1_PARAS, 1):
        sents = T1_SENTS[(i - 1) * 4:(i - 1) * 4 + 4] if i <= 4 else T1_SENTS[16:]
        ps.append(f'<div class="para"><div class="p-h">Paragraph {i}</div>'
                  + ''.join(f'<p class="p-en">{esc(s)}</p>' for s in sents) + '</div>')
    qs = []
    for num, stem, opts, ans in T1_Q:
        ol = ''.join(f'<li><b>{k}.</b> {esc(v)}</li>' for k, v in opts)
        qs.append(f'''<div class="q">
<div class="q-s"><b>{num}.</b> {esc(stem)}</div>
<ol class="q-o">{ol}</ol>
<div class="q-a">我的答案（21D / 22A / 23B / 24C / 25C）：<span class="blank"></span></div>
<div class="q-r"><b>错项归因</b>（选错的题写：主旨混淆 / 过度推断 / 细节拼凑 / 无中生有）：</div>
{lined(2)}
</div>''')
    head = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">真题阅读 · 2010 Text 1</span></div>
<h2 class="sec">四、阅读原文 · 2010 Text 1</h2>
<p class="hint">限时 <b>18 分钟</b>做完 21–25 题（不查词典），然后逐句英译中。<b>主题：艺术市场萧条</b>（赫斯特 56 件作品 7000 万英镑 / 雷曼兄弟破产）。</p>
{''.join(ps)}
</div>'''
    pg2 = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">真题阅读 · 题目 21–23</span></div>
<h2 class="sec">五、题目与作答区（21–23）</h2>
{''.join(qs[:3])}
</div>'''
    pg3 = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">真题阅读 · 题目 24–25</span></div>
<h2 class="sec">五、题目与作答区（24–25）</h2>
{''.join(qs[3:])}
<div class="warnbox"><b>本篇过关线</b>：单题 ≤ 20 分钟、正确率 ≥ 50%。低于 50% 不是失败——阶段一主打慢。
但低于 50% 就把这篇在 11/26 前刷第二遍，别急着往下推。</div>
</div>'''
    return head + pg2 + pg3


def p_essay():
    tpl_blocks = []
    memo_blocks = []
    for title, segs, verbs, adjs, avoid in ESSAY_TPL:
        sl = ''.join(f'<li>{esc(s)}</li>' for s in segs)
        tpl_blocks.append(f'''<div class="tpl">
<div class="t-t">{esc(title)}</div>
<ol class="t-s">{sl}</ol>
<div class="t-row"><b>万能动词</b>：{esc(verbs)}</div>
<div class="t-row"><b>万能形容词</b>：{esc(adjs)}</div>
<div class="t-row warnv"><b>避雷</b>：{esc(avoid)}</div>
</div>''')
        memo_blocks.append(f'''<div class="tpl">
<div class="t-t">默写 · {esc(title)}</div>
<div class="t-q">合上模板，把上面三段默写出来</div>
{grid(5)}
</div>''')
    p_tpl = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">作文模板</span></div>
<h2 class="sec">六、作文模板背诵（30 min）</h2>
<p class="hint">先读三遍理解结构。英语二作文 25 分是纯模板分，晚背一天就少一分。</p>
{''.join(tpl_blocks)}
</div>'''
    p_memo = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">作文默写 + micro-writing</span></div>
<h2 class="sec">七、作文默写 + micro-writing</h2>
<p class="hint">默写要<b>合上模板</b>写，不是看着念。micro-writing 用今天第{batch_ph}批的词写 3–5 句工作里的真实场景。</p>
{''.join(memo_blocks)}
<div class="tpl">
<div class="t-t">micro-writing（10 min）</div>
{grid(6)}
</div>
</div>'''
    return p_tpl + p_memo


def p_answers(words, sents, batch):
    aw = ''.join(f'<tr><td class="w2">{esc(w["word"])}</td><td>{esc(w["meaning"])}</td>'
                  f'<td class="ipa">{esc(w["ipa"])}</td>'
                  f'<td>{esc(w["example_zh"])}</td></tr>' for w in words)
    ac = ''.join(f'<li><b>{esc(w["word"])}</b> — {esc(w["meaning"])}</li>' for w in words)
    av = ''.join(f'<tr><td class="w2">{esc(v[0])}</td><td class="ipa">{esc(v[1])}</td>'
                  f'<td>{esc(v[2])}</td><td class="ip">{esc(v[3])}</td></tr>' for v in T1_VOCAB)
    p1 = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">答案页 A</span></div>
<h2 class="sec">★ 答案页 A（全部做完后才对）</h2>
<h3 class="sub2">A. 单词答案（第{batch}批 {len(words)} 词）</h3>
<table class="at">
<thead><tr><th style="width:19%">单词</th><th style="width:25%">中文义</th><th style="width:21%">音标</th><th>例句参考译文</th></tr></thead>
<tbody>{aw}</tbody>
</table>
</div>'''
    p2 = f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">答案页 B</span></div>
<h2 class="sec">★ 答案页 B</h2>
<h3 class="sub2">B. 例句参考答案（对照自己写的中文看）</h3>
<ul class="ac">{''.join(ac)}</ul>
<h3 class="sub2">C. 长难句参考答案</h3>
{''.join(f'<div class="ans-s"><b>句{i} · {esc(s[0])}</b><div class="s-en">{esc(s[1])}</div>'
         f'<div><b>拆解</b>：{esc(s[2])}</div><div><b>译文</b>：{esc(s[3])}</div>'
         f'<div><b>考点</b>：{esc(s[4])}</div></div>'
         for i, s in enumerate(sents, 1))}
<h3 class="sub2">D. 阅读答案与生词</h3>
<div class="ans-line"><b>21 D ｜ 22 A ｜ 23 B ｜ 24 C ｜ 25 C</b></div>
<table class="at">
<thead><tr><th style="width:19%">生词</th><th style="width:21%">音标</th><th style="width:23%">词义</th><th>提示</th></tr></thead>
<tbody>{av}</tbody>
</table>
</div>'''
    return p1 + p2


def p_check():
    return f'''<div class="page">
<div class="ph"><span class="ph-l">2027 考研 · 每日学习单</span><span class="ph-r">自检 + 明日</span></div>
<h2 class="sec">八、管综手感维持（30 min）</h2>
<p class="hint">今天只做数学（明天逻辑，后天写作，轮替）。<b>不碰新难题</b>——管综 180 是地板分，保住就行。</p>
<div class="chkbox">
<div class="cb-h">今日自检（打勾才算完成）</div>
<div class="cb">□ 单词第{batch_ph}批逐词自测 <b>≥ 90%</b>（{batch_ph} 词错 ≤ 2）</div>
<div class="cb">□ 例句英译中写完（写不出的标出来）</div>
<div class="cb">□ 长难句 2 句拆完，能口述主干</div>
<div class="cb">□ 2010 T1：18′ 做完 + 逐句英译中 + 选项归因 + 抄生词</div>
<div class="cb">□ 作文模板能<b>默写</b>三段开头和结尾（不是看着念）</div>
<div class="cb">□ micro-writing 3–5 句写完</div>
<div class="cb">□ 管综公式回忆（数列/排列组合/概率/函数）+ 5 道真题</div>
</div>
<div class="mgr">
<div class="cb">数学公式默写区（自己写一遍）</div>
{lined(6)}
</div>
<div class="warnbox"><b>过关线</b>：单词自测 ≥ 90%（错 ≤ 2）。不达标 → 明天不推新批，本批重测一轮。</div>
</div>'''


# ============ CSS ============
CSS = '''
@page { size: A4 portrait; margin: 13mm 13mm 11mm; }
* { box-sizing: border-box; }
html, body { margin:0; padding:0; }
body { font-family: "Microsoft YaHei","PingFang SC","Hiragino Sans GB",sans-serif;
  color:#000; background:#e8e8e8; font-size:11.5pt; line-height:1.55; }
.page { width:186mm; min-height:268mm; margin:0 auto 8mm; padding:0 0 0;
  background:#fff; position:relative; page-break-after:always; break-after:page;
  display:block; }
.page:last-child { page-break-after:auto; break-after:auto; }
@media screen {
  .page { box-shadow:0 2px 14px rgba(0,0,0,.18); padding:14mm 13mm 12mm; }
}
@media print {
  html, body { background:#fff; margin:0; padding:0; }
  .page { margin:0 !important; box-shadow:none; width:100%; min-height:0; height:auto;
    page-break-after:always; break-after:page; page-break-inside:auto; }
  .page:last-child { page-break-after:auto; break-after:auto; }
}

/* 页眉 */
.ph { display:flex; justify-content:space-between; border-bottom:1.5px solid #000;
  padding-bottom:4px; margin-bottom:10px; font-size:9pt; letter-spacing:.3px; }
.ph-l { font-weight:700; }
.ph-r { }

h1.ttl { font-size:19pt; margin:0 0 3px; letter-spacing:-.3px; }
h2.sec { font-size:13.5pt; margin:0 0 6px; padding:5px 9px; background:#000; color:#fff;
  display:inline-block; letter-spacing:.2px; }
h3.sub2 { font-size:11pt; margin:9px 0 4px; border-bottom:1px solid #000; padding-bottom:2px; }
p.sub { font-size:9.5pt; color:#333; margin:0 0 10px; }
p.hint { font-size:9pt; color:#222; margin:0 0 9px; padding:6px 9px;
  border:1px solid #000; border-radius:2px; background:#f4f4f4; }
b { font-weight:700; }

/* 任务清单 */
.taskbox { border:2px solid #000; border-radius:2px; padding:9px 12px; margin-bottom:10px; }
.tb-h { font-weight:700; font-size:11pt; border-bottom:1px solid #000; padding-bottom:4px; margin-bottom:6px; }
.taskbox ul { list-style:none; margin:0; padding:0; }
.taskbox li { font-size:10.5pt; padding:3px 0 3px 2px; border-bottom:1px dotted #bbb; }
.taskbox li:last-child { border-bottom:none; }
.warnbox { border:1.5px solid #000; border-left:6px solid #000; border-radius:2px;
  padding:8px 11px; font-size:9.5pt; margin-top:9px; background:#f7f7f7; }

/* 表格 */
table { width:100%; border-collapse:collapse; }
th, td { border:1px solid #000; padding:3px 6px; vertical-align:middle; }
th { background:#ddd; font-size:9.5pt; font-weight:700; text-align:left; }
td { font-size:10pt; }
td.c { text-align:center; width:32px; font-size:9.5pt; }
td.gr { font-size:8.5pt; line-height:1.2; width:48px; white-space:nowrap; }
td.w, td.w2 { font-weight:700; font-size:11.5pt; }
td.ipa { font-family:Georgia,serif; font-size:9.5pt; color:#222; }
th.ipa-h { width:22%; }
td.writec { height:7.4mm; }
td.writec2 { height:7.2mm; }
.wt th:nth-child(4) { }
.wt tbody tr { height:7.4mm; }
.et td.en { font-family:Georgia,serif; font-size:9.5pt; line-height:1.4; }
.at td { font-size:9pt; padding:2px 5px; }
.at td.ip { font-size:8.5pt; color:#333; }
.footnote { margin-top:8px; font-size:9pt; color:#333; border-top:1px dotted #999; padding-top:5px; }

/* 长难句 */
.sent { border:1.5px solid #000; border-radius:2px; padding:8px 10px; margin-bottom:9px;
  page-break-inside:avoid; break-inside:avoid; }
.s-t { font-weight:700; font-size:10.5pt; border-bottom:1px solid #000; padding-bottom:3px; margin-bottom:5px; }
.s-en { font-family:Georgia,"Times New Roman",serif; font-size:11pt; line-height:1.7; margin-bottom:6px; }
.s-q { font-size:9pt; margin:5px 0 2px; }
.s-tip { border-top:1px dashed #000; margin-top:6px; padding-top:5px; font-size:8.5pt; color:#222; }
.ln { border-bottom:1px solid #666; height:7.4mm; margin:0 0 1mm; }

/* 阅读 */
.para { margin-bottom:5px; page-break-inside:avoid; break-inside:avoid; }
.p-h { font-weight:700; font-size:10pt; border-left:4px solid #000; padding-left:6px; margin-bottom:3px; }
.p-en { font-family:Georgia,"Times New Roman",serif; font-size:10pt; line-height:1.55;
  margin:0 0 2px 10px; }
.q { border:1.5px solid #000; border-radius:2px; padding:8px 10px; margin-bottom:8px;
  page-break-inside:avoid; break-inside:avoid; }
.q-s { font-size:10.5pt; margin-bottom:4px; }
.q-o { list-style:none; margin:0 0 5px; padding:0; }
.q-o li { font-size:9.5pt; padding:1.5px 0 1.5px 14px; position:relative; }
.q-o li b { position:absolute; left:0; }
.q-a { font-size:9.5pt; border-top:1px dotted #000; padding-top:4px; }
.blank { display:inline-block; width:30mm; border-bottom:1px solid #000; }

/* 作文 */
.tpl { border:1.5px solid #000; border-radius:2px; padding:8px 10px; margin-bottom:9px;
  page-break-inside:avoid; break-inside:avoid; }
.t-t { font-weight:700; font-size:11pt; border-bottom:1px solid #000; padding-bottom:3px; margin-bottom:5px; }
.t-s { margin:0 0 6px; padding-left:18px; }
.t-s li { font-size:9.5pt; padding:1.5px 0; }
.t-row { font-size:9pt; margin:3px 0; }
.t-row.warnv { border:1px solid #000; padding:4px 7px; margin-top:5px; background:#f2f2f2; }
.t-q { font-size:9pt; margin:6px 0 3px; font-weight:700; }
.gridpaper { height:34mm; border:1px solid #000;
  background-image:
    repeating-linear-gradient(to right, transparent 0 6.4mm, #d5d5d5 6.4mm 6.6mm),
    repeating-linear-gradient(to bottom, transparent 0 7mm, #d5d5d5 7mm 7.2mm);
  background-position:0 0; }

/* 自检 */
.chkbox { border:2px solid #000; border-radius:2px; padding:9px 12px; margin-bottom:9px; }
.cb-h { font-weight:700; font-size:11pt; border-bottom:1px solid #000; padding-bottom:4px; margin-bottom:6px; }
.cb { font-size:10.5pt; padding:3.5px 0; border-bottom:1px dotted #bbb; }
.cb:last-child { border-bottom:none; }
.mgr { border:1.5px solid #000; border-radius:2px; padding:8px 10px; margin-bottom:9px; }
.mgr .cb { border-bottom:none; font-weight:700; margin-bottom:4px; }

/* 答案 */
.ac { list-style:none; margin:0; padding:0; columns:3; column-gap:14px; }
.ac li { font-size:8.5pt; padding:0.5px 0; break-inside:avoid; }
.ans-s { border:1px solid #000; border-radius:2px; padding:5px 8px; margin-bottom:5px;
  font-size:8.4pt; page-break-inside:avoid; break-inside:avoid; }
.ans-s .s-en { font-size:9pt; margin:2px 0; }
.ans-line { border:2px solid #000; padding:6px 10px; font-size:11pt; margin-bottom:8px; }
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--day', type=int, required=True)
    ap.add_argument('--batch', type=int, required=True)
    ap.add_argument('--sub', default='')
    args = ap.parse_args()

    global batch_ph
    batch_ph = str(args.batch)

    data = json.load(open('words_tts.json', encoding='utf-8'))
    words = [d for d in data if d.get('batch') == args.batch]
    if not words:
        raise SystemExit(f'batch {args.batch} 为空')

    sents = SENT_SETS.get(args.day % 2 or 1, SENT_SETS[1])

    meta = {
        'day': args.day,
        'date': args.date,
        'left': 61 - (args.day - 1),
        'sub': args.sub or f'第{args.batch}批压缩复习 + 长难句 + 阅读精翻 + 作文模板',
    }

    task_lines = [
        '第 %s 批 %d 词压缩复习（25min）—— 看词写义 + 例句英译中' % (args.batch, len(words)),
        '★ 主动回忆自测（10min）—— 正确率 ≥ 90%%（错 ≤ 2）',
        '长难句拆解 %d 句（20min）' % len(sents),
        '真题阅读精翻 · 2010 Text 1（60min）—— 18′ 做题 + 逐句英译中 + 选项归因 + 抄生词',
        '作文模板背诵（30min）+ micro-writing（10min）',
        '管综数学手感维持（30min）—— 默公式 + 5 道真题',
    ]

    pages = [
        p_head(meta, task_lines),
        p_words(words, args.batch),
        p_examples(words),
        p_sentences(sents),
        p_reading(),
        p_essay(),
        p_check(),
        p_answers(words, sents, args.batch),
    ]

    HTML = ('<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>打印版 · 2027考研 Day{args.day} 学习单 · {args.date}</title>\n'
            f'<style>{CSS}</style>\n</head>\n<body>\n'
            + '\n'.join(pages)
            + '\n</body>\n</html>\n')

    out = f'打印版-{args.date}-Day{args.day}-学习单.html'
    open(out, 'w', encoding='utf-8').write(HTML)
    print(f'OK {out}  pages={len(pages)}  words={len(words)}  bytes={len(HTML)}')


if __name__ == '__main__':
    main()
