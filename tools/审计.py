# -*- coding: utf-8 -*-
"""考研站代码审计工具 —— 一次性扫出多类隐患。

覆盖：
  1. Python 脚本语法（py_compile）
  2. 生成产物 HTML 的 JS 语法（node --check）
  3. JS 非法混用：function(...) =>  （匿名函数表达式后接箭头，JS 语法错误）
  4. 运行时错误（无头 Edge 注入探针，捕获 error / unhandledrejection）
  5. 死链（相对路径 href/src 指向不存在的文件）
  6. 答案泄露（学习单类页面：答案出现在作答区之前）
  7. 数据一致性（words_tts.json ↔ audio/ ↔ audio_pack/）
  8. f-string 花括号陷阱（生成脚本里未转义的单花括号出现在 JS 字面量位置）

用法：
    python -B tools/审计.py            # 全量审计
    python -B tools/审计.py --quick    # 只做静态检查（不起浏览器，快）
"""
import io
import json
import os
import re
import subprocess
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NODE = r'C:\Users\cyql0\.workbuddy\binaries\node\versions\22.22.2-6\node.exe'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'

# 结果收集
ISSUES = []


def rep(level, where, msg):
    ISSUES.append((level, where, msg))


def js_of(html):
    """抽出所有内联 <script> 内容"""
    return re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)


def check_python():
    print('【1】Python 脚本语法')
    for f in sorted(glob.glob(os.path.join(ROOT, 'tools', '*.py'))):
        r = subprocess.run([sys.executable, '-m', 'py_compile', f],
                           capture_output=True)
        if r.returncode:
            err = r.stderr.decode('utf-8', 'ignore').strip().split('\n')[-3:]
            rep('ERROR', os.path.basename(f), '语法错误: ' + ' | '.join(err))
            print('  ✗', os.path.basename(f))
        else:
            print('  ✓', os.path.basename(f))


def check_js_syntax():
    print('【2】生成产物 JS 语法')
    pages = [f for f in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)
              if '.git' not in f]
    for f in pages:
        html = io.open(f, encoding='utf-8', errors='ignore').read()
        blocks = js_of(html)
        if not blocks:
            continue
        tmp = os.path.join(ROOT, '_audit_tmp.js')
        io.open(tmp, 'w', encoding='utf-8').write('\n'.join(blocks))
        r = subprocess.run([NODE, '--check', tmp], capture_output=True)
        os.remove(tmp)
        if r.returncode:
            err = r.stderr.decode('utf-8', 'ignore')
            m = re.search(r'_audit_tmp\.js:(\d+)\s*\n(.*?)\n', err)
            where = m.group(0)[:120] if m else err[:120]
            rep('ERROR', os.path.relpath(f, ROOT), 'JS 语法错误: ' + where.replace('\n', ' '))
            print('  ✗', os.path.relpath(f, ROOT))
    print('  扫描 %d 页' % len(pages))


def check_function_arrow_mix():
    print('【3】function(...) => 非法混用')
    targets = sorted(f for f in glob.glob(os.path.join(ROOT, 'tools', '*.py'))
                     if not f.endswith('审计.py'))
    targets += [f for f in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)
                if '.git' not in f]
    total = 0
    for f in targets:
        s = io.open(f, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'function\([^)]*\)\s*=>', s):
            ctx = s[max(0, m.start() - 50):m.start() + 50].replace('\n', ' ')
            rep('ERROR', os.path.relpath(f, ROOT), 'function+箭头 混用: ...' + ctx)
            total += 1
    print('  发现 %d 处' % total)


def check_runtime():
    print('【4】运行时错误（无头 Edge）')
    if not os.path.exists(EDGE):
        print('  跳过（无 Edge）')
        return
    probe = """<script>
window.__errs=[];
window.addEventListener('error',function(e){
  window.__errs.push((e.message||'?')+' @'+(e.filename||'').split('/').pop()+':'+(e.lineno||'?'));
});
window.addEventListener('unhandledrejection',function(e){
  window.__errs.push('REJECT: '+((e.reason&&(e.reason.message||e.reason))||'?'));
});
setTimeout(function(){
  var d=document.createElement('div');d.id='__AUDIT__';
  d.textContent=window.__errs.length? window.__errs.join(' ;; ') : 'CLEAN';
  (document.body||document.documentElement).appendChild(d);
},2000);
</script>
"""
    pages = [f for f in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)
              if '.git' not in f and js_of(io.open(f, encoding='utf-8', errors='ignore').read())]
    for f in pages:
        s = io.open(f, encoding='utf-8', errors='ignore').read()
        s = s.replace('<head>', '<head>' + probe, 1) if '<head>' in s else probe + s
        d = os.path.dirname(f) or ROOT
        tmp = os.path.join(d, '__audit_tmp.html')   # 同目录 → 相对路径仍有效
        io.open(tmp, 'w', encoding='utf-8').write(s)
        url = 'file:///' + os.path.abspath(tmp).replace('\\', '/')
        try:
            r = subprocess.run(
                [EDGE, '--headless', '--disable-gpu', '--no-sandbox',
                 '--allow-file-access-from-files', '--virtual-time-budget=7000',
                 '--dump-dom', url], capture_output=True, timeout=90)
            out = r.stdout.decode('utf-8', 'ignore')
        except Exception:
            out = ''
        os.remove(tmp)
        m = re.search(r'id="__AUDIT__">([^<]*)', out)
        res = m.group(1) if m else 'NO-PROBE(页面未渲染?)'
        if res != 'CLEAN':
            rep('ERROR', os.path.relpath(f, ROOT), '运行时错误: ' + res[:200])
            print('  ✗', os.path.relpath(f, ROOT), '→', res[:100])
    print('  扫描 %d 页' % len(pages))


