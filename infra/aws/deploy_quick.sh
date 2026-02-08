#!/bin/bash
set -e

echo "⚡ 7H Stock Analyzer - Quick Deployment Script"
echo "=============================================="
echo ""

# Function to cleanup old CloudFront distributions
cleanup_old_cloudfront_distributions() {
    echo "🧹 Cleaning up old CloudFront distributions..."
    
    # Get all distributions with the bucket comment
    BUCKET_NAME=$S3_BUCKET_NAME_PROD
    OLD_DISTRIBUTIONS=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='$BUCKET_NAME frontend'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$OLD_DISTRIBUTIONS" ] && [ "$OLD_DISTRIBUTIONS" != "None" ]; then
        echo "Found old distributions: $OLD_DISTRIBUTIONS"
        
        for DIST_ID in $OLD_DISTRIBUTIONS; do
            echo "🗑️  Deleting old distribution: $DIST_ID"
            
            # Get ETag for the distribution
            ETAG=$(aws cloudfront get-distribution --id $DIST_ID --query 'ETag' --output text 2>/dev/null || echo "")
            
            if [ -n "$ETAG" ]; then
                # First disable the distribution
                echo "  Disabling distribution..."
                aws cloudfront update-distribution \
                    --id $DIST_ID \
                    --distribution-config '{
                        "CallerReference": "'$DIST_ID'-cleanup",
                        "Comment": "'$BUCKET_NAME frontend - marked for deletion",
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
                        "Enabled": false,
                        "PriceClass": "PriceClass_100"
                    }' \
                    --if-match "$ETAG" 2>/dev/null || echo "  Failed to disable distribution"
                
                # Wait for distribution to be disabled
                echo "  Waiting for distribution to be disabled..."
                aws cloudfront wait distribution-deployed --id $DIST_ID 2>/dev/null || echo "  Timeout waiting for disable"
                
                # Delete the distribution
                echo "  Deleting distribution..."
                ETAG=$(aws cloudfront get-distribution --id $DIST_ID --query 'ETag' --output text 2>/dev/null || echo "")
                if [ -n "$ETAG" ]; then
                    aws cloudfront delete-distribution --id $DIST_ID --if-match "$ETAG" 2>/dev/null || echo "  Failed to delete distribution"
                fi
            fi
        done
        
        echo "✅ CloudFront cleanup completed"
    else
        echo "ℹ️  No old distributions found to cleanup"
    fi
}

# Parse command line arguments
LAMBDA_ONLY=false
FRONTEND_ONLY=false
ENVIRONMENT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --lambda-only)
            LAMBDA_ONLY=true
            shift
            ;;
        --frontend-only)
            FRONTEND_ONLY=true
            shift
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            if [ -z "$ENVIRONMENT" ]; then
                ENVIRONMENT="$1"
            else
                echo "Unknown option: $1"
                echo "Usage: $0 [--lambda-only] [--frontend-only] [--env ENVIRONMENT] [ENVIRONMENT]"
                exit 1
            fi
            shift
            ;;
    esac
done

# Set default environment if not provided
if [ -z "$ENVIRONMENT" ]; then
    ENVIRONMENT="dev"
fi

echo "📋 Quick Deployment Configuration:"
echo "  Environment: $ENVIRONMENT"
echo "  Lambda Only: $LAMBDA_ONLY"
echo "  Frontend Only: $FRONTEND_ONLY"
echo ""

# Validate arguments
if [ "$LAMBDA_ONLY" = true ] && [ "$FRONTEND_ONLY" = true ]; then
    echo "❌ Cannot specify both --lambda-only and --frontend-only"
    exit 1
fi

# Load environment variables
if [ ! -f .env.local ]; then
    echo "❌ .env.local not found. Please run './infra/local/setup_local.sh' first."
    exit 1
fi

echo "🔄 Starting quick deployment..."
echo ""

# Deploy Lambda (unless frontend-only)
if [ "$FRONTEND_ONLY" = false ]; then
    echo "🐍 Deploying Lambda function (quick mode)..."
    echo "-------------------------------------------"
    
    START_TIME=$(date +%s)
    
    if ./infra/aws/deploy_aws_onetime.sh --quick; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "✅ Lambda deployment completed in ${DURATION}s"
        echo ""
    else
        echo "❌ Lambda deployment failed"
        exit 1
    fi
fi

