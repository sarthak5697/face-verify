# setup.ps1 - one-time setup on a fresh Windows machine.
# Run from the project folder:  powershell -ExecutionPolicy Bypass -File .\setup.ps1

Set-Location $PSScriptRoot

function Fail([string]$message) {
    Write-Host "ERROR: $message" -ForegroundColor Red
    exit 1
}

# 1. Find Python. Prefer 3.10, the version requirements-lock.txt was made with.
$pyExe = $null
$pyArgs = @()
$pyVersion = $null

if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in "3.10", "3.11", "3.12") {
        py "-$v" -c "import sys" 2>$null
        if ($LASTEXITCODE -eq 0) { $pyExe = "py"; $pyArgs = @("-$v"); $pyVersion = $v; break }
    }
}
if (-not $pyExe -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $v = python -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
    if ($v -in "3.10", "3.11", "3.12") { $pyExe = "python"; $pyVersion = $v }
}
if (-not $pyExe) {
    Fail "Python 3.10, 3.11 or 3.12 not found. Install Python 3.10 from python.org (tick 'Add python.exe to PATH'), then run this again."
}
Write-Host "Using Python $pyVersion"

# 2. Create the virtual environment (skipped if it already exists).
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    & $pyExe @pyArgs -m venv venv
    if ($LASTEXITCODE -ne 0) { Fail "Could not create the virtual environment." }
}
$venvPython = ".\venv\Scripts\python.exe"

# 3. Install dependencies. The lock file has exact versions but only fits Python 3.10.
$reqFile = if ($pyVersion -eq "3.10") { "requirements-lock.txt" } else { "requirements.txt" }

Write-Host "Upgrading pip..."
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail "Could not upgrade pip." }

Write-Host "Installing dependencies from $reqFile (TensorFlow is large; this takes a few minutes)..."
& $venvPython -m pip install -r $reqFile
if ($LASTEXITCODE -ne 0) { Fail "Dependency install failed. Read the pip error above." }

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Start the API with:  powershell -ExecutionPolicy Bypass -File .\run.ps1"
