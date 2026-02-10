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

# Package Lambda code with proper structure
cd ../target/deployments
rm -rf temp app_structure
mkdir -p app_structure/app
cp -r ../../backend/app/* app_structure/app/
cd app_structure
zip -r ../stock-analyzer-lambda.zip .
cd ..
rm -rf app_structure
cd ../../backend

echo "� Uploading Lambda package to S3..."

# Upload to S3
aws s3 cp "$DEPLOY_DIR/stock-analyzer-lambda.zip" "s3://7h-stock-analyzer/" --region "$AWS_REGION"

# Update Lambda function code
echo "🔄 Updating Lambda function code..."
aws lambda update-function-code \
    --function-name arn:aws:lambda:us-east-1:986440453821:function:stock-analyzer-lambda-StockAnalyzerFunction-BoJLhnbgfJxl \
    --s3-bucket 7h-stock-analyzer \
    --s3-key stock-analyzer-lambda.zip \
    --region "$AWS_REGION"

echo "✅ Lambda code deployment completed!"
echo "📊 Function code updated without layer changes"
echo "🔐 Environment variables unchanged (use deploy_lambda_full.sh to update)"

# Test Lambda function
echo "🧪 Testing Lambda function..."
aws lambda invoke \
    --function-name arn:aws:lambda:us-east-1:986440453821:function:stock-analyzer-lambda-StockAnalyzerFunction-BoJLhnbgfJxl \
    --payload '{"httpMethod":"GET","path":"/health","headers":{"X-API-Key":"e0fb50277426ebfb42e571710cade9a8e0d5cfb58738a199cd256408374a02a8"}}' \
    --cli-binary-format raw-in-base64-out \
    ../target/response.json
