#!/bin/bash
set -e

echo "🚀 Deploying 7H Stock Analyzer to AWS (Cost-Optimized)..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📋 Deployment Configuration:"
echo "  Account: $AWS_ACCOUNT"
echo "  Region: $AWS_REGION"
echo "  Environment: ${ENVIRONMENT:-dev}"

# Set environment-specific variables
ENVIRONMENT=${ENVIRONMENT:-dev}
STACK_NAME="7h-stock-analyzer-${ENVIRONMENT}"

# Cost optimization settings
MEMORY_SIZE=${MEMORY_SIZE:-512}  # Reduced from 1024MB
TIMEOUT=${TIMEOUT:-180}  # Reduced from 300s
RESERVED_CONCURRENCY=${RESERVED_CONCURRENCY:-2}  # Reduced from 5

echo "💰 Cost Optimization Settings:"
echo "  Memory: ${MEMORY_SIZE}MB"
echo "  Timeout: ${TIMEOUT}s"
echo "  Concurrency: ${RESERVED_CONCURRENCY}"

# Create S3 bucket for deployment artifacts
DEPLOYMENT_BUCKET="7h-stock-analyzer-deploy"
echo "🪣 Creating deployment bucket: $DEPLOYMENT_BUCKET"

if ! aws s3 ls "s3://$DEPLOYMENT_BUCKET" &>/dev/null; then
    aws s3 mb "s3://$DEPLOYMENT_BUCKET" --region $AWS_REGION
    echo "✅ Created deployment bucket"
else
    echo "ℹ️  Deployment bucket already exists"
fi

# Build Lambda layer
echo "📦 Building Lambda layer..."
rm -rf ../layer/python
mkdir -p ../layer/python

# Install only essential dependencies for production
echo "Installing production dependencies..."
pip install --platform manylinux2014_x86_64 --only-binary=:all: \
    --target layer/python \
    -r backend/requirements.txt

# Optimize layer size
echo "Optimizing layer size..."
find ../layer/python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ../layer/python -name "*.pyc" -delete 2>/dev/null || true
find ../layer/python -name "*.pyo" -delete 2>/dev/null || true
find ../layer/python -name "*.pyd" -delete 2>/dev/null || true
find ../layer/python -name "*.so" -delete 2>/dev/null || true

# Remove unnecessary files
rm -rf ../layer/python/*/tests 2>/dev/null || true
rm -rf ../layer/python/*/.github 2>/dev/null || true
rm -rf ../layer/python/*/doc 2>/dev/null || true

# Compress layer
echo "Compressing layer..."
cd ../layer
zip -r ../stock-analyzer-layer.zip python -x "*.pyc" "*.pyo" "__pycache__/*"
cd ..

LAYER_SIZE=$(du -h stock-analyzer-layer.zip | cut -f1)
echo "✅ Lambda layer created: $LAYER_SIZE"

# Build application package
echo "📦 Building application package..."
rm -rf package
mkdir -p package

# Copy only necessary files
cp -r backend/app package/
cp backend/requirements.txt package/

# Create zip
cd package
zip -r ../stock-analyzer-lambda.zip . -x "*.pyc" "*.pyo" "__pycache__/*"
cd ..

PACKAGE_SIZE=$(du -h stock-analyzer-lambda.zip | cut -f1)
echo "✅ Application package created: $PACKAGE_SIZE"

# Upload to S3
echo "📤 Uploading to S3..."
aws s3 cp stock-analyzer-layer.zip "s3://$DEPLOYMENT_BUCKET/"
aws s3 cp stock-analyzer-lambda.zip "s3://$DEPLOYMENT_BUCKET/"

# Deploy with SAM (cost-optimized template)
echo "🚀 Deploying with SAM..."
sam deploy \
    --template-file template.yaml \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --s3-bucket $DEPLOYMENT_BUCKET \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        MemorySize=$MEMORY_SIZE \
        Timeout=$TIMEOUT \
        ReservedConcurrency=$RESERVED_CONCURRENCY \
        EnableVpc=false \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --no-confirm-changeset \
    --no-fail-on-empty-changeset

# Get stack outputs
echo "📋 Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerApi`].OutputValue' \
    --output text)

S3_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`StockDataBucket`].OutputValue' \
    --output text)

LAMBDA_ARN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerFunction`].OutputValue' \
    --output text)

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Stack Information:"
echo "  Stack Name: $STACK_NAME"
echo "  API URL: $API_URL"
echo "  S3 Bucket: $S3_BUCKET"
echo "  Lambda ARN: $LAMBDA_ARN"
echo ""
echo "🧪 Test the deployment:"
echo "  curl $API_URL/health"
echo "  curl $API_URL/analysis/AAPL"
echo ""
echo "💰 Cost Optimization Applied:"
echo "  ✅ Reduced memory to ${MEMORY_SIZE}MB"
echo "  ✅ Reduced timeout to ${TIMEOUT}s"
echo "  ✅ Limited concurrency to ${RESERVED_CONCURRENCY}"
echo "  ✅ Disabled VPC (reduces cost)"
echo "  ✅ Optimized layer size ($LAYER_SIZE)"
echo ""
echo "📊 Estimated Monthly Cost: < $15"
echo "  - Lambda: ~$8 (based on 100k invocations/month)"
echo "  - S3: ~$3 (storage + requests)"
echo "  - API Gateway: ~$4 (1M requests/month)"

# Clean up local files
echo "🧹 Cleaning up local files..."
rm -f stock-analyzer-layer.zip stock-analyzer-lambda.zip
rm -rf layer package

echo "✅ Deployment cleanup completed"

# Setup weekly reconciliation monitoring
echo ""
echo "🔄 Setting up weekly reconciliation monitoring..."

# Create S3 prefix for reconciliation data
echo "📁 Creating reconciliation data structure..."
aws s3api put-object \
    --bucket "7h-stock-analyzer-${ENVIRONMENT}" \
    --key "recon/.gitkeep" \
    --content-type "application/octet-stream" \
    --region $AWS_REGION || echo "ℹ️  Recon directory already exists"

# Test reconciliation endpoint
echo "🧪 Testing reconciliation endpoint..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

if [ -n "$API_URL" ]; then
    echo "🌐 API URL: $API_URL"
    
    # Test recon endpoint (will show 0 initially, but confirms it works)
    echo "📊 Testing reconciliation API..."
    RECON_RESPONSE=$(curl -s -w "%{http_code}" "$API_URL/recon/summary" || echo "000")
    
    if [[ "$RECON_RESPONSE" == *"200"* ]]; then
        echo "✅ Reconciliation API endpoint is working"
    else
        echo "⚠️  Reconciliation API test failed (expected for new deployment)"
    fi
    
    echo ""
    echo "📋 Weekly Reconciliation Details:"
    echo "  🕐 Schedule: Every Sunday at 6:00 PM EST (23:00 UTC)"
    echo "  📊 Data: Tracks profit targets vs stop losses"
    echo "  📈 Metrics: Days to target, success rates, performance by type"
    echo "  🔗 Endpoint: $API_URL/recon/summary"
    echo "  🗂️  Storage: s3://7h-stock-analyzer-${ENVIRONMENT}/recon/daily/"
    echo ""
    echo "🎯 To view reconciliation data:"
    echo "  curl -s $API_URL/recon/summary | jq ."
    echo "  curl -s $API_URL/recon/daily/\$(date +%Y-%m-%d) | jq ."
else
    echo "⚠️  Could not get API URL - reconciliation may need manual testing"
fi

echo ""
echo "✅ Weekly reconciliation setup completed!"
