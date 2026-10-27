param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
& $python (Join-Path $root 'tools\build_source_zip.py')
if ($LASTEXITCODE -ne 0) { throw 'No se pudo preparar el codigo fuente.' }
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) { throw 'Falta el compilador .NET Framework de Windows.' }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$payload = Join-Path (Split-Path -Parent $root) 'Naatik-next-windows-source.zip'
$exe = Join-Path $OutputDirectory 'Naatik-Next-1.0-Setup.exe'
& $compiler /nologo /target:winexe /platform:x64 /optimize+ /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll /reference:System.IO.Compression.dll /reference:System.IO.Compression.FileSystem.dll "/resource:$payload,payload.zip" "/resource:$root\naatik_next\locales\es.json,es.json" "/resource:$root\naatik_next\locales\en.json,en.json" "/out:$exe" (Join-Path $PSScriptRoot 'Setup.cs')
if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el instalador.' }
Copy-Item -LiteralPath $payload -Destination (Join-Path $OutputDirectory 'Naatik-Next-1.0-source.zip') -Force
Get-FileHash -LiteralPath $exe -Algorithm SHA256
