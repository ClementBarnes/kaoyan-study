@echo off
REM ============================================================
REM  Kaoyan Word Card APK builder (manual toolchain, no Gradle)
REM  Toolchain: D:\jdk\jdk-17.0.2 + D:\android-sdk
REM ============================================================
setlocal enabledelayedexpansion

set "JAVA_HOME=D:\jdk\jdk-17.0.2"
set "SDK=D:\android-sdk"
set "BUILD=%SDK%\build-tools"
set "PLATFORM=%SDK%\platforms\android-35"
set "PROJ=D:\githubprogram\kaoyan-study\android"
set "APPDIR=%PROJ%\app\src\main"
set "OUT=%PROJ%\build"
set "KEYSTORE=%PROJ%\kaoyan-release.jks"
set "KS_PASS=kaoyan2027"

set "PATH=%JAVA_HOME%\bin;%PATH%"

echo [1/7] clean output
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%\compiled" 2>nul
mkdir "%OUT%\gen" 2>nul
mkdir "%OUT%\classes" 2>nul
mkdir "%OUT%\dex" 2>nul

echo [2/7] aapt2 compile resources
"%BUILD%\aapt2.exe" compile --dir "%APPDIR%\res" -o "%OUT%\compiled\res.zip"
if errorlevel 1 goto :fail

echo [3/7] aapt2 link
"%BUILD%\aapt2.exe" link -o "%OUT%\unsigned.apk" -I "%PLATFORM%\android.jar" --manifest "%APPDIR%\AndroidManifest.xml" -A "%APPDIR%\assets" --java "%OUT%\gen" --min-sdk-version 24 --target-sdk-version 34 --version-code 1 --version-name "1.0.0" --auto-add-overlay "%OUT%\compiled\res.zip"
if errorlevel 1 goto :fail

echo [4/7] javac
python "%PROJ%\..\tools\list_sources.py" "%OUT%\gen" "%APPDIR%\java" > "%OUT%\sources.txt"
javac -encoding UTF-8 -source 8 -target 8 -nowarn -bootclasspath "%PLATFORM%\android.jar" -classpath "%PLATFORM%\android.jar" -d "%OUT%\classes" @"%OUT%\sources.txt"
if errorlevel 1 goto :fail

echo [5/7] d8 to dex
python "%PROJ%\..\tools\list_sources.py" --classes "%OUT%\classes" > "%OUT%\classes.txt"
python "%PROJ%\..\tools\d8_build.py" "%BUILD%" "%OUT%\classes.txt" "%OUT%\dex"
if errorlevel 1 goto :fail

echo [6/7] add dex and assets into apk
pushd "%OUT%\dex"
"%BUILD%\aapt.exe" add "%OUT%\unsigned.apk" classes.dex
popd
pushd "%APPDIR%"
"%BUILD%\aapt.exe" add -f "%OUT%\unsigned.apk" assets
popd

echo [7/7] sign
if not exist "%KEYSTORE%" (
  keytool -genkeypair -v -keystore "%KEYSTORE%" -storepass %KS_PASS% -keypass %KS_PASS% -alias kaoyan -keyalg RSA -keysize 2048 -validity 10950 -dname "CN=KaoyanWordCard, OU=Personal, O=Clement, L=Taiyuan, ST=Shanxi, C=CN" 2>nul
  if errorlevel 1 goto :fail
)
"%BUILD%\zipalign.exe" -f -p 4 "%OUT%\unsigned.apk" "%OUT%\aligned.apk"
if errorlevel 1 goto :fail
"%BUILD%\apksigner.bat" sign --ks "%KEYSTORE%" --ks-pass pass:%KS_PASS% --key-pass pass:%KS_PASS% --ks-key-alias kaoyan --out "%OUT%\kaoyan-words.apk" "%OUT%\aligned.apk"
if errorlevel 1 goto :fail

"%BUILD%\apksigner.bat" verify --verbose "%OUT%\kaoyan-words.apk"
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo  BUILD OK: %OUT%\kaoyan-words.apk
echo ==========================================
goto :eof

:fail
echo.
echo [FAILED] build aborted, check errors above.
exit /b 1
