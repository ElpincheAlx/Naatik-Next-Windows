$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUTF8 = '1'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    Write-Host 'Primero ejecuta install.cmd (requiere Python 3.13 x64 de python.org).'
    Read-Host 'Enter para cerrar'
    exit 1
}
# Console execution and transcript preserve diagnostics, including Python stderr.
Start-Transcript -LiteralPath (Join-Path $PSScriptRoot 'launch.log') -Force | Out-Null
$status = 1
try {
    $ErrorActionPreference = 'Continue'
    & $python -u -m naatik_next.app @args
    $status = $LASTEXITCODE
} finally {
    Stop-Transcript | Out-Null
}
exit $status
