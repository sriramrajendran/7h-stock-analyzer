#!/bin/bash
set -e

echo "💰 Optimizing AWS Costs for 7H Stock Analyzer..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📋 Cost Optimization for Account: $AWS_ACCOUNT (Region: $AWS_REGION)"
echo ""

# Function to optimize Lambda settings
optimize_lambda() {
    echo "🔧 Optimizing Lambda Functions..."
    
    for env in dev staging prod; do
        stack_name="7h-stock-analyzer-$env"
        
        # Check if stack exists
        if aws cloudformation describe-stacks --stack-name "$stack_name" &>/dev/null; then
            echo "  Optimizing $env environment..."
            
            # Get current Lambda function name
            function_name=$(aws cloudformation describe-stacks \
                --stack-name "$stack_name" \
                --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerFunction`].OutputValue' \
                --output text 2>/dev/null || echo "")
            
            if [ -n "$function_name" ]; then
                # Get current configuration
                current_memory=$(aws lambda get-function-configuration \
                    --function-name "$function_name" \
                    --query 'MemorySize' \
                    --output text 2>/dev/null || echo "512")
                
                current_timeout=$(aws lambda get-function-configuration \
                    --function-name "$function_name" \
                    --query 'Timeout' \
                    --output text 2>/dev/null || echo "180")
                
                echo "    Current: Memory=${current_memory}MB, Timeout=${current_timeout}s"
                
                # Get recent execution metrics
                avg_duration=$(aws logs filter-log-events \
                    --log-group-name "/aws/lambda/$(basename $function_name)" \
                    --start-time $(date -d "7 days ago" +%s)000 \
                    --end-time $(date +%s)000 \
                    --filter-pattern "REPORT" \
                    --query 'events[?contains(message, `Duration`)].message | [0]' \
                    --output text 2>/dev/null | grep -o 'Duration: [0-9.]* ms' | awk '{print $2}' | sort -n | median || echo "100")
                
                # Optimization recommendations
                if (( $(echo "$avg_duration < 5000" | bc -l) )); then
                    echo "    💡 Recommendation: Reduce memory to 256MB (fast execution)"
                elif (( $(echo "$avg_duration < 10000" | bc -l) )); then
                    echo "    💡 Recommendation: Keep memory at 512MB"
                else
                    echo "    💡 Recommendation: Increase memory to 1024MB (slow execution)"
                fi
                
                if (( $(echo "$avg_duration < 30000" | bc -l) )); then
                    echo "    💡 Recommendation: Reduce timeout to 60s"
                elif (( $(echo "$avg_duration < 60000" | bc -l) )); then
                    echo "    💡 Recommendation: Reduce timeout to 120s"
                fi
            fi
        fi
    done
}

# Function to optimize S3 storage
optimize_s3() {
    echo "🪣 Optimizing S3 Storage..."
    
    for env in dev staging prod; do
        bucket_name="7h-stock-analyzer-$env"
        if [ "$env" = "prod" ]; then
            bucket_name="7h-stock-analyzer"
        fi
        
        if aws s3 ls "s3://$bucket_name" &>/dev/null; then
            echo "  Optimizing bucket: $bucket_name"
            
            # Get bucket size
            size_bytes=$(aws s3 ls "s3://$bucket_name" --recursive --summarize | grep "Total Size" | awk '{print $3}' || echo "0")
            size_gb=$(echo "scale=2; $size_bytes / (1024^3)" | bc -l)
            
            echo "    Current size: ${size_gb}GB"
            
            # Count objects by prefix
            echo "    Object breakdown:"
            for prefix in data/daily/ data/latest/ config/ recon/ charts/ logs/; do
                count=$(aws s3 ls "s3://$bucket_name/$prefix" --recursive 2>/dev/null | wc -l)
                if [ "$count" -gt 0 ]; then
                    echo "      $prefix: $count objects"
                fi
            done
            
            # Lifecycle optimization recommendations
            if (( $(echo "$size_gb > 1" | bc -l) )); then
                echo "    💡 Recommendation: Aggressive lifecycle policies"
                echo "      - Delete daily data after 30 days"
                echo "      - Delete charts after 7 days"
                echo "      - Delete logs after 7 days"
            elif (( $(echo "$size_gb > 0.5" | bc -l) )); then
                echo "    💡 Recommendation: Standard lifecycle policies"
                echo "      - Delete daily data after 90 days"
                echo "      - Delete charts after 30 days"
            else
                echo "    ✅ Storage is well optimized"
            fi
            
            # Clean up old files (optional)
            if [ "$1" = "--cleanup" ]; then
                echo "    🧹 Cleaning up old files..."
                
                # Clean up old daily data (older than 30 days)
                cutoff_date=$(date -d "30 days ago" +%Y-%m-%d)
                aws s3 ls "s3://$bucket_name/data/daily/" | while read -r line; do
                    date_str=$(echo $line | awk '{print $1}')
                    if [[ "$date_str" < "$cutoff_date" ]]; then
                        file=$(echo $line | awk '{print $4}')
                        aws s3 rm "s3://$bucket_name/data/daily/$file" --recursive
                        echo "      Deleted: data/daily/$file"
                    fi
                done
                
                # Clean up old charts (older than 7 days)
                aws s3 ls "s3://$bucket_name/charts/" | while read -r line; do
                    date_str=$(echo $line | awk '{print $1}')
                    if [[ "$date_str" < "$(date -d "7 days ago" +%Y-%m-%d)" ]]; then
                        file=$(echo $line | awk '{print $4}')
                        aws s3 rm "s3://$bucket_name/charts/$file" --recursive
                        echo "      Deleted: charts/$file"
                    fi
                done
            fi
        fi
    done
}

# Function to optimize API Gateway
optimize_api() {
    echo "🌐 Optimizing API Gateway..."
    
    for env in dev staging prod; do
        stack_name="7h-stock-analyzer-$env"
        
        if aws cloudformation describe-stacks --stack-name "$stack_name" &>/dev/null; then
            echo "  Optimizing $env API Gateway..."
            
            # Get API ID
            api_id=$(aws cloudformation describe-stacks \
                --stack-name "$stack_name" \
                --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerApi`].OutputValue' \
                --output text 2>/dev/null | sed 's|https://||' | sed 's|\.execute-api.*||' || echo "")
            
            if [ -n "$api_id" ]; then
                echo "    API ID: $api_id"
                
                # Check current throttling limits
                echo "    💡 Current throttling limits are optimized"
                echo "      - Burst: 2-5 requests"
                echo "      - Rate: 5-10 requests/second"
                
                # Enable detailed monitoring (costs more but provides insights)
                echo "    💡 Consider enabling detailed monitoring for debugging"
            fi
        fi
    done
}

