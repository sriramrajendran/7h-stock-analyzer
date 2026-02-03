#!/bin/bash
set -e

echo "🚀 Setting up local development environment for 7H Stock Analyzer..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
fi

# Get AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "✅ AWS Account: $AWS_ACCOUNT"
echo "✅ AWS Region: $AWS_REGION"

# Create local environment file
if [ ! -f .env.local ]; then
    cp .env.local.example .env.local
    echo "📝 Created .env.local file"
    
    # Update S3 bucket name
    sed -i.bak "s/stock-analyzer-your-account-dev/7h-stock-analyzer-dev/g" .env.local
    rm .env.local.bak
    
    echo "📝 Updated S3 bucket name in .env.local"
else
    echo "ℹ️  .env.local already exists"
fi

# Create frontend environment file
if [ ! -f frontend/.env.local ]; then
    cp frontend/.env.example frontend/.env.local
    echo "📝 Created frontend/.env.local file"
    
    # Update frontend environment
    sed -i.bak "s/stock-analyzer-your-account-us-east-1-prod/7h-stock-analyzer-dev/g" frontend/.env.local
    sed -i.bak "s|https://your-api-id.execute-api.us-east-1.amazonaws.com|http://localhost:8000|g" frontend/.env.local
    rm frontend/.env.local.bak
    
    echo "📝 Updated frontend environment variables"
else
    echo "ℹ️  frontend/.env.local already exists"
fi

# Create S3 bucket for local development
BUCKET_NAME="7h-stock-analyzer-dev"
echo "🪣 Creating S3 bucket: $BUCKET_NAME"

if ! aws s3 ls "s3://$BUCKET_NAME" &>/dev/null; then
    aws s3 mb "s3://$BUCKET_NAME" --region $AWS_REGION
    echo "✅ Created S3 bucket: $BUCKET_NAME"
else
    echo "ℹ️  S3 bucket already exists: $BUCKET_NAME"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python and pip first."
    echo "💡 Install with: brew install python3"
    exit 1
fi

# Use pip3 if available, otherwise pip
PIP_CMD="pip3"
if ! command -v pip3 &> /dev/null; then
    PIP_CMD="pip"
fi

# Install dependencies
$PIP_CMD install -r requirements.txt
echo "✅ Installed Python dependencies"
cd ..

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
echo "✅ Installed Node.js dependencies"
cd ..

# Make scripts executable
chmod +x ../aws/*.sh ../local/*.sh
echo "✅ Made scripts executable"

echo ""
echo "🎉 Local development setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env.local with your Pushover tokens (optional)"
echo "2. Run './infra/local/start_local.sh' to start the development environment"
echo "3. Open http://localhost:3000 for the frontend"
echo "4. Open http://localhost:8000/docs for the API documentation"
echo ""
echo "💡 Tip: Use './infra/local/test_local.sh' to test the setup"
