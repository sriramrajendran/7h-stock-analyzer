#!/bin/bash
set -e

# Configuration
STACK_NAME="7h-stock-analyzer"
REGION="us-east-1"
ENVIRONMENT="prod"

echo "Deploying 7H Stock Analyzer to AWS..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed"
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Error: SAM CLI is not installed"
    exit 1
fi

# Build and package layer
echo "Building Lambda layer..."
./infra/scripts/build_layer.sh

# Build and package application
echo "Building Lambda package..."
./infra/scripts/build_package.sh

# Deploy using SAM
echo "Deploying stack with SAM..."
sam deploy \
    --template-file infra/template.yaml \
    --stack-name $STACK_NAME \
    --region $REGION \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        EnableVpc=false \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

echo "Deployment completed successfully!"

# Get outputs
echo "Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "API Gateway URL: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerApi`].OutputValue' --output text)"
echo "S3 Bucket: $(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query 'Stacks[0].Outputs[?OutputKey==`StockDataBucket`].OutputValue' --output text)"
