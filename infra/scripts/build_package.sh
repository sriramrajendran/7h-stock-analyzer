#!/bin/bash
set -e

echo "Building Lambda package for 7H Stock Analyzer..."

# Create package directory
rm -rf package
mkdir -p package

# Copy application code
echo "Copying application code..."
cp -r ../backend/app package/
cp ../backend/requirements.txt package/

# Create zip file
echo "Creating deployment package..."
cd package
zip -r ../stock-analyzer-lambda.zip .
cd ..

echo "Lambda package built successfully: stock-analyzer-lambda.zip"
echo "Package size: $(du -h stock-analyzer-lambda.zip | cut -f1)"
