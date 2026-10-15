$ErrorActionPreference = "Stop"
$ProjectDir = $PSScriptRoot
Set-Location $ProjectDir

Write-Host "LEED Studio 0.11.1 setup"
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python Launcher 'py' was not found. Install Python 3.11 or 3.12 from python.org and enable the launcher."
}

$PythonVersion = $null
foreach ($Candidate in @("3.12", "3.11")) {
    & py -$Candidate --version *> $null
    if ($LASTEXITCODE -eq 0) { $PythonVersion = $Candidate; break }
}
if (-not $PythonVersion) {
    throw "Python 3.11 or 3.12 was not found. Install one from python.org, then rerun this script."
}
Write-Host "Using Python $PythonVersion"
if (-not (Test-Path (Join-Path $ProjectDir ".venv"))) {
    & py -$PythonVersion -m venv (Join-Path $ProjectDir ".venv")
}
$Python = Join-Path $ProjectDir ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -e ".[dev]"
Write-Host "Setup complete. Launching LEED Studio..."
& $Python -m leed_studio
