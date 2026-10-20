@echo off
REM ============================================================
REM  Kaoyan Word Card APK builder (manual toolchain, no Gradle)
REM  Toolchain: D:\jdk\jdk-17.0.2 + D:\android-sdk
REM
REM  Signing password is NOT stored here. Put it on the first line of
REM  android\signpass.txt (git-ignored). Never commit that file.
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
set "PASSFILE=%PROJ%\signpass.txt"
set "VER_CODE=5"
set "VER_NAME=1.1.3"

set "PATH=%JAVA_HOME%\bin;%PATH%"

if not exist "%PASSFILE%" (
  echo [ERROR] Missing %PASSFILE%
  echo         Create it with the keystore password on the first line.
  exit /b 1
)
set "KS_PASS="
set /p KS_PASS=<"%PASSFILE%"
if "%KS_PASS%"=="" (
  echo [ERROR] Password file is empty.
  exit /b 1
)

echo [1/9] clean output
if exist "%OUT%" rmdir /s /q "%OUT%"
mkdir "%OUT%\compiled" 2>nul
mkdir "%OUT%\gen" 2>nul
mkdir "%OUT%\classes" 2>nul
mkdir "%OUT%\dex" 2>nul

echo [2/9] aapt2 compile resources
"%BUILD%\aapt2.exe" compile --dir "%APPDIR%\res" -o "%OUT%\compiled\res.zip"
if errorlevel 1 goto :fail

echo [3/9] aapt2 link (assets packed here via -A)
"%BUILD%\aapt2.exe" link -o "%OUT%\unsigned.apk" -I "%PLATFORM%\android.jar" --manifest "%APPDIR%\AndroidManifest.xml" -A "%APPDIR%\assets" --java "%OUT%\gen" --min-sdk-version 24 --target-sdk-version 34 --version-code %VER_CODE% --version-name "%VER_NAME%" --auto-add-overlay "%OUT%\compiled\res.zip"
if errorlevel 1 goto :fail

echo [4/9] javac
python "%PROJ%\..\tools\list_sources.py" "%OUT%\gen" "%APPDIR%\java" > "%OUT%\sources.txt"
javac -encoding UTF-8 -source 8 -target 8 -nowarn -bootclasspath "%PLATFORM%\android.jar" -classpath "%PLATFORM%\android.jar" -d "%OUT%\classes" @"%OUT%\sources.txt"
if errorlevel 1 goto :fail

echo [5/9] d8 to dex
python "%PROJ%\..\tools\list_sources.py" --classes "%OUT%\classes" > "%OUT%\classes.txt"
python "%PROJ%\..\tools\d8_build.py" "%BUILD%" "%OUT%\classes.txt" "%OUT%\dex"
if errorlevel 1 goto :fail

echo [6/9] add classes.dex into apk
pushd "%OUT%\dex"
"%BUILD%\aapt.exe" add "%OUT%\unsigned.apk" classes.dex
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [7/9] normalize zip entry names
REM aapt2 link -A on Windows writes local headers with backslashes while the
REM central directory uses forward slashes. Android reads the local headers,
REM so assets break on device. Patch local header names in place, then verify.
python "%PROJ%\..\tools\fix_apk_names.py" "%OUT%\unsigned.apk"
if errorlevel 1 goto :fail

echo [8/9] sign
if not exist "%KEYSTORE%" (
  echo     generating keystore...
  keytool -genkeypair -v -keystore "%KEYSTORE%" -storepass %KS_PASS% -keypass %KS_PASS% -alias kaoyan -keyalg RSA -keysize 2048 -validity 10950 -dname "CN=KaoyanWordCard, OU=Personal, O=Clement, L=Taiyuan, ST=Shanxi, C=CN"
  if errorlevel 1 goto :fail
)
"%BUILD%\zipalign.exe" -f -p 4 "%OUT%\unsigned.apk" "%OUT%\aligned.apk"
if errorlevel 1 goto :fail
call "%BUILD%\apksigner.bat" sign --ks "%KEYSTORE%" --ks-pass pass:%KS_PASS% --key-pass pass:%KS_PASS% --ks-key-alias kaoyan --out "%OUT%\kaoyan-words.apk" "%OUT%\aligned.apk"
if errorlevel 1 goto :fail

call "%BUILD%\apksigner.bat" verify --verbose "%OUT%\kaoyan-words.apk"
if errorlevel 1 goto :fail

echo [9/9] strict verify (local/central names, assets, mp3, CRC)
python "%PROJ%\..\tools\verify_apk.py" "%OUT%\kaoyan-words.apk"
if errorlevel 1 goto :fail

REM tidy intermediates, keep only the final apk
del "%OUT%\unsigned.apk" "%OUT%\aligned.apk" 2>nul
rmdir /s /q "%OUT%\compiled" "%OUT%\gen" "%OUT%\classes" "%OUT%\dex" 2>nul

echo.
echo ==========================================
echo  BUILD OK: %OUT%\kaoyan-words.apk  (v%VER_NAME% / %VER_CODE%)
echo ==========================================
goto :eof

:fail
echo.
echo [FAILED] build aborted, check errors above.
exit /b 1
