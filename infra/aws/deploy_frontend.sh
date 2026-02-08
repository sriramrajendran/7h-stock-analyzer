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

# =============================================================================
# FRONTEND INFRASTRUCTURE AS CODE - CONSOLIDATED FUNCTIONS
# =============================================================================

# Function to cleanup old CloudFront distributions (from cleanup_cloudfront.sh)
cleanup_old_cloudfront_distributions() {
    echo "🧹 Cleaning up old CloudFront distributions..."
    
    # Get all distributions with the bucket comment
    local bucket_name="$BUCKET_NAME"
    local old_distributions=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='$bucket_name frontend'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$old_distributions" ] && [ "$old_distributions" != "None" ]; then
        echo "Found old distributions: $old_distributions"
        
        for dist_id in $old_distributions; do
            echo "🗑️  Deleting old distribution: $dist_id"
            
            # Get ETag for the distribution
            local etag=$(aws cloudfront get-distribution --id $dist_id --query 'ETag' --output text 2>/dev/null || echo "")
            
            if [ -n "$etag" ]; then
                # First disable the distribution
                echo "  Disabling distribution..."
                aws cloudfront update-distribution \
                    --id $dist_id \
                    --distribution-config '{
                        "CallerReference": "'$dist_id'-cleanup",
                        "Comment": "'$bucket_name frontend - marked for deletion",
                        "DefaultRootObject": "index.html",
                        "Origins": {
                            "Quantity": 1,
                            "Items": [{
                                "Id": "S3-'$bucket_name'",
                                "DomainName": "'$bucket_name'.s3.'$AWS_REGION'.amazonaws.com",
                                "S3OriginConfig": {
                                    "OriginAccessIdentity": ""
                                }
                            }]
                        },
                        "DefaultCacheBehavior": {
                            "TargetOriginId": "S3-'$bucket_name'",
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
                    --if-match "$etag" 2>/dev/null || echo "  Failed to disable distribution"
                
                # Wait for distribution to be disabled
                echo "  Waiting for distribution to be disabled..."
                aws cloudfront wait distribution-deployed --id $dist_id 2>/dev/null || echo "  Timeout waiting for disable"
                
                # Delete the distribution
                echo "  Deleting distribution..."
                etag=$(aws cloudfront get-distribution --id $dist_id --query 'ETag' --output text 2>/dev/null || echo "")
                if [ -n "$etag" ]; then
                    aws cloudfront delete-distribution --id $dist_id --if-match "$etag" 2>/dev/null || echo "  Failed to delete distribution"
                fi
            fi
        done
        
        echo "✅ CloudFront cleanup completed"
    else
        echo "ℹ️  No old distributions found to cleanup"
    fi
}

# Function to monitor frontend costs
monitor_frontend_costs() {
    echo "💰 Frontend Cost Monitoring for 7H Stock Analyzer..."
    
    # Get CloudFront costs
    local cloudfront_cost=$(aws ce get-cost-and-usage \
        --time-period Start=$(date -d "30 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
        --filter Dimensions={Key=SERVICE,Values=["Amazon CloudFront"]} \
        --metrics BlendedCost \
        --granularity MONTHLY \
        --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
        --output text 2>/dev/null || echo "0")
    
    # Get S3 costs
    local s3_cost=$(aws ce get-cost-and-usage \
        --time-period Start=$(date -d "30 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
        --filter Dimensions={Key=SERVICE,Values=["Amazon S3"]} \
        --metrics BlendedCost \
        --granularity MONTHLY \
        --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
        --output text 2>/dev/null || echo "0")
    
    echo "📈 Frontend Cost Analysis (Last 30 Days)"
    echo "======================================"
    echo "🌐 CloudFront: $${cloudfront_cost}"
    echo "🪣 S3 Storage: $${s3_cost}"
    
    local total_frontend_cost=$(echo "$cloudfront_cost + $s3_cost" | bc -l 2>/dev/null || echo "0")
    echo "💸 Frontend Total: $${total_frontend_cost}"
    
    # Get CloudFront usage metrics
    local distribution_id=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='$BUCKET_NAME frontend'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$distribution_id" ] && [ "$distribution_id" != "None" ]; then
        echo ""
        echo "📊 CloudFront Usage Metrics:"
        aws cloudwatch get-metric-statistics \
            --namespace "AWS/CloudFront" \
            --metric-name "Requests" \
            --dimensions Name=DistributionId,Value=$distribution_id \
            --statistics Sum \
            --period 86400 \
            --start-time $(date -d "30 days ago" -u +%Y-%m-%dT%H:%M:%SZ) \
            --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
            --query 'Datapoints[*].{Date:Timestamp,Requests:Sum}' \
            --output table 2>/dev/null || echo "  ℹ️  Usage metrics not available"
    fi
}

# Function to sync frontend infrastructure
sync_frontend_infra() {
    echo "🔄 Frontend Infrastructure Sync Check"
    echo "==================================="
    
    local sync_issues=0
    local bucket_name="$S3_BUCKET_NAME_PROD"
    
    echo "📋 Checking S3 bucket sync..."
    
    # Check S3 bucket
    if aws s3 ls "s3://$bucket_name" &>/dev/null; then
        echo "✅ Bucket '$bucket_name' exists"
        
        # Check bucket website configuration
        local website_config=$(aws s3api get-bucket-website \
            --bucket "$bucket_name" \
            --query 'IndexDocument' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$website_config" ]; then
            echo "✅ Website hosting configured"
        else
            echo "❌ Website hosting not configured"
            sync_issues=$((sync_issues + 1))
        fi
        
        # Check bucket policy
        local bucket_policy=$(aws s3api get-bucket-policy \
            --bucket "$bucket_name" \
            --query 'Policy' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$bucket_policy" ] && [ "$bucket_policy" != "None" ]; then
            echo "✅ Bucket policy configured"
        else
            echo "⚠️  No bucket policy (may be intentional)"
        fi
        
        # Check CORS configuration
        local cors_config=$(aws s3api get-bucket-cors \
            --bucket "$bucket_name" \
            --query 'CORSRules' \
            --output text 2>/dev/null || echo "")
        
        if [ -n "$cors_config" ] && [ "$cors_config" != "None" ]; then
            echo "✅ CORS configured"
        else
            echo "⚠️  No CORS configuration"
        fi
        
        # Check for frontend files
        echo ""
        echo "📁 Frontend Files Check:"
        
        local has_index=false
        local has_js=false
        local has_css=false
        
        # Check for key files
        if aws s3 ls "s3://$bucket_name/index.html" &>/dev/null; then
            echo "  ✅ index.html found"
            has_index=true
        else
            echo "  ❌ index.html missing"
            sync_issues=$((sync_issues + 1))
        fi
        
        local js_count=$(aws s3 ls "s3://$bucket_name/" | grep -c "\.js$" || echo "0")
        if [ "$js_count" -gt 0 ]; then
            echo "  ✅ JavaScript files found ($js_count)"
            has_js=true
        else
            echo "  ❌ No JavaScript files found"
            sync_issues=$((sync_issues + 1))
        fi
        
        local css_count=$(aws s3 ls "s3://$bucket_name/" | grep -c "\.css$" || echo "0")
        if [ "$css_count" -gt 0 ]; then
            echo "  ✅ CSS files found ($css_count)"
            has_css=true
        else
            echo "  ⚠️  No CSS files found (may be inline)"
        fi
        
        # Check file sizes
        echo ""
        echo "📊 File Size Analysis:"
        
        local total_size=$(aws s3 ls "s3://$bucket_name" --recursive --summarize | grep "Total Size" | awk '{print $3}' || echo "0")
        local total_mb=$(echo "scale=2; $total_size / (1024^2)" | bc -l)
        
        echo "  Total size: ${total_mb}MB"
        
        if (( $(echo "$total_mb > 50" | bc -l) )); then
            echo "  ⚠️  Large frontend - consider optimization"
        elif (( $(echo "$total_mb > 10" | bc -l) )); then
            echo "  ✅ Moderate size"
        else
            echo "  ✅ Well optimized"
        fi
        
        # Check for large files
        echo "  Large files (>1MB):"
        aws s3 ls "s3://$bucket_name" --recursive --human-readable | awk '$5 > "1MB" {print "    " $4 " - " $5}' || echo "    No large files found"
        
    else
        echo "❌ Bucket '$bucket_name' not found"
        sync_issues=$((sync_issues + 1))
    fi
    
    echo ""
    echo "🌐 CloudFront Distribution Sync:"
    
    # Check CloudFront distribution
    local distribution_id=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='$bucket_name frontend'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$distribution_id" ] && [ "$distribution_id" != "None" ]; then
        echo "✅ CloudFront distribution found: $distribution_id"
        
        local distribution_status=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.Status' \
            --output text 2>/dev/null || echo "")
        
        local distribution_domain=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.DomainName' \
            --output text 2>/dev/null || echo "")
        
        echo "  Status: $distribution_status"
        echo "  Domain: $distribution_domain"
        
        # Check distribution configuration
        local origin_config=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.DistributionConfig.Origins.Items[0].DomainName' \
            --output text 2>/dev/null || echo "")
        
        local expected_origin="$bucket_name.s3.$AWS_REGION.amazonaws.com"
        
        if [ "$origin_config" = "$expected_origin" ]; then
            echo "  ✅ Origin configured correctly"
        else
            echo "  ❌ Origin mismatch - Expected: $expected_origin, Found: $origin_config"
            sync_issues=$((sync_issues + 1))
        fi
        
        # Check cache behavior
        local default_ttl=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.DistributionConfig.DefaultCacheBehavior.DefaultTTL' \
            --output text 2>/dev/null || echo "")
        
        echo "  Default TTL: ${default_ttl}s"
        
        if [ "$default_ttl" -ge 3600 ]; then
            echo "  ✅ Cache TTL optimized"
        else
            echo "  ⚠️  Short cache TTL - consider increasing"
        fi
        
        # Check price class
        local price_class=$(aws cloudfront get-distribution \
            --id "$distribution_id" \
            --query 'Distribution.DistributionConfig.PriceClass' \
            --output text 2>/dev/null || echo "")
        
        echo "  Price Class: $price_class"
        
        if [ "$price_class" = "PriceClass_100" ]; then
            echo "  ✅ Cost-optimized price class"
        else
            echo "  ⚠️  Consider using PriceClass_100 for cost savings"
        fi
        
        # Test distribution accessibility
        echo ""
        echo "🧪 Distribution Accessibility Test:"
        
        if [ "$distribution_status" = "Deployed" ]; then
            local test_response=$(curl -s -w "%{http_code}" "https://$distribution_domain" -o /dev/null 2>/dev/null || echo "000")
            
            if [ "$test_response" = "200" ]; then
                echo "  ✅ Distribution accessible (HTTP 200)"
            elif [ "$test_response" = "403" ]; then
                echo "  ⚠️  Distribution returns 403 (may be policy issue)"
            elif [ "$test_response" = "404" ]; then
                echo "  ❌ Distribution returns 404 (missing files)"
                sync_issues=$((sync_issues + 1))
            else
                echo "  ❌ Distribution inaccessible (HTTP $test_response)"
                sync_issues=$((sync_issues + 1))
            fi
        else
            echo "  ⚠️  Distribution not deployed - skipping test"
        fi
        
    else
        echo "❌ CloudFront distribution not found"
        sync_issues=$((sync_issues + 1))
    fi
    
    echo ""
    echo "📊 Frontend Sync Summary:"
    echo "========================="
    
    if [ $sync_issues -eq 0 ]; then
        echo "✅ All frontend infrastructure is synced with production"
        echo "   Your frontend deployment matches the deployed infrastructure"
    else
        echo "❌ Found $sync_issues frontend sync issues that need attention"
        echo ""
        echo "🔧 To fix frontend sync issues:"
        echo "  1. Review the mismatches above"
        echo "  2. Run frontend deployment: $0 prod"
        echo "  3. Check S3 bucket permissions and policies"
        echo "  4. Verify CloudFront distribution configuration"
    fi
    
    echo ""
    echo "💡 Frontend Sync Recommendations:"
    echo "  - Run this check after any manual S3/CloudFront changes"
    echo "  - Verify before frontend deployments"
    echo "  - Use to troubleshoot frontend accessibility issues"
    echo "  - Check after CDN cache invalidations"
    
    return $sync_issues
}

# Function to optimize frontend costs
optimize_frontend_costs() {
    echo "💰 Optimizing Frontend Costs for 7H Stock Analyzer..."
    
    # Check CloudFront distribution settings
    local distribution_id=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Comment=='$BUCKET_NAME frontend'].Id" \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$distribution_id" ] && [ "$distribution_id" != "None" ]; then
        echo "🌐 Analyzing CloudFront distribution..."
        
        local price_class=$(aws cloudfront get-distribution \
            --id $distribution_id \
            --query 'Distribution.DistributionConfig.PriceClass' \
            --output text 2>/dev/null || echo "PriceClass_100")
        
        echo "    Current Price Class: $price_class"
        
        if [ "$price_class" != "PriceClass_100" ]; then
            echo "    💡 Recommendation: Use PriceClass_100 (North America & Europe only)"
            echo "      - Reduces cost by ~30%"
            echo "      - Sufficient for most use cases"
        fi
        
        # Check cache settings
        local default_ttl=$(aws cloudfront get-distribution \
            --id $distribution_id \
            --query 'Distribution.DistributionConfig.DefaultCacheBehavior.DefaultTTL' \
            --output text 2>/dev/null || echo "86400")
        
        echo "    Default TTL: ${default_ttl}s"
        
        if [ "$default_ttl" -lt 86400 ]; then
            echo "    💡 Recommendation: Increase TTL to 86400s (24 hours)"
            echo "      - Reduces origin requests"
            echo "      - Improves performance"
        fi
    fi
    
    # Check S3 storage optimization
    echo "🪣 Analyzing S3 storage..."
    if aws s3 ls "s3://$BUCKET_NAME" &>/dev/null; then
        local size_bytes=$(aws s3 ls "s3://$BUCKET_NAME" --recursive --summarize | grep "Total Size" | awk '{print $3}' || echo "0")
        local size_gb=$(echo "scale=2; $size_bytes / (1024^3)" | bc -l)
        
        echo "    Frontend size: ${size_gb}GB"
        
        if (( $(echo "$size_gb > 0.5" | bc -l) )); then
            echo "    💡 Recommendation: Optimize frontend assets"
            echo "      - Compress images and fonts"
            echo "      - Enable gzip/brotli compression"
            echo "      - Remove unused assets"
        fi
        
        # Check for large files
        echo "    Large files (>1MB):"
        aws s3 ls "s3://$BUCKET_NAME" --recursive --human-readable | awk '$5 > "1MB" {print "      " $4 " - " $5}' || echo "      No large files found"
    fi
    
    echo ""
    echo "💡 Frontend Cost Optimization Tips:"
    echo "  1. Use CloudFront PriceClass_100 for cost savings"
    echo "  2. Increase cache TTLs to reduce origin requests"
    echo "  3. Compress and optimize frontend assets"
    echo "  4. Remove unused JavaScript and CSS"
    echo "  5. Enable HTTP/2 and compression"
}

# =============================================================================
# FRONTEND INFRASTRUCTURE MANAGEMENT COMMANDS
# =============================================================================

# Add frontend infrastructure management commands
case "${1:-}" in
    "cleanup-cloudfront")
        echo "🧹 Running CloudFront cleanup..."
        cleanup_old_cloudfront_distributions
        echo ""
        echo "📋 Current distributions:"
        aws cloudfront list-distributions --query 'DistributionList.Items[*].{Id:Id,DomainName:DomainName,Comment:Comment,Status:Status}' --output table
        ;;
    "monitor-costs")
        monitor_frontend_costs
        ;;
    "optimize-costs")
        optimize_frontend_costs
        ;;
    "sync-check")
        sync_frontend_infra
        ;;
    "help")
        echo "🎨 7H Stock Analyzer - Frontend Infrastructure Management"
        echo "======================================================"
        echo ""
        echo "Usage: $0 [COMMAND] [ENVIRONMENT]"
        echo ""
        echo "Commands:"
        echo "  (no args)           Full frontend deployment"
        echo "  --quick             Quick frontend update"
        echo "  cleanup-cloudfront  Clean up old CloudFront distributions"
        echo "  monitor-costs      Monitor frontend costs"
        echo "  optimize-costs     Optimize frontend costs"
        echo "  sync-check         Verify frontend sync"
        echo "  help               Show this help"
        echo ""
        echo "Environments:"
        echo "  dev, staging, prod  Target environment"
        echo ""
        echo "Examples:"
        echo "  $0 prod                    # Full deployment to production"
        echo "  $0 --quick prod            # Quick update to production"
        echo "  $0 cleanup-cloudfront     # Cleanup CloudFront"
        echo "  $0 monitor-costs           # Check frontend costs"
        echo "  $0 optimize-costs prod     # Optimize production costs"
        echo "  $0 sync-check              # Verify frontend sync"
        ;;
esac

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
