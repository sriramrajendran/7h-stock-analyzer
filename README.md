# 🚀 7H Stock Analyzer - Enhanced Serverless Lambda Version

A comprehensive serverless stock analysis system built with AWS Lambda, EventBridge, S3, and React. This enhanced version provides automated daily stock recommendations with advanced features including target prices, stop losses, confidence levels, reconciliation tracking, and complete monitoring.

## 🏗️ Enhanced Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  EventBridge    │───▶│   AWS Lambda     │───▶│   S3 Storage    │
│   Cron Trigger  │    │ Enhanced Engine  │    │  (JSON + UI)    │
└─────────────────┘    │  (FastAPI + TA)  │    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Pushover API    │
                       │  Smart Alerts    │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  Recon Service   │
                       │  Performance     │
                       │  Tracking        │
                       └──────────────────┘
```

## 🌟 Enhanced Features

### Backend (Enhanced Lambda)
- **Automated Analysis**: Daily cron triggers at market open (9:30 AM EST weekdays)
- **Manual Triggers**: `/run-now` API endpoint for on-demand analysis
- **Enhanced Technical Analysis**: RSI, MACD, Moving Averages, Bollinger Bands, Stochastic, ATR, OBV
- **Target Price System**: Automatic calculation of target and stop-loss prices based on recommendation strength
- **Confidence Levels**: High/Medium/Low confidence scoring with detailed reasoning
- **Technical Indicators Tracking**: List all indicators used for each recommendation
- **Reconciliation Service**: Daily tracking of target/stop-loss achievement with performance metrics
- **Purge Service**: Automatic cleanup of old data (1000+ days) with dry-run capability
- **Enhanced Configuration**: Full CRUD operations with validation, backup, and history
- **Smart Notifications**: Target/stop-loss alerts with priority levels and detailed information
- **Security Service**: API key management, access control, and request validation
- **Chart Generation**: Automatic price chart generation for each recommendation
- **Performance Analytics**: Detailed tracking of recommendation performance over time

### Frontend (Enhanced React)
- **Modern UI**: Built with React 18, Tailwind CSS, and responsive design
- **Real-time Dashboard**: Latest recommendations with enhanced details, charts, and performance tracking
- **Advanced Filtering**: Filter by confidence level, recommendation type, technical indicators
- **Historical Analysis**: View past recommendations with recon data and performance metrics
- **Configuration UI**: Manage stock symbols with validation, backup, and history tracking
- **System Health**: Real-time system status and health monitoring
- **Performance Summary**: Detailed analytics and recommendation distribution
- **Chart Integration**: Interactive price charts with technical overlays
- **Recon Dashboard**: View target/stop-loss achievements and performance analytics

### Storage (Enhanced S3)
- **Latest Data**: `data/latest.json` - Current recommendations with enhanced fields
- **Historical Data**: `data/daily/YYYY-MM-DD.json` - Immutable daily snapshots
- **Recon Data**: `recon/daily/YYYY-MM-DD.json` - Daily reconciliation tracking
- **Chart Storage**: `charts/` - Generated price charts for recommendations
- **Configuration**: `config/` - Stock lists with backup and versioning
- **Security**: Enhanced bucket policies, encryption, and access controls
- **Lifecycle Management**: Automatic cleanup and cost optimization
- **Static Website**: Serves the React frontend with enhanced security

## 📦 Project Structure

```
7h-stock-analyzer/
├── backend/                    # Enhanced Lambda function code
│   ├── app/
│   │   ├── main.py            # FastAPI + Lambda handler
│   │   ├── engine/
│   │   │   └── enhanced_recommender.py # Enhanced technical analysis
│   │   ├── services/
│   │   │   ├── s3_store.py    # Enhanced S3 storage service
│   │   │   ├── pushover.py    # Enhanced notification service
│   │   │   ├── config_manager.py # Enhanced configuration management
│   │   │   ├── recon_service.py # Reconciliation service
│   │   │   ├── purge_service.py # Data cleanup service
│   │   │   ├── chart_service.py # Chart generation service
│   │   │   └── security_service.py # Security and API management
│   │   ├── config.py          # Application configuration
│   │   ├── models.py          # Enhanced Pydantic models
│   │   └── __init__.py
│   ├── requirements.txt       # Python dependencies
│   └── local_run.py          # Local development runner
├── frontend/                  # Enhanced React web application
│   ├── src/
│   │   ├── pages/            # Enhanced page components
│   │   │   ├── Dashboard.jsx  # Enhanced dashboard with charts
│   │   │   ├── History.jsx    # Historical analysis with recon data
│   │   │   └── Config.jsx     # Enhanced configuration management
│   │   ├── components/
│   │   │   ├── RecommendationTable.jsx # Enhanced table
│   │   │   ├── PriceChart.jsx # Chart component
│   │   │   └── PerformanceSummary.jsx # Performance analytics
│   │   ├── services/
│   │   │   └── api.js        # Enhanced API service layer
│   │   ├── App.jsx           # Enhanced main app component
│   │   ├── main.jsx          # React entry point
│   │   └── index.css         # Tailwind styles
│   ├── package.json          # Node.js dependencies
│   ├── vite.config.js        # Vite configuration
│   └── tailwind.config.js    # Tailwind configuration
├── infra/
│   └── template.yaml         # Enhanced AWS SAM infrastructure
├── input/                    # Configuration files
│   ├── config_portfolio.txt
│   ├── config_watchlist.txt
│   ├── config_us_stocks.txt
│   └── config_etfs.txt
├── doc/                      # Specifications
│   ├── spec_lambda.md
│   └── spec_lambda_enhance.md
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- AWS CLI configured with appropriate permissions
- SAM CLI installed (`pip install aws-sam-cli`)
- Node.js 18+ and npm
- Python 3.10+

