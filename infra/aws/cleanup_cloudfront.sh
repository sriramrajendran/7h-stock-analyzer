#!/bin/bash
set -e

echo "🧹 CloudFront Cleanup Script"
echo "=========================="

# Load environment variables
if [ ! -f .env.local ]; then
    echo "❌ .env.local not found. Please run './infra/local/setup_local.sh' first."
    exit 1
fi

export $(grep -v '^#' .env.local | xargs)

# Get bucket name
BUCKET_NAME=$S3_BUCKET_NAME_PROD
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📋 Cleanup Configuration:"
echo "  Bucket: $BUCKET_NAME"
echo "  Region: $AWS_REGION"
echo ""

# Function to cleanup old CloudFront distributions
cleanup_old_cloudfront_distributions() {
    echo "🧹 Cleaning up old CloudFront distributions..."
    
    # Get all distributions with the bucket comment
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

# Run cleanup
cleanup_old_cloudfront_distributions

echo ""
echo "🎉 Cleanup completed!"
echo ""
echo "📋 Current distributions:"
aws cloudfront list-distributions --query 'DistributionList.Items[*].{Id:Id,DomainName:DomainName,Comment:Comment,Status:Status}' --output table
