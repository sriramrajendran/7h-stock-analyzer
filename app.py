#!/usr/bin/env python3
"""
Flask Web Application for Stock Technical Analysis
"""

from flask import Flask, render_template, request, jsonify
from core.stock_analyzer import StockAnalyzer
from core.batch_stock_analyzer import BatchStockAnalyzer
from core.portfolio_forklift import PortfolioForklift
from core.portfolio_storage import PortfolioStorage
import json
import os
from typing import List, Dict
import numpy as np

from core.in_app_scheduler import start_background_schedulers


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle NumPy types and booleans"""
    
    def default(self, obj):
        if isinstance(obj, bool) or isinstance(obj, np.bool_):
            return str(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def convert_bools_to_strings(obj):
    """
    Recursively convert boolean values and NumPy types to JSON-serializable types
    """
    import numpy as np
    
    if isinstance(obj, bool) or isinstance(obj, np.bool_):
        return str(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_bools_to_strings(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_bools_to_strings(item) for item in obj]
    else:
        return obj

app = Flask(__name__, template_folder='assets', static_folder='assets')
app.config['JSON_SORT_KEYS'] = False
app.json_encoder_class = CustomJSONEncoder

CONFIG_PORTFOLIO_FILE = 'input/config_portfolio.txt'
CONFIG_WATCHLIST_FILE = 'input/config_watchlist.txt'
CONFIG_US_STOCKS_FILE = 'input/config_us_stocks.txt'
CONFIG_ETFS_FILE = 'input/config_etfs.txt'


def load_stocks_from_config(filename: str) -> List[str]:
    """Load stock symbols from config file"""
    stocks = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        stocks.append(line.upper())
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    return stocks


@app.route('/')
def index():
    """Home page - Portfolio stocks"""
    return render_template('index.html', page_type='portfolio')


@app.route('/watchlist')
def watchlist():
    """Watchlist page"""
    return render_template('index.html', page_type='watchlist')


@app.route('/market')
def market():
    """US Market analysis page"""
    return render_template('index.html', page_type='market')


@app.route('/etf')
def etf():
    """ETF/Index analysis page"""
    return render_template('index.html', page_type='etf')


@app.route('/api/config_stocks', methods=['GET'])
def get_config_stocks():
    """Get stocks from config files"""
    try:
        config_type = request.args.get('type', 'portfolio')  # 'portfolio', 'watchlist', 'us_stocks', or 'etfs'
        
        if config_type == 'watchlist':
            filename = CONFIG_WATCHLIST_FILE
        elif config_type == 'us_stocks':
            filename = CONFIG_US_STOCKS_FILE
        elif config_type == 'etfs':
            filename = CONFIG_ETFS_FILE
        else:
            filename = CONFIG_PORTFOLIO_FILE
        
        stocks = load_stocks_from_config(filename)
        
        return jsonify({
            'success': True,
            'type': config_type,
            'stocks': stocks
        })
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/analyze', methods=['POST'])
def analyze_stock():
    """Analyze a single stock"""
    try:
        data = request.get_json()
        symbol = data.get('symbol', '').upper().strip()
        period = data.get('period', '1y')
        
        if not symbol:
            return jsonify({'error': 'Stock symbol is required'}), 400
        
        analyzer = StockAnalyzer(symbol, period)
        
        if not analyzer.fetch_data():
            return jsonify({'error': f'Failed to fetch data for {symbol}'}), 404
        
        analyzer.calculate_indicators()
        summary = analyzer.get_summary()
        recommendation = analyzer.get_recommendation()
        
        result = {
            'success': True,
            'symbol': symbol,
            'summary': convert_bools_to_strings(summary),
            'recommendation': convert_bools_to_strings(recommendation)
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/analyze_portfolio', methods=['POST'])
def analyze_portfolio():
    """Analyze multiple stocks for portfolio recommendations using batch processing"""
    try:
        data = request.get_json()
        symbols_str = data.get('symbols', '')
        period = data.get('period', '6mo')  # Changed default to 6mo for more accurate data
        top_n = int(data.get('top_n', 10))
        
        if not symbols_str:
            return jsonify({'error': 'Stock symbols are required'}), 400
        
        # Parse symbols (comma or space separated)
        symbols = [s.strip().upper() for s in symbols_str.replace(',', ' ').split() if s.strip()]
        
        if not symbols:
            return jsonify({'error': 'No valid stock symbols provided'}), 400
        
        # Use batch analyzer for efficient processing
        batch_analyzer = BatchStockAnalyzer(symbols, period, batch_size=30)
        analysis_results = batch_analyzer.analyze_all()
        
        results = []
        failed_symbols = []
        
        for symbol in symbols:
            if symbol in analysis_results:
                result = analysis_results[symbol]
                if 'error' in result:
                    failed_symbols.append(f"{symbol} ({result['error']})")
                else:
                    summary = result['summary']
                    recommendation = result['recommendation']
                    fundamental = summary.get('fundamental', {})
                    
                    results.append({
                        'symbol': symbol,
                        'company': summary.get('company_name', 'N/A'),
                        'price': round(summary.get('current_price', 0), 2),
                        'change': round(summary.get('price_change_pct', 0), 2),
                        'change_1d': round(summary.get('price_change_1d_pct', 0), 2),
                        'change_1w': round(summary.get('price_change_1w_pct', 0), 2),
                        'change_1m': round(summary.get('price_change_1m_pct', 0), 2),
                        'change_6m': round(summary.get('price_change_6m_pct', 0), 2),
                        'change_1y': round(summary.get('price_change_1y_pct', 0), 2),
                        'rsi': round(summary.get('rsi', 0), 2),
                        'macd': round(summary.get('macd', 0), 2),
                        'sma_20': round(summary.get('sma_20', 0), 2),
                        'sma_50': round(summary.get('sma_50', 0), 2),
                        'vcp_pattern': convert_bools_to_strings(summary.get('vcp_pattern', {})),
                        'rsi_divergence': convert_bools_to_strings(summary.get('rsi_divergence', {})),
                        'macd_divergence': convert_bools_to_strings(summary.get('macd_divergence', {})),
                        'enhanced_crossovers': convert_bools_to_strings(summary.get('enhanced_crossovers', {})),
                        'breakout_setup': convert_bools_to_strings(summary.get('breakout_setup', {})),
                        'recommendation': recommendation['recommendation'],
                        'score': recommendation['score'],
                        'reasoning': recommendation['reasoning'],
                        'fundamental': convert_bools_to_strings(fundamental)
                    })
            else:
                failed_symbols.append(symbol)
        
        if not results:
            # Check if all symbols failed due to authentication/API issues
            if len(failed_symbols) == len(symbols):
                return jsonify({
                    'error': 'Unable to fetch stock data. This may be due to Yahoo Finance API issues or network problems. Please try again in a few minutes.',
                    'failed_symbols': failed_symbols,
                    'suggestion': 'Check your internet connection and try refreshing the page. If the issue persists, some symbols may be temporarily unavailable.'
                }), 503  # Service Unavailable
            else:
                return jsonify({'error': 'No stocks were successfully analyzed'}), 404
        
        # Sort by score
        results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Separate BUY and SELL
        buy_stocks = [r for r in results_sorted if 'BUY' in r['recommendation']]
        sell_stocks = sorted([r for r in results_sorted if 'SELL' in r['recommendation']], 
                            key=lambda x: x['score'])
        hold_stocks = [r for r in results_sorted if r['recommendation'] == 'HOLD']
        
        # Calculate statistics
        avg_score = sum(r['score'] for r in results) / len(results) if results else 0
        highest = results_sorted[0] if results_sorted else None
        lowest = results_sorted[-1] if results_sorted else None
        
        portfolio_result = {
            'success': True,
            'total_analyzed': len(results),
            'buy_stocks': buy_stocks[:top_n],
            'sell_stocks': sell_stocks[:top_n],
            'hold_stocks': hold_stocks,
            'failed_symbols': failed_symbols,
            'summary': {
                'total': len(results),
                'buy_count': len(buy_stocks),
                'sell_count': len(sell_stocks),
                'hold_count': len(hold_stocks),
                'avg_score': round(avg_score, 2),
                'highest': highest,
                'lowest': lowest
            }
        }
        
        return jsonify(convert_bools_to_strings(portfolio_result))
    
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


# Load major stocks and ETFs from config files
MAJOR_US_STOCKS = load_stocks_from_config(CONFIG_US_STOCKS_FILE)
MAJOR_ETFS = load_stocks_from_config(CONFIG_ETFS_FILE)


@app.route('/analyze_market', methods=['POST'])
def analyze_market():
    """Analyze US market stocks using batch processing and return top BUY recommendations"""
    try:
        data = request.get_json()
        period = data.get('period', '1y')
        top_n = int(data.get('top_n', 10))
        
        # Use batch analyzer for efficient processing
        batch_analyzer = BatchStockAnalyzer(MAJOR_US_STOCKS, period, batch_size=40)
        analysis_results = batch_analyzer.analyze_all()
        
        results = []
        failed_symbols = []
        
        for symbol in MAJOR_US_STOCKS:
            if symbol in analysis_results:
                result = analysis_results[symbol]
                if 'error' in result:
                    failed_symbols.append(f"{symbol} ({result['error']})")
                else:
                    summary = result['summary']
                    recommendation = result['recommendation']
                    
                    # Only include BUY recommendations
                    if 'BUY' in recommendation['recommendation']:
                        fundamental = summary.get('fundamental', {})
                        results.append({
                            'symbol': symbol,
                            'company': summary.get('company_name', 'N/A'),
                            'price': round(summary.get('current_price', 0), 2),
                            'change': round(summary.get('price_change_pct', 0), 2),
                            'change_1d': round(summary.get('price_change_1d_pct', 0), 2),
                            'change_1w': round(summary.get('price_change_1w_pct', 0), 2),
                            'change_1m': round(summary.get('price_change_1m_pct', 0), 2),
                            'change_6m': round(summary.get('price_change_6m_pct', 0), 2),
                            'change_1y': round(summary.get('price_change_1y_pct', 0), 2),
                            'rsi': round(summary.get('rsi', 0), 2),
                            'vcp_pattern': convert_bools_to_strings(summary.get('vcp_pattern', {})),
                            'rsi_divergence': convert_bools_to_strings(summary.get('rsi_divergence', {})),
                            'macd_divergence': convert_bools_to_strings(summary.get('macd_divergence', {})),
                            'enhanced_crossovers': convert_bools_to_strings(summary.get('enhanced_crossovers', {})),
                            'breakout_setup': convert_bools_to_strings(summary.get('breakout_setup', {})),
                            'recommendation': recommendation['recommendation'],
                            'score': recommendation['score'],
                            'reasoning': recommendation['reasoning'],
                            'fundamental': convert_bools_to_strings(fundamental)
                        })
            else:
                failed_symbols.append(symbol)
        
        if not results:
            # Check if this is likely an API issue
            if len(failed_symbols) >= len(MAJOR_US_STOCKS) * 0.8:  # If 80% or more failed
                return jsonify({
                    'error': 'Unable to fetch market data. This may be due to Yahoo Finance API issues or network problems. Please try again in a few minutes.',
                    'failed_symbols': failed_symbols,
                    'suggestion': 'Market data temporarily unavailable. Check your internet connection and try refreshing the page.'
                }), 503
            else:
                return jsonify({'error': 'No BUY recommendations found in US market'}), 404
        
        # Sort by score (highest first) and take top N
        results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)[:top_n]
        
        response_data = {
            'success': True,
            'total_analyzed': len(MAJOR_US_STOCKS),
            'buy_recommendations': results_sorted,
            'failed_symbols': failed_symbols
        }
        
        return jsonify(convert_bools_to_strings(response_data))
    
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/import_portfolio')
def import_portfolio_page():
    """Portfolio import page"""
    return render_template('index.html', page_type='import_portfolio')


@app.route('/api/import_portfolio', methods=['POST'])
def import_portfolio_api():
    """Import portfolio from uploaded file"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400
        
        # Save uploaded file temporarily
        temp_path = os.path.join('temp', file.filename)
        os.makedirs('temp', exist_ok=True)
        file.save(temp_path)
        
        # Get broker type from form or auto-detect
        broker = request.form.get('broker', 'auto')
        save_to_storage = request.form.get('save_to_storage', 'true') == 'true'
        save_to_config = request.form.get('save_to_config', 'false') == 'true'
        
        # Initialize forklift and import
        forklift = PortfolioForklift()
        storage = PortfolioStorage()
        
        if broker == 'auto':
            result = forklift.import_portfolio(temp_path)
        else:
            result = forklift.import_portfolio(temp_path, broker=broker)
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if result['success']:
            # Save to persistent storage if requested
            if save_to_storage and 'validated_portfolio' in result:
                storage_result = storage.save_portfolio_data(
                    result['validated_portfolio'], 
                    result['broker'], 
                    file.filename
                )
                result['storage_save'] = storage_result
            
            # Update config file if requested
            if save_to_config and 'validated_portfolio' in result:
                config_result = forklift.save_portfolio_to_config(result['validated_portfolio'])
                result['config_save'] = config_result
            elif save_to_config and 'storage_save' in result and result['storage_save']['success']:
                # Update config from storage
                config_result = storage.update_portfolio_config()
                result['config_save'] = config_result
            
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500


