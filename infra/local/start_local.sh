#!/bin/bash
set -e

echo "🚀 Starting local development environment..."

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ .env.local not found. Please run './infra/local/setup_local_onetime.sh' first."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env.local | xargs)

# Override environment variables for local development
export ENVIRONMENT=development
export REACT_APP_ENVIRONMENT=development

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure'."
    exit 1
fi

echo "✅ Environment variables loaded"
echo "🪣 S3 Bucket: $S3_BUCKET_NAME"
echo "🌍 AWS Region: $AWS_REGION"

# Kill existing processes on ports 8000 and 3000
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "  No process on port 8000"
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "  No process on port 3000"

# Also kill any uvicorn or npm processes
pkill -f "uvicorn app.main:app" 2>/dev/null || echo "  No uvicorn processes found"
pkill -f "npm start" 2>/dev/null || echo "  No npm processes found"
pkill -f "react-scripts start" 2>/dev/null || echo "  No react-scripts processes found"

echo "✅ Cleanup completed"

# Start backend server in background
echo "🔧 Starting backend server..."
cd backend

# Check if Python dependencies are installed
python3 -c "import fastapi, mangum, pandas, yfinance" 2>/dev/null || python -c "import fastapi, mangum, pandas, yfinance" 2>/dev/null || {
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt
}

# Start FastAPI server
python3 -m uvicorn app.main:app --host $API_HOST --port $API_PORT --reload &
BACKEND_PID=$!
echo "✅ Backend server started (PID: $BACKEND_PID)"
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Test backend health
if curl -s http://localhost:$API_PORT/health > /dev/null; then
    echo "✅ Backend health check passed"
else
    echo "❌ Backend health check failed"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend in background
echo "🎨 Starting frontend server..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start React development server
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend server started (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "🎉 Local development environment is running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:$API_PORT"
echo "📚 API Docs: http://localhost:$API_PORT/docs"
echo "🪣 S3 Bucket: s3://$S3_BUCKET_NAME"
echo ""
echo "🛑 To stop: Press Ctrl+C or run './infra/local/stop_local.sh'"
echo ""
echo "💡 Useful commands:"
echo "  - Test API: curl http://localhost:$API_PORT/health"
echo "  - Test analysis: curl http://localhost:$API_PORT/analysis/AAPL"
echo "  - View logs: tail -f backend/app.log"

# Wait for user interrupt
trap 'echo -e "\n🛑 Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0' INT

# Keep script running
while true; do
    sleep 1
done
