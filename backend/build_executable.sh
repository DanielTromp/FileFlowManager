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

# Create architecture-specific symlink for Tauri externalBin
ARCH=$(uname -m)
if [ "$ARCH" = "arm64" ]; then
  TARGET_TRIPLE="aarch64-apple-darwin"
else
  TARGET_TRIPLE="x86_64-apple-darwin"
fi

cd dist
ln -sf fileflow-backend fileflow-backend-${TARGET_TRIPLE}
cd ..

echo "✓ Build complete! Executable at: dist/fileflow-backend"
echo "✓ Created Tauri-compatible symlink: dist/fileflow-backend-${TARGET_TRIPLE}"
