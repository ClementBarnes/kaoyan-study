# -*- coding: utf-8 -*-
"""TTS 工作流：把 words_tts.json 渲染成「单词×2 → 词义 → 例句 → 翻译」连续音频。

引擎：edge-tts（微软在线神经语音，免费、无需密钥/GPU）
拼接：miniaudio 解码 MP3 → 统一 24kHz 单声道 PCM → 插入静音间隔 → ffmpeg(libmp3lame 64k) 编码 MP3
      （edge-tts/miniaudio 零密钥；最终编码 MP3 需 ffmpeg，体积约为 WAV 的 1/6，加载更快）

听书结构（与轻听英语一致）：
    [单词] [停顿] [单词] [较长停顿] [词义(中音)] [停顿]
    [例句(英音)] [停顿] [例句翻译(中音)] [尾停顿]

用法：
    python gen_audio.py                 # 生成全部 185 词
    python gen_audio.py --limit 8       # 仅生成前 8 词（试听）
    python gen_audio.py --voice-en en-US-GuyNeural --voice-zh zh-CN-YunxiNeural
依赖：
    pip install edge-tts miniaudio
输入：words_tts.json（由 build_master.py 导出，单一事实源）
输出：audio/<word>.mp3  +  听书播放器.html（按词播放，可挂 GitHub Pages 在手机听）
"""
import asyncio, json, os, re, subprocess, sys, wave, html
import edge_tts, miniaudio

SR = 24000                      # 统一采样率（语音足够清晰，文件更小）
CH = 1                          # 单声道
EN_VOICE = "en-US-AriaNeural"   # 英文：清晰中性美音
ZH_VOICE = "zh-CN-XiaoxiaoNeural"  # 中文：自然女声
OUT_DIR = "audio"
IDX = "听书播放器.html"   # 纯音频播放页独立命名；合并页是 单词总表.html（含每词播放条+每批联播）。绝不写 index.html / 听书.html

# 停顿（秒）：单词两遍之间短、词义前后长一点，模拟"听书"节奏
PAUSE_WORD_GAP = 0.35      # 单词第1遍→第2遍
PAUSE_AFTER_WORD = 0.65    # 单词两遍→词义
PAUSE_AFTER_MEAN = 0.55    # 词义→例句
PAUSE_AFTER_EX_EN = 0.55   # 例句→翻译
PAUSE_TAIL = 0.80          # 整词结尾

POS_RE = re.compile(r"^[a-z][a-z./]*\s+", re.I)  # 去掉释义开头的 "v. " / "v./n. "

def strip_pos(meaning: str) -> str:
    """词义字段形如 'v. 检查，视察'，去掉词性前缀只留中文，听感更干净。"""
    m = POS_RE.match(meaning)
    if m:
        return meaning[m.end():].strip() or meaning
    return meaning

async def synth(text: str, voice: str) -> bytes:
    """用 edge-tts 拉取一段 MP3 的字节流。"""
    com = edge_tts.Communicate(text, voice)
    buf = b""
    async for chunk in com.stream():
        if chunk["type"] == "audio":
            buf += chunk["data"]
    return buf

async def synth_retry(text: str, voice: str, tries: int = 3) -> bytes:
    """带重试的合成，规避偶发网络/限流失败。"""
    last = None
    for i in range(tries):
        try:
            return await synth(text, voice)
        except Exception as e:
            last = e
            if i < tries - 1:
                await asyncio.sleep(1.5 * (i + 1))
    raise last

def decode_mp3(data: bytes) -> bytes:
    """MP3 字节 → 16-bit PCM 原始字节（24kHz 单声道）。"""
    snd = miniaudio.decode(data, output_format=miniaudio.SampleFormat.SIGNED16,
                           nchannels=CH, sample_rate=SR)
    samples = snd.samples
    return samples.tobytes() if hasattr(samples, "tobytes") else bytes(samples)

def silence(sec: float) -> bytes:
    return b"\x00" * int(SR * CH * 2 * sec)

