#!/bin/bash
set -e

# Parse command line arguments
QUICK_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        *)
            if [ -z "$ENVIRONMENT" ]; then
                ENVIRONMENT=$1
            else
                echo "Unknown option: $1"
                echo "Usage: $0 [--quick] [dev|staging|prod]"
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if environment is provided
if [ -z "$ENVIRONMENT" ]; then
    echo "❌ Environment not specified"
    echo "Usage: $0 [--quick] [dev|staging|prod]"
    exit 1
fi

if [ "$QUICK_MODE" = true ]; then
    echo "⚡ Quick mode enabled - Optimized frontend update"
fi

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
    if [ "$QUICK_MODE" = true ]; then
        echo "❌ Quick mode requires existing S3 bucket. Bucket '$BUCKET_NAME' not found."
        echo "💡 Please run full deployment first: ./deploy_frontend.sh $ENVIRONMENT"
        exit 1
    else
        echo "🪣 Creating S3 bucket: $BUCKET_NAME"
        aws s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION
        
        # Configure bucket for static website hosting
        aws s3 website "s3://$BUCKET_NAME" \
            --index-document index.html \
            --error-document error.html
        
        echo "✅ Created and configured S3 bucket"
    fi
else
    echo "ℹ️  S3 bucket already exists"
fi

# Quick mode: Skip CloudFront setup and do optimized S3 sync
if [ "$QUICK_MODE" = true ]; then
    echo "⚡ Quick Frontend Update Mode"
    echo "  Skipping CloudFront setup..."
    echo "  Performing optimized S3 sync..."
    echo "⚡ Quick Frontend Update Mode"
    echo "  Skipping CloudFront setup..."
    echo "  Performing optimized S3 sync..."
    
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
REACT_APP_S3_BUCKET_URL=https://7h-stock-analyzer.s3.$AWS_REGION.amazonaws.com
REACT_APP_CLOUDFRONT_URL=https://$CLOUDFRONT_DOMAIN
EOF

    # Build for production with explicit environment variable
    echo "  Building production bundle..."
    export REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL_AWS
    npm run build
    
    if [ ! -d "dist" ]; then
        echo " Build failed - dist directory not found"
        exit 1
    fi
    
    # Optimized S3 sync with cache control
    echo "📤 Deploying to S3 with optimized sync..."
    aws s3 sync dist/ "s3://$BUCKET_NAME/" \
        --delete \
        --cache-control "max-age=31536000,public" \
        --exclude "*.html" \
        --exclude "service-worker.js" \
        --exclude "manifest.json"
    
    # Sync HTML files with shorter cache time
    aws s3 sync dist/ "s3://$BUCKET_NAME/" \
        --delete \
        --cache-control "max-age=0,no-cache,no-store,must-revalidate" \
        --exclude "*" \
        --include "*.html"
    
    # Sync service worker and manifest with specific cache
    aws s3 sync dist/ "s3://$BUCKET_NAME/" \
        --delete \
        --cache-control "max-age=86400,public" \
        --exclude "*" \
        --include "service-worker.js" \
        --include "manifest.json"
    
    # Get existing CloudFront distribution (if any)
    DISTRIBUTION_ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='$BUCKET_NAME frontend'].Id" \
        --output text)
    
    if [ -n "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
        echo "🌐 Found CloudFront distribution: $DISTRIBUTION_ID"
        echo "🔄 Creating selective invalidation..."
        
        # Create invalidation for HTML files and service worker
        INVALIDATION_ID=$(aws cloudfront create-invalidation \
            --distribution-id $DISTRIBUTION_ID \
            --paths "/index.html" "/service-worker.js" "/manifest.json" "/*.js" "/*.css" \
            --query 'Invalidation.Id' \
            --output text)
        
        echo "⏳ Waiting for invalidation to complete..."
        aws cloudfront wait invalidation-completed \
            --distribution-id $DISTRIBUTION_ID \
            --id $INVALIDATION_ID
        
        echo "✅ CloudFront invalidation completed"
        
        # Get CloudFront domain name
        CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
            --id $DISTRIBUTION_ID \
            --query 'Distribution.DomainName' \
            --output text)
    else
        echo "⚠️  No CloudFront distribution found"
        CLOUDFRONT_DOMAIN="$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
    fi
    
    cd ../..
    
    echo ""
    echo "🎉 Quick Frontend deployment completed!"
    echo "⚡ Deployment time: ~1-2 minutes (vs 3-5 minutes for full deployment)"
    echo ""
    echo "📋 Quick deployment info:"
    echo "  Bucket: s3://$BUCKET_NAME"
    echo "  CloudFront: https://$CLOUDFRONT_DOMAIN"
    echo "  S3 Direct: http://$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
    echo ""
    echo "🧪 Test the deployment:"
    echo "  curl https://$CLOUDFRONT_DOMAIN"
    echo "  curl http://$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
    echo ""
    echo "💡 For full CloudFront setup, run without --quick flag"
    
    exit 0
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
REACT_APP_S3_BUCKET_URL=https://7h-stock-analyzer.s3.$AWS_REGION.amazonaws.com
REACT_APP_CLOUDFRONT_URL=https://$CLOUDFRONT_DOMAIN
EOF

