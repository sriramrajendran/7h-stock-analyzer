#!/bin/bash
set -e

echo "Testing 7H Stock Analyzer locally..."

# Set environment variables
export AWS_REGION="us-east-1"
export S3_BUCKET_NAME="stock-analyzer-local"
export PUSHOVER_TOKEN="test-token"
export PUSHOVER_USER="test-user"
export ENABLE_NOTIFICATIONS="false"
export LOG_LEVEL="INFO"

# Change to backend directory
cd ../backend

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the FastAPI server
echo "Starting local server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "Local server running at http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
