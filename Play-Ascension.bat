@echo off
setlocal
title Ascension Card Oracle
cd /d "%~dp0"

REM file:// can block or mishandle media. Prefer HTTP (Python). Else Chrome/Edge + autoplay flag.

where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
  echo Starting local server on http://127.0.0.1:8765 ...
  start "Ascension server" /MIN cmd /c "python -m http.server 8765"
  timeout /t 1 /nobreak >nul
  start "" "http://127.0.0.1:8765/"
  exit /b 0
)

set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
  set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
)

if defined CHROME (
  echo Using Chrome with --autoplay-policy=no-user-gesture-required
  start "" "%CHROME%" --autoplay-policy=no-user-gesture-required "%~dp0index.html"
  exit /b 0
)

set "EDGE="
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
) else if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
)

if defined EDGE (
  echo Using Edge with --autoplay-policy=no-user-gesture-required
  start "" "%EDGE%" --autoplay-policy=no-user-gesture-required "%~dp0index.html"
  exit /b 0
)

echo Python not found. Opening default handler for index.html ^(audio may not autoplay on file://^).
start "" "%~dp0index.html"
exit /b 0