### 1. Deploy Infrastructure

```bash
# Navigate to project directory
cd 7h-stock-analyzer

# Deploy with AWS SAM (guided mode for first time)
sam deploy --guided

# Note your API Gateway URL and S3 bucket URL from the output
```

### 2. Configure Environment Variables

Set these in the Lambda function console or via SAM parameters:
- `PUSHOVER_TOKEN`: Your Pushover app token (optional)
- `PUSHOVER_USER`: Your Pushover user key (optional)
- `S3_BUCKET_NAME`: Your S3 bucket name (auto-configured)
- `ENABLE_NOTIFICATIONS`: Set to "true" to enable Pushover alerts

### 3. Build and Deploy Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Upload to S3 (replace with your bucket name from deployment)
aws s3 sync dist/ s3://your-bucket-name/ --delete
```

### 4. Test the Application

1. **Health Check**: `https://your-api-gateway-url.com/health`
2. **Manual Run**: `POST https://your-api-gateway-url.com/run-now`
3. **Web Interface**: `http://your-bucket-name.s3-website-us-east-1.amazonaws.com`

## 🔧 Configuration

### Stock Lists Management

Update stock symbols via API or edit files in `input/`:

```bash
# Update portfolio via API
curl -X POST https://your-api-gateway-url.com/config/update \
  -H "Content-Type: application/json" \
  -d '{
    "config_type": "portfolio",
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "backup": true
  }'

# Get all configurations
curl https://your-api-gateway-url.com/config

# Validate symbols
curl -X POST https://your-api-gateway-url.com/config/validate \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "INVALID", "MSFT"]}'
```

### Pushover Notifications Setup (Optional)

