﻿$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'language.ps1')
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$expected = Join-Path $env:LOCALAPPDATA 'Programs\NaatikNext\1.0'
if ([IO.Path]::GetFullPath($root).TrimEnd('\') -ne [IO.Path]::GetFullPath($expected).TrimEnd('\')) { throw (L 'setup.invalid_destination') }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'install.ps1')
if ($LASTEXITCODE -ne 0) { throw (L 'setup.dependencies_failed') }
$python = Join-Path $root '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $python)) { throw (L 'setup.missing_python') }
# Save only interface language after dependencies succeeded. No settings.json rewrite.
if ($env:NAATIK_UI_LANGUAGE -in @('es','en')) {
    & (Join-Path $root '.venv\Scripts\python.exe') -E -s -X utf8 -m naatik_next.i18n --set-language $env:NAATIK_UI_LANGUAGE
    if ($LASTEXITCODE -ne 0) { throw (L 'setup.language_failed') }
}
$menu = Join-Path ([Environment]::GetFolderPath('Programs')) 'Naatik Next'
New-Item -ItemType Directory -Path $menu -Force | Out-Null
$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path $menu 'Naatik Next 1.0.lnk'))
$link.TargetPath = $python
$link.Arguments = '-E -s -X utf8 -m naatik_next.app'
$link.WorkingDirectory = $root
$link.Description = (L 'setup.shortcut')
$link.Save()
$uninstall = Join-Path $PSScriptRoot 'uninstall-user.ps1'
$key = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\NaatikNext1.0'
New-Item -Path $key -Force | Out-Null
$properties = @{DisplayName='Naatik Next 1.0'; DisplayVersion='1.0.0'; InstallLocation=$root; UninstallString=('powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' + $uninstall + '"')}
$properties.GetEnumerator() | ForEach-Object { Set-ItemProperty -Path $key -Name $_.Key -Value $_.Value }
Set-Content -LiteralPath (Join-Path $root '.naatik-installed') -Value '1.0.0'
Write-Host (L 'setup.done')
