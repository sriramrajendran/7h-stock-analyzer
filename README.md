# 7H Stock Analyzer

A comprehensive, modular stock analysis system built with serverless architecture. Features automated technical analysis, recommendation engine, and real-time notifications.

![Architecture Overview](readme.png)

## 🚀 Features

- **Modular Architecture**: Data Loader → Indicator Engine → Signal Engine → Recommendation Engine
- **Technical Analysis**: 15+ indicators (RSI, MACD, Bollinger Bands, ADX, etc.)
- **Smart Recommendations**: 5-tier system (Strong Buy → Strong Sell) with target prices
- **S3 Caching**: Parquet-based caching for performance and cost optimization
- **Serverless**: AWS Lambda + API Gateway + EventBridge
- **Cost Optimized**: < $15/month estimated cost
- **Real-time Notifications**: Pushover integration for significant recommendations

## ⏰ Automated Scheduling

### EventBridge Rules (Active)
- **Market Open Alert**: 9:00 AM EST (2:00 PM UTC) Monday-Friday
- **Midday Alert**: 12:30 PM EST (5:30 PM UTC) Monday-Friday  
- **Weekly Reconciliation**: Sunday 6:00 PM EST (11:00 PM UTC)

### Manual Triggers
```bash
# Manual analysis trigger with notifications
curl -X POST -H "X-API-Key: $API_KEY" https://your-api-gateway-url/run-now

# Manual reconciliation trigger
curl -X POST -H "X-API-Key: $API_KEY" https://your-api-gateway-url/recon/run

# View performance summary
curl -H "X-API-Key: $API_KEY" https://your-api-gateway-url/recon/summary
```

### Notification Setup
Pushover notifications are automatically sent for:
- ✅ **Manual triggers** (`/run-now` endpoint)
- ✅ **Scheduled runs** (EventBridge triggers)
- ✅ **Significant recommendations** (Buy/Strong Buy signals)

Configure Pushover credentials in `.env.local`:
```bash
PUSHOVER_TOKEN=your_pushover_api_token
PUSHOVER_USER=your_pushover_user_key
```

## 🧪 Testing & Quality Assurance

### Comprehensive Test Suite
```bash
# Run all tests with coverage
./infra/local/run_tests.sh

# Run specific test categories
python -m pytest backend/tests/test_recommendation_engine.py -v  # Target prices & risk/reward
python -m pytest backend/tests/test_signal_engine.py -v         # Technical indicators
python -m pytest backend/tests/test_reconciliation_service.py -v # Performance tracking
python -m pytest backend/tests/test_api_endpoints.py -v         # API integrity
```

### Test Coverage Areas
- ✅ **Target Price Calculations**: Ensures profit targets are accurate
- ✅ **Risk/Reward Ratios**: Validates favorable risk vs reward
- ✅ **Signal Generation**: Tests technical indicator logic
- ✅ **Reconciliation Tracking**: Verifies performance calculations
- ✅ **API Security**: Tests authentication and data structures
- ✅ **Error Handling**: Ensures robust error management

### Integrity Guarantees
- 🎯 **Target Prices**: 20% (Strong Buy), 10% (Buy), 2% (Hold) - always verified
- 🛡️ **Risk Management**: Stop losses always smaller than profit targets
- 📊 **Signal Accuracy**: Technical indicators generate consistent signals
- 🔄 **Performance Tracking**: Days to target and success rates are precise
- 🔒 **API Security**: All endpoints require proper authentication

## 📊 Performance Tracking

```
[Tickers] → [Data Loader] → [S3 Cache] → [Indicator Engine] → [Signal Engine] → [Recommendation Engine] → [Output]
```

### Core Modules

- **Data Loader**: Yahoo Finance integration with batch processing and rate limiting
- **Indicator Engine**: Comprehensive technical indicators (Trend, Momentum, Volatility, Volume)
- **Signal Engine**: Weighted scoring system (Trend 40%, Momentum 30%, Volatility 20%, Volume 10%)
- **Recommendation Engine**: BUY/HOLD/SELL with target prices and confidence levels

## 🛠️ Quick Start

### Prerequisites

- AWS CLI configured
- Node.js 16+
- Python 3.10+
- SAM CLI (for deployment)

### Local Development
1. **Setup Environment**
   ```bash
   ./infra/local/setup_local_onetime.sh
   ```

2. **Start Development Servers**
   ```bash
   ./infra/local/start_local.sh
   ```

3. **Run Tests**
   ```bash
   ./infra/local/run_tests.sh
   ```

4. **Test Setup**
   ```bash
   ./infra/local/test_local.sh
   ```

5. **Manual reconciliation (for testing)**
   ```bash
   curl -X POST http://localhost:8000/recon/run
   ```

6. **View performance summary**
   ```bash
   curl http://localhost:8000/recon/summary
   ```

### Access Applications
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health

### AWS Deployment

#### 🚀 One-Click Deployment (Recommended)
```bash
# Smart deployment - auto-detects changes and deploys accordingly
./infra/aws/deploy_aws_onetime.sh deploy
```