1. Create an app at [Pushover.net](https://pushover.net/)
2. Get your app token and user key
3. Set environment variables in Lambda function
4. Enable notifications with `ENABLE_NOTIFICATIONS=true`

### Cron Schedule

Default: Weekdays at 9:30 AM EST (14:30 UTC)
```yaml
Schedule: cron(30 14 ? * MON-FRI *)
```

Modify in `infra/template.yaml` if needed.

## 📊 Enhanced API Endpoints

### Core Endpoints
- `GET /health` - Enhanced health check with system status
- `POST /run-now` - Trigger manual analysis with enhanced results
- `GET /recommendations` - Get latest recommendations with enhanced fields
- `GET /history/{date}` - Get historical data with recon information

### Enhanced Configuration Endpoints
- `GET /config/{type}` - Get configuration with metadata
- `GET /config` - Get all configurations with summary
- `POST /config/update` - Update configuration with validation and backup
- `POST /config/validate` - Validate stock symbols with detailed feedback
- `POST /config/sync` - Sync S3 configs to local files
- `GET /config/history/{type}` - Get configuration change history

### New Management Endpoints
- `POST /recon/run` - Trigger manual reconciliation
- `GET /recon/summary` - Get recon performance summary
- `POST /purge/run` - Run data cleanup with dry-run option
- `GET /purge/stats` - Get storage statistics
- `POST /security/api-keys` - Generate new API key
- `GET /security/api-keys` - List API keys
- `POST /charts/generate` - Generate price charts

### Notification Endpoints
- `POST /notifications/test` - Test notification system
- `POST /notifications/target-alert` - Send target achievement alert
- `POST /notifications/stop-loss-alert` - Send stop loss alert
- `GET /notifications/stats` - Get notification statistics

## 🎯 Enhanced Recommendation Logic

### Target Price Calculation
- **Strong Buy**: Target +20%, Stop Loss -5%
- **Buy**: Target +10%, Stop Loss -5%
- **Hold**: Target 0%, Stop Loss -5%
- **Sell**: Target -5%, Stop Loss +5%
- **Strong Sell**: Target -20%, Stop Loss +5%

### Confidence Level Calculation
- **High**: Score ≥ 0.8 + indicator consistency ≥ 0.8
- **Medium**: Score 0.6-0.8 + indicator consistency 0.6-0.8
- **Low**: Score < 0.6 or indicator consistency < 0.6

### Enhanced Scoring System
- **RSI**: +2 (oversold <30), -2 (overbought >70), +1 (favorable), -1 (unfavorable)
- **MACD**: +1 (bullish crossover), -1 (bearish crossover)
- **Moving Averages**: +1 per MA above price (20, 50, 200-day)
- **Price Momentum**: +0.5 (positive weekly/monthly change)
- **Indicator Consistency**: Bonus for aligned signals
- **Total Score**: Determines recommendation strength and confidence

### Recommendation Types
- **Score ≥ 0.7**: Strong Buy
- **Score 0.3-0.7**: Buy
- **Score -0.3 to 0.3**: Hold
- **Score -0.7 to -0.3**: Sell
- **Score ≤ -0.7**: Strong Sell

### Technical Indicators Used
- **RSI**: Momentum oscillator
- **MACD**: Trend following indicator
- **SMA (20, 50)**: Moving averages
- **Bollinger Bands**: Volatility bands
- **Volume SMA**: Volume analysis
- **Price Action**: Current vs historical patterns

## 💰 Enhanced Cost Estimate

Monthly costs (typical usage with enhanced features):
- **Lambda**: ~$0.08 (enhanced processing, 1024MB avg)
- **EventBridge**: $0.00
- **API Gateway**: ~$0.02 (enhanced endpoints)
- **S3**: ~$0.08 (charts, recon data, enhanced storage)
- **SNS**: ~$0.01 (enhanced alarms)
- **CloudWatch**: ~$0.02 (enhanced monitoring)
- **Pushover**: Depends on plan (free tier available)
- **Total**: <$0.25/month

### Cost Optimization Features
- **Lifecycle Policies**: Automatic cleanup of old data
- **Reserved Concurrency**: Control Lambda costs
- **Data Compression**: Optimized JSON storage
- **Smart Caching**: Reduce S3 requests
- **Efficient Charts**: Optimized image generation

## 🧪 Local Development

### Backend Testing

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run all tests
python local_run.py --test all

# Run specific test
python local_run.py --test engine
python local_run.py --test s3
python local_run.py --test pushover
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview build locally
npm run preview
```

## 📈 Enhanced Monitoring and Logging

### CloudWatch Integration
- **Enhanced Lambda Logs**: Structured logging with correlation IDs
- **Advanced Alarms**: Error rates, duration, costs, and performance metrics
- **SNS Notifications**: Multi-channel alerts with filtering
- **Custom Metrics**: Recommendation counts, confidence levels, recon performance
- **Dashboard**: Pre-built CloudWatch dashboard for system overview

### Enhanced Log Locations
- Lambda: `/aws/lambda/stock-analyzer-function`
- API Gateway: Enhanced request/response logging
- S3: Access logs with detailed tracking
- Recon: Separate log group for reconciliation tracking
- Charts: Log group for chart generation metrics

### Performance Monitoring
- **Recommendation Accuracy**: Track target/stop-loss achievement
- **System Performance**: Lambda duration and memory usage
- **Data Quality**: Validation and error tracking
- **User Analytics**: API usage patterns and popular features

## 🔒 Enhanced Security

- **IAM Roles**: Least privilege principle with enhanced policies
- **S3 Security**: Bucket encryption, versioning, and access controls
- **API Gateway**: Enhanced CORS, rate limiting, and request validation
- **API Key Management**: Secure key generation and rotation
- **Environment Variables**: Encrypted storage for sensitive data
- **VPC Isolation**: Optional VPC deployment for enhanced security
- **Data Encryption**: AES-256 encryption for all S3 data
- **Access Logging**: Comprehensive audit trail
- **Input Validation**: Sanitization and validation of all inputs

## 🚨 Important Notes

⚠️ **Disclaimer**: This tool is for educational purposes only. Stock recommendations are based on technical analysis and should not be considered financial advice. Always do your own research and consult with a financial advisor.

- **Data Source**: Yahoo Finance (free, rate-limited)
- **Analysis**: Technical indicators only (no fundamental analysis)
- **Recommendations**: Use as one input among many for investment decisions
- **Market Hours**: Analysis runs during market hours for best data quality

## 🔄 Updates and Maintenance

### Updating Stock Lists
1. Use the Configuration UI in the web app
2. Update files in `input/` and sync via `/config/sync` endpoint
3. Call `/config/update` endpoint directly

### Updating Lambda Code
```bash
# Build and deploy
sam build
sam deploy
```

### Updating Frontend
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://your-bucket-name/ --delete
```

## 🐛 Troubleshooting

### Common Issues

**Lambda Timeout**
- Increase timeout in `template.yaml` (max 15 minutes)
- Reduce number of symbols in configuration
- Check for Yahoo Finance API rate limits

**S3 Access Issues**
- Verify bucket policy allows public read for website
- Check IAM permissions for Lambda function
- Ensure CORS configuration is correct

**Frontend Not Loading**
- Check S3 bucket website configuration
- Verify build files uploaded to correct bucket
- Check browser console for JavaScript errors

**Missing Recommendations**
- Check Lambda logs in CloudWatch for errors
- Verify stock symbols are valid and traded
- Check Yahoo Finance API availability

**Pushover Not Working**
- Verify PUSHOVER_TOKEN and PUSHOVER_USER are set
- Check Pushover app is enabled
- Test with `/config/validate` endpoint first

## 📞 Support and Debugging

For issues and questions:
1. Check CloudWatch logs for Lambda errors
2. Verify API endpoints with health check
3. Test configuration with local development setup
4. Review SAM template for deployment issues

## 🛣️ Enhanced Roadmap

### Implemented Features ✅
- [x] Enhanced recommendation engine with target prices
- [x] Confidence level scoring system
- [x] Reconciliation service for performance tracking
- [x] Chart generation for price analysis
- [x] Enhanced security with API key management
- [x] Purge service for data lifecycle management
- [x] Advanced monitoring and alerting
- [x] Enhanced frontend with real-time updates

### Future Enhancements 🚀
- **Machine Learning Integration**: Advanced prediction models
- **Backtesting Engine**: Historical performance analysis
- **Portfolio Management**: Track multiple portfolios
- **Real-time WebSocket**: Live price updates
- **Mobile Application**: React Native mobile app
- **Advanced Charting**: TradingView integration
- **Social Features**: Community recommendations
- **Multi-market Support**: International exchanges
- **Alternative Data**: News sentiment, social media analysis
- **Risk Management**: Portfolio risk analytics
- **Automated Trading**: Broker integration (paper trading)
- **Custom Indicators**: User-defined technical indicators
- **API Marketplace**: Third-party integrations

## 📄 License

This project is provided as-is for educational purposes. Feel free to fork, modify, and improve according to your needs.
