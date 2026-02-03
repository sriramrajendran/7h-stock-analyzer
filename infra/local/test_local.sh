#!/bin/bash
set -e

echo "🧪 Testing local development environment..."

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ .env.local not found. Please run './infra/local/setup_local_onetime.sh' first."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env.local | xargs)

echo "🔧 Testing backend API..."

# Test health endpoint
echo "  📊 Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s http://localhost:$API_PORT/health || echo "")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo "  ✅ Health check passed"
else
    echo "  ❌ Health check failed: $HEALTH_RESPONSE"
    echo "  💡 Make sure backend is running: './infra/local/start_local.sh'"
    exit 1
fi

# Test single stock analysis
echo "  📈 Testing single stock analysis..."
ANALYSIS_RESPONSE=$(curl -s http://localhost:$API_PORT/analysis/AAPL || echo "")
if [[ $ANALYSIS_RESPONSE == *"success"* ]]; then
    echo "  ✅ Single stock analysis passed"
else
    echo "  ❌ Single stock analysis failed: $ANALYSIS_RESPONSE"
    exit 1
fi

# Test configuration endpoints
echo "  ⚙️  Testing configuration endpoints..."
CONFIG_RESPONSE=$(curl -s http://localhost:$API_PORT/config || echo "")
if [[ $CONFIG_RESPONSE == *"watchlist"* ]] || [[ $CONFIG_RESPONSE == *"config"* ]]; then
    echo "  ✅ Configuration endpoint passed"
else
    echo "  ⚠️  Configuration endpoint returned: $CONFIG_RESPONSE"
fi

# Test S3 connectivity
echo "  🪣 Testing S3 connectivity..."
if aws s3 ls "s3://$S3_BUCKET_NAME" &>/dev/null; then
    echo "  ✅ S3 bucket accessible: $S3_BUCKET_NAME"
else
    echo "  ❌ S3 bucket not accessible: $S3_BUCKET_NAME"
    echo "  💡 Check AWS credentials and bucket permissions"
    exit 1
fi

# Test frontend
echo "  🎨 Testing frontend..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "  ✅ Frontend accessible"
else
    echo "  ❌ Frontend not accessible"
    echo "  💡 Make sure frontend is running: './infra/local/start_local.sh'"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Local development environment is working correctly."
echo ""
echo "📋 Quick test commands:"
echo "  curl http://localhost:$API_PORT/health"
echo "  curl http://localhost:$API_PORT/analysis/AAPL"
echo "  curl http://localhost:$API_PORT/analysis/MSFT"
echo ""
echo "🌐 Open in browser:"
echo "  Frontend: http://localhost:3000"
echo "  API Docs: http://localhost:$API_PORT/docs"
