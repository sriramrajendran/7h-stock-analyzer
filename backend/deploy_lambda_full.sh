#!/bin/bash
set -e

echo "🚀 DEPLOYING LAMBDA - NUCLEAR APPROACH"

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

echo "📦 Building minimal Lambda package..."

# Create deployment directory
DEPLOY_DIR="../target/deployments"
mkdir -p "$DEPLOY_DIR"

# Create minimal layer
LAYER_DIR="../target/layer"
rm -rf "$LAYER_DIR"
mkdir -p "$LAYER_DIR/python"

cd "$LAYER_DIR/python"
pip install fastapi==0.68.2 mangum==0.12.2 boto3==1.26.137 requests==2.28.2 --target . --no-deps --force-reinstall --quiet
cd ../..

# Package layer
cd "$LAYER_DIR"
zip -r "../../target/deployments/stock-analyzer-layer.zip" .
cd ../../backend

# Upload layer
echo "📤 Uploading Lambda layer to S3..."
aws s3 cp "$DEPLOY_DIR/stock-analyzer-layer.zip" "s3://7h-stock-analyzer/" --region "$AWS_REGION"

# Package function code
cd ../target/deployments
rm -rf app_structure
mkdir -p app_structure/app
cp -r ../../backend/app/* app_structure/app/
cd app_structure
zip -r ../stock-analyzer-lambda.zip .
cd ..
rm -rf app_structure
cd ../../backend

# Upload function code
echo "📤 Uploading Lambda package to S3..."
aws s3 cp "$DEPLOY_DIR/stock-analyzer-lambda.zip" "s3://7h-stock-analyzer/" --region "$AWS_REGION"

# Deploy infrastructure
echo "🏗️ Deploying Lambda infrastructure..."
aws cloudformation deploy \
    --template-file template.yaml \
    --stack-name stock-analyzer-lambda \
    --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
    --parameter-overrides Environment=production ApiKeyParameter=$API_KEY PushoverTokenParameter=$PUSHOVER_TOKEN PushoverUserParameter=$PUSHOVER_USER \
    --region "$AWS_REGION"

# Create layer version
echo "🔄 Creating new Lambda layer version..."
LAYER_VERSION=$(aws lambda publish-layer-version \
    --layer-name StockAnalyzerDependencies \
    --description "NUCLEAR MINIMAL LAYER" \
    --license-info "MIT" \
    --compatible-runtimes python3.10 \
    --zip-file fileb://"$DEPLOY_DIR/stock-analyzer-layer.zip" \
    --region "$AWS_REGION" \
    --query 'LayerVersionArn' \
    --output text)

# Update function
echo "🔄 Updating Lambda to use new layer..."
aws lambda update-function-configuration \
    --function-name arn:aws:lambda:us-east-1:986440453821:function:stock-analyzer-lambda-StockAnalyzerFunction-BoJLhnbgfJxl \
    --layers "$LAYER_VERSION" \
    --region "$AWS_REGION"

# Update function code
echo "🔄 Updating Lambda function code..."
aws lambda update-function-code \
    --function-name arn:aws:lambda:us-east-1:986440453821:function:stock-analyzer-lambda-StockAnalyzerFunction-BoJLhnbgfJxl \
    --s3-bucket 7h-stock-analyzer \
    --s3-key stock-analyzer-lambda.zip \
    --region "$AWS_REGION"

echo "✅ NUCLEAR DEPLOYMENT COMPLETED!"
echo "🧪 Testing Lambda function..."
aws lambda invoke \
    --function-name arn:aws:lambda:us-east-1:986440453821:function:stock-analyzer-lambda-StockAnalyzerFunction-BoJLhnbgfJxl \
    --payload '{"httpMethod":"GET","path":"/health","headers":{"X-API-Key":"e0fb50277426ebfb42e571710cade9a8e0d5cfb58738a199cd256408374a02a8"}}' \
    --cli-binary-format raw-in-base64-out \
    ../target/response.json

echo "📊 Response:"
cat ../target/response.json
