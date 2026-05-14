#Requires -Version 5.1
<#
  Builds a debug APK and installs it on the USB-connected device (USB debugging on).
  Usage (from repo):  powershell -ExecutionPolicy Bypass -File .\android\Build-InstallDebug.ps1
  Or:                 cd android; .\Build-InstallDebug.ps1
#>
param(
  [string]$JavaHome = "${env:ProgramFiles}\Android\Android Studio\jbr",
  [string]$AndroidHome = "${env:LOCALAPPDATA}\Android\Sdk"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

if (-not (Test-Path "$JavaHome\bin\java.exe")) {
  Write-Error "Java not found at $JavaHome. Pass -JavaHome 'C:\Path\To\Android Studio\jbr'"
}

$adb = Join-Path $AndroidHome "platform-tools\adb.exe"
if (-not (Test-Path $adb)) {
  Write-Error "adb not found at $adb. Install Android SDK Platform-Tools (SDK Manager in Android Studio)."
}

$env:JAVA_HOME = $JavaHome
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = $AndroidHome }

Push-Location $Root
try {
  Write-Host ">>> gradlew assembleDebug" -ForegroundColor Cyan
  & .\gradlew.bat assembleDebug
  $apk = Join-Path $Root "app\build\outputs\apk\debug\app-debug.apk"
  if (-not (Test-Path $apk)) { throw "Missing APK: $apk" }

  Write-Host ">>> adb devices" -ForegroundColor Cyan
  $adbList = & $adb devices 2>&1 | Out-String
  Write-Host $adbList

  if ($adbList -match "unauthorized") {
    Write-Host ""
    Write-Host "PHONE SHOWS AS unauthorized - accept USB debugging on the phone, then retry." -ForegroundColor Red
    Write-Host "Developer options - Revoke USB debugging authorizations if the RSA prompt never appears." -ForegroundColor Yellow
    exit 1
  }
  if ($adbList -notmatch "`tdevice") {
    Write-Host "No device connected. Plug in USB and enable USB debugging." -ForegroundColor Red
    exit 1
  }

  Write-Host ">>> adb install -r (debug APK)" -ForegroundColor Cyan
  & $adb install -r $apk
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host "Done. Open Ascension on the phone." -ForegroundColor Green
}
finally {
  Pop-Location
}
