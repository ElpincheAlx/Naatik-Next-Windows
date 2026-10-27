$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'packaging\language.ps1')
Set-Location -LiteralPath $PSScriptRoot
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUTF8 = '1'
# Native stderr is diagnostic output, not a PowerShell terminating error.
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
$log = Join-Path $PSScriptRoot 'install.log'
$status = 1
Start-Transcript -LiteralPath $log -Force | Out-Null
try {
    if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
        throw (L 'setup.x64')
    }
    $probe = "import sys,sysconfig,struct; assert sys.platform=='win32' and sys.version_info[:2]==(3,13) and struct.calcsize('P')==8 and not sysconfig.get_config_var('Py_GIL_DISABLED')"
    $python = $null
    $candidates = @((Join-Path $PSScriptRoot '.python\tools\python.exe'))
    if ($env:NAATIK_PYTHON) { $candidates += $env:NAATIK_PYTHON }
    # The launcher is optional; never execute the Windows Store python alias.
    if (Get-Command py.exe -ErrorAction SilentlyContinue) {
        $ErrorActionPreference = 'Continue'
        $found = & py.exe -3.13 -c 'import sys; print(sys.executable)' 2>$null
        $ErrorActionPreference = 'Stop'
        if ($LASTEXITCODE -eq 0) { $candidates += $found }
    }
    $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe')
    foreach ($command in @(Get-Command python.exe -All -ErrorAction SilentlyContinue)) {
        if ($command.Source -notlike '*\WindowsApps\*') { $candidates += $command.Source }
    }
    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            $ErrorActionPreference = 'Continue'
            & $candidate -c $probe 2>$null
            $ErrorActionPreference = 'Stop'
            if ($LASTEXITCODE -eq 0) { $python = $candidate; break }
        }
    }
    if (-not $python) {
        Write-Host (L 'setup.python')
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $archive = Join-Path $PSScriptRoot '.python-download.zip'
        $staging = Join-Path $PSScriptRoot ('.python-stage-' + [guid]::NewGuid().ToString('N'))
        try {
            if ($env:NAATIK_PYTHON_ARCHIVE) {
                Copy-Item -LiteralPath $env:NAATIK_PYTHON_ARCHIVE -Destination $archive
            } else {
                Invoke-WebRequest -UseBasicParsing -Uri 'https://api.nuget.org/v3-flatcontainer/python/3.13.17/python.3.13.17.nupkg' -OutFile $archive
            }
            $expected = 'dce409744b088f94c6e37ba41f8100c384c27e029e843237364c602d30d475e5'
            if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
                throw (L 'setup.hash')
            }
            Expand-Archive -LiteralPath $archive -DestinationPath $staging
            $candidate = Join-Path $staging 'tools\python.exe'
            & $candidate -c $probe
            if ($LASTEXITCODE -ne 0) { throw (L 'setup.python_incompatible') }
            if (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.python')) {
                throw (L 'setup.python_existing')
            }
            Move-Item -LiteralPath $staging -Destination (Join-Path $PSScriptRoot '.python')
            $python = Join-Path $PSScriptRoot '.python\tools\python.exe'
        } finally {
            Remove-Item -LiteralPath $archive -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "Python: $python"
    $ErrorActionPreference = 'Continue'
    & $python -u (Join-Path $PSScriptRoot 'tools\install_windows.py') @args
    $status = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($status -ne 0) { throw ((L 'setup.exit') + $status + '. install.log') }
} catch {
    Write-Host ((L 'setup.error_details') + $_.Exception.Message) -ForegroundColor Red
    Write-Host (L 'setup.python_help')
    $status = 1
} finally {
    Stop-Transcript | Out-Null
}
exit $status
