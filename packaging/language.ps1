# Catalogs shared with the application and embedded in Setup.exe.
$uiCode = if ($env:NAATIK_UI_LANGUAGE -eq 'en') { 'en' } else { 'es' }
$uiRoot = Split-Path -Parent $PSScriptRoot
# PowerShell 5 ConvertFrom-Json rejects keys differing only by case (e.g.
# Traducción / TRADUCCIÓN). Use the same case-sensitive reader as Setup.exe.
Add-Type -AssemblyName System.Web.Extensions
$uiReader = New-Object System.Web.Script.Serialization.JavaScriptSerializer
$uiCatalog = $uiReader.DeserializeObject([IO.File]::ReadAllText((Join-Path $uiRoot ('naatik_next\locales\' + $uiCode + '.json'))))
function L([string]$key) { return $uiCatalog[$key] }
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
