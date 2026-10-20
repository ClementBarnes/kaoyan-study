// 检测 file:// 协议下 localStorage / fetch / XHR 的可用性（模拟 APK 内的运行环境）
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ROOT = 'C:\\tmp\\apkcheck\\www';

const probe = `<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<div id="out">RUNNING</div>
<script>
var r = [];
function t(name, fn){
  try { r.push(name + '=' + fn()); }
  catch(e){ r.push(name + '=THROW(' + (e && e.name) + ')'); }
}
t('localStorage.write', function(){ localStorage.setItem('__k','v1'); return 'ok'; });
t('localStorage.read', function(){ return localStorage.getItem('__k') || 'null'; });
t('localStorage.len', function(){ return localStorage.length; });
t('sessionStorage', function(){ sessionStorage.setItem('a','b'); return 'ok'; });
t('origin', function(){ return String(location.origin); });
t('protocol', function(){ return location.protocol; });
t('indexedDB', function(){ return (typeof indexedDB === 'object' && indexedDB) ? 'present' : 'absent'; });
t('serviceWorker', function(){ return ('serviceWorker' in navigator) ? 'present' : 'absent'; });
t('caches', function(){ return (typeof caches === 'object') ? 'present' : 'absent'; });
document.getElementById('out').textContent = 'RESULT ' + r.join(' | ');
</script></body></html>`;

fs.mkdirSync(ROOT, { recursive: true });
fs.writeFileSync(path.join(ROOT, 'probe.html'), probe, 'utf8');

function run(tag, target) {
  return new Promise(resolve => {
    const p = spawn(EDGE, [
      '--headless=new', '--disable-gpu', '--no-sandbox',
      '--allow-file-access-from-files',
      '--user-data-dir=C:\\tmp\\apkcheck\\profile-' + tag,
      '--virtual-time-budget=4000', '--dump-dom', target
    ], { cwd: ROOT });
    let out = '';
    p.stdout.on('data', d => { out += d.toString(); });
    p.on('close', () => {
      const m = out.match(/id="out"[^>]*>([^<]*)</);
      resolve(m ? m[1] : '(无结果)');
    });
  });
}

(async () => {
  const fileUrl = 'file:///' + ROOT.replace(/\\/g, '/') + '/probe.html';
  console.log('--- file:// 环境 ---');
  console.log(await run('a', fileUrl));
  console.log('--- 同一 profile 二次打开（验证持久化）---');
  console.log(await run('a', fileUrl));
})();
