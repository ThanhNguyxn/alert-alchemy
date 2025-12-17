# Alert Alchemy Build Script for Windows
# Builds the executable into dist/

$ErrorActionPreference = "Stop"

Write-Host "🔧 Alert Alchemy - Windows Build Script" -ForegroundColor Cyan
Write-Host ""

# Navigate to repo root
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Check Python
Write-Host "📦 Checking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"
pip install pyinstaller

# Run tests first
Write-Host "🧪 Running tests..." -ForegroundColor Yellow
pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed. Aborting build." -ForegroundColor Red
    exit 1
}

# Build with PyInstaller
Write-Host "🔨 Building executable..." -ForegroundColor Yellow
pyinstaller build/alert-alchemy.spec --clean --noconfirm

# Check if build succeeded
if (Test-Path "dist/alert-alchemy.exe") {
    Write-Host ""
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host "📁 Executable: dist/alert-alchemy.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To run: .\dist\alert-alchemy.exe --help" -ForegroundColor White
} else {
    Write-Host "❌ Build failed. Check the output above for errors." -ForegroundColor Red
    exit 1
}