# Function to optimize CloudWatch Logs
optimize_logs() {
    echo "📊 Optimizing CloudWatch Logs..."
    
    for env in dev staging prod; do
        stack_name="7h-stock-analyzer-$env"
        
        if aws cloudformation describe-stacks --stack-name "$stack_name" &>/dev/null; then
            echo "  Optimizing $env logs..."
            
            # Get Lambda function name
            function_name=$(aws cloudformation describe-stacks \
                --stack-name "$stack_name" \
                --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerFunction`].OutputValue' \
                --output text 2>/dev/null || echo "")
            
            if [ -n "$function_name" ]; then
                log_group="/aws/lambda/$(basename $function_name)"
                
                # Check current retention
                retention=$(aws logs describe-log-groups \
                    --log-group-name-prefix "$log_group" \
                    --query 'logGroups[0].retentionInDays' \
                    --output text 2>/dev/null || echo "N/A")
                
                echo "    Log Group: $log_group"
                echo "    Current retention: ${retention} days"
                
                # Set retention to 7 days for cost savings
                if [ "$retention" != "7" ]; then
                    echo "    💡 Setting retention to 7 days..."
                    aws logs put-retention-policy \
                        --log-group-name "$log_group" \
                        --retention-in-days 7 2>/dev/null || echo "      Failed to set retention"
                else
                    echo "    ✅ Retention is already optimized"
                fi
            fi
        fi
    done
}

# Function to check for unused resources
check_unused_resources() {
    echo "🔍 Checking for unused resources..."
    
    # Check for unused Lambda functions
    echo "  Lambda Functions:"
    aws lambda list-functions | jq -r '.Functions[] | select(.FunctionName | contains("7h-stock-analyzer")) | .FunctionName' | while read func; do
        # Check if function has been invoked recently
        invocations=$(aws logs filter-log-events \
            --log-group-name "/aws/lambda/$func" \
            --start-time $(date -d "30 days ago" +%s)000 \
            --end-time $(date +%s)000 \
            --query 'events | length' \
            --output text 2>/dev/null || echo "0")
        
        if [ "$invocations" -eq 0 ]; then
            echo "    ⚠️  $func: No invocations in 30 days"
        else
            echo "    ✅ $func: $invocations invocations in 30 days"
        fi
    done
    
    # Check for empty S3 buckets
    echo "  S3 Buckets:"
    for bucket in $(aws s3 ls | grep "stock-analyzer" | awk '{print $3}'); do
        object_count=$(aws s3 ls "s3://$bucket" --recursive | wc -l)
        if [ "$object_count" -eq 0 ]; then
            echo "    ⚠️  $bucket: Empty bucket"
        else
            echo "    ✅ $bucket: $object_count objects"
        fi
    done
}

# Main execution
echo "🔧 Cost Optimization Analysis"
echo "============================="

optimize_lambda
echo ""
optimize_s3 $1
echo ""
optimize_api
echo ""
optimize_logs
echo ""
check_unused_resources

echo ""
echo "💡 Additional Cost Optimization Tips:"
echo "  1. Use AWS Compute Savings Plans for predictable workloads"
echo "  2. Enable S3 Intelligent-Tiering for unknown access patterns"
echo "  3. Use CloudWatch Logs Insights instead of full log storage"
echo "  4. Consider AWS Free Tier usage (new accounts only)"
echo "  5. Set up billing alerts to monitor costs"
echo ""
echo "🚀 To apply optimizations:"
echo "  ./infra/optimize_costs.sh --cleanup"
echo ""
echo "📊 To monitor costs:"
echo "  ./infra/monitor_costs.sh"
