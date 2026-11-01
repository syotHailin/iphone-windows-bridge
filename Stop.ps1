$ErrorActionPreference='Stop'
$py=Join-Path $PSScriptRoot 'runtime/python/python.exe'
& $py -X utf8 (Join-Path $PSScriptRoot 'src/viewer.py') stop
if ($LASTEXITCODE -ne 0) { throw 'Viewer stop failed.' }
& $py -X utf8 (Join-Path $PSScriptRoot 'src/control.py') stop
if ($LASTEXITCODE -ne 0) { throw 'Control stop failed or another WDA runner is still active.' }
