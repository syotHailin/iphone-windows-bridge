$ErrorActionPreference='Stop'
$py=Join-Path $PSScriptRoot 'runtime/python/python.exe'
& $py -X utf8 (Join-Path $PSScriptRoot 'src/control.py') start
if ($LASTEXITCODE -ne 0) { throw 'WDA startup failed.' }
$url=& $py -X utf8 (Join-Path $PSScriptRoot 'src/viewer.py') start
if ($LASTEXITCODE -ne 0 -or $url -notmatch '^http://127\.0\.0\.1:\d+$') { throw 'Viewer startup failed.' }
Start-Process $url
