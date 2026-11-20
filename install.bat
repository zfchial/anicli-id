@echo off
setlocal EnableExtensions EnableDelayedExpansion
title anicli-id installer
echo Nano
echo.
echo anicli-id installer for Windows
echo.

set "INSTALL_DIR=%USERPROFILE%\anicli-id"
set "TOOLS_DIR=%LOCALAPPDATA%\anicli-id-tools"
set "INSTALL_YTDLP=1"
set "PY="
set "GIT="

echo [1/6] Checking Python
where python >nul 2>&1
if not errorlevel 1 (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
  if not errorlevel 1 for /f "delims=" %%P in ('where python') do if not defined PY set "PY=%%P"
)
if not defined PY (
  echo Python 3.9+ not found. Trying winget.
  where winget >nul 2>&1
  if not errorlevel 1 (
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements --silent
    for %%P in ("%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe" "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" "%ProgramFiles%\Python311\python.exe" "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" "%ProgramFiles%\Python310\python.exe") do if not defined PY if exist %%~P set "PY=%%~P"
  )
)
if not defined PY (
  echo Downloading Python 3.12 installer.
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe' -OutFile '%TEMP%\python-3.12.10-amd64.exe'"
  if not errorlevel 1 "%TEMP%\python-3.12.10-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1
  for %%P in ("%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe") do if not defined PY if exist %%~P set "PY=%%~P"
)
if not defined PY (
  echo Install Python 3.9+ from https://www.python.org/downloads/ then run this file again.
  goto :fail
)
echo Python: !PY!

echo [2/6] Checking git
where git >nul 2>&1
if not errorlevel 1 for /f "delims=" %%G in ('where git') do if not defined GIT set "GIT=%%G"
if not defined GIT (
  where winget >nul 2>&1
  if not errorlevel 1 (
    winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements --silent
    for %%G in ("%ProgramFiles%\Git\cmd\git.exe" "%ProgramFiles(x86)%\Git\cmd\git.exe" "%LOCALAPPDATA%\Programs\Git\cmd\git.exe") do if not defined GIT if exist %%~G set "GIT=%%~G"
  )
)
if defined GIT (echo Git: !GIT!) else (echo Git not found. Source will be downloaded as ZIP.)

echo [3/6] Checking mpv
where mpv >nul 2>&1
if not errorlevel 1 goto :mpv_done
where winget >nul 2>&1
if not errorlevel 1 (
  winget install --id mpv.io.mpv -e --accept-package-agreements --accept-source-agreements --silent
  where mpv >nul 2>&1
  if errorlevel 1 winget install --id mpv-player.mpv-CI.MSVC -e --accept-package-agreements --accept-source-agreements --silent
)
where mpv >nul 2>&1
if not errorlevel 1 goto :mpv_done
if exist "%ProgramFiles%\mpv" set "PATH=%ProgramFiles%\mpv;%PATH%"
if exist "%LOCALAPPDATA%\Programs\mpv" set "PATH=%LOCALAPPDATA%\Programs\mpv;%PATH%"
where mpv >nul 2>&1
if not errorlevel 1 goto :mpv_done
echo Downloading portable mpv.
if not exist "%TOOLS_DIR%\mpv" mkdir "%TOOLS_DIR%\mpv"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; $r=Invoke-RestMethod -Uri 'https://api.github.com/repos/mpv-player/mpv/releases/latest' -Headers @{'User-Agent'='anicli-id-installer'}; $a=$r.assets | Where-Object { $_.name -like 'mpv-x86_64-*.zip' -and $_.name -notlike '*vulkan*' } | Select-Object -First 1; if (-not $a) { exit 1 }; Invoke-WebRequest -Uri $a.browser_download_url -OutFile '%TOOLS_DIR%\mpv\mpv.zip'"
if errorlevel 1 goto :mpv_missing
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Expand-Archive -Path '%TOOLS_DIR%\mpv\mpv.zip' -DestinationPath '%TOOLS_DIR%\mpv' -Force"
if not exist "%TOOLS_DIR%\mpv\mpv.exe" goto :mpv_missing
set "PATH=%TOOLS_DIR%\mpv;%PATH%"
echo mpv: %TOOLS_DIR%\mpv\mpv.exe
goto :mpv_after
:mpv_done
echo mpv already available.
:mpv_after

echo [4/6] Getting source
if exist "%INSTALL_DIR%\.git" goto :source_done
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
pushd "%INSTALL_DIR%"
set "EMPTY="
for /f %%F in ('dir /b 2^>nul') do set "EMPTY=1"
popd
if defined EMPTY (
  set "INSTALL_DIR=%USERPROFILE%\anicli-id-%RANDOM%"
  mkdir "%INSTALL_DIR%"
)
if defined GIT (
  "%GIT%" clone --depth 1 https://github.com/zfchial/anicli-id.git "%INSTALL_DIR%"
  if errorlevel 1 goto :zip_fallback
) else (
  goto :zip_fallback
)
goto :source_done
:zip_fallback
echo Downloading source ZIP.
if exist "%TEMP%\anicli-id-src" rmdir /s /q "%TEMP%\anicli-id-src"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://github.com/zfchial/anicli-id/archive/refs/heads/main.zip' -OutFile '%TEMP%\anicli-id.zip'; Expand-Archive -Path '%TEMP%\anicli-id.zip' -DestinationPath '%TEMP%\anicli-id-src' -Force; Copy-Item -Path '%TEMP%\anicli-id-src\anicli-id-main\*' -Destination '%INSTALL_DIR%' -Recurse -Force"
if not exist "%INSTALL_DIR%\pyproject.toml" goto :fail
:source_done
echo Source: !INSTALL_DIR!

echo [5/6] Installing Python packages
"%PY%" -m venv "%INSTALL_DIR%\.venv"
if errorlevel 1 goto :fail
set "VENV=%INSTALL_DIR%\.venv"
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail
"%VENV%\Scripts\python.exe" -m pip install -e "%INSTALL_DIR%"
if errorlevel 1 goto :fail
if "%INSTALL_YTDLP%"=="1" "%VENV%\Scripts\python.exe" -m pip install yt-dlp

echo [6/6] Creating launcher
set "PATH=%VENV%\Scripts;%PATH%"
if not exist "%USERPROFILE%\Desktop" mkdir "%USERPROFILE%\Desktop"
set "LAUNCHER=%USERPROFILE%\Desktop\anicli-id.bat"
> "%LAUNCHER%" echo @echo off
>> "%LAUNCHER%" echo call "%VENV%\Scripts\anicli-id.exe" %%*
echo Launcher: !LAUNCHER!
"%VENV%\Scripts\anicli-id.exe" --version
if errorlevel 1 goto :fail
echo.
echo Done. Open the Desktop shortcut or run: anicli-id
timeout /t 8 >nul
exit /b 0

:mpv_missing
echo mpv could not be installed automatically. Download it from https://mpv.io/installation/
echo Streaming will not work until mpv is installed and on PATH.
goto :mpv_after

:fail
echo Installation failed. See the messages above.
pause
exit /b 1
