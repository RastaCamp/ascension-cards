#Requires -Version 5.1
<#
  Builds a debug-signed .aab (same shape as Play) and installs via bundletool (universal APK).
  First run downloads bundletool into android\tools\ if missing.

  Usage:  powershell -ExecutionPolicy Bypass -File .\android\Build-InstallBundleDebug.ps1

  Requires: platform-tools (adb), Java, device with USB debugging.
#>
param(
  [string]$JavaHome = "${env:ProgramFiles}\Android\Android Studio\jbr",
  [string]$AndroidHome = "${env:LOCALAPPDATA}\Android\Sdk",
  [string]$BundletoolVersion = "1.17.2"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Tools = Join-Path $Root "tools"
$BtJar = Join-Path $Tools "bundletool-all.jar"

if (-not (Test-Path "$JavaHome\bin\java.exe")) {
  Write-Error "Java not found at $JavaHome"
}

$adb = Join-Path $AndroidHome "platform-tools\adb.exe"
if (-not (Test-Path $adb)) {
  Write-Error "adb not found at $adb"
}

$env:JAVA_HOME = $JavaHome
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = $AndroidHome }

if (-not (Test-Path $BtJar)) {
  New-Item -ItemType Directory -Force -Path $Tools | Out-Null
  $url = "https://github.com/google/bundletool/releases/download/$BundletoolVersion/bundletool-all-$BundletoolVersion.jar"
  Write-Host "Downloading bundletool -> $BtJar" -ForegroundColor Cyan
  Invoke-WebRequest -Uri $url -OutFile $BtJar -UseBasicParsing
}

Push-Location $Root
try {
  Write-Host ">>> gradlew bundleDebug" -ForegroundColor Cyan
  & .\gradlew.bat bundleDebug

  $aab = Join-Path $Root "app\build\outputs\bundle\debug\app-debug.aab"
  if (-not (Test-Path $aab)) { throw "Missing AAB: $aab" }

  $apks = Join-Path $Root "app\build\outputs\bundle\debug\ascension-local.apks"
  Write-Host ">>> bundletool build-apks (universal)" -ForegroundColor Cyan
  & "$JavaHome\bin\java.exe" -jar $BtJar build-apks --bundle=$aab --output=$apks --mode=universal --overwrite

  Write-Host ">>> adb devices" -ForegroundColor Cyan
  $adbList = & $adb devices 2>&1 | Out-String
  Write-Host $adbList

  if ($adbList -match "unauthorized") {
    Write-Host ""
    Write-Host "PHONE SHOWS AS unauthorized - the app was NOT installed." -ForegroundColor Red
    Write-Host "On the phone: unlock screen, accept Allow USB debugging (RSA fingerprint)." -ForegroundColor Yellow
    Write-Host "If no popup: Developer options - Revoke USB debugging authorizations, unplug/replug USB." -ForegroundColor Yellow
    Write-Host "Then run: adb kill-server  then  adb devices  (expect state: device, not unauthorized)" -ForegroundColor Yellow
    exit 1
  }
  if ($adbList -notmatch "`tdevice") {
    Write-Host ""
    Write-Host "No phone in device state. Plug in USB, enable Developer options and USB debugging, try another cable." -ForegroundColor Red
    exit 1
  }

  Write-Host ">>> bundletool install-apks" -ForegroundColor Cyan
  & "$JavaHome\bin\java.exe" -jar $BtJar install-apks --apks=$apks --adb=$adb
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host "Done. Open Ascension on the phone." -ForegroundColor Green
}
finally {
  Pop-Location
}
