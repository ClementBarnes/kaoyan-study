# -*- coding: utf-8 -*-
"""生成手机版单词卡 PWA（单词音频 + 主动回忆自测）。

特点：
  - 手机浏览器打开即用，可「添加到主屏幕」当 App
  - 音频走 GitHub Pages（audio/<word>.mp3），离线后仍可播放已缓存词
  - 主动回忆：先看词想义 → 点「显示答案」→ 标记 熟/生
  - 学习进度存 localStorage，换设备不同步（进度在资料库表里同步）
  - 11 批全覆盖（385 词），可按批切换

用法：python -B tools/gen_pwa_words.py
输出：单词卡.html + manifest.webmanifest + sw.js
"""
import json
import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)

data = json.load(open('words_tts.json', encoding='utf-8'))
batches = {}
for d in data:
    batches.setdefault(d['batch'], []).append(d)
# 全部 20 批都可用（385 词，音频齐），01-11 批是 61 天冲刺主线
LEARN_BATCHES = list(range(1, 21))
CORE_BATCHES = list(range(1, 12))   # 主线：冲刺期必背
OUT_BATCHES = list(range(12, 21))    # 拓展：有余力再背

FAM = {
    '-mob / -mot / -mov': ('动', 'mo- 移动｜im- 移入=移民｜ex- 移出=出口｜com- 一起动=共同｜trans- 转移'),
    '-sol': ('独/全', 'sol- 独自｜con- 一起=整体｜ab- 离开=绝对｜dis- 分开=解散'),
    '-lev': ('轻/举', 'lev- 举起＝重量｜re- 举回=相关｜de- 放下=减轻｜sub- 举起下面=字幕'),
    '-magn / -maj / -max': ('大', 'magn- 大｜max- 最大｜major- 更大的｜magnate- 大亨'),
    '-cert': ('确定/证实', 'cert- 确信｜ac- 加上=认可｜con- 共同=一致'),
    '-fac / -fact / -fect': ('做/造', 'fact- 制造｜ef- 做出=效果｜manu- 手工制造｜facility 设施'),
    '-pel / -puls': ('推/驱', 'pel- 推｜ex- 推出=排除｜com- 一起推=迫使｜impel 推动'),
    '-sequ / -secut': ('跟随', 'sequ- 跟随｜con- 连续｜sub- 随后｜sequel 续集'),
    '-gen / -gener': ('产生/类', 'gen- 产生｜con- 一起=共同｜im- 向内=固有｜de- 向下=退化'),
    '-solv / -solut': ('松开/解决', 'solv- 松开｜ab- 离开=解脱｜dis- 分开=溶解｜solution 解决'),
    '-serv': ('服务/保持', 'serv- 服务｜con- 一起=保存｜pre- 在前=预防｜deserve 值得'),
    '-sist': ('站立', 'sist- 站｜con- 一起=坚持｜ex- 出去=退出｜insist 坚持'),
    '-aud': ('听/敢', 'aud- 听｜e- 出去=发出｜audience 听众'),
    '-cred': ('信/贷', 'cred- 相信｜in- 内在=信用｜dis- 不信=不信任｜credit 信用'),
    '-flu': ('流', 'flu- 流｜con- 一起=汇流｜in- 流入｜influ- 影响'),
    '-her / -hes': ('粘/继承', 'her- 粘附｜in- 内在=固有｜co- 一起=继承｜heritage 遗产'),
    '-manu / -mani': ('手', 'manu- 手｜manu- 手写｜man- 手艺'),
    '-med': ('中间/医疗', 'med- 中间｜im- 立即=修复｜medi- 中间'),
    '-mem': ('记', 'mem- 记｜memo- 记忆｜im- 记住=铭记'),
    '-migr': ('迁移', 'migr- 迁移｜im- 移入=移民｜trans- 转移｜emigrate 移出'),
    '-mon': ('警告/提醒', 'mon- 警告｜ad- 附加=任命｜pre- 预先=预告'),
    '-nat': ('出生/天生', 'nat- 出生｜na- 出生地｜pre- 预先=先天的'),
    '-neg': ('否定', 'neg- 否认｜ab- 离开=缺省｜ir- 不=否定'),
    '-nomin / -nomen': ('名字/任命', 'nomin- 名字｜nom- 名字｜denom- 单元=分母'),
    '-path': ('感情/苦', 'path- 感情｜sym- 共同=同情｜ap- 加强=同感'),
    '-ped': ('脚/儿童', 'ped- 脚｜ex- 出去=剔除｜ped- 儿童'),
    '-phil': ('爱', 'phil- 爱｜am- 无=非爱｜philo 哲学'),
    '-phon': ('声音', 'phon- 声音｜micro- 小=扩音器｜tel- 远=电话'),
    '-plac': ('放置/请求', 'plac- 放置｜com- 一起=安抚｜sup- 下面=替代'),
    '-plen / -plet': ('满/填', 'plen- 满｜com- 一起=充满｜ple- 填=补充'),
    '-quest / -quir / -quis': ('问/求', 'quest- 询问｜ac- 获得=征服｜re- 再次=要求'),
    '-viv / -vit': ('活/生命', 'viv- 活｜vi- 活｜re- 复活'),
    '-rect / -reg': ('直/规则', 'rect- 直｜cor- 一起=纠正｜reg- 规则'),
    '-scend': ('爬', 'scend- 爬｜con- 一起=上升｜trans- 越过=超越'),
    '-sci': ('知道', 'sci- 知道｜con- 一起=意识｜pre- 预先=科学'),
    '-sed / -sid / -sess': ('坐', 'sed- 坐｜con- 一起=会议｜pre- 预先=总统'),
    '-simil / -sembl': ('相似', 'simil- 相似｜as- 相似=类似｜simul- 同时=模拟'),
    '-tang / -tact': ('接触', 'tang- 接触｜con- 一起=接触｜con- 一起=接触'),
    '-term / -termin': ('界限/结束', 'term- 界限｜con- 一起=确定｜termin- 结束'),
    '-tort': ('扭', 'tort- 扭｜con- 一起=扭曲｜extor- 拉出=勒索'),
    '-spect / -spic': ('看', 'in- 往里看=检查｜re- 再看重=尊重｜ex- 往外看=期待｜per- 透过看=视角｜pro- 往前看=前景'),
    '-port': ('拿/运/带', 'im- 运入=进口｜ex- 运出=出口｜trans- 转运=运输｜re- 往回带=报告｜sup- 在下托=支持'),
    '-dict / -dic': ('说', 'dict- 说｜pre- 预先说=预测｜contra- 反着说=反驳｜in- 说进去=指示｜de- 说下去=奉献'),
    '-mit / -miss': ('送/派', 'ad- 送进=承认｜com- 一起送=承诺｜per- 送过=允许｜sub- 送下去=提交｜dis- 送走=解散'),
    '-struct': ('建造', 'structure 结构｜con- 一起建=建造｜in- 建进去=指导｜de- 拆建=摧毁'),
}
ALL_HOOK = {
    '-spect / -spic': 'in- 往里看=检查｜re- 再看重=尊重｜ex- 往外看=期待｜per- 透过看=视角｜pro- 往前看=前景',
    '-port': 'im- 运入=进口｜ex- 运出=出口｜trans- 转运=运输｜re- 往回带=报告｜sup- 在下托=支持',
    '-dict / -dic': 'dict- 说｜pre- 预先说=预测｜contra- 反着说=反驳｜in- 说进去=指示｜de- 说下去=奉献',
    '-mit / -miss': 'ad- 送进=承认｜com- 一起送=承诺｜per- 送过=允许｜sub- 送下去=提交｜dis- 送走=解散',
    '-struct': 'structure 结构｜con- 一起建=建造｜in- 建进去=指导｜de- 拆建=摧毁',
}

