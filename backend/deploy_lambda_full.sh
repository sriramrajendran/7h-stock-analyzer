#!/bin/bash
set -e

echo "🚀 Deploying Lambda + Infrastructure..."

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

# Upload Lambda layer to S3 (if not already uploaded)
echo "📤 Uploading Lambda layer to S3..."
aws s3 cp "$DEPLOY_DIR/stock-analyzer-layer.zip" "s3://7h-stock-analyzer/" --region "$AWS_REGION" || echo "Layer already exists"

# Package Lambda code
cd app
zip -r "../../target/deployments/stock-analyzer-lambda.zip" . -x "__pycache__/*"
cd ..

echo "📤 Uploading Lambda package to S3..."

# Upload to S3
aws s3 cp "$DEPLOY_DIR/stock-analyzer-lambda.zip" "s3://7h-stock-analyzer/" --region "$AWS_REGION"

echo "🏗️ Deploying Lambda infrastructure..."

# Check if stack exists and is in ROLLBACK_COMPLETE state, delete if needed
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name stock-analyzer-lambda --query "Stacks[0].StackStatus" --output text 2>/dev/null || echo "DOES_NOT_EXIST")

if [ "$STACK_STATUS" = "ROLLBACK_COMPLETE" ]; then
    echo "🗑️ Deleting existing stack in ROLLBACK_COMPLETE state..."
    aws cloudformation delete-stack --stack-name stock-analyzer-lambda --region "$AWS_REGION"
    aws cloudformation wait stack-delete-complete --stack-name stock-analyzer-lambda --region "$AWS_REGION"
fi

# Deploy Lambda stack
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name stock-analyzer-lambda \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment=production ApiKeyParameter=$API_KEY PushoverTokenParameter=$PUSHOVER_TOKEN PushoverUserParameter=$PUSHOVER_USER \
    --region "$AWS_REGION"

echo "✅ Lambda + infrastructure deployment completed!"
echo "📊 Stack: 7h-stock-analyzer-lambda"
echo "🔗 Function and infrastructure updated"
