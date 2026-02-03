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
├── infra/                     # Infrastructure and deployment
│   ├── template.yaml         # AWS SAM infrastructure template
│   ├── scripts/              # Deployment and build scripts
│   │   ├── deploy.sh        # Main deployment script
│   │   ├── build_layer.sh   # Lambda layer build script
│   │   ├── build_package.sh # Lambda packaging script
│   │   └── test_local.sh    # Local testing script
│   └── env.example          # Environment variables template
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
- Pushover account (optional, for notifications)

### 1. Clone and Setup
```bash
git clone <repository>
cd 7h-stock-analyzer
```

### 2. Deploy Infrastructure

```bash
# Deploy with AWS SAM (guided mode for first time)
sam deploy --guided

# Or use the quick deployment script
chmod +x infra/scripts/deploy.sh
./infra/scripts/deploy.sh
```

This will:
- Build Lambda layer and package
- Deploy CloudFormation stack
- Configure all resources (Lambda, EventBridge, S3, API Gateway)
- Set up monitoring and alarms
- Output API endpoints and S3 bucket URL

### 3. Configure Environment Variables

Set these in the Lambda function console or via SAM parameters:
- `PUSHOVER_TOKEN`: Your Pushover app token (optional)
- `PUSHOVER_USER`: Your Pushover user key (optional)
- `S3_BUCKET_NAME`: Your S3 bucket name (auto-configured)
- `ENABLE_NOTIFICATIONS`: Set to "true" to enable Pushover alerts
- `ALERT_EMAIL`: Email for CloudWatch alerts (optional)

### 4. Configure and Deploy Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
cp infra/env.example .env.local
# Edit .env.local with your deployed values:
# - REACT_APP_S3_BUCKET: From deployment output
# - REACT_APP_API_BASE_URL: From deployment output  
# - REACT_APP_S3_REGION: Your AWS region

# Build for production
npm run build

# Upload to S3 (replace with your bucket name from deployment)
aws s3 sync dist/ s3://your-bucket-name/ --delete
```

### 5. Test the Application

1. **Health Check**: `https://your-api-gateway-url.com/health`
2. **Manual Run**: `POST https://your-api-gateway-url.com/run-now`
3. **Web Interface**: `http://your-bucket-name.s3-website-us-east-1.amazonaws.com`
4. **Test Notifications**: `POST https://your-api-gateway-url.com/notifications/test`

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

## �️ Detailed Deployment Options

### Manual Deployment Steps

#### Build Lambda Layer
```bash
./infra/scripts/build_layer.sh
```

#### Build Lambda Package
```bash
./infra/scripts/build_package.sh
```

#### Deploy with SAM (Advanced)
```bash
sam deploy \
    --template-file infra/template.yaml \
    --stack-name 7h-stock-analyzer \
    --region us-east-1 \
    --parameter-overrides \
        Environment=prod \
        EnableVpc=false \
    --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
    --no-confirm-changeset
```

### Environment Configuration

#### Backend Environment Variables
```bash
# Required
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name

# Optional (Notifications)
PUSHOVER_TOKEN=your_app_token
PUSHOVER_USER=your_user_key
ENABLE_NOTIFICATIONS=true
ALERT_EMAIL=alerts@example.com

# Performance
DEFAULT_PERIOD=6mo
BATCH_SIZE=50
MAX_RETRIES=3
REQUEST_TIMEOUT=30
```

#### Frontend Environment Variables (.env.local)
```bash
# Copy from infrastructure template
cp infra/env.example frontend/.env.local

# Edit with your deployed values:
REACT_APP_S3_BUCKET=your-bucket-name
REACT_APP_API_BASE_URL=https://your-api-gateway-url.com
REACT_APP_S3_REGION=us-east-1
```

## 📊 S3 Data Structure

```
s3://bucket/
├── data/
│   ├── latest.json          # Latest recommendations
│   └── daily/
│       ├── 2024-01-01.json  # Daily snapshots
│       └── ...
├── config/
│   ├── watchlist.json       # Watchlist configuration
│   ├── portfolio.json       # Portfolio configuration
│   ├── us_stocks.json       # US stocks configuration
│   └── etfs.json           # ETFs configuration
├── recon/
│   └── daily/              # Daily reconciliation data
├── charts/                 # Price chart images
└── public/                 # Static website files
```

## 🔒 Enhanced Security Configuration

