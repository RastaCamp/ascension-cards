# Build a Play-ready signed release AAB (requires android/keystore.properties + .jks).
$ErrorActionPreference = "Stop"
$androidDir = $PSScriptRoot
$props = Join-Path $androidDir "keystore.properties"
if (-not (Test-Path $props)) {
    Write-Host "Missing keystore.properties. Copy keystore.properties.example to keystore.properties and create your keystore (.jks) in this folder."
    Write-Host "Example keytool (run from android folder):"
    Write-Host '  keytool -genkeypair -v -keystore ascension-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias ascension'
    exit 1
}
Push-Location $androidDir
try {
    .\gradlew.bat bundleRelease
    $aab = Join-Path $androidDir "app\build\outputs\bundle\release\app-release.aab"
    if (Test-Path $aab) {
        Write-Host "AAB: $aab"
    }
} finally {
    Pop-Location
}