@app.route('/api/portfolio_summary', methods=['GET'])
def get_portfolio_summary():
    """Get summary of current portfolio"""
    try:
        storage = PortfolioStorage()
        storage_info = storage.get_storage_info()
        
        if not storage_info['has_data']:
            return jsonify({'error': 'No portfolio data found'}), 404
        
        # Load portfolio data
        portfolio_result = storage.load_portfolio_data()
        if not portfolio_result['success']:
            return jsonify({'error': portfolio_result['error']}), 500
        
        portfolio_data = portfolio_result['portfolio_data']
        
        # Create summary using forklift
        forklift = PortfolioForklift()
        summary = forklift.get_portfolio_summary(portfolio_data)
        
        # Add storage info
        summary['storage_info'] = storage_info
        summary['symbols'] = [h['symbol'] for h in portfolio_data]
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/api/portfolio_data', methods=['GET'])
def get_portfolio_data():
    """Get stored portfolio data"""
    try:
        storage = PortfolioStorage()
        result = storage.load_portfolio_data()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/api/portfolio_data', methods=['DELETE'])
def clear_portfolio_data():
    """Clear stored portfolio data"""
    try:
        storage = PortfolioStorage()
        result = storage.clear_portfolio_data()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/api/portfolio_config', methods=['POST'])
