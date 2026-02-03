#!/bin/bash
set -e

echo "🎨 Deploying frontend to S3..."

# Check if environment is provided
if [ -z "$1" ]; then
    echo "❌ Environment not specified"
    echo "Usage: ./infra/aws/deploy_frontend.sh [dev|staging|prod]"
    exit 1
fi

ENVIRONMENT=$1

# Load environment variables
if [ ! -f ../../.env.local ]; then
    echo "❌ .env.local not found. Please run './infra/local/setup_local.sh' first."
    exit 1
fi

export $(grep -v '^#' ../../.env.local | xargs)

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

# Set bucket name based on environment
BUCKET_NAME=$S3_BUCKET_NAME_PROD

echo "📋 Frontend Deployment Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Bucket: $BUCKET_NAME"
echo "  Region: $AWS_REGION"

# Check if bucket exists
if ! aws s3 ls "s3://$BUCKET_NAME" &>/dev/null; then
    echo "🪣 Creating S3 bucket: $BUCKET_NAME"
    aws s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION
    
    # Configure bucket for static website hosting
    aws s3 website "s3://$BUCKET_NAME" \
        --index-document index.html \
        --error-document error.html
    
    echo "✅ Created and configured S3 bucket"
else
    echo "ℹ️  S3 bucket already exists"
fi

# Build frontend
echo "🔨 Building frontend..."
cd ../../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Update environment variables for production
echo "📝 Updating environment variables..."
cat > .env.production << EOF
REACT_APP_S3_BUCKET=$S3_BUCKET_NAME_PROD
REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL_AWS
REACT_APP_S3_REGION=$AWS_REGION
REACT_APP_ENVIRONMENT=$ENVIRONMENT
EOF

# Build for production
echo "🏗️  Building production bundle..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed - dist directory not found"
    exit 1
fi

# Deploy to S3
echo "📤 Deploying to S3..."
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --delete

# Set bucket policy for public read access
echo "🔐 Setting bucket policy..."
aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::'$BUCKET_NAME'/*"
            }
        ]
    }'

# Configure CORS
echo "🌐 Configuring CORS..."
aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration '{
        "CORSRules": [
            {
                "AllowedHeaders": ["*"],
                "AllowedMethods": ["GET", "HEAD"],
                "AllowedOrigins": ["*"],
                "MaxAgeSeconds": 3600
            }
        ]
    }'

cd ../..

echo ""
echo "🎉 Frontend deployment completed!"
echo ""
echo "🌐 S3 Website URL: http://$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
echo "🪣 S3 Bucket: s3://$BUCKET_NAME"
echo ""
echo "🧪 Test the deployment:"
echo "  curl http://$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
echo ""
echo "💡 To update content:"
echo "  ./infra/aws/deploy_frontend.sh $ENVIRONMENT"