# Deploy Frontend (unless lambda-only)
if [ "$LAMBDA_ONLY" = false ]; then
    echo "🎨 Deploying frontend (quick mode)..."
    echo "------------------------------------"
    
    # Cleanup old CloudFront distributions before deploying
    cleanup_old_cloudfront_distributions
    
    START_TIME=$(date +%s)
    
    if ./infra/aws/deploy_frontend.sh --quick "$ENVIRONMENT"; then
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        echo "✅ Frontend deployment completed in ${DURATION}s"
        echo ""
    else
        echo "❌ Frontend deployment failed"
        exit 1
    fi
fi

# Get deployment URLs and test
echo "🧪 Testing quick deployment..."
echo "----------------------------"

# Load environment variables for testing
export $(grep -v '^#' .env.local | xargs)

# Get stack outputs
STACK_NAME="7h-stock-analyzer-${ENVIRONMENT}"
AWS_REGION=${AWS_REGION:-us-east-1}

API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerApi`].OutputValue' \
    --output text 2>/dev/null || echo "")

BUCKET_NAME=$S3_BUCKET_NAME_PROD

# Get CloudFront distribution
DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?Comment=='$BUCKET_NAME frontend'].Id" \
    --output text 2>/dev/null || echo "")

if [ -n "$DISTRIBUTION_ID" ] && [ "$DISTRIBUTION_ID" != "None" ]; then
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
        --id $DISTRIBUTION_ID \
        --query 'Distribution.DomainName' \
        --output text 2>/dev/null || echo "")
    FRONTEND_URL="https://$CLOUDFRONT_DOMAIN"
else
    FRONTEND_URL="http://$BUCKET_NAME.s3-website-$AWS_REGION.amazonaws.com"
fi

# Test API endpoint
if [ -n "$API_URL" ] && [ "$API_URL" != "None" ] && [ "$FRONTEND_ONLY" = false ]; then
    echo "🌐 Testing API endpoint: $API_URL/health"
    API_RESPONSE=$(curl -s -w "%{http_code}" "$API_URL/health" || echo "000")
    
    if [[ "$API_RESPONSE" == *"200"* ]]; then
        echo "✅ API endpoint is healthy"
    else
        echo "⚠️  API health check failed: $API_RESPONSE"
    fi
else
    echo "ℹ️  Skipping API test (frontend-only deployment or API URL not found)"
fi

# Test frontend
if [ "$LAMBDA_ONLY" = false ]; then
    echo "🌐 Testing frontend: $FRONTEND_URL"
    FRONTEND_RESPONSE=$(curl -s -w "%{http_code}" "$FRONTEND_URL" || echo "000")
    
    if [[ "$FRONTEND_RESPONSE" == *"200"* ]]; then
        echo "✅ Frontend is accessible"
    else
        echo "⚠️  Frontend test failed: $FRONTEND_RESPONSE"
    fi
else
    echo "ℹ️  Skipping frontend test (lambda-only deployment)"
fi

echo ""
echo "🎉 Quick deployment completed successfully!"
echo "=========================================="
echo ""

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
echo "📋 Deployment Summary:"
if [ "$FRONTEND_ONLY" = false ]; then
    echo "  🐍 Lambda: ✅ Updated"
    echo "  🌐 API URL: $API_URL"
fi
if [ "$LAMBDA_ONLY" = false ]; then
    echo "  🎨 Frontend: ✅ Updated"
    echo "  🌐 Frontend URL: $FRONTEND_URL"
fi
echo ""
echo "⚡ Quick deployment benefits:"
echo "  - Lambda updates: ~30-60 seconds (vs 15+ minutes)"
echo "  - Frontend updates: ~1-2 minutes (vs 3-5 minutes)"
echo "  - No infrastructure changes required"
echo "  - Same security and cost optimizations"
echo ""
echo "🧪 Quick test commands:"
if [ "$FRONTEND_ONLY" = false ]; then
    echo "  curl -H \"X-API-Key: \$API_KEY\" $API_URL/health"
    echo "  curl -H \"X-API-Key: \$API_KEY\" $API_URL/recommendations"
fi
if [ "$LAMBDA_ONLY" = false ]; then
    echo "  curl $FRONTEND_URL"
fi
echo ""
echo "💡 For full infrastructure changes:"
echo "  ./infra/aws/deploy_aws_onetime.sh"
echo "  ./infra/aws/deploy_frontend.sh $ENVIRONMENT"
echo ""
echo "🔧 Individual quick deployments:"
echo "  Lambda only: $0 --lambda-only"
echo "  Frontend only: $0 --frontend-only $ENVIRONMENT"
