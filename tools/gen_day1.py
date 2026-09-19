import json, re
tpl = open('今日学习单_2026-08-24.html', encoding='utf-8').read()
data = json.load(open('words_tts.json', encoding='utf-8'))
b1 = [d for d in data if d.get('batch') == 1]

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
 ('-spect / -spic','看（look / see）','#0e7490','都和"看/视野"有关：in-往里看=检查，re-再看重=尊重，ex-往外看=期待，per-透过看=视角，pro-往前看=前景',[d for d in b1 if d['root']=='-spect / -spic']),
 ('-port','拿/运/带（carry）','#7c3aed','拿/运/带：im-运入=进口，ex-运出=出口，trans-转运=运输，re-往回带=报告，sup-在下托=支持，portable 可携带',[d for d in b1 if d['root']=='-port']),
 ('-dict / -dic','说（say / tell）','#d97706','说：dict-说，pre-预先说=预言，contra-反着说=反驳，in-说进去=指，de-说下去=奉献',[d for d in b1 if d['root']=='-dict / -dic']),
 ('-mit / -miss','送/派（send）','#be123c','送/派：ad-送进=承认，com-一起送=承诺，per-送过=允许，sub-送下去=提交，mission 任务，dis-送走=解散',[d for d in b1 if d['root']=='-mit / -miss']),
 ('-struct','建造（build）','#15803d','建造：structure 结构，con-一起建=建造，in-建进去=指导，de-拆建=摧毁',[d for d in b1 if d['root']=='-struct']),
]

def root_block(idx, root, mean_cn, color, hook, ws):
    L = ['      <div class="root" style="border-left-color:%s">' % color]
    L.append('        <div class="rt" style="color:%s">词根 %d %s <span class="mean">= = %s</span> <button class="seqFamily" data-root="%d">▶ 本族</button></div>' % (color, idx, root, mean_cn, idx))
    L.append('        <p class="hook">钩子：%s</p>' % hook)
    for d in ws:
        w = d['word']; ipa = d['ipa']; mn = d['meaning']; exen = d['example_en']; exzh = d['example_zh']; b = brk[w]
        L.append('        <div class="w"><button class="spk" data-w="%s" title="播放发音">🔊</button><span class="wmain"><b>%s</b><span class="ipa">%s</span><span class="mean2">%s</span><span class="brk">（%s）</span></span><span class="ex">例：%s %s</span></div>' % (w, w, ipa, mn, b, exen, exzh))
    L.append('      </div>')
    return '\n'.join(L)

blocks = '\n'.join(root_block(i+1, *f) for i, f in enumerate(fam))

self_test = '''      <h3>★ 主动回忆自测（强制环节）· 30 min · 本批正确率 ≥ 90% 才过关</h3>
      <p class="sub">被动听看不算学会。先<b>遮住下面"答案"</b>，用两种方式逼自己输出：① <b>听音写词</b>——点 🔊 听发音，默写拼写；② <b>遮义回想</b>——看单词，默写中文义 + 例句关键词。27 词错 ≤ 2 个（≈93%）即过关，否则本批次日重测（这是重启后"扎实"的硬门槛）。</p>
      <div class="tip purple">📝 自测清单（先别看右侧答案列）：<b>inspect · respect · expect · aspect · prospect · perspective · import · export · transport · report · support · portable · dictate · predict · contradict · indicate · dedicate · admit · commit · permit · submit · mission · dismiss · structure · construct · instruct · destroy</b></div>
      <details class="ans"><summary>点开看答案（自测完再对）</summary>
        <p>inspect 检查/视察｜respect 尊重｜expect 期待｜aspect 方面｜prospect 前景｜perspective 视角｜import 进口｜export 出口｜transport 运输｜report 报告｜support 支持｜portable 便携｜dictate 口述/命令｜predict 预测｜contradict 反驳｜indicate 表明｜dedicate 致力于｜admit 承认｜commit 承诺/犯｜permit 允许｜submit 提交｜mission 任务｜dismiss 解散/解雇｜structure 结构｜construct 建造｜instruct 指导｜destroy 摧毁</p>
      </details>'''

output_zone = '''      <h3>★ 输出倒逼（强制环节）· 25 min · 用本批词写 micro-writing</h3>
      <p class="sub">学完不"用"一次，等于没学。从本批挑 <b>至少 8 个词</b>，写一段 <b>80–120 字</b>小短文（主题任意：学习/工作/生活皆可），或口述 30 秒小故事。写作日(管综)也用这些词练论证段，双重固化。</p>
      <div class="sent">✍️ 示例框架：用 <i>inspect / expect / aspect / support / construct / structure / contradict / perspective</i> 写"我对重启备考的看法"——先列骨架，再成段。</div>
      <div class="ans"><b>提交方式</b>：把写好的短文发回对话，我按"用词准确 + 搭配自然 + 逻辑通顺"三档反馈；或口述录音自行核对。</div>'''

