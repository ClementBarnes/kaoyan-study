# -*- coding: utf-8 -*-
"""从学信网（yz.chsi.com.cn）抓取历年考研英语二真题，落盘为 papers/<year>/text.txt。

官方来源：教育部学生服务与素质发展中心 / 跨考教育转载，页面含完形+阅读4篇+新题型+翻译+写作。
用法：python -B tools/fetch_kaoyan_papers.py 2010
"""
import io, os, re, sys, time
import urllib.request

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36Chrome/120.0 Safari/537.36'
BASE = 'https://yz.chsi.com.cn/kyzx/en/{ym}/{ym}13/{id}-{p}.html'


def get(url, tries=3):
    """用 curl 取（urllib 对该站会静默截断，返回不完整 HTML）。"""
    import subprocess
    for i in range(tries):
        try:
            r = subprocess.run(
                ['curl', '-sL', '--max-time', '60', '-A', UA, url],
                capture_output=True)
            if r.returncode == 0 and len(r.stdout) > 5000:
                return r.stdout.decode('utf-8', 'ignore')
            print(f'  retry {i+1}: rc={r.returncode} bytes={len(r.stdout)}')
        except Exception as e:
            print(f'  retry {i+1}: {e}')
        time.sleep(2)
    return ''


def clean(html):
    s = re.sub(r'(?is)<(script|style).*?</\1>', ' ', html)
    s = re.sub(r'(?s)<[^>]+>', '\n', s)
    for a, b in [('&nbsp;', ' '), ('&ensp;', ' '), ('&emsp;', ' '), ('&amp;', '&'),
                 ('&quot;', '"'), ('&ldquo;', '"'), ('&rdquo;', '"'),
                 ('&lsquo;', "'"), ('&rsquo;', "'"), ('&mdash;', '—'),
                 ('&ndash;', '–'), ('&lt;', '<'), ('&gt;', '>'), ('&middot;', '·')]:
        s = s.replace(a, b)
    lines = [x.strip() for x in s.split('\n')]
    return '\n'.join([x for x in lines if x])


def ocr_fix(t):
    """修官方页 OCR 错字（空格丢失、字母大小写、实体残留）。"""
    r = [('\u101b70m', '\u00a370m'), ('\u010170m', '\u00a370m'),
         ('\u0100m', 'm'),
         ('hadwitnessed', 'had witnessed'), ('hadsuffered', 'had suffered'),
         ('victoryies', 'victories'), ('to2008', 'to 2008'), ('from2003', 'from 2003'),
         ('ture', 'true'), ('DuDa', 'D. A'), ('Da female', 'D. A female'),
         ('public tan women', 'public than women'), ('tan women', 'than women'),
         ('50percent', '50 percent'), ('D.a brief', 'D. A brief'),
         ('20007', '2007'), ('Mian idea', 'main idea'), ('wofe', 'wife'),
         ('Shsring', 'Sharing'), ('2025,17th,19th', '2025, 17th, 19th')]
    for a, b in r:
        t = t.replace(a, b)
    # 修复选项字母粘连（Dxxx / Axxx）
    t = re.sub(r'\b([ABCD]) (?=[a-z]{3,})', r'\1. ', t)
    t = re.sub(r'(?<=[a-z])\b([ABCD])(?=\s*[A-Z][a-z])', r' \1 ', t)
    return t


def fetch(year, artid):
    out = f'papers/{year}'
    os.makedirs(out, exist_ok=True)
    full = []
    for p in (1, 2):
        ym = f'{year}01'
        url = BASE.format(ym=ym, id=artid, p=p)
        print(f'  p{p} <- {url}')
        full.append(get(url))
    # 逐页清洗并各自切正文再合并。
    # 注意：p2 里 'Section III'（翻译部分）出现在 Text3/Text4 之后，
    # 所以锚点必须取「最早出现」的那个，否则会把 Text3/4 切掉。
    parts = []
    for html in full:
        t = clean(html)
        cands = []
        for kw in ('Use of English', 'Txet', 'Text1'):
            i = t.find(kw)
            if i >= 0:
                cands.append(i)
        a = min(cands) if cands else 0
        ends = []
        for k in ('近期热点', '考研工具箱', '版权所有', 'Copyright'):
            i = t.find(k)
            if i > a:
                ends.append(i)
        b = min(ends) if ends else len(t)
        parts.append(t[a:b] if b > a else t[a:])
    body = ocr_fix('\n'.join(parts))

    txt = body
    path = f'{out}/text.txt'
    io.open(path, 'w', encoding='utf-8').write(txt)
    io.open(f'{out}/body.txt', 'w', encoding='utf-8').write(body)

    marks = {k: (k in body) for k in
             ['Text1', 'Text2', 'Txet3', 'Text4', '真题答案', '新题型', 'Directions']}
    print(f'  -> {path} ({len(body)} chars) marks={marks}')
    return body


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        year, artid = arg.split(':')
        print(f'=== {year} ===')
        fetch(year, artid)
