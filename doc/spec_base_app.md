# 7H Stock Analyzer - Technical Specification

## Overview
A comprehensive Python-based stock analysis application that provides AI-powered technical analysis, portfolio management, and automated alerting capabilities through a modern web interface.

## Core Features

### 1. Technical Analysis Engine
- **Indicators Calculated:**
  - RSI (Relative Strength Index) - Momentum oscillator
  - MACD (Moving Average Convergence Divergence) - Trend following
  - Simple Moving Averages (SMA 20, 50, 200) - Price trend analysis
  - Exponential Moving Averages (EMA 12, 26) - Weighted trend analysis
  - Bollinger Bands - Volatility and price levels
  - Stochastic Oscillator - Momentum indicator
  - Average True Range (ATR) - Volatility measurement
  - On-Balance Volume (OBV) - Volume-based indicator

- **Recommendation System:**
  - Scoring algorithm: -10 to +10 range
  - Score classifications:
    - ≥ 5: STRONG BUY
    - 2-4: BUY  
    - -1 to 1: HOLD
    - -4 to -2: SELL
    - ≤ -5: STRONG SELL
  - Multi-factor reasoning with detailed explanations

### 2. Web Application Interface
- **Framework:** Flask-based responsive web app
- **Pages:**
  - Portfolio Analysis
  - Watchlist Analysis  
  - US Market Analysis
  - ETF & Index Analysis
  - Single Stock Analysis
  - Import Portfolio

- **UI Features:**
  - Modern gradient design with smooth animations
  - Real-time AJAX analysis
  - Color-coded recommendations (Green/Yellow/Red)
  - Mobile-responsive layout
  - Interactive forms with validation

### 3. Portfolio Management
- **Import Capabilities:**
  - Robinhood CSV export support
  - E-Trade CSV export support
  - Fidelity CSV export support
  - Charles Schwab CSV export support
  - Generic CSV format support
  - Auto-detection of brokerage format

- **Persistent Storage:**
  - JSON-based portfolio data storage
  - CSV backup files
  - Configuration file integration
  - Cross-session data persistence

### 4. Batch Analysis System
- **Efficient Multi-Stock Processing:**
  - Rate limit avoidance through batching
  - Configurable batch sizes (default: 50 symbols)
  - Parallel data fetching
  - Error handling for individual stocks

- **Analysis Modes:**
  - Portfolio batch analysis
  - Market-wide scanning
  - ETF universe analysis
  - Custom symbol lists

### 5. Automated Alert System
- **Pushover Integration:**
  - iPhone/Android notifications
  - Configurable alert thresholds
  - Market hours scheduling
  - ETF daily scanning

- **Alert Types:**
  - BUY signal alerts (score ≥ 3)
  - Portfolio-specific alerts
  - Market-wide opportunity alerts
  - ETF analysis alerts

- **State Management:**
  - Deduplication to avoid repeat alerts
  - Persistent alert state storage
  - Customizable scheduling

### 6. Data Sources & Configuration
- **Market Data:**
  - Yahoo Finance API integration
  - Historical price data
  - Real-time quotes
  - Fundamental data (P/E, market cap, dividends)

- **Configuration Files:**
  - `config_portfolio.txt` - Portfolio symbols
  - `config_watchlist.txt` - Watchlist symbols
  - `config_us_stocks.txt` - US market universe
  - `config_etfs.txt` - ETF symbols
  - `.alerts_state.json` - Alert state persistence

### 7. Technical Architecture
- **Core Modules:**
  - `stock_analyzer.py` - Single stock analysis engine
  - `batch_stock_analyzer.py` - Multi-stock batch processing
  - `portfolio_forklift.py` - Portfolio import system
  - `portfolio_storage.py` - Data persistence layer
  - `alerts_runner.py` - Alert notification system
  - `in_app_scheduler.py` - Background task scheduling

- **Web Components:**
  - `app.py` - Flask application main
  - `assets/index.html` - Main web interface
  - `assets/base.html` - Base template
  - `assets/css/style.css` - Styling
  - `assets/js/main.js` - Client-side functionality

### 8. API Endpoints
- **Analysis Endpoints:**
  - `/analyze_portfolio` - Portfolio batch analysis
  - `/analyze_market` - Market-wide analysis
  - `/analyze_etf` - ETF universe analysis
  - `/analyze_single` - Single stock analysis

