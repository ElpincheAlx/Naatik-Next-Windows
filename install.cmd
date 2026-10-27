@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH="
set "PYTHONHOME="
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
if errorlevel 1 (
  echo La instalacion no se completo. Revisa el mensaje anterior.
  pause
  exit /b 1
)
pause