**What it does:**
- 🔍 **Auto-detects** changes in frontend/ and backend/ directories
- 📦 **Deploys Lambda** if backend code changed (quick mode)
- 🌐 **Deploys Frontend** if UI code changed
- ⚡ **Quick updates** for frequent code changes
- 🔐 **Auto-configures** all environment variables from .env.local

#### Manual Deployment Options
```bash
# Full deployment (first time setup)
./infra/aws/deploy_aws_onetime.sh

# Quick Lambda update (code changes only)
./infra/aws/deploy_aws_onetime.sh --quick

# Frontend only deployment
./infra/aws/deploy_frontend.sh prod

# Monitor costs
./infra/aws/deploy_aws_onetime.sh monitor-costs
```

#### Environment Setup
Create `.env.local` with your credentials:
```bash
# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET_NAME_PROD=7h-stock-analyzer

# API Authentication  
API_KEY=your-api-key-here

# Pushover Notifications
PUSHOVER_TOKEN=your_pushover_api_token
PUSHOVER_USER=your_pushover_user_key

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

## 📋 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `POST /run-now` - Manual analysis trigger
- `GET /recommendations` - Latest recommendations
- `GET /history/{date}` - Historical data

### Single Stock Analysis
- `GET /analysis/{ticker}` - Analyze single stock
- `GET /analysis/{ticker}/signals` - Get detailed signals
- `GET /analysis/{ticker}/indicators` - Get technical indicators

### Configuration Management
- `GET /config/{type}` - Get configuration
- `POST /config/update` - Update configuration
- `POST /config/validate` - Validate symbols

## 💰 Cost Optimization

### Monthly Cost Breakdown (Estimated)
- **Lambda**: ~$8 (100k invocations/month)
- **S3**: ~$3 (storage + requests)
- **API Gateway**: ~$4 (1M requests/month)
- **CloudWatch Logs**: ~$4-6 (after optimization)
- **Total**: < $20/month

## 🔒 Simple API Security

### Option 1: Static API Key (Simplest)
Add this to your Lambda environment variables:
```bash
API_KEY=your-secure-api-key-here
```

Then use this simple middleware:
```python
# In main.py
from fastapi import HTTPException, Header

API_KEY = os.getenv('API_KEY')

def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY or x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# Add to endpoints
@app.get("/recommendations")
def get_recommendations(api_key: str = Depends(verify_api_key)):
    # Your code
```

### Option 2: Environment-Based Security
```bash
# Production: Require API key
REQUIRE_AUTH=true
API_KEY=your-production-api-key

# Development: No auth required
REQUIRE_AUTH=false
```

### Option 3: IP Whitelist (Simple Network Security)
Add to template.yaml:
```yaml
# In API Gateway CORS
AllowOrigins:
  - "https://yourdomain.com"  # Only your domain
  - "https://your-static-site.s3.amazonaws.com"  # Your S3 UI
```

### Recommended Setup: Static Key + CORS
1. **Single API key** in environment variables
2. **CORS restricted** to your S3 domain only
3. **Simple header validation** in code

**Frontend usage:**
```javascript
fetch('/api/recommendations', {
  headers: { 'X-API-Key': 'your-static-key' }
})
```

### Optimization Features
- **Memory**: 512MB (auto-optimized based on execution time)
- **Timeout**: 180s (reduced from 300s)
- **Concurrency**: 2 (limited to control costs)
- **S3 Lifecycle**: 30-90 day retention policies
- **Log Retention**: 3 days (reduced from 7, cost-optimized)
- **Structured Logging**: JSON format with environment-based filtering

### Cost Management Commands
```bash
# Monitor current costs
./infra/aws/monitor_costs.sh

# Optimize resources
./infra/aws/optimize_costs.sh

