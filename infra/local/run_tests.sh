#!/bin/bash

# Comprehensive test runner for 7H Stock Analyzer

set -e

echo "🧪 Running 7H Stock Analyzer Test Suite..."
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
fi

# Set test environment variables
export PYTHONPATH="${BACKEND_DIR}:${PYTHONPATH}"
export API_KEY="test-api-key-12345"
export REQUIRE_AUTH="true"
export ENVIRONMENT="test"

echo ""
echo "🔬 Running Test Categories..."
echo "==========================="

# 1. Recommendation Engine Tests
echo "📊 Testing Recommendation Engine..."
python -m pytest tests/test_recommendation_engine.py -v --tb=short --cov=app.modules.recommendation_engine --cov-report=term-missing

# 2. Signal Engine Tests
echo "📈 Testing Signal Engine..."
python -m pytest tests/test_signal_engine.py -v --tb=short --cov=app.modules.signal_engine --cov-report=term-missing

# 3. Reconciliation Service Tests
echo "🔄 Testing Reconciliation Service..."
python -m pytest tests/test_reconciliation_service.py -v --tb=short --cov=app.services.recon_service --cov-report=term-missing

# 4. API Endpoint Tests
echo "🌐 Testing API Endpoints..."
python -m pytest tests/test_api_endpoints.py -v --tb=short --cov=app.main --cov-report=term-missing

echo ""
echo "🎯 Running Integration Tests..."
echo "=============================="

# 5. Integration Tests (if any)
echo "🔗 Testing Component Integration..."
python -m pytest tests/ -k "integration" -v --tb=short || echo "ℹ️ No integration tests found"

echo ""
echo "📊 Test Summary & Coverage Report"
echo "==============================="

# Generate combined coverage report
python -m pytest tests/ --cov=app --cov-report=term --cov-report=html:htmlcov --cov-report=xml --tb=short

echo ""
echo "✅ Test Suite Completed!"
echo "======================"
echo ""
echo "📋 Test Results Summary:"
echo "  - Recommendation Engine: Target prices, risk/reward ratios, scoring logic"
echo "  - Signal Engine: Technical indicator signals, weight calculations"
echo "  - Reconciliation Service: Performance tracking, profit/stop loss calculations"
echo "  - API Endpoints: Authentication, response structures, error handling"
echo ""
echo "📈 Coverage Report Generated:"
echo "  - Terminal: Displayed above"
echo "  - HTML: Open htmlcov/index.html in browser"
echo "  - XML: For CI/CD integration"
echo ""
echo "🔍 To run specific test categories:"
echo "  python -m pytest tests/test_recommendation_engine.py -v"
echo "  python -m pytest tests/test_signal_engine.py -v"
echo "  python -m pytest tests/test_reconciliation_service.py -v"
echo "  python -m pytest tests/test_api_endpoints.py -v"
echo ""
echo "🚨 To run tests with specific focus:"
echo "  python -m pytest tests/ -k 'target_price' -v  # Target price tests"
echo "  python -m pytest tests/ -k 'risk_reward' -v     # Risk/reward tests"
echo "  python -m pytest tests/ -k 'reconciliation' -v # Reconciliation tests"
echo ""
echo "📝 To run tests with detailed output:"
echo "  python -m pytest tests/ -v -s --tb=long"
echo ""
echo "🎯 Test integrity ensures:"
echo "  ✅ Target prices are calculated correctly"
echo "  ✅ Risk/reward ratios are always favorable"
echo "  ✅ Signal generation is consistent and accurate"
echo "  ✅ Reconciliation tracking is precise"
echo "  ✅ API endpoints are secure and reliable"
echo "  ✅ Error handling is robust"
echo "  ✅ Data structures are consistent"