def update_portfolio_config():
    """Update portfolio config from stored data"""
    try:
        storage = PortfolioStorage()
        result = storage.update_portfolio_config()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


@app.route('/analyze_etf', methods=['POST'])
def analyze_etf():
    """Analyze ETFs/Indexes using batch processing and return top BUY recommendations"""
    try:
        data = request.get_json()
        period = data.get('period', '1y')
        top_n = int(data.get('top_n', 10))
        
        # Use batch analyzer for efficient processing
        batch_analyzer = BatchStockAnalyzer(MAJOR_ETFS, period, batch_size=30)
        analysis_results = batch_analyzer.analyze_all()
        
        results = []
        failed_symbols = []
        
        for symbol in MAJOR_ETFS:
            if symbol in analysis_results:
                result = analysis_results[symbol]
                if 'error' in result:
                    failed_symbols.append(f"{symbol} ({result['error']})")
                else:
                    summary = result['summary']
                    recommendation = result['recommendation']
                    
                    # Only include BUY recommendations
                    if 'BUY' in recommendation['recommendation']:
                        fundamental = summary.get('fundamental', {})
                        results.append({
                            'symbol': symbol,
                            'company': summary.get('company_name', 'N/A'),
                            'price': round(summary.get('current_price', 0), 2),
                            'change': round(summary.get('price_change_pct', 0), 2),
                            'change_1d': round(summary.get('price_change_1d_pct', 0), 2),
                            'change_1w': round(summary.get('price_change_1w_pct', 0), 2),
                            'change_1m': round(summary.get('price_change_1m_pct', 0), 2),
                            'change_6m': round(summary.get('price_change_6m_pct', 0), 2),
                            'change_1y': round(summary.get('price_change_1y_pct', 0), 2),
                            'rsi': round(summary.get('rsi', 0), 2),
                            'vcp_pattern': convert_bools_to_strings(summary.get('vcp_pattern', {})),
                            'rsi_divergence': convert_bools_to_strings(summary.get('rsi_divergence', {})),
                            'macd_divergence': convert_bools_to_strings(summary.get('macd_divergence', {})),
                            'enhanced_crossovers': convert_bools_to_strings(summary.get('enhanced_crossovers', {})),
                            'breakout_setup': convert_bools_to_strings(summary.get('breakout_setup', {})),
                            'recommendation': recommendation['recommendation'],
                            'score': recommendation['score'],
                            'reasoning': recommendation['reasoning'],
                            'fundamental': convert_bools_to_strings(fundamental)
                        })
            else:
                failed_symbols.append(symbol)
        
        if not results:
            # Check if this is likely an API issue
            if len(failed_symbols) >= len(MAJOR_ETFS) * 0.8:  # If 80% or more failed
                return jsonify({
                    'error': 'Unable to fetch ETF data. This may be due to Yahoo Finance API issues or network problems. Please try again in a few minutes.',
                    'failed_symbols': failed_symbols,
                    'suggestion': 'ETF data temporarily unavailable. Check your internet connection and try refreshing the page.'
                }), 503
            else:
                return jsonify({'error': 'No BUY recommendations found in ETFs'}), 404
        
        # Sort by score (highest first) and take top N
        results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)[:top_n]
        
        response_data = {
            'success': True,
            'total_analyzed': len(MAJOR_ETFS),
            'buy_recommendations': results_sorted,
            'failed_symbols': failed_symbols
        }
        
        return jsonify(convert_bools_to_strings(response_data))
    
    except Exception as e:
        return jsonify({'error': convert_bools_to_strings(str(e))}), 500


if __name__ == '__main__':
    enable_alerts = os.getenv('ALERTS_ENABLE', '').strip().lower() in {'1', 'true', 'yes', 'y', 'on'}
    is_reloader_child = os.getenv('WERKZEUG_RUN_MAIN') == 'true'

    if enable_alerts and (not app.debug or is_reloader_child):
        start_background_schedulers()

    app.run(debug=True, host='0.0.0.0', port=80)