- **Portfolio Management:**
  - `/import_portfolio` - Portfolio CSV import
  - `/api/portfolio_data` - Retrieve stored portfolio
  - `/DELETE /api/portfolio_data` - Clear portfolio data
  - `/api/portfolio_summary` - Portfolio summary with storage info

- **Configuration:**
  - `/api/config_stocks` - Stock configuration
  - `/api/config_portfolio` - Portfolio configuration

### 9. Testing Framework
- **Test Categories:**
  - Core functionality tests (`test_stock_analyzer.py`)
  - Web application tests (`test_flask_app.py`)
  - Recommendation engine tests (`test_recommendation_engine.py`)
  - Integration tests (`test_integration.py`)
  - Portfolio import tests (`test_portfolio_forklift.py`)

- **Coverage Areas:**
  - Technical indicator calculations
  - API endpoint functionality
  - Form validation and submission
  - Error handling and edge cases
  - Portfolio import workflows

### 10. Environment Configuration
- **Required Environment Variables:**
  - `ALERTS_ENABLE` - Enable alert system
  - `PUSHOVER_APP_TOKEN` - Pushover app token
  - `PUSHOVER_USER_KEY` - Pushover user key

- **Optional Configuration:**
  - `ALERT_MARKET_MIN_SCORE` - Market alert threshold
  - `ALERT_ETF_MIN_SCORE` - ETF alert threshold
  - `ALERT_MARKET_PORTFOLIO_ONLY` - Portfolio-only alerts
  - `ALERT_MARKET_TOP_N` - Market scan results limit
  - `ALERT_ETF_RUN_HOUR` - Daily ETF scan hour

### 11. Deployment & Operations
- **Server Configuration:**
  - Default port: 80 (configurable)
  - Background schedulers for alerts
  - Graceful error handling
  - Rate limit management

- **Data Persistence:**
  - Portfolio data storage in `input/portfolio_data.json`
  - Alert state in `input/.alerts_state.json`
  - CSV backups for human readability
  - Configuration file integration

### 12. Security & Performance
- **Security Measures:**
  - Input validation and sanitization
  - File upload restrictions
  - Error message sanitization
  - No sensitive data in logs

- **Performance Optimizations:**
  - Batch processing for API efficiency
  - Caching of market data
  - Asynchronous operations
  - Rate limit handling

## Dependencies
- **Core Libraries:**
  - `yfinance` - Market data fetching
  - `pandas` - Data manipulation
  - `numpy` - Numerical operations
  - `ta` - Technical analysis calculations
  - `flask` - Web framework

- **Additional Libraries:**
  - `requests` - HTTP client for alerts
  - `python-dotenv` - Environment variable management
  - `pytest` - Testing framework

## File Structure
```
7H-Stock-Analyzer/
├── app.py                           # Flask web application
├── core/                            # Core analysis modules
│   ├── stock_analyzer.py           # Single stock analysis
│   ├── batch_stock_analyzer.py     # Batch processing
│   ├── portfolio_forklift.py       # Portfolio import
│   ├── portfolio_storage.py        # Data persistence
│   ├── alerts_runner.py            # Alert notifications
│   └── in_app_scheduler.py         # Background tasks
├── assets/                          # Web interface files
│   ├── index.html                  # Main interface
│   ├── base.html                   # Base template
│   ├── css/style.css               # Styling
│   └── js/main.js                  # Client scripts
├── input/                           # Configuration & data
│   ├── config_*.txt                # Symbol lists
│   ├── portfolio_data.json        # Portfolio storage
│   └── .alerts_state.json          # Alert state
├── tests/                           # Test suite
├── doc/                            # Documentation
├── requirements.txt                 # Dependencies
└── .env.example                    # Environment template
```

## Usage Workflow
1. **Setup:** Install dependencies, configure environment
2. **Configuration:** Update symbol lists in input/ directory
3. **Import:** Upload portfolio CSV (optional)
4. **Analysis:** Use web interface for stock analysis
5. **Alerts:** Configure Pushover for notifications
6. **Monitoring:** Review recommendations and alerts

## Extension Points
- Additional technical indicators
- Custom alert channels (email, SMS)
- Database integration for historical data
- Trading API integration
- Advanced charting and visualization
- Machine learning recommendation models