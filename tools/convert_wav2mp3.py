# -*- coding: utf-8 -*-
"""把 audio/*.wav 批量转成 audio/*.mp3（libmp3lame 64k 单声道 24kHz，约 1/6 体积，加载更快）。

依赖：系统 PATH 里已有 ffmpeg（本机 WinGet Gyan.FFmpeg 9.0 full）。
用法：
    python -B tools/convert_wav2mp3.py            # 全部转换，跳过已存在
    python -B tools/convert_wav2mp3.py --delete   # 转换后删除同名 .wav
"""
import glob, os, subprocess, sys

SRC = "audio"
DELETE = "--delete" in sys.argv
files = sorted(glob.glob(os.path.join(SRC, "*.wav")))
total = len(files)
done = skip = fail = 0

for f in files:
    out = f[:-4] + ".mp3"
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        skip += 1
        continue
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", f,
         "-c:a", "libmp3lame", "-b:a", "64k", "-ac", "1", "-ar", "24000", out])
    if r.returncode == 0:
        done += 1
        if DELETE:
            os.remove(f)
    else:
        fail += 1
        print("FAIL:", f)
    if (done + skip + fail) % 50 == 0:
        print(f"进度 {done + skip + fail}/{total}")

print(f"完成：新建 {done}、跳过 {skip}、失败 {fail}、共 {total}")
