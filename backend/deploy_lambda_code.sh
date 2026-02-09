#!/bin/bash
set -e

echo "🚀 Deploying Lambda Code Only..."

# Load environment variables
if [ ! -f ../.env.local ]; then
    echo "❌ .env.local not found. Please create .env.local with AWS configuration."
    exit 1
fi

export $(grep -v '^#' ../.env.local | xargs)

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📦 Building Lambda package..."

# Create deployment directory
DEPLOY_DIR="../target/deployments"
mkdir -p "$DEPLOY_DIR"

# Package Lambda code
cd app
zip -r "$DEPLOY_DIR/stock-analyzer-lambda.zip" .
cd ..

echo "📤 Uploading Lambda package to S3..."

# Upload to S3
aws s3 cp "$DEPLOY_DIR/stock-analyzer-lambda.zip" "s3://7h-stock-analyzer/" --region "$AWS_REGION"

echo "🔄 Updating Lambda function code..."

# Update Lambda function code (no infrastructure changes)
aws lambda update-function-code \
    --function-name StockAnalyzerFunction \
    --s3-bucket 7h-stock-analyzer \
    --s3-key stock-analyzer-lambda.zip \
    --region "$AWS_REGION"

echo "✅ Lambda code deployment completed!"
echo "📊 Function updated without infrastructure changes"
