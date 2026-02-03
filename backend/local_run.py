"""
Local development runner for testing the Lambda function
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import handler
from app.engine.recommender import run_engine
from app.services.s3_store import persist_results, get_latest_results
from app.services.pushover import send_push_notification, validate_pushover_config


def simulate_cron_event():
    """Simulate an EventBridge cron event"""
    return {
        "source": "aws.events",
        "detail-type": "Scheduled Event",
        "detail": {},
        "resources": [],
        "id": "test-cron-id",
        "time": datetime.utcnow().isoformat()
    }


def simulate_api_event():
    """Simulate an API Gateway event for /run-now"""
    return {
        "version": "2.0",
        "routeKey": "POST /run-now",
        "rawPath": "/run-now",
        "rawQueryString": "",
        "headers": {
            "content-type": "application/json",
            "host": "localhost:8000"
        },
        "requestContext": {
            "http": {
                "method": "POST",
                "path": "/run-now",
                "sourceIp": "127.0.0.1",
                "userAgent": "test-agent"
            }
        },
        "body": "",
        "isBase64Encoded": False
    }


def test_cron_trigger():
    """Test the cron trigger functionality"""
    print("=" * 60)
    print("Testing EventBridge Cron Trigger")
    print("=" * 60)
    
    event = simulate_cron_event()
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "stock-analyzer-test"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:stock-analyzer-test"
            self.memory_limit_in_mb = 1024
            self.aws_request_id = "test-request-id"
            self.log_group_name = "/aws/lambda/stock-analyzer-test"
            self.log_stream_name = "2023/01/01/[$LATEST]test-stream"
            self.remaining_time_in_millis = 30000
    
    context = MockContext()
    
    try:
        response = handler(event, context)
        print("✅ Cron trigger test successful")
        print(f"Response: {json.dumps(response, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Cron trigger test failed: {e}")
        return False


def test_api_trigger():
    """Test the API Gateway trigger functionality"""
    print("=" * 60)
    print("Testing API Gateway Trigger (/run-now)")
    print("=" * 60)
    
    event = simulate_api_event()
    
    # Mock context
    class MockContext:
        def __init__(self):
            self.function_name = "stock-analyzer-test"
            self.function_version = "$LATEST"
            self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:stock-analyzer-test"
            self.memory_limit_in_mb = 1024
            self.aws_request_id = "test-request-api"
            self.remaining_time_in_millis = 30000
    
    context = MockContext()
    
    try:
        response = handler(event, context)
        print("✅ API trigger test successful")
        print(f"Response: {json.dumps(response, indent=2)}")
        return True
    except Exception as e:
        print(f"❌ API trigger test failed: {e}")
        return False


def test_engine_directly():
    """Test the recommendation engine directly"""
    print("=" * 60)
    print("Testing Recommendation Engine Directly")
    print("=" * 60)
    
    try:
        recommendations = run_engine()
        print(f"✅ Engine test successful - Found {len(recommendations)} recommendations")
        
        if recommendations:
            print("\nTop recommendations:")
            for i, rec in enumerate(recommendations[:3], 1):
                print(f"{i}. {rec['symbol']} - ${rec['price']:.2f} ({rec['change_pct']:+.1f}%) - Score: {rec['score']}")
        
        return True
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False


def test_s3_storage():
    """Test S3 storage functionality"""
    print("=" * 60)
    print("Testing S3 Storage")
    print("=" * 60)
    
    try:
        # Create test recommendations
        test_recommendations = [
            {
                'symbol': 'TEST',
                'company': 'Test Company',
                'price': 100.0,
                'change_pct': 1.5,
                'rsi': 45.0,
                'macd': 0.5,
                'sma_20': 98.0,
                'sma_50': 95.0,
                'recommendation': 'BUY',
                'score': 3,
                'reasoning': 'Test reasoning',
                'fundamental': {},
                'timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        # Test persistence
        success = persist_results(test_recommendations)
        if success:
            print("✅ S3 persistence test successful")
            
            # Test retrieval
            latest = get_latest_results()
            if 'error' not in latest:
                print("✅ S3 retrieval test successful")
                print(f"Retrieved {latest.get('count', 0)} recommendations")
            else:
                print(f"❌ S3 retrieval test failed: {latest['error']}")
                return False
        else:
            print("❌ S3 persistence test failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ S3 storage test failed: {e}")
        return False


def test_pushover_notifications():
    """Test Pushover notification functionality"""
    print("=" * 60)
    print("Testing Pushover Notifications")
    print("=" * 60)
    
    try:
        # Test configuration validation
        config = validate_pushover_config()
        print(f"Pushover config: {config}")
        
        if config['token_configured'] and config['user_configured']:
            if config['test_successful']:
                print("✅ Pushover test successful")
            else:
                print("❌ Pushover test failed")
                return False
        else:
            print("⚠️  Pushover not configured - skipping notification tests")
        
        return True
    except Exception as e:
        print(f"❌ Pushover test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Local Development Tests")
    print("=" * 60)
    
    # Set environment variables for local testing
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['S3_BUCKET_NAME'] = 'stock-ui-test'
    
    tests = [
        ("Recommendation Engine", test_engine_directly),
        ("S3 Storage", test_s3_storage),
        ("Pushover Notifications", test_pushover_notifications),
        ("Cron Trigger", test_cron_trigger),
        ("API Trigger", test_api_trigger),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed - check logs above")
    
    return passed == total


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Local development runner")
    parser.add_argument("--test", choices=["engine", "s3", "pushover", "cron", "api", "all"], 
                       default="all", help="Which test to run")
    
    args = parser.parse_args()
    
    if args.test == "all":
        run_all_tests()
    elif args.test == "engine":
        test_engine_directly()
    elif args.test == "s3":
        test_s3_storage()
    elif args.test == "pushover":
        test_pushover_notifications()
    elif args.test == "cron":
        test_cron_trigger()
    elif args.test == "api":
        test_api_trigger()
