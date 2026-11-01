param([string]$Udid, [string]$BundleId, [int]$ViewerPort=19101, [int]$TunnelPort=60105)
$ErrorActionPreference='Stop'
$argsList=@('-X','utf8',(Join-Path $PSScriptRoot 'src/bridge.py'),'configure','--viewer-port',"$ViewerPort",'--tunnel-port',"$TunnelPort")
if ($Udid) { $argsList += @('--udid',$Udid) }
if ($BundleId) { $argsList += @('--bundle-id',$BundleId) }
& (Join-Path $PSScriptRoot 'runtime/python/python.exe') @argsList
if ($LASTEXITCODE -ne 0) { throw 'Device configuration failed. See README.md.' }
