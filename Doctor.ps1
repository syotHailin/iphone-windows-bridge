param([switch]$Network)
$ErrorActionPreference='Stop'
$argsList=@('-X','utf8',(Join-Path $PSScriptRoot 'src/doctor.py'))
if ($Network) { $argsList += '--network' }
& (Join-Path $PSScriptRoot 'runtime/python/python.exe') @argsList
exit $LASTEXITCODE
