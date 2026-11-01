param([ValidateSet('Sideloadly','iTunes','iCloud','i4')][string]$Component='Sideloadly')
$ErrorActionPreference='Stop'
$items=@{
 Sideloadly=@{Url='https://sideloadly.io/SideloadlySetup64.exe';File='SideloadlySetup64.exe';Hash='2E7D9A80BCD7912A9A2DAE1969645F8AF386AF46802A79303E727773B506362E'}
 iTunes=@{Url='https://www.apple.com/itunes/download/win64';File='iTunes64Setup.exe'}
 iCloud=@{Url='https://updates.cdn-apple.com/2020/windows/001-39935-20200911-1A70AA56-F448-11EA-8CC0-99D41950005E/iCloudSetup.exe';File='iCloudSetup.exe'}
 i4=@{Url='https://d-app6.i4.cn/i4tools/V9/9.21/i4Tools_v9.21.010_Setup_x64.exe';File='i4Tools_v9.21.010_Setup_x64.exe';Hash='764E66F748F1DD91DBA5F36DC842B4139EB0190A85D5B29A6D5E2D35E8E4997E'}
}
$dir=Join-Path $env:LOCALAPPDATA 'iPhoneWindowsBridge/downloads'
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$item=$items[$Component]; $dest=Join-Path $dir $item.File
if (Test-Path -LiteralPath $dest) { throw "Already exists: $dest. Inspect it before downloading again." }
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $item.Url -OutFile $dest -UseBasicParsing
$hash=(Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash
if ($Component -eq 'Sideloadly') {
 if ($hash -ne $item.Hash) { throw "Upstream file changed. Download retained for inspection; do not execute without reviewing the new version. SHA256=$hash" }
 Write-Host 'Pinned Sideloadly installer verified. It has no Windows signature; review the third-party login implications before running it.'
} elseif ($Component -eq 'i4') {
 if ($hash -ne $item.Hash) { throw 'i4 installer hash mismatch; do not execute this file.' }
 $signature=Get-AuthenticodeSignature -LiteralPath $dest
 if ($signature.Status -ne 'Valid') { throw 'i4 Authenticode verification failed; do not execute this file.' }
 Write-Host 'Pinned i4 installer verified. WDA signing compatibility remains untested.'
 Write-Host "Signer: $($signature.SignerCertificate.Subject)"
} else {
 $signature=Get-AuthenticodeSignature -LiteralPath $dest
 if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Apple Inc\.') { throw 'Apple Authenticode verification failed; do not run this file.' }
}
Write-Host "Downloaded only; not executed: $dest"
Write-Host "SHA256=$hash"
