#!/bin/bash
set -e

echo "Building Lambda layer for 7H Stock Analyzer..."

# Create layer directory structure
rm -rf layer/python
mkdir -p layer/python

# Install Python dependencies to layer
echo "Installing Python dependencies..."
pip install -r ../backend/requirements.txt -t layer/python/

# Remove unnecessary files to reduce layer size
echo "Optimizing layer size..."
find layer/python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find layer/python -name "*.pyc" -delete
find layer/python -name "*.pyo" -delete
find layer/python -name "*.pyd" -delete

# Remove tests and documentation
rm -rf layer/python/*/tests 2>/dev/null || true
rm -rf layer/python/*/test 2>/dev/null || true
rm -rf layer/python/*/.github 2>/dev/null || true

# Compress the layer
echo "Compressing layer..."
cd layer
zip -r ../stock-analyzer-layer.zip python
cd ..

echo "Lambda layer built successfully: stock-analyzer-layer.zip"
echo "Layer size: $(du -h stock-analyzer-layer.zip | cut -f1)"
