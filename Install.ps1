$ErrorActionPreference = 'Stop'
if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'This release requires Windows x64 (Intel/AMD).' }
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'dependencies.json') -Raw | ConvertFrom-Json
foreach ($item in $manifest.files) {
    $path = Join-Path $PSScriptRoot $item.path
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing asset: $($item.path). Download the full Release ZIP, not Source code.zip." }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $item.sha256) { throw "Hash mismatch: $($item.path)" }
}
$runtime = Join-Path $PSScriptRoot 'runtime'
if (Test-Path -LiteralPath $runtime) { throw 'runtime already exists. Extract a fresh copy to another folder for reinstall/upgrade.' }
New-Item -ItemType Directory -Path $runtime | Out-Null
Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'vendor/python-3.13.17-embed-amd64.zip') -DestinationPath (Join-Path $runtime 'python')
Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'vendor/python-packages.zip') -DestinationPath (Join-Path $runtime 'python/Lib/site-packages')
Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'vendor/go-ios-v1.3.2.zip') -DestinationPath (Join-Path $runtime 'go-ios')
@('python313.zip','.','Lib/site-packages','../../src','import site') | Set-Content -LiteralPath (Join-Path $runtime 'python/python313._pth') -Encoding ASCII
& (Join-Path $runtime 'python/python.exe') -X utf8 -c 'import aiohttp, psutil; from pymobiledevice3.services.wda import WdaServiceClient; print("Offline runtime ready")'
if ($LASTEXITCODE -ne 0) { throw 'Runtime import check failed.' }
Write-Host 'Next: read README.md, install Apple components + Sideloadly, sign WDA, then run Configure.ps1.'