# 压缩成 JS 数据
JS_DATA = {}
for b in LEARN_BATCHES:
    JS_DATA[str(b)] = [
        {
            'w': d['word'], 'i': d['ipa'], 'm': d['meaning'],
            'e': d['example_en'], 'z': d['example_zh'], 'r': d['root'],
        }
        for d in batches.get(b, [])
    ]

HOOK_JSON = json.dumps(ALL_HOOK, ensure_ascii=False)
FAM_JSON = json.dumps({k: v[0] for k, v in FAM.items()}, ensure_ascii=False)

HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no">
<meta name="theme-color" content="#185FA5">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="考研单词">
<link rel="manifest" href="manifest.webmanifest">
<title>考研单词卡 · 主动回忆</title>
<style>
*{{box-sizing:border-box;-webkit-tap-highlight-color:transparent}}
html,body{{margin:0;padding:0}}
body{{font-family:-apple-system,system-ui,"PingFang SC","Microsoft YaHei",sans-serif;
 background:#F4F6F8;color:#1F2937;min-height:100vh;
 padding:env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left)}}
.wrap{{max-width:520px;margin:0 auto;padding:14px 14px 30px}}

/* 顶栏 */
.top{{display:flex;align-items:center;gap:10px;margin-bottom:12px}}
.top h1{{font-size:17px;margin:0;font-weight:700;flex:1}}
.badge{{background:#185FA5;color:#fff;border-radius:999px;padding:3px 10px;font-size:12px;font-weight:600}}
.iconbtn{{width:34px;height:34px;border-radius:50%;border:1px solid #D3D1C7;background:#fff;
 font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center}}

/* 批次条 */
.batches{{display:flex;gap:6px;overflow-x:auto;padding-bottom:6px;margin-bottom:10px;
 scrollbar-width:none;-webkit-overflow-scrolling:touch}}
.batches::-webkit-scrollbar{{display:none}}
.bchip{{flex:0 0 auto;border:1px solid #D3D1C7;background:#fff;border-radius:999px;
 padding:6px 13px;font-size:13px;cursor:pointer;white-space:nowrap;color:#444}}
.bchip.on{{background:#185FA5;color:#fff;border-color:#185FA5;font-weight:600}}
/* 整批音频缓存 */
.dlbox {{ background:#fff; border:1px solid #E3E1D8; border-radius:12px; padding:9px 11px; margin:8px 0 2px; }}
.dlbox button {{ width:100%; background:#F1EFE8; border:1px solid #D3D1C7; border-radius:9px;
  padding:10px; font-size:14.5px; font-weight:600; color:#2C2C2A; cursor:pointer; font-family:inherit; }}
.dlbox button:active {{ transform:scale(.99); }}
.dlbox button.on {{ background:#E1F5EE; border-color:#1D9E75; color:#085041; }}
.dlstat {{ display:block; font-size:12.5px; color:#5F5E5A; margin-top:6px; min-height:16px; }}
.dlprog {{ height:4px; background:#EEEDFE; border-radius:2px; margin-top:5px; overflow:hidden; }}
.dlprog i {{ display:block; height:100%; width:0; background:#1D9E75; border-radius:2px; transition:width .2s; }}

.bchip.done{{border-color:#1D9E75;color:#1D9E75}}
.bchip.ext{{opacity:.62}}
.bchip.done.on{{background:#1D9E75;color:#fff}}

/* 进度条 */
.prog{{height:7px;background:#E3E1D8;border-radius:999px;overflow:hidden;margin-bottom:4px}}
.prog i{{display:block;height:100%;background:linear-gradient(90deg,#185FA5,#1D9E75);border-radius:999px;
 transition:width .25s}}
.ptext{{font-size:12px;color:#6B7280;margin-bottom:12px;display:flex;justify-content:space-between}}

/* 卡片 */
.card{{background:#fff;border:1px solid #D3D1C7;border-radius:16px;padding:18px 16px;
 box-shadow:0 2px 10px rgba(0,0,0,.05)}}
.rootline{{font-size:12px;color:#6B7280;background:#F1EFE8;border-radius:8px;
 padding:5px 10px;margin-bottom:12px}}
.word{{font-size:34px;font-weight:800;letter-spacing:-.5px;line-height:1.15;margin:0 0 4px;
 font-family:Georgia,"Times New Roman",serif}}
.ipa{{font-family:Georgia,serif;font-size:15px;color:#6B7280;margin-bottom:14px}}
.row{{display:flex;gap:9px;align-items:center;margin-bottom:14px;flex-wrap:wrap}}
.spk{{border:none;border-radius:999px;background:#085041;color:#fff;font-size:15px;
 padding:11px 20px;cursor:pointer;font-weight:600;box-shadow:0 2px 6px rgba(8,80,65,.25)}}
.spk:active{{transform:scale(.96)}}
.spk.playing{{background:#D97706}}
.reveal{{flex:1;min-width:130px;border:1.5px solid #185FA5;background:#fff;color:#185FA5;
 border-radius:999px;padding:11px 16px;font-size:14px;font-weight:600;cursor:pointer}}
.reveal:active{{transform:scale(.97)}}
.mean{{font-size:17px;font-weight:600;color:#1F2937;padding:12px;background:#EAF3DE;
 border-radius:10px;margin-bottom:12px;line-height:1.6}}
.ex{{border-top:1px dashed #C9C7BD;padding-top:10px;font-size:13.5px;line-height:1.7;color:#4B5563}}
.ex b{{display:block;font-size:11.5px;color:#6B7280;margin-bottom:2px;font-weight:600}}
.ex .en{{font-family:Georgia,serif;font-size:14.5px;color:#1F2937}}

/* 判定 */
.judge{{display:flex;gap:10px;margin-top:14px}}
.judge button{{flex:1;border-radius:12px;padding:14px;font-size:15px;font-weight:700;cursor:pointer;
 border:1.5px solid #D3D1C7;background:#fff;color:#374151}}
.judge button.known{{border-color:#1D9E75;background:#E1F5EE;color:#085041}}
.judge button.unknown{{border-color:#C2410C;background:#FFF7ED;color:#9A3412}}

/* 底部操作 */
.foot{{display:flex;gap:10px;margin-top:14px}}
.foot button{{flex:1;border:1.5px solid #D3D1C7;background:#fff;border-radius:12px;
 padding:12px;font-size:14px;font-weight:600;cursor:pointer;color:#374151}}
.foot button.primary{{background:#185FA5;border-color:#185FA5;color:#fff}}

/* 弹层 */
.sheet{{position:fixed;inset:0;background:rgba(0,0,0,.45);display:none;z-index:99;
 align-items:flex-end;justify-content:center}}
.sheet.on{{display:flex}}
.sheetbox{{background:#fff;width:100%;max-width:520px;border-radius:18px 18px 0 0;
 padding:18px 16px 26px;max-height:86vh;overflow:auto}}
.sheetbox h3{{margin:0 0 10px;font-size:16px}}
.sheetbox p{{font-size:13.5px;line-height:1.8;color:#4B5563;margin:0 0 8px}}
.sheetbox .kv{{font-size:13px;background:#F4F6F8;border-radius:8px;padding:9px 11px;margin:6px 0}}
.sheetbox ul{{margin:6px 0 10px;padding-left:20px;font-size:13.5px;line-height:1.8}}
.close{{width:100%;border:none;background:#185FA5;color:#fff;border-radius:12px;
 padding:12px;font-size:15px;font-weight:700;margin-top:8px}}

.toast{{position:fixed;left:50%;bottom:26px;transform:translateX(-50%) translateY(20px);
 background:rgba(32,32,30,.94);color:#fff;padding:10px 18px;border-radius:999px;font-size:14px;
 opacity:0;pointer-events:none;transition:.24s;z-index:200}}
.toast.on{{opacity:1;transform:translateX(-50%) translateY(0)}}

.hook{{font-size:12px;color:#5F5E5A;background:#F1EFE8;border-left:3px solid #C9C7BD;
 padding:7px 10px;border-radius:0 6px 6px 0;margin-top:10px;line-height:1.7}}
</style>
</head>
<body>
<div class="wrap">

<div class="top">
  <h1>🎓 考研单词卡</h1>
  <span class="badge" id="streak">连续 0 天</span>
  <button class="iconbtn" id="btnHelp" title="说明">?</button>
</div>

<div class="batches" id="batches"></div>

<div class="dlbox">
  <button id="btnDl">⬇️ 缓存本批音频（之后离线可听）</button>
  <span class="dlstat" id="dlstat"></span>
  <div class="dlprog"><i id="dlbar" style="width:0%"></i></div>
</div>

<div class="prog"><i id="bar" style="width:0%"></i></div>
<div class="ptext">
  <span id="stat">加载中…</span>
  <span id="idx">— / —</span>
</div>

<div class="card" id="card">
  <div class="rootline" id="rootline">—</div>
  <div class="word" id="word">—</div>
  <div class="ipa" id="ipa">—</div>
  <div class="row">
    <button class="spk" id="spk">🔊 播放</button>
    <button class="reveal" id="reveal">显示词义与例句</button>
  </div>
  <div id="ans" style="display:none">
    <div class="mean" id="mean">—</div>
    <div class="ex">
      <b>例句</b>
      <div class="en" id="exEn">—</div>
      <div id="exZh">—</div>
    </div>
    <div class="hook" id="hook">—</div>
  </div>
  <div class="judge">
    <button class="unknown" id="btnUnknown">😵 不认识</button>
    <button class="known" id="btnKnown">😀 认识</button>
  </div>
</div>

<div class="foot">
  <button id="btnPrev">← 上一个</button>
  <button class="primary" id="btnNext">下一个 →</button>
</div>
<div class="foot">
  <button id="btnAuto">▶ 自动联播本批</button>
  <button id="btnReset">重置本批进度</button>
</div>

</div>

<div class="sheet" id="sheet">
  <div class="sheetbox">
    <h3>怎么用</h3>
    <p><b>1. 先看词想义</b> —— 点「显示词义与例句」前，在脑子里说出中文意思。</p>
    <p><b>2. 听发音</b> —— 点 🔊 播放单词发音。音频来自本地词库，随仓库同步到 GitHub Pages。</p>
    <p><b>3. 标记</b> —— 认识点绿，不认识点橙。不认识的词会排到本批末尾再考一次。</p>
    <p><b>4. 加到主屏幕</b> —— 浏览器菜单 →「添加到主屏幕」，之后像 App 一样打开。</p>
    <div class="kv">进度存在本机浏览器（localStorage），换设备不跟着走。<b>要跨设备看进度，用资料库的「2027考研学习进度」表</b>。</div>
    <p><b>批次节奏</b>：<b>01–11 批共 205 词</b>是 61 天冲刺主线，每天 1 批、61 天过 2 轮。
12–20 批（180 词）灰色显示，属拓展，有余力再背。</p>
    <button class="close" id="btnClose">知道了</button>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
var DATA = {json.dumps(JS_DATA, ensure_ascii=False)};
var HOOK = {HOOK_JSON};
var FAM = {FAM_JSON};
var LEARN = {json.dumps(LEARN_BATCHES)};
var CORE = {json.dumps(CORE_BATCHES)};

var state = {{
  batch: 1, i: 0, order: [], unknown: [], auto: false, autoIdx: 0
}};
/* 音频源可切换：默认 GitHub Pages；实测 GitHub Pages 最快，jsDelivr 主站在国内连不上 */
var AUDIO_SOURCES = {{
  'gh':  'https://clementbarnes.github.io/kaoyan-study/audio/',
  'rel': 'audio/'
}};
var AUDIO_MODE = 'gh';
var AUDIO_BASE = AUDIO_SOURCES[AUDIO_MODE];
/* 整批预下载状态：batch -> {{done:n, total:n}} */
var PREFETCH = {{}};
function audioUrl(w){{ return AUDIO_SOURCES[AUDIO_MODE] + w + '.mp3'; }}

/* 整批预下载：一次请求把本批所有音频拉进 Service Worker 缓存，
   之后整批播放零等待、彻底离线。放在页面开头由用户手动触发，避免一进页面就吃流量。 */
function prefetchBatch(b, onProgress){{
  var list = DATA[String(b)] || [];
  if(!list.length) return Promise.resolve();
  var total = list.length, done = 0;
  var i = 0;
  var CONC = 4;                       /* 4路并发，再多会被浏览器掐 */
  function next(){{
    if(i >= total) {{ PREFETCH[b] = {{done:total, total:total}}; if(onProgress) onProgress(total, total, true); return; }}
    var w = list[i++].w;
    var img = new Image();           /* 用Image 预热，走SW fetch 缓存，最省代码 */
    img.onload = img.onerror = function(){{
      done++; if(onProgress) onProgress(done, total, false); next();
    }};
    img.src = audioUrl(w) + '?pf=' + Date.now();
  }}
  for(var k=0;k<CONC;k++) next();
}}

/* 把本批音频下载到浏览器本地缓存（之后整批离线可播） */
function cacheBatch(b, onProg){{
  if(!('caches' in window)) {{ toast('此浏览器不支持离线缓存'); return Promise.reject('no-cache-api'); }}
  var list = DATA[String(b)] || [];
  var total = list.length, done = 0, i = 0;
  var CONC = 4;
  return caches.open('ky-audio-v1').then(function(c){{
    return new Promise(function(resolve, reject){{
      function step(){{
        if(i >= total) {{ resolve({{batch:b, n:total}}); return; }}
        var w = list[i++].w;
        var req = new Request(audioUrl(w), {{mode:'no-cors'}});
        c.match(req).then(function(hit){{
          if(hit) {{ bump(); return; }}
          return fetch(req).then(function(res){{ return c.put(req, res); }})
            .catch(function(){{ /* 离线或失败，跳过 */ }})
            .then(bump);
        }}).catch(bump);
      }}
      function bump(){{
        done++;
        if(onProg) onProg(done, total);
        step();
      }}
      for(var k = 0; k < CONC; k++) step();
    }});
  }});
}}

function loadStore(){{
  try {{ return JSON.parse(localStorage.getItem(STORE_KEY) || '{{}}'); }} catch(e) {{ return {{}}; }}
}}
function saveStore(){{
  /* 迁移旧数据：seen 曾存成数字 0 的批次，统一转成空对象，否则读时索引报错 */
  try {{
    if(store.progress){{
      Object.keys(store.progress).forEach(function(b){{
        var s = store.progress[b];
        if(s && (!s.seen || typeof s.seen !== 'object' || Array.isArray(s.seen))) {{
          s.seen = {{}};
          if(typeof s.known !== 'number') s.known = 0;
          if(!Array.isArray(s.unknownIdx)) s.unknownIdx = [];
        }}
      }});
    }}
    localStorage.setItem(STORE_KEY, JSON.stringify(store));
  }} catch(e) {{}}
}}
var store = loadStore();
if(!store.progress) store.progress = {{}};
if(!store.streak) store.streak = {{count:0, last:''}};

function $(s){{ return document.querySelector(s); }}

function toast(msg){{
  var t=$('#toast'); t.textContent=msg; t.classList.add('on');
  clearTimeout(window.__tt); window.__tt=setTimeout(function(){{t.classList.remove('on');}},1900);
}}

function today(){{
  var d=new Date(); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}}

/* 批次条 */
function renderBatches(){{
  var box=$('#batches'); box.innerHTML='';
  LEARN.forEach(function(b){{
    var total=DATA[String(b)].length;
    var done=(store.progress[b]||{{}}).known||0;
    var el=document.createElement('button');
    el.className='bchip'+(b===state.batch?' on':'')+((done>=total&&total>0)?' done':'')
      +(CORE.indexOf(b)<0?' ext':'');
    el.textContent=String(b).padStart(2,'0')+'批 '+(done>0?done+'/'+total:'');
    el.onclick=function(){{ switchBatch(b); }};
    box.appendChild(el);
  }});
}}

function batchStat(b){{
  var s=store.progress[b]||{{known:0,seen:{{}}}};
  /* 容错：旧版本 seen 存的是数字 0，直接下标访问会抛 TypeError 把整个渲染打断。
     这里统一规范成对象，seen 不是对象就当空。 */
  if(!s || typeof s !== 'object') s = {{known:0, seen:{{}}}};
  if(!s.seen || typeof s.seen !== 'object' || Array.isArray(s.seen)) s.seen = {{}};
  if(typeof s.known !== 'number') s.known = 0;
  if(!Array.isArray(s.unknownIdx)) s.unknownIdx = [];
  /* knownSet：记录哪些词已计入 known，判重用，防止重复点「认识」导致计数溢出 */
  if(!s.knownSet || typeof s.knownSet !== 'object' || Array.isArray(s.knownSet)) s.knownSet = {{}};
  return s;
}}

function switchBatch(b){{
  state.batch=b; state.i=0; state.unknown=[]; state.auto=false;
  updateAutoBtn();
  renderBatches();
  render();
}}

/* 组装当前批的顺序：未标记的在前（按原序），标记过的不再出现；不认识的排到末尾 */
function buildOrder(){{
  var list=DATA[String(state.batch)]||[];
  var st=batchStat(state.batch);
  var pending=[], done=[];
  list.forEach(function(d,idx){{
    if(st.seen&&st.seen[idx]) done.push(idx); else pending.push(idx);
  }});
  // 未标记的先来，unknown 追加到末尾
  var unknownSet={{}};
  (st.unknownIdx||{{}}).forEach(function(x){{unknownSet[x]=1;}});
  /* 「不认识」的词必须排到本批末尾重考 —— 哪怕它已经 seen 过。
     所以先从 done 里摘出来，放到 pending 之后。 */
  var doneReal = done.filter(function(x){{ return !unknownSet[x]; }});
  var reTest  = done.filter(function(x){{ return unknownSet[x]; }});
  var head = pending.filter(function(x){{return !unknownSet[x];}});
  var tail = pending.filter(function(x){{return unknownSet[x];}});
  /* 顺序：未看过的 → 未看但不认识的 → 已看过但不认识的（重考）→ 已掌握的 */
  return head.concat(tail, reTest, doneReal);
}}

function cur(){{
  var order=buildOrder();
  if(!order.length) return null;
  if(state.i>=order.length) state.i=0;
  return order[state.i];
}}

function render(){{
  var list=DATA[String(state.batch)]||[];
  var st=batchStat(state.batch);
  var total=list.length;
  var order=buildOrder();
  var idx=cur();
  var pct=total?Math.round((st.known||0)/total*100):0;
  $('#bar').style.width=pct+'%';
  $('#stat').textContent='已掌握 '+(st.known||0)+' / '+total+' 词';
  $('#idx').textContent=order.length? ((state.i+1)+' / '+order.length) : '— / —';

  if(idx==null){{
    $('#word').textContent='🎉'; $('#ipa').textContent='本批已完成';
    $('#rootline').textContent='点「重置本批进度」再来一轮';
    $('#ans').style.display='none';
    $('#idx').textContent='✓';
    return;
  }}
  var d=list[idx];
  $('#rootline').textContent=(FAM[d.r]? FAM[d.r]+' · ':'')+d.r+'   第'+(idx+1)+'/'+total+' 词';
  $('#word').textContent=d.w;
  $('#ipa').textContent=d.i;
  $('#mean').textContent=d.m;
  $('#exEn').textContent=d.e;
  $('#exZh').textContent=d.z;
  $('#hook').textContent=HOOK[d.r]||'';
  $('#ans').style.display='none';
  $('#reveal').textContent='显示词义与例句';
}}

var curAudio=null;
function play(w){{
  if(curAudio){{curAudio.pause();curAudio=null;}}
  var a=new Audio(audioUrl(w));
  var btn=$('#spk');
  a.onplay=function(){{btn.classList.add('playing');btn.textContent='🔊 播放中';}};
  a.onended=function(){{btn.classList.remove('playing');btn.textContent='🔊 播放';}};
  a.onerror=function(){{
    btn.classList.remove('playing'); btn.textContent='🔊 播放';
    /* 自动降级到相对路径重试一次（本地双击打开时有效） */
    if(AUDIO_MODE !== 'rel'){{
      AUDIO_MODE = 'rel';
      toast('主源加载失败，已切换本地源');
      play(w);
      return;
    }}
    toast('音频加载失败，请检查网络');
  }};
  a.play();
  curAudio=a;
}}

/* 联播 */
var autoTimer=null;
function updateAutoBtn(){{ $('#btnAuto').textContent = state.auto?'⏸ 停止联播':'▶ 自动联播本批'; }}

function autoPlay(){{
  var list=DATA[String(state.batch)]||[];
  var st=batchStat(state.batch);
  var order=buildOrder();
  state.autoIdx=0;
  state.auto=true; updateAutoBtn();
  function next(){{
    if(!state.auto) return;
    if(state.autoIdx>=order.length){{
      state.auto=false; updateAutoBtn(); toast('本批联播完成');
      return;
    }}
    var idx=order[state.autoIdx++];
    var d=list[idx];
    // 同步界面到当前词
    state.i = state.autoIdx-1;
    var realIdx = idx;
    var full=buildOrder();
    var pos=full.indexOf(realIdx);
    if(pos>=0) state.i=pos;
    render();
    play(d.w);
    autoTimer=setTimeout(next,3200);
  }}
  next();
}}

/* 判定 */
function judge(known){{
  var list=DATA[String(state.batch)]||[];
  var st=batchStat(state.batch);
  if(!st.seen) st.seen={{}};
  if(!st.unknownIdx) st.unknownIdx=[];
  var idx=cur();
  if(idx==null) return;
  var wasKnown = !!st.knownSet[idx];     /* 之前是否已算作「认识」 */
  st.seen[idx]=1;
  if(known){{
    /* 计数去重：同一词重复点「认识」不重复累加，否则 known 会超过总词数 */
    if(!wasKnown){{ st.known=(st.known||0)+1; st.knownSet[idx]=1; }}
    var p=st.unknownIdx.indexOf(idx);
    if(p>=0) st.unknownIdx.splice(p,1);
  }} else {{
    /* 标「不认识」= 撤销「认识」资格，该词必须重新考 */
    if(wasKnown){{ st.known=Math.max(0,(st.known||0)-1); delete st.knownSet[idx]; }}
    if(st.unknownIdx.indexOf(idx)<0) st.unknownIdx.push(idx);
  }}
  store.progress[state.batch]=st;
  // 连续天数
  var t=today();
  if(store.streak.last!==t){{
    var y=new Date(); y.setDate(y.getDate()-1);
    var ys=y.getFullYear()+'-'+String(y.getMonth()+1).padStart(2,'0')+'-'+String(y.getDate()).padStart(2,'0');
    store.streak.count = (store.streak.last===ys) ? (store.streak.count||0)+1 : 1;
    store.streak.last=t;
  }}
  saveStore();
  renderBatches();
  state.i++;
  render();
  toast(known?'✓ 标记为认识':'↻ 排到本批末尾再考');
}}

/* 事件 */
$('#spk').onclick=function(){{
  var idx=cur(); if(idx==null) return;
  play((DATA[String(state.batch)]||[])[idx].w);
}};
$('#reveal').onclick=function(){{
  var a=$('#ans');
  if(a.style.display==='none'){{a.style.display='block';this.textContent='收起答案';}}
  else {{a.style.display='none';this.textContent='显示词义与例句';}}
}};
$('#btnKnown').onclick=function(){{ judge(true); }};
$('#btnUnknown').onclick=function(){{ judge(false); }};
$('#btnNext').onclick=function(){{ state.i++; render(); }};
$('#btnPrev').onclick=function(){{ state.i=Math.max(0,state.i-1); render(); }};
$('#btnAuto').onclick=function(){{
  if(state.auto){{ state.auto=false; clearTimeout(autoTimer); updateAutoBtn(); }}
  else autoPlay();
}};
/* 整批音频缓存：一次下载本批，之后离线可听 */
$('#btnDl').onclick = function(){{
  var btn = this;
  if(btn.classList.contains('on')) {{
    btn.textContent = '⬇️ 缓存本批音频（之后离线可听）';
    btn.classList.remove('on');
    $('#dlstat').textContent = '';
    $('#dlbar').style.width = '0%';
    return;
  }}
  var b = state.batch, list = DATA[String(b)] || [];
  if(!list.length) return;
  btn.classList.add('on');
  btn.textContent = '⏳ 正在缓存…';
  $('#dlstat').textContent = '0 / ' + list.length;
  cacheBatch(b, function(d, t){{
    $('#dlbar').style.width = Math.round(d / t * 100) + '%';
    if(d >= t){{
      btn.textContent = '✓ 本批已缓存 · 点此清除';
      $('#dlstat').textContent = '本批 ' + t + ' 个音频已存本地，断网也能播';
      toast('本批缓存完成，之后离线可听');
    }} else {{
      $('#dlstat').textContent = d + ' / ' + t + ' 下载中…';
    }}
  }}).catch(function(){{
    btn.classList.remove('on');
    btn.textContent = '⬇️ 缓存本批音频（之后离线可听）';
    $('#dlstat').textContent = '缓存失败，请检查网络';
  }});
}};

$('#btnReset').onclick=function(){{
  if(!confirm('重置第'+String(state.batch).padStart(2,'0')+'批的掌握记录？')) return;
  store.progress[state.batch]={{known:0,seen:{{}},unknownIdx:[]}};
  state.i=0; saveStore(); renderBatches(); render(); toast('已重置');
}};
$('#btnHelp').onclick=function(){{ $('#sheet').classList.add('on'); }};
$('#btnClose').onclick=function(){{ $('#sheet').classList.remove('on'); }};
$('#sheet').onclick=function(e){{ if(e.target===this) this.classList.remove('on'); }};

document.addEventListener('keydown',function(e){{
  if(e.key===' '){{e.preventDefault();$('#spk').click();}}
  else if(e.key==='ArrowRight'){{$('#btnNext').click();}}
  else if(e.key==='ArrowLeft'){{$('#btnPrev').click();}}
}});

/* 初始化 */
(function init(){{
  try {{
    var t=today();
    $('#streak').textContent='连续 '+(store.streak.count||0)+' 天';
    renderBatches();
    render();
  }} catch(err){{
    /* 兜底：渲染失败时给出可见提示，而不是留一块白板让人以为没词了 */
    console.error('[单词卡] 初始化失败:', err);
    var w=$('#word');
    if(w) w.textContent='⚠️';
    var st=$('#stat');
    if(st) st.textContent='数据读取出错：'+(err && err.message || err);
    var rs=$('#rootline');
    if(rs) rs.textContent='点「重置本批进度」可修复';
  }}
  // PWA 注册
  if('serviceWorker' in navigator){{
    navigator.serviceWorker.register('sw.js').catch(function(){{}});
  }}
}})();
</script>
</body>
</html>
'''

MANIFEST = {
    "name": "考研单词卡",
    "short_name": "考研单词",
    "description": "2027 考研英语二 · 主动回忆单词卡（385 词 / 01-11 批为主线）",
    "start_url": "单词卡.html",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#F4F6F8",
    "theme_color": "#185FA5",
    "lang": "zh-CN",
    "icons": [
        {
            "src": "data:image/svg+xml;base64," + __import__('base64').b64encode(
                b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">'
                b'<rect width="192" height="192" rx="42" fill="#185FA5"/>'
                b'<text x="96" y="128" font-size="96" text-anchor="middle" fill="#fff" '
                b'font-family="Georgia,serif" font-weight="bold">W</text></svg>'
            ).decode(),
            "sizes": "192x192",
            "type": "image/svg+xml",
            "purpose": "any maskable"
        }
    ]
}

SW = '''/* 考研单词卡 Service Worker —— 缓存页面与已播放过的音频 */
var CACHE = 'ky-words-v1';
var SHELL = ['单词卡.html', 'manifest.webmanifest'];

self.addEventListener('install', function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return c.addAll(SHELL).catch(function () {});
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        return k === CACHE ? null : caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

/* 音频：cache-first（学过的词离线也能播），其余网络优先 */
self.addEventListener('fetch', function (e) {
  var req = e.request;
  if (req.method !== 'GET') return;
  var url = new URL(req.url);
  if (url.origin !== location.origin) return;

  if (/\\.mp3$/.test(url.pathname)) {
    e.respondWith(
      caches.match(req).then(function (hit) {
        if (hit) return hit;
        return fetch(req).then(function (res) {
          if (res && res.status === 200) {
            var copy = res.clone();
            caches.open(CACHE).then(function (c) { c.put(req, copy); });
          }
          return res;
        });
      })
    );
    return;
  }

  e.respondWith(
    caches.match(req).then(function (hit) {
      return hit || fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic') {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })
  );
});
'''

open('单词卡.html', 'w', encoding='utf-8').write(HTML)
open('manifest.webmanifest', 'w', encoding='utf-8').write(
    json.dumps(MANIFEST, ensure_ascii=False, indent=1))
open('sw.js', 'w', encoding='utf-8').write(SW)
print(f"OK 单词卡.html  bytes={len(HTML)}  batches={len(LEARN_BATCHES)}  "
      f"words={sum(len(v) for v in JS_DATA.values())}")
