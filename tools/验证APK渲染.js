// APK 离线渲染验证：用无头 Edge 打开 APK 内解出的页面，检查词库渲染与音频路径
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ROOT = 'C:\\tmp\\apktest\\assets\\www';
const PAGE = 'file:///' + ROOT.replace(/\\/g, '/') + '/index.html';

// 极简静态服务器：模拟 WebView 的 file:// 访问不到某些行为时的兜底
// 直接用 file:// 打开
const args = [
  '--headless=new',
  '--disable-gpu',
  '--no-sandbox',
  '--allow-file-access-from-files',
  '--virtual-time-budget=6000',
  '--dump-dom',
  PAGE
];

const p = spawn(EDGE, args, { cwd: ROOT });
let out = '';
let err = '';
p.stdout.on('data', d => { out += d.toString(); });
p.stderr.on('data', d => { err += d.toString(); });

p.on('close', code => {
  fs.writeFileSync('C:/tmp/apk_dom.html', out);
  console.log('退出码:', code);
  console.log('DOM 长度:', out.length);
  if (err) console.log('stderr(前500):', err.slice(0, 500));

  // 检查关键渲染结果
  const checks = [
    ['单词区有内容', /class="word"[^>]*>[^<]*[A-Za-z一-龥]/],
    ['词根行有内容', /class="rootline"[^>]*>[^<]*[A-Za-z一-龥]/],
    ['进度文字非加载中', /id="stat"[^>]*>(?!加载中)/],
    ['音标存在', /id="ipa"[^>]*>[^<]+/],
  ];
  let bad = 0;
  for (const [name, re] of checks) {
    const ok = re.test(out);
    if (!ok) bad++;
    console.log((ok ? '  [OK] ' : '  [!!] ') + name);
  }
  // 抓一段实际内容看看
  const m = out.match(/id="word"[^>]*>([^<]*)</);
  const r = out.match(/id="rootline"[^>]*>([^<]*)</);
  const s = out.match(/id="stat"[^>]*>([^<]*)</);
  const ip = out.match(/id="ipa"[^>]*>([^<]*)</);
  console.log('  单词:', m ? m[1] : '(无)');
  console.log('  词根:', r ? r[1] : '(无)');
  console.log('  进度:', s ? s[1] : '(无)');
  console.log('  音标:', ip ? ip[1] : '(无)');
  console.log(bad === 0 ? '\n结论: 渲染全部通过' : '\n结论: 有 ' + bad + ' 项未通过');
});
