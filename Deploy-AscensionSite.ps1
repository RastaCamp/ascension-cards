#Requires -Version 5.1
<#
  Builds site/ from index.html + cards/ + audio/ and deploys to Cloudflare Pages (project: ascension).
  Requires: npm/npx wrangler, and either wrangler login OR CLOUDFLARE_API_TOKEN in .env / environment.

  Usage:
    cd path\to\ascension-cards
    .\Deploy-AscensionSite.ps1
#>
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Site = Join-Path $Root "site"

function Load-DotEnv {
  param([string]$Path)
  if (-not (Test-Path $Path)) { return }
  Get-Content $Path | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { return }
    $name = $Matches[1]
    $val = $Matches[2].Trim().Trim('"').Trim("'")
    if (-not [string]::IsNullOrWhiteSpace($val) -and -not [Environment]::GetEnvironmentVariable($name)) {
      [Environment]::SetEnvironmentVariable($name, $val, "Process")
    }
  }
}

Load-DotEnv (Join-Path $Root ".env")

if (-not $env:CLOUDFLARE_API_TOKEN) {
  Write-Host ""
  Write-Host "CLOUDFLARE_API_TOKEN is not set." -ForegroundColor Yellow
  Write-Host "  Option A: copy .env.example to .env and add your API token" -ForegroundColor Yellow
  Write-Host "  Option B: run:  wrangler login" -ForegroundColor Yellow
  Write-Host "  Then run this script again." -ForegroundColor Yellow
  Write-Host ""
  exit 1
}

Write-Host ">>> Preparing site/ ..." -ForegroundColor Cyan
if (Test-Path $Site) { Remove-Item $Site -Recurse -Force }
New-Item -ItemType Directory -Path $Site | Out-Null
Copy-Item (Join-Path $Root "index.html") $Site
Copy-Item (Join-Path $Root "cards") (Join-Path $Site "cards") -Recurse
Copy-Item (Join-Path $Root "audio") (Join-Path $Site "audio") -Recurse

$accountArg = @()
if ($env:CLOUDFLARE_ACCOUNT_ID) {
  $accountArg = @("--account-id", $env:CLOUDFLARE_ACCOUNT_ID)
}

Write-Host ">>> wrangler pages deploy site --project-name=ascension" -ForegroundColor Cyan
Push-Location $Root
try {
  npx --yes wrangler@4 pages deploy site --project-name=ascension @accountArg --branch=main --commit-dirty=true
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  Write-Host ""
  Write-Host "Deployed. Check https://ascension.rastacamp.com/ (may take a minute; hard-refresh if cached)." -ForegroundColor Green
}
finally {
  Pop-Location
}