### Lambda Security
- IAM roles with minimal permissions
- VPC isolation (optional)
- Environment variable encryption
- X-Ray tracing enabled

### S3 Security
- Server-side encryption (AES256)
- Public access blocked for data buckets
- Versioning enabled
- Lifecycle policies for cost optimization
- Bucket policies for least privilege access

### API Gateway Security
- Throttling limits (100 requests per minute)
- CORS configuration
- Request validation
- API keys (optional)
- WAF integration (optional)

## 💰 Cost Optimization Details

### Lambda Configuration
- **Memory**: 1024MB (adjustable)
- **Timeout**: 5 minutes (max 15)
- **Reserved Concurrency**: 5
- **Layer Reuse**: Shared dependencies

### S3 Optimization
- **Lifecycle Policies**: 
  - Transition to Standard-IA after 30 days
  - Transition to Glacier after 90 days
  - Delete after 1000 days
- **Intelligent Tiering**: Automatic cost optimization
- **Compression**: JSON data compression

### Monitoring Costs
- **CloudWatch Logs**: 14-day retention
- **Metrics**: Custom metrics for recommendations
- **Alarms**: Cost and performance alerts
- **Dashboard**: Pre-built monitoring dashboard

## 🐛 Enhanced Troubleshooting

### Common Issues and Solutions

#### Lambda Timeout Issues
```bash
# Check current configuration
sam logs -n StockAnalyzerFunction --tail

# Solutions:
# 1. Increase timeout in template.yaml
# 2. Reduce batch size in configuration
# 3. Monitor Yahoo Finance API rate limits
# 4. Optimize symbol processing
```

#### S3 Access Issues
```bash
# Verify bucket policy
aws s3api get-bucket-policy --bucket your-bucket

# Check IAM permissions
aws iam get-role-policy --role-name YourLambdaRole --policy-name YourPolicy

# Test S3 access
aws s3 ls s3://your-bucket/
```

#### Frontend Loading Issues
```bash
# Check S3 website configuration
aws s3api get-bucket-website --bucket your-bucket

# Verify build files
aws s3 ls s3://your-bucket/ --recursive

# Check CORS settings
aws s3api get-bucket-cors --bucket your-bucket
```

#### Pushover Notification Issues
```bash
# Test configuration
curl -X POST https://your-api-gateway-url.com/notifications/test

# Check environment variables
aws lambda get-function-configuration --function-name YourFunction

# Verify Pushover credentials
curl -X POST "https://api.pushover.net/1/users/validate.json" \
  -d "token=YOUR_TOKEN" \
  -d "user=YOUR_USER"
```

### Debug Commands

```bash
# Monitor Lambda logs in real-time
aws logs tail /aws/lambda/stock-analyzer-function --follow

# Test Lambda locally
sam local invoke StockAnalyzerFunction --event events/test-event.json

# Check CloudFormation stack status
aws cloudformation describe-stacks --stack-name 7h-stock-analyzer

# Monitor S3 storage usage
aws s3 ls s3://your-bucket --recursive --human-readable --summarize

# Test API endpoints
aws apigateway test-invoke-method \
  --rest-api-id your-api-id \
  --resource-id your-resource-id \
  --http-method GET \
  --path-with-query-string "/health"
```

## 📅 Maintenance Schedule

### Daily Tasks
- Monitor CloudWatch alarms
- Check recommendation quality
- Review cost metrics
- Verify data freshness

### Weekly Tasks
- Update watchlist configurations
- Review reconciliation data
- Optimize Lambda performance
- Check notification effectiveness

### Monthly Tasks
- Review and rotate API keys
- Update dependencies
- Audit security settings
- Analyze performance trends
- Review cost optimization

### Quarterly Tasks
- Full security audit
- Architecture review
- Disaster recovery testing
- Performance benchmarking

## 🚀 Scaling Considerations

### High Volume Scenarios
- Increase Lambda concurrency limits
- Implement batch processing optimization
- Consider Step Functions for complex workflows
- Add DynamoDB for caching

### Multi-Region Deployment
- Deploy to multiple AWS regions
- Configure Route53 for failover
- Implement S3 cross-region replication
- Set up regional API Gateways

### Enterprise Features
- AWS WAF integration for security
- Lambda authorizers for authentication
- VPC endpoints for private connectivity
- CloudTrail for comprehensive auditing
- Config Rules for compliance monitoring

## � Troubleshooting

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
