#!/bin/bash
# Build standalone executable using PyInstaller

set -e

echo "Building FileFlow backend executable..."

cd "$(dirname "$0")"

# Build with PyInstaller
poetry run pyinstaller \
  --name=fileflow-backend \
  --onefile \
  --clean \
  --noconfirm \
  --log-level=INFO \
  --hidden-import=fileflow_core \
  --hidden-import=fileflow_api \
  --hidden-import=fileflow_config \
  --hidden-import=fileflow_storage \
  --hidden-import=fileflow_cli \
  main.py

echo "✓ Build complete! Executable at: dist/fileflow-backend"
