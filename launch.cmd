@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1" %*
if errorlevel 1 (
  echo No se pudo iniciar. Revisa launch.log y ejecuta install.cmd para reparar.
  pause
  exit /b 1
)
