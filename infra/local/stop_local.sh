#!/bin/bash
set -e

echo "🛑 Stopping local development environment..."

# Kill processes on common ports
echo "🔧 Stopping backend server (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "  No process found on port 8000"

echo "🎨 Stopping frontend server (port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "  No process found on port 3000"

# Also check for specific processes
echo "🧹 Cleaning up remaining processes..."
pkill -f "uvicorn app.main:app" 2>/dev/null || echo "  No uvicorn processes found"
pkill -f "npm run dev" 2>/dev/null || echo "  No npm dev processes found"
pkill -f "vite" 2>/dev/null || echo "  No vite processes found"

# Wait a moment for processes to terminate
sleep 2

# Final check
if lsof -ti:8000 >/dev/null 2>&1 || lsof -ti:3000 >/dev/null 2>&1; then
    echo "⚠️  Some processes may still be running. You can manually kill them:"
    echo "  kill \$(lsof -ti:8000)"
    echo "  kill \$(lsof -ti:3000)"
else
    echo "✅ All development servers stopped successfully"
fi

echo "✅ Local development environment stopped"