def check_dead_links():
    print('【5】死链检查')
    pages = [f for f in glob.glob(os.path.join(ROOT, '**', '*.html'), recursive=True)
              if '.git' not in f]
    n = 0
    for f in pages:
        s = io.open(f, encoding='utf-8', errors='ignore').read()
        base = os.path.dirname(f)
        for m in re.finditer(r'(?:href|src)="([^"#][^"]*)"', s):
            u = m.group(1)
            if u.startswith(('http', 'data:', 'mailto:', 'javascript:', '?', '/')):
                continue
            p = os.path.normpath(os.path.join(base, u.split('#')[0].split('?')[0]))
            if p and not os.path.exists(p):
                rep('WARN', os.path.relpath(f, ROOT), '死链: ' + u)
                n += 1
    print('  发现 %d 处死链' % n)


def check_answer_leak():
    print('【6】答案泄露（学习单类）')
    # 答案特征串：整组答案连写
    pat = re.compile(r'(21\s*D\s*[｜|]\s*22\s*A\s*[｜|]\s*23\s*B\s*[｜|]\s*24\s*C\s*[｜|]\s*25\s*C)')
    for f in glob.glob(os.path.join(ROOT, '*学习单*.html')):
        s = io.open(f, encoding='utf-8', errors='ignore').read()
        pages = re.findall(r'<div class="page">.*?(?=<div class="page">|</body>)', s, re.S)
        for i, pg in enumerate(pages, 1):
            if pat.search(pg):
                # 答案页允许有：页面标题含「答案页」
                if '答案页' in pg:
                    continue
                rep('ERROR', os.path.basename(f), '第 %d 页出现答案串' % i)
                print('  ✗', os.path.basename(f), '第%d 页' % i)
    print('  完成')


def check_data_consistency():
    print('【7】数据一致性')
    wp = os.path.join(ROOT, 'words_tts.json')
    if not os.path.exists(wp):
        return
    data = json.load(io.open(wp, encoding='utf-8'))
    words = [x['word'] for x in data]
    # 音频
    audio_dir = os.path.join(ROOT, 'audio')
    if os.path.isdir(audio_dir):
        am = {os.path.basename(f)[:-4] for f in glob.glob(os.path.join(audio_dir, '*.mp3'))}
        wm = set(words)
        miss = wm - am
        extra = am - wm
        if miss:
            rep('ERROR', 'words_tts.json ↔ audio/', '缺音频: %d 个 %s' % (len(miss), list(miss)[:5]))
            print('  ✗ 缺音频', len(miss))
        if extra:
            rep('WARN', 'words_tts.json ↔ audio/', '多余音频: %d 个 %s' % (len(extra), list(extra)[:5]))
        print('  ✓ 音频 %d/%d 对应' % (len(wm & am), len(wm)))
    # 批次包
    pack_dir = os.path.join(ROOT, 'audio_pack')
    if os.path.isdir(pack_dir):
        from collections import Counter
        cnt = Counter(x.get('batch') for x in data)
        bad = 0
        for b in sorted(cnt):
            mp3 = os.path.join(pack_dir, 'batch%02d.mp3' % b)
            js = os.path.join(pack_dir, 'batch%02d.json' % b)
            if not (os.path.exists(mp3) and os.path.exists(js)):
                rep('ERROR', 'audio_pack/', '第%02d批 包缺失' % b)
                bad += 1
                continue
            idx = json.load(io.open(js, encoding='utf-8'))
            if len(idx.get('items', [])) != cnt[b]:
                rep('ERROR', 'audio_pack/batch%02d.json' % b,
                    '索引词数 %d ≠ 词库 %d' % (len(idx.get('items', [])), cnt[b]))
                bad += 1
        if not bad:
            print('  ✓ 批次包 %d 个全部一致' % len(cnt))


def check_fstring_braces():
    print('【8】f-string 花括号陷阱')
    # 生成脚本里出现「未转义的单花括号 + JS 关键字」→ 高危
    danger = re.compile(r'(?<!\{)\{(?!\{)(?![\'"]?[a-zA-Z_][a-zA-Z0-9_]*[\'"]?\s*[:=])')
    n = 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'tools', '*.py'))):
        s = io.open(f, encoding='utf-8', errors='ignore').read()
        for m in re.finditer(r'function\([^)]*\)\s*=\s*\{(?!\{)', s):
            # 源码里 ={ 单花括号 → f-string 输出会被吃掉
            ctx = s[max(0, m.start() - 60):m.start() + 40].replace('\n', ' ')
            rep('WARN', os.path.basename(f), 'f-string 风险: ...' + ctx)
            n += 1
    print('  发现 %d 处可疑' % n)


def main():
    quick = '--quick' in sys.argv
    print('=' * 66)
    print('考研站代码审计')
    print('=' * 66)
    check_python()
    check_js_syntax()
    check_function_arrow_mix()
    if not quick:
        check_runtime()
    check_dead_links()
    check_answer_leak()
    check_data_consistency()
    check_fstring_braces()
    print()
    print('=' * 66)
    errs = [i for i in ISSUES if i[0] == 'ERROR']
    warns = [i for i in ISSUES if i[0] == 'WARN']
    if not ISSUES:
        print('审计结论：全部通过 ✓')
    else:
        print('审计结论：%d 个错误，%d 个警告' % (len(errs), len(warns)))
        for lv, where, msg in ISSUES:
            print('  [%s] %s → %s' % (lv, where, msg))
    print('=' * 66)
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
