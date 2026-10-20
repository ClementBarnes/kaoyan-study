// 验证 APK 内音频可加载（file:// 下的相对路径 audio/xxx.mp3）
// 结果写进 DOM 文本，--dump-dom 才能读到
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
const ROOT = 'C:\\tmp\\apktest\\assets\\www';

const probe = `<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
<div id="out">RUNNING</div>
<script>
var words = ['inspect','abrupt','absolute','accept','access','acclaim','acquire','adhere','admit','abide'];
var ok = 0, fail = 0, i = 0, details = [];
function finish(){
  document.getElementById('out').textContent =
    'RESULT ok=' + ok + ' fail=' + fail + ' | ' + details.join(', ');
}
function next(){
  if(i >= words.length){ finish(); return; }
  var w = words[i++];
  var a = new Audio('audio/' + w + '.mp3');
  var settled = false;
  var to = setTimeout(function(){
    if(settled) return; settled = true;
    fail++; details.push(w+':TIMEOUT'); next();
  }, 4000);
  a.addEventListener('canplaythrough', function(){
    if(settled) return; settled = true; clearTimeout(to);
    ok++; details.push(w+':'+(Math.round(a.duration*10)/10)+'s'); next();
  });
  a.addEventListener('error', function(){
    if(settled) return; settled = true; clearTimeout(to);
    fail++; details.push(w+':ERROR'); next();
  });
  a.load();
}
next();
</script></body></html>`;

fs.writeFileSync(path.join(ROOT, '__probe.html'), probe, 'utf8');

const p = spawn(EDGE, [
  '--headless=new', '--disable-gpu', '--no-sandbox',
  '--allow-file-access-from-files', '--autoplay-policy=no-user-gesture-required',
  '--virtual-time-budget=25000', '--dump-dom',
  'file:///' + ROOT.replace(/\\/g, '/') + '/__probe.html'
], { cwd: ROOT });

let out = '';
p.stdout.on('data', d => { out += d.toString(); });
p.on('close', () => {
  const m = out.match(/id="out"[^>]*>([^<]*)</);
  const line = m ? m[1] : '(未捕获结果)';
  console.log('音频探测结果:', line);
  const mm = line.match(/ok=(\d+)\s+fail=(\d+)/);
  if (mm && parseInt(mm[1]) > 0 && parseInt(mm[2]) === 0) {
    console.log('结论: 本地音频全部可加载 ✓');
  } else {
    console.log('结论: 音频加载有异常 ✗');
  }
});