async def build_pcm(segments) -> bytes:
    """segments = [(text, voice), ...]；按顺序拼接并插入停顿。"""
    pcm = b""
    gaps = [PAUSE_WORD_GAP, PAUSE_AFTER_WORD, PAUSE_AFTER_MEAN,
            PAUSE_AFTER_EX_EN, PAUSE_TAIL]
    for i, (text, voice) in enumerate(segments):
        pcm += decode_mp3(await synth_retry(text, voice))
        if i < len(gaps):
            pcm += silence(gaps[i])
    return pcm

def write_mp3(path: str, pcm: bytes):
    tmp = path + ".tmp.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(CH)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp,
                    "-c:a", "libmp3lame", "-b:a", "64k", "-ac", "1", "-ar", str(SR),
                    path], check=True)
    os.remove(tmp)

async def main():
    def argval(flag):
        return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None

    limit = int(argval("--limit")) if argval("--limit") else None
    from_b = int(argval("--from-batch")) if argval("--from-batch") else None
    to_b = int(argval("--to-batch")) if argval("--to-batch") else None
    if argval("--voice-en"):
        global EN_VOICE
        EN_VOICE = argval("--voice-en")
    if argval("--voice-zh"):
        global ZH_VOICE
        ZH_VOICE = argval("--voice-zh")

    words = json.load(open("words_tts.json", encoding="utf-8"))
    if from_b is not None:
        words = [w for w in words if w["batch"] >= from_b]
    if to_b is not None:
        words = [w for w in words if w["batch"] <= to_b]
    if limit:
        words = words[:limit]
    os.makedirs(OUT_DIR, exist_ok=True)

    rows = []
    done = skip = 0
    for w in words:
        word = w["word"]
        path = os.path.join(OUT_DIR, word + ".mp3")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            skip += 1
            rows.append(w)
            continue
        meaning_zh = strip_pos(w["meaning"])
        segments = [
            (word, EN_VOICE),
            (word, EN_VOICE),
            (meaning_zh, ZH_VOICE),
            (w["example_en"], EN_VOICE),
            (w["example_zh"], ZH_VOICE),
        ]
        try:
            pcm = await build_pcm(segments)
        except Exception as e:
            print(f"  ✗ {word} 失败: {e}")
            continue
        write_mp3(path, pcm)
        done += 1
        rows.append(w)
        print(f"  ✓ {word} ({len(pcm)//(SR*CH*2)}s)")

    # 生成按词播放页（按批次分组）
    def card(w):
        return (
            f"<div class='c'><div class='w'>{html.escape(w['word'])} "
            f"<span class='ipa'>{html.escape(w['ipa'])}</span></div>"
            f"<div class='m'>{html.escape(w['meaning'])}</div>"
            f"<div class='ex'>{html.escape(w['example_en'])} {html.escape(w['example_zh'])}</div>"
            f"<audio controls preload='none' src='{OUT_DIR}/{html.escape(w['word'])}.mp3'></audio></div>")
    parts, last_b = [], None
    for w in rows:
        if w["batch"] != last_b:
            parts.append(f"<div class='batchH'>第{w['batch']:02d}批</div>")
            last_b = w["batch"]
        parts.append(card(w))
    cards_html = "\n".join(parts)
    page = """<!DOCTYPE html><html lang='zh-CN'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>考研词根 · 听书音频</title><style>
body{font-family:system-ui,'Microsoft YaHei',sans-serif;background:#f6f7f9;color:#1f2937;max-width:760px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:20px;margin:0 0 4px} .sub{color:#6b7280;font-size:13px;margin-bottom:14px}
.toolbar{position:sticky;top:0;z-index:10;background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:10px 12px;margin-bottom:14px;display:flex;gap:8px;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.toolbar button{border:none;border-radius:8px;padding:9px 16px;font-size:14px;font-weight:600;cursor:pointer;color:#fff}
#playAll{background:#2f6bff} #stop{background:#9aa3af}
.c{border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;margin:12px 0;background:#fff;transition:box-shadow .2s}
.c.on{border-color:#2f6bff;box-shadow:0 0 0 2px rgba(47,107,255,.25);background:#f7faff}
.w{font-size:17px;font-weight:700} .ipa{color:#6b7280;font-style:italic;font-weight:400;margin-left:6px}
.m{color:#374151;font-size:14px;margin:2px 0} .ex{color:#6b7280;font-size:13px;margin-bottom:8px}
.batchH{font-size:13px;font-weight:700;color:#2f6bff;background:#eaf1ff;border-radius:6px;padding:5px 10px;margin:18px 0 4px}
audio{width:100%}
.back-home{position:fixed;right:18px;bottom:18px;z-index:9999;display:inline-flex;align-items:center;gap:6px;padding:10px 16px;background:#2C2C2A;color:#fff;font-size:14px;font-weight:600;text-decoration:none;border-radius:999px;box-shadow:0 4px 14px rgba(0,0,0,.22);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.back-home:active{transform:scale(.96)}
@media(max-width:600px){.back-home{padding:9px 13px;font-size:13px;right:12px;bottom:12px}}
</style></head><body>
<a href='index.html' class='back-home' title='返回备考中心首页'>← 目录</a>
<h1>考研词根 · 听书音频</h1>
<p class='sub'>每词：单词×2 → 词义 → 例句 → 翻译。点「联播全部」连续听，播完自动下一个。</p>
<div class='toolbar'>
  <button id='playAll'>▶ 联播全部</button>
  <button id='stop'>■ 停止</button>
</div>
__CARDS__
<script>
const audios = Array.from(document.querySelectorAll('audio'));
const cards  = Array.from(document.querySelectorAll('.c'));
const playAll = document.getElementById('playAll');
const stopBtn = document.getElementById('stop');
let chained = false;

function setActive(i){
  cards.forEach((c,idx)=>c.classList.toggle('on', idx===i));
}

// 同一时间只允许一个音频播放 + 每次都从头开始
audios.forEach(a => a.addEventListener('play', ()=>{
  audios.forEach(o => { if(o !== a) o.pause(); });
  setActive(audios.indexOf(a));
  // 无论之前停在哪，每次播放都重置到 0:00，保证完整从头听
  if(a.currentTime > 0.3) a.currentTime = 0;
}));

// 联播：播完自动播下一个
audios.forEach((a, i) => a.addEventListener('ended', ()=>{
  if(chained && i < audios.length - 1){
    audios[i+1].currentTime = 0;
    audios[i+1].play();
  } else if(i === audios.length - 1){
    chained = false;
    playAll.textContent = '▶ 联播全部';
    setActive(-1);
  }
}));

playAll.addEventListener('click', ()=>{
  chained = !chained;
  if(chained){
    audios.forEach(o => o.pause());
    audios[0].currentTime = 0;
    audios[0].play();
    playAll.textContent = '⏸ 停止联播';
  } else {
    audios.forEach(o => o.pause());
    playAll.textContent = '▶ 联播全部';
    setActive(-1);
  }
});

stopBtn.addEventListener('click', ()=>{
  chained = false;
  audios.forEach(o => o.pause());
  playAll.textContent = '▶ 联播全部';
  setActive(-1);
});
</script>
</body></html>"""
    if "--page" in sys.argv:  # 可选：生成纯音频播放页（合并页《单词总表》已内嵌音频，默认不再生成）
        page = page.replace("__CARDS__", cards_html)
        with open(IDX, "w", encoding="utf-8") as f:
            f.write(page)
        print(f"\n完成：新建 {done} 个、跳过已存在 {skip} 个；播放页 → {IDX}")
    else:
        print(f"\n完成：新建 {done} 个、跳过已存在 {skip} 个（音频就绪；播放展示见《单词总表》）")

asyncio.run(main())