s = tpl
s = s.replace('DAY 19 · 2026年8月24日 · 周一 · 累计学习第 19 天（连续打卡中）· 🆕 新词日',
              'DAY 1 · 2026年8月27日 · 周四 · 累计学习第 1 天（★重启·新阶段）· 🆕 重学第01批')
s = s.replace('<div class="v">19 天</div>', '<div class="v">1 天</div>')
s = s.replace('<div class="focus">新词日：词根第 11 批 20 词（4 族·动/单独/轻/大）＋ 听书联播 ＋ 2022 阅读推进 ＋ 综合数学轻维持</div>',
              '<div class="focus">★重启：重学词根第 01 批 27 词（5 族·看/拿运带/说/送派/建造）＋ 听书联播 ＋ 主动回忆自测(≥90%过关) ＋ micro-writing输出 ＋ 综合数学轻维持</div>')
week_old = '''    <div class="week">
      📌 <b>里程碑</b>：今天 <b>第 11 批词根正式启用</b>——01–10 批 208 词已学完，从今天起进入 11–20 批（40 族 / 200 词）的按序启用阶段（<b>周一/周四各一批</b>，8.24 第11批 → 8.27 第12批 → …）。第 11 批 4 个词根族：<b>-mob/-mot/-mov 动、-sol 单独、-lev 轻/举、-magn/-maj/-max 大</b>，共 20 词，音频与例句已就绪。
    </div>'''
week_new = '''    <div class="week">
      📌 <b>★ 重启里程碑</b>：今天进入「生产式学习」新阶段——经自评估，前期偏"听+看"不够扎实，现从 <b>Day1 重新夯实地基</b>。词根 01–11 批（385 词/74 族）全部保留复用，状态降级为「待重学/待巩固」。新机制：① 主动回忆自测（本批≥90%过关）② 遗忘曲线间隔复习（第1/2/4/7/15/30天，见《复习排程表》）③ 输出倒逼（micro-writing）。新批改为"自测过关+首轮间隔复习完成"才解锁，缓加新（近期约3-4天/批）。今天重学 <b>第 01 批 27 词 / 5 族</b>。
    </div>'''
s = s.replace(week_old, week_new)
s = s.replace('找到第 11 批', '找到第 01 批')
s = s.replace('▶ 词根联播（按词根顺序·20词）', '▶ 词根联播（按词根顺序·27词）')

new_region = ('      <h3>2. 新词精学 · 重学第 01 批 27 词（六层格式）· 60 min</h3>\n'
 '      <p class="sub">每词六要素：🔊 发音 / 单词 / 音标 / 词义 / <b>结构拆解</b>（辅助记忆）/ 例句（英+中，与音频逐字一致）。先听→再跟读→再闭眼回忆词义→最后用例句造句。<b>这是重学，不是初学</b>：重点不是"认不认得"，而是"能不能瞬间反应 + 会不会用"。</p>\n'
 '      <div class="tip purple" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">🎧 <b>连续播放</b>：<button id="seqAll" class="seqBtn">▶ 词根联播（按词根顺序·27词）</button> 每个词根块标题后也有「▶ 本族」按钮，可单族连播。</div>\n'
 + blocks + '\n' + self_test + '\n' + output_zone)
s = re.sub(r'<h3>2\. 新词精学.*?(?=<h3>3\. 阅读)', new_region, s, flags=re.DOTALL)

night_old = '回顾第 11 批 20 词，卡壳的再听 1 遍 🔊（尤其 -lev 族 liev=lev 的变形、relevant 的"被提及→相关"逻辑）；② 把今天阅读的"诊断三问"答案过一遍；③ 默念明天开场："第 12 批周四（8.27）启用，继续往前走"。'
night_new = '回顾第 01 批 27 词，卡壳的再听 1 遍 🔊（尤其 -dict/-dic 族 dict=说 的派生、contradict 的"反着说=反驳"逻辑）；② 把今天自测错词 + micro-writing 过一遍；③ 默念明天开场："本批自测过关 + 首轮间隔复习做完，才解锁第 02 批（缓加新）"。'
s = s.replace(night_old, night_new)

open('今日学习单_2026-08-27.html', 'w', encoding='utf-8').write(s)
print('written; batch1 words in sheet:', s.count('data-w='))
print('self_test present:', '主动回忆自测' in s, '| output present:', '输出倒逼' in s)
print('leftover 第 11 批:', '第 11 批' in s, '| DAY 19:', 'DAY 19' in s)
