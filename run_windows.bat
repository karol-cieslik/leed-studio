@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo LEED Studio is not installed yet. Run install_windows.ps1 from PowerShell first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m leed_studio
