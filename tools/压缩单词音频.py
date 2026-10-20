# -*- coding: utf-8 -*-
"""把 audio/ 下 385 个单词发音压缩瘦身，体积约为原来的一半。

原参数：24kHz / mono / 64kbps（单词发音用这个规格浪费）
新参数：16kHz / mono / 32kbps（语音频段 300–3400Hz，足够清晰）

同时按批次生成「批次音频包」：把同批所有词拼成一个大 mp3 + 索引 JSON，
前端一次请求就能拿到整批，避开 385 次零散往返。

用法：
    python -B tools/压缩单词音频.py compress   # 只压缩
    python -B tools/压缩单词音频.py pack       # 只打包（需先 compress）
    python -B tools/压缩单词音频.py all
"""
import io
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, 'audio')
PACK = os.path.join(ROOT, 'audio_pack')
WORDS = os.path.join(ROOT, 'words_tts.json')

FFMPEG = 'ffmpeg'
FFPROBE = 'ffprobe'


def load_words():
    with io.open(WORDS, encoding='utf-8') as f:
        return json.load(f)


def compress_one(word):
    src = os.path.join(AUDIO, word + '.mp3')
    if not os.path.exists(src):
        return word, 'missing', 0
    before = os.path.getsize(src)
    tmp = src + '.new.mp3'          # 结尾必须保留 .mp3，否则 ffmpeg 猜不出输出格式
    cmd = [FFMPEG, '-v', 'error', '-i', src,
           '-ac', '1', '-ar', '16000', '-b:a', '32k',
           '-codec:a', 'libmp3lame', '-map_metadata', '-1',
           '-f', 'mp3', tmp, '-y']
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0 or not os.path.exists(tmp):
        return word, 'fail', before
    after = os.path.getsize(tmp)
    if after >= before:
        os.remove(tmp)          # 压不动就保留原文件
        return word, 'skip', before
    os.replace(tmp, src)
    return word, 'ok', before - after


def do_compress(words):
    targets = [w['word'] for w in words]
    saved = 0
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for word, status, delta in ex.map(compress_one, targets):
            if status == 'ok':
                ok += 1
                saved += delta
    total = sum(os.path.getsize(os.path.join(AUDIO, w + '.mp3'))
                for w in targets if os.path.exists(os.path.join(AUDIO, w + '.mp3')))
    print('压缩完成：%d/%d 个文件变小，总体积 %.1f MB' % (ok, len(targets), total / 1048576))
    return total


def pack_one(batch, words):
    items = [w for w in words if w.get('batch') == batch]
    if not items:
        return batch, 0, []
    items.sort(key=lambda x: x['word'])

    # 用 concat demuxer 无损拼接
    listf = os.path.join(PACK, '_b%02d.txt' % batch)
    lines = []
    for w in items:
        lines.append("file '%s'" % os.path.join(AUDIO, w['word'] + '.mp3').replace('\\', '/'))
    with io.open(listf, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    out = os.path.join(PACK, 'batch%02d.mp3' % batch)
    r = subprocess.run(
        [FFMPEG, '-v', 'error', '-f', 'concat', '-safe', '0', '-i', listf,
         '-c', 'copy', out, '-y'], capture_output=True)
    os.remove(listf)
    if r.returncode != 0 or not os.path.exists(out):
        return batch, 0, []

    # 逐词测时长，拼索引
    index = []
    for w in items:
        p = os.path.join(AUDIO, w['word'] + '.mp3')
        d = subprocess.run(
            [FFPROBE, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'csv=p=0', p], capture_output=True)
        try:
            dur = float(d.stdout.decode().strip())
        except Exception:
            dur = 0.0
        index.append({'word': w['word'], 'start': None, 'dur': round(dur, 3)})

    t = 0.0
    for it in index:
        it['start'] = round(t, 3)
        t += it['dur']
    index[-1]['dur'] = round(index[-1]['dur'] + (t - sum(x['dur'] for x in index)), 3)

    idx = {'batch': batch, 'file': 'batch%02d.mp3' % batch,
           'total': round(t, 3), 'items': index}
    with io.open(os.path.join(PACK, 'batch%02d.json' % batch), 'w', encoding='utf-8') as f:
        json.dump(idx, f, ensure_ascii=False, separators=(',', ':'))

    return batch, os.path.getsize(out), len(items)


def do_pack(words):
    batches = sorted(set(w.get('batch') for w in words))
    os.makedirs(PACK, exist_ok=True)
    rows = []
    for b in batches:
        bno, size, n = pack_one(b, words)
        rows.append((bno, n, size))
        print('  第%02d批  %2d 词  %.0f KB' % (bno, n, size / 1024))
    print('打包完成：%d 个批次包' % len(rows))
    return rows


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    ws = load_words()
    if cmd in ('compress', 'all'):
        do_compress(ws)
    if cmd in ('pack', 'all'):
        do_pack(ws)