$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
$root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot)).TrimEnd('\')
$expected = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'Programs\NaatikNext\1.0')).TrimEnd('\')
if ($root -ne $expected -or -not (Test-Path -LiteralPath (Join-Path $root '.naatik-installed'))) { throw 'No se reconoce esta instalacion.' }
if ([Windows.Forms.MessageBox]::Show('Cierra Naatik Next antes de continuar. Se eliminara la aplicacion 1.0. Tus modelos, diccionarios y ajustes del perfil se conservaran.','Desinstalar Naatik Next','OKCancel') -ne 'OK') { exit }
try {
    $menu = Join-Path ([Environment]::GetFolderPath('Programs')) 'Naatik Next\Naatik Next 1.0.lnk'
    Remove-Item -LiteralPath $root -Recurse -Force
    Remove-Item -LiteralPath $menu -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\NaatikNext1.0' -Force -ErrorAction SilentlyContinue
    [Windows.Forms.MessageBox]::Show('Aplicacion eliminada. El perfil y sus datos se conservaron.','Naatik Next') | Out-Null
} catch { [Windows.Forms.MessageBox]::Show('No se pudo completar. Cierra la aplicacion y vuelve a intentarlo. ' + $_.Exception.Message,'Naatik Next') | Out-Null }
