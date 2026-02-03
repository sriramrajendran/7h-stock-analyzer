#!/bin/bash
set -e

echo "💰 AWS Cost Monitoring for 7H Stock Analyzer..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${AWS_REGION:-us-east-1}

echo "📋 Cost Analysis for Account: $AWS_ACCOUNT (Region: $AWS_REGION)"
echo ""

# Function to get cost for specific service
get_service_cost() {
    local service=$1
    local days=${2:-30}
    
    aws ce get-cost-and-usage \
        --time-period Start=$(date -d "$days days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
        --filter Dimensions={Key=SERVICE,Values=[$service]} \
        --metrics BlendedCost \
        --granularity MONTHLY \
        --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
        --output text 2>/dev/null || echo "0"
}

# Function to get Lambda costs
get_lambda_costs() {
    echo "🔧 Lambda Function Costs:"
    
    # Get Lambda cost
    lambda_cost=$(get_service_cost "AWS Lambda")
    echo "  Lambda Service: $${lambda_cost}"
    
    # Get invocation metrics
    echo "  Invocation Metrics:"
    
    for env in dev staging prod; do
        stack_name="7h-stock-analyzer-$env"
        
        # Check if stack exists
        if aws cloudformation describe-stacks --stack-name "$stack_name" &>/dev/null; then
            # Get Lambda function name
            lambda_name=$(aws cloudformation describe-stacks \
                --stack-name "$stack_name" \
                --query 'Stacks[0].Outputs[?OutputKey==`StockAnalyzerFunction`].OutputValue' \
                --output text 2>/dev/null || echo "")
            
            if [ -n "$lambda_name" ]; then
                # Get invocation count
                invocations=$(aws logs filter-log-events \
                    --log-group-name "/aws/lambda/$(basename $lambda_name)" \
                    --start-time $(date -d "30 days ago" +%s)000 \
                    --end-time $(date +%s)000 \
                    --query 'events[0].timestamp' \
                    --output text 2>/dev/null | wc -l || echo "0")
                
                echo "    $env: ~$invocations invocations (30 days)"
            fi
        fi
    done
}

# Function to get S3 costs
get_s3_costs() {
    echo "🪣 S3 Storage Costs:"
    
    s3_cost=$(get_service_cost "Amazon S3")
    echo "  S3 Service: $${s3_cost}"
    
    # Get storage metrics for each bucket
    for env in dev staging prod; do
        bucket_name="7h-stock-analyzer-$env"
        if [ "$env" = "prod" ]; then
            bucket_name="7h-stock-analyzer"
        fi
        
        if aws s3 ls "s3://$bucket_name" &>/dev/null; then
            # Get bucket size
            size=$(aws s3 ls "s3://$bucket_name" --recursive --human-readable --summarize | grep "Total Size" | awk '{print $3, $4}' || echo "0 B")
            object_count=$(aws s3 ls "s3://$bucket_name" --recursive | wc -l)
            
            echo "    $env: $size ($object_count objects)"
        fi
    done
}

# Function to get API Gateway costs
get_api_costs() {
    echo "🌐 API Gateway Costs:"
    
    api_cost=$(get_service_cost "Amazon API Gateway")
    echo "  API Gateway Service: $${api_cost}"
    
    # Note: API Gateway detailed metrics require CloudWatch Logs
    echo "  Request counts: Check CloudWatch Logs for detailed metrics"
}

# Function to get total cost
get_total_cost() {
    echo "💸 Total Cost Summary:"
    
    total_cost=$(aws ce get-cost-and-usage \
        --time-period Start=$(date -d "30 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
        --filter Dimensions={Key=SERVICE,Values=["AWS Lambda","Amazon S3","Amazon API Gateway","Amazon CloudWatch"]} \
        --metrics BlendedCost \
        --granularity MONTHLY \
        --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
        --output text 2>/dev/null || echo "0")
    
    echo "  Total (30 days): $${total_cost}"
    echo "  Estimated Monthly: $${total_cost}"
    
    # Cost optimization recommendations
    if (( $(echo "$total_cost > 20" | bc -l) )); then
        echo "  ⚠️  Cost is above $20 - consider optimization"
    elif (( $(echo "$total_cost > 10" | bc -l) )); then
        echo "  ✅ Cost is moderate - monitor usage"
    else
        echo "  ✅ Cost is well optimized"
    fi
}

# Function to get cost forecast
get_cost_forecast() {
    echo "📊 Cost Forecast:"
    
    forecast=$(aws ce get-cost-forecast \
        --time-period Start=$(date +%Y-%m-%d),End=$(date -d "30 days" +%Y-%m-%d) \
        --metric "BLENDED_COST" \
        --granularity "MONTHLY" \
        --query 'MeanValue' \
        --output text 2>/dev/null || echo "N/A")
    
    echo "  Next 30 days: $${forecast}"
}

# Main execution
echo "📈 Cost Analysis (Last 30 Days)"
echo "================================"

get_lambda_costs
echo ""
get_s3_costs
echo ""
get_api_costs
echo ""
get_total_cost
echo ""
get_cost_forecast

echo ""
echo "💡 Cost Optimization Tips:"
echo "  1. Reduce Lambda memory size if execution time is low"
echo "  2. Decrease Lambda timeout to minimum required"
echo "  3. Use S3 lifecycle policies to delete old data"
echo "  4. Limit API Gateway requests with throttling"
echo "  5. Reduce CloudWatch log retention period"
echo "  6. Monitor and clean up unused resources"
echo ""
echo "🔧 To optimize costs:"
echo "  ./infra/optimize_costs.sh"

# Check for high costs
total_cost=$(aws ce get-cost-and-usage \
    --time-period Start=$(date -d "30 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --filter Dimensions={Key=SERVICE,Values=["AWS Lambda","Amazon S3","Amazon API Gateway","Amazon CloudWatch"]} \
    --metrics BlendedCost \
    --granularity MONTHLY \
    --query 'ResultsByTime[0].Total.BlendedCost.Amount' \
    --output text 2>/dev/null || echo "0")

if (( $(echo "$total_cost > 50" | bc -l) )); then
    echo ""
    echo "🚨 HIGH COST ALERT: Monthly cost exceeds $50"
    echo "   Consider running cost optimization immediately"
fi
