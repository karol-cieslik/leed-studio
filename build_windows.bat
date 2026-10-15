@echo off
setlocal
cd /d "%~dp0"
py -3.12 -m pip install --upgrade pip
if errorlevel 1 goto :error
py -3.12 -m pip install -e ".[dev]" pyinstaller
if errorlevel 1 goto :error
set QT_QPA_PLATFORM=offscreen
py -3.12 -m compileall -q leed_studio tests tools
if errorlevel 1 goto :error
py -3.12 -m pytest -q -ra
if errorlevel 1 goto :error
py -3.12 -m leed_studio --self-test-core
if errorlevel 1 goto :error
py -3.12 -m leed_studio --self-test-gui
if errorlevel 1 goto :error
py -3.12 -m PyInstaller --clean --noconfirm LEED_Studio.spec
if errorlevel 1 goto :error
"dist\LEED Studio\LEED Studio.exe" --self-test-core
if errorlevel 1 goto :error
"dist\LEED Studio\LEED Studio.exe" --self-test-gui
if errorlevel 1 goto :error
echo.
echo Build and frozen-app smoke test passed.
echo Portable app: dist\LEED Studio\LEED Studio.exe
echo For an installer, install Inno Setup 6 and run:
echo   iscc packaging\LEED-Studio.iss
exit /b 0
:error
echo Build or test failed. Review the error above.
exit /b 1