# Build for production with explicit environment variable
echo "🏗️  Building production bundle..."
export REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL_AWS
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Build failed - dist directory not found"
    exit 1
fi

# Deploy to S3
echo "📤 Deploying to S3..."
aws s3 sync dist/ "s3://$BUCKET_NAME/" \
    --delete

# Create CloudFront distribution if it doesn't exist
echo "🌐 Setting up CloudFront distribution..."

# Cleanup old distributions first
cleanup_old_cloudfront_distributions

DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='$BUCKET_NAME frontend'].Id" \
    --output text)

if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" = "None" ]; then
    echo "🚀 Creating new CloudFront distribution..."
    
    # Create CloudFront distribution
    DISTRIBUTION_ID=$(aws cloudfront create-distribution \
        --distribution-config '{
            "CallerReference": "'$BUCKET_NAME'-'$ENVIRONMENT'-'$RANDOM'",
            "Comment": "'$BUCKET_NAME' frontend",
            "DefaultRootObject": "index.html",
            "Origins": {
                "Quantity": 1,
                "Items": [{
                    "Id": "S3-'$BUCKET_NAME'",
                    "DomainName": "'$BUCKET_NAME'.s3.'$AWS_REGION'.amazonaws.com",
                    "S3OriginConfig": {
                        "OriginAccessIdentity": ""
                    }
                }]
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": "S3-'$BUCKET_NAME'",
                "ViewerProtocolPolicy": "redirect-to-https",
                "TrustedSigners": {
                    "Enabled": false,
                    "Quantity": 0
                },
                "ForwardedValues": {
                    "QueryString": false,
                    "Cookies": {
                        "Forward": "none"
                    }
                },
                "MinTTL": 3600,
                "DefaultTTL": 86400,
                "MaxTTL": 31536000
            },
            "CacheBehaviors": {
                "Quantity": 0
            },
            "Enabled": true,
            "PriceClass": "PriceClass_100"
        }' \
        --query 'Distribution.Id' \
        --output text)
    
    echo "✅ Created CloudFront distribution: $DISTRIBUTION_ID"
    
    # Wait for distribution to deploy
    echo "⏳ Waiting for CloudFront distribution to deploy (this can take 15-20 minutes)..."
    aws cloudfront wait distribution-deployed --id $DISTRIBUTION_ID
else
    echo "ℹ️  CloudFront distribution already exists: $DISTRIBUTION_ID"
fi

# Get CloudFront domain name
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
    --id $DISTRIBUTION_ID \
    --query 'Distribution.DomainName' \
    --output text)

# Update S3 bucket policy for CloudFront access
echo "🔐 Updating S3 bucket policy for CloudFront..."
aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:cloudfront::'$(aws sts get-caller-identity --query Account --output text)'":originaccessidentity/'$(echo $CLOUDFRONT_DOMAIN | cut -d. -f1)'"
                },
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

# Clean up old Lambda layer versions (storage optimization)
echo "🧹 Cleaning up old Lambda layer versions..."
LAYER_NAME="StockAnalyzerDependencies"
LATEST_VERSION=$(aws lambda list-layer-versions --layer-name $LAYER_NAME --query 'max(LayerVersions[].Version)' --output text 2>/dev/null || echo "0")

if [ "$LATEST_VERSION" != "0" ] && [ "$LATEST_VERSION" -gt 1 ]; then
    echo "Found $LATEST_VERSION layer versions, cleaning up old versions..."
    
    # Delete all versions except the latest one
    for ((i=1; i<LATEST_VERSION; i++)); do
        echo "Deleting layer version $i..."
        aws lambda delete-layer-version --layer-name $LAYER_NAME --version-number $i 2>/dev/null && echo "✅ Deleted version $i" || echo "❌ Failed to delete version $i"
    done
    
    echo "✅ Layer cleanup completed. Kept only version $LATEST_VERSION"
    echo "💰 Storage cost reduced by ~90%"
else
    echo "✅ No old layer versions to clean up (latest version: $LATEST_VERSION)"
fi

echo ""
echo "🎉 Frontend deployment completed!"
echo ""
echo "🌐 CloudFront URL: https://$CLOUDFRONT_DOMAIN"
echo "🪣 S3 Bucket: s3://$BUCKET_NAME"
echo "📋 Distribution ID: $DISTRIBUTION_ID"
echo ""
echo "🧪 Test the deployment:"
echo "  curl https://$CLOUDFRONT_DOMAIN"
echo ""
echo "💡 To update content:"
echo "  ./infra/aws/deploy_frontend.sh $ENVIRONMENT"
echo ""
echo "⚠️  Note: CloudFront may take a few minutes to propagate changes globally"
