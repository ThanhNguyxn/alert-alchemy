#!/usr/bin/env bash
# Alert Alchemy Build Script for macOS/Linux
# Builds the executable into dist/

set -e

echo "🔧 Alert Alchemy - Build Script (macOS/Linux)"
echo ""

# Navigate to repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Check Python
echo "📦 Checking Python..."
python3 --version || { echo "❌ Python3 not found. Please install Python 3.11+"; exit 1; }

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -e ".[dev]"
pip3 install pyinstaller

# Run tests first
echo "🧪 Running tests..."
pytest tests/ -v || { echo "❌ Tests failed. Aborting build."; exit 1; }

# Build with PyInstaller
echo "🔨 Building executable..."
pyinstaller build/alert-alchemy.spec --clean --noconfirm

# Check if build succeeded
if [ -f "dist/alert-alchemy" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📁 Executable: dist/alert-alchemy"
    echo ""
    echo "To run: ./dist/alert-alchemy --help"
else
    echo "❌ Build failed. Check the output above for errors."
    exit 1
fi
