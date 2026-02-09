#!/bin/bash
set -e

echo "🚀 Deploying Infrastructure Only (S3, CloudFront, API Gateway)..."

# Load environment variables
if [ ! -f ../../.env.local ]; then
    echo "❌ .env.local not found. Please create .env.local with AWS configuration."
    exit 1
fi

export $(grep -v '^#' ../../.env.local | xargs)

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "🏗️ Deploying infrastructure stack..."

# Deploy infrastructure stack (no Lambda changes)
aws cloudformation deploy \
    --template-file infra-template.yaml \
    --stack-name 7h-stock-analyzer-infra \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Environment=production \
    --region "$AWS_REGION"

echo "✅ Infrastructure deployment completed!"
echo "📊 Stack: 7h-stock-analyzer-infra"
echo "🪣 S3 Bucket, CloudFront, and API Gateway updated"
echo "🔗 No Lambda functions were modified"