# Clean up old data
./infra/aws/optimize_costs.sh --cleanup
```

## 🔧 Configuration

### Environment Variables

#### Local Development (.env.local)
```bash
AWS_REGION=us-east-1
S3_BUCKET=7h-stock-analyzer-dev
PUSHOVER_TOKEN=your_token
PUSHOVER_USER=your_user_key
ENABLE_NOTIFICATIONS=false
LOG_LEVEL=INFO
ENABLE_VERBOSE_LOGGING=true
ENVIRONMENT=dev
```

#### Production (via SAM parameters)
```bash
Environment=prod
MemorySize=512
Timeout=180
ReservedConcurrency=2
LOG_LEVEL=WARNING
ENABLE_VERBOSE_LOGGING=false
ENABLE_STRUCTURED_LOGGING=true
LOG_RETENTION_DAYS=3
```

### S3 Data Structure

```
s3://bucket/
├── data/
│   ├── latest.json          # Latest recommendations
│   └── daily/
│       ├── 2024-01-01.json  # Daily snapshots
├── config/
│   ├── watchlist.json       # Stock configurations
│   ├── portfolio.json
│   ├── us_stocks.json
│   └── etfs.json
├── recon/
│   └── daily/              # Reconciliation data
└── charts/                 # Price chart images
```

## 📈 Technical Indicators

### Trend (40% weight)
- EMA (12, 26)
- SMA (50, 200)
- MACD
- ADX (14)

### Momentum (30% weight)
- RSI (14)
- Stochastic Oscillator
- Rate of Change (10)
- CCI (20)
- Williams %R

### Volatility (20% weight)
- ATR (14)
- Bollinger Bands (20, 2)
- Historical Volatility

### Volume (10% weight)
- On-Balance Volume
- Volume SMA (20)
- Volume Rate of Change
- Price-Volume Trend
- VWAP

## 🎯 Recommendation Logic

### Score Thresholds
- **Strong Buy**: Score ≥ 0.5
- **Buy**: Score ≥ 0.2
- **Hold**: -0.2 ≤ Score < 0.2
- **Sell**: Score ≤ -0.2
- **Strong Sell**: Score ≤ -0.5

### Target Prices
- **Strong Buy**: Current price + 20%
- **Buy**: Current price + 10%
- **Hold**: Current price
- **Sell**: Current price - 5%
- **Strong Sell**: Current price - 20%

### Stop Losses
- **Strong Buy/Sell**: 10%
- **Buy**: 8%
- **Hold/Sell**: 5%

## 🔄 Data Flow

1. **Data Loading**: Fetch OHLCV from Yahoo Finance with S3 cache
2. **Indicator Computation**: Calculate 15+ technical indicators
3. **Signal Generation**: Convert indicators to +1/0/-1 signals
4. **Score Aggregation**: Weighted combination into final score
5. **Recommendation**: Convert score to actionable recommendation
6. **Storage**: Save to S3 with metadata and timestamps

## 🧪 Testing

### Local Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test single analysis
curl http://localhost:8000/analysis/AAPL

# Test configuration
curl http://localhost:8000/config/watchlist
```

### AWS Testing
```bash
# Test deployed API
curl https://your-api.execute-api.region.amazonaws.com/health

# Test analysis
curl https://your-api.execute-api.region.amazonaws.com/analysis/AAPL
```

## 📊 Monitoring

### CloudWatch Metrics
- Lambda invocations and errors
- Duration and memory usage
- S3 storage and requests
- API Gateway request counts

### Cost Alerts
- Monthly cost > $20
- Lambda errors > 5/hour
- S3 storage > 1GB

### Health Checks
- API endpoint availability
- S3 bucket accessibility
- Lambda function responsiveness

## 🛠️ Development

### Project Structure
```
├── backend/
│   ├── app/
│   │   ├── modules/          # Core analysis modules
│   │   ├── engine/           # Orchestration layer
│   │   ├── services/         # AWS integrations
│   │   └── api/              # API endpoints
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── infra/
│   ├── aws/                 # AWS deployment scripts
│   │   ├── deploy_aws_onetime.sh   # AWS backend deployment (one-time)
│   │   ├── deploy_frontend.sh     # Frontend deployment
│   │   ├── monitor_costs.sh       # Cost monitoring
│   │   ├── optimize_costs.sh       # Cost optimization
│   │   └── template.yaml           # CloudFormation template
│   └── local/               # Local development scripts
│       ├── setup_local_onetime.sh  # Local environment setup (one-time)
│       ├── start_local.sh         # Start dev servers
│       ├── stop_local.sh          # Stop dev servers
│       └── test_local.sh           # Test local setup
└── README.md
```

### Adding New Indicators
1. Update `IndicatorEngine` in `backend/app/modules/indicator_engine.py`
2. Add signal logic in `SignalEngine`
3. Update weights if needed
4. Test with single stock analysis

### Extending Recommendations
1. Modify thresholds in `RecommendationEngine`
2. Update target price calculations
3. Add new reasoning logic
4. Test with various market conditions

## 🔒 Security

### AWS Security
- IAM roles with minimal permissions
- S3 encryption (AES256)
- VPC isolation (optional)
- API key authentication (configurable)

### Data Protection
- No sensitive data in logs
- Encrypted S3 storage
- Secure parameter handling
- Environment variable protection

## 🚨 Troubleshooting

### Common Issues

**Lambda Timeout**
- Check memory allocation
- Monitor execution duration
- Optimize batch processing

**S3 Access Issues**
- Verify IAM permissions
- Check bucket policies
- Validate region settings

**High Costs**
- Run cost optimization script
- Review Lambda memory usage
- Check S3 lifecycle policies

**Data Quality Issues**
- Validate Yahoo Finance data
- Check indicator calculations
- Review signal generation logic

### Debug Commands
```bash
# Check Lambda logs (cost-optimized)
aws logs tail /aws/lambda/7h-stock-analyzer-prod-StockAnalyzerFunction --follow

# Test Lambda locally
sam local invoke StockAnalyzerFunction --event events/test-event.json

# Monitor S3 storage
aws s3 ls s3://your-bucket --recursive --human-readable --summarize

# Monitor CloudWatch log costs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/
```

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure cost optimization
5. Submit pull request

## 📞 Support

For issues and questions:
1. Check CloudWatch logs
2. Review deployment outputs
3. Validate configuration
4. Test with manual triggers

---

**Built with ❤️ for quantitative analysis and automated trading insights**
