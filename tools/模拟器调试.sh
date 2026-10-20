#!/bin/bash
# 模拟器一键调试：启动 → 装包 → 拉起 → 截图
# 用法：./tools/模拟器调试.sh [apk路径]
set -u
SDK=/d/android-sdk
ADB="$SDK/platform-tools/adb.exe"
APK="${1:-交付/考研单词卡-v1.1.3.apk}"

cd "$(dirname "$0")/.." || exit 1
export ANDROID_SDK_ROOT="D:/android-sdk"
export ANDROID_HOME="D:/android-sdk"

# 1) 模拟器没跑就拉起来
if ! "$ADB" devices 2>/dev/null | grep -q "emulator-5554.*device"; then
  echo "[1/4] 启动模拟器..."
  "$SDK/emulator/emulator.exe" -avd kaoyan -no-window -no-audio -no-boot-anim \
    -no-snapshot -gpu swiftshader_indirect -memory 2048 > "$SDK/emu.log" 2>&1 &
  "$ADB" wait-for-device
  for _ in $(seq 1 40); do
    [ "$("$ADB" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r\n')" = "1" ] && break
    sleep 10
  done
else
  echo "[1/4] 模拟器已在运行"
fi

# 2) 装包
echo "[2/4] 安装 $APK"
"$ADB" install -r "$APK" 2>&1 | tail -1

# 3) 拉起
echo "[3/4] 启动应用"
"$ADB" shell am start -n com.clementbarnes.kaoyan/.MainActivity 2>&1 | tail -1
sleep 6

# 4) 截图
echo "[4/4] 截图"
"$ADB" shell screencap -p //sdcard/shot.png
mkdir -p /c/tmp
"$ADB" pull //sdcard/shot.png /c/tmp/shot.png 2>&1 | tail -1
echo "截图: C:\\tmp\\shot.png"
echo
echo "常用命令："
echo "  看错误   $ADB logcat -d | grep -iE 'ERR_|Failed|Exception' | tail -20"
echo "  点按     $ADB shell input tap <x> <y>    (分辨率 1080x2400)"
echo "  返回     $ADB shell input keyevent 4"
echo "  关模拟器 $ADB emu kill"
