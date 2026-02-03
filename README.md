# 7H Stock Analyzer

A comprehensive, modular stock analysis system built with serverless architecture. Features automated technical analysis, recommendation engine, and real-time notifications.

## 🚀 Features

- **Modular Architecture**: Data Loader → Indicator Engine → Signal Engine → Recommendation Engine
- **Technical Analysis**: 15+ indicators (RSI, MACD, Bollinger Bands, ADX, etc.)
- **Smart Recommendations**: 5-tier system (Strong Buy → Strong Sell) with target prices
- **S3 Caching**: Parquet-based caching for performance and cost optimization
- **Serverless**: AWS Lambda + API Gateway + EventBridge
- **Cost Optimized**: < $15/month estimated cost
- **Real-time Notifications**: Pushover integration for significant recommendations

## 📊 Architecture

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

3. **Test Setup**
   ```bash
   ./infra/local/test_local.sh
   ```

4. **Access Applications**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - API Health: http://localhost:8000/health

### AWS Deployment

1. **Deploy Backend**
   ```bash
   ENVIRONMENT=dev ./infra/aws/deploy_aws_onetime.sh
   ```

2. **Deploy Frontend**
   ```bash
   ./infra/aws/deploy_frontend.sh dev
   ```

3. **Monitor Costs**
   ```bash
   ./infra/aws/monitor_costs.sh
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
