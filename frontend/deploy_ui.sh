#!/bin/bash
set -e

echo "🚀 Deploying UI..."

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
BUCKET_NAME=$S3_BUCKET_NAME_PROD

echo "📋 UI Deployment:"
echo "  Bucket: $BUCKET_NAME"
echo "  Region: $AWS_REGION"

# Check if bucket exists
if ! aws s3 ls "s3://$BUCKET_NAME" &>/dev/null; then
    echo "❌ S3 bucket '$BUCKET_NAME' not found."
    echo "💡 Please deploy infrastructure first: ./infra/aws/deploy_infra.sh"
    exit 1
fi

echo "🔨 Building frontend..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Update environment variables for production
echo "📝 Updating environment variables..."
cat > .env.production << EOF
REACT_APP_S3_BUCKET=$S3_BUCKET_NAME_PROD
REACT_APP_API_GATEWAY_URL=$API_GATEWAY_URL
REACT_APP_ENVIRONMENT=aws
EOF

# Build frontend
echo "🏗️ Building production bundle..."
npm run build

echo "📤 Uploading to S3..."

# Sync build files to S3
aws s3 sync build/ "s3://$BUCKET_NAME/" \
    --delete \
    --exclude "*.html" \
    --include "*.html" \
    --content-type "text/html" \
    --cache-control "max-age=0,no-cache,no-store,must-revalidate"

# Set cache control for static assets
aws s3 sync build/ "s3://$BUCKET_NAME/" \
    --delete \
    --exclude "*.html" \
    --cache-control "max-age=31536000,public"

echo "🌐 Updating CloudFront distribution..."

# Get CloudFront distribution ID
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='7h-stock-analyzer frontend'].Id" \
    --output text)

if [ -z "$DISTRIBUTION_ID" ]; then
    echo "❌ CloudFront distribution not found."
    echo "💡 Please deploy infrastructure first: ./infra/aws/deploy_infra.sh"
    exit 1
fi

# Create invalidation
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query "Invalidation.Id" \
    --output text)

echo "⏳ Waiting for CloudFront invalidation..."
aws cloudfront wait invalidation-completed \
    --distribution-id "$DISTRIBUTION_ID" \
    --id "$INVALIDATION_ID"

echo "✅ UI deployment completed!"
echo "🌐 S3: https://$BUCKET_NAME.s3-website-us-east-1.amazonaws.com"
echo "🚀 CloudFront: https://d37m5zz5fkglhg.cloudfront.net"
echo "📊 CDN cache invalidated and updated"
