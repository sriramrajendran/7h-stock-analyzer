#!/usr/bin/env python3
"""
Portfolio Data Forklift Module
Imports portfolio data from Robinhood, E-Trade, and other brokerages
"""

import pandas as pd
import json
import csv
import os
from typing import List, Dict, Optional, Union
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PortfolioForklift:
    """Data forklift for importing portfolio data from various sources"""
    
    def __init__(self):
        self.supported_brokers = ['robinhood', 'etrade', 'csv', 'fidelity', 'schwab']
        self.portfolio_data = []
        
    def import_from_robinhood(self, file_path: str) -> Dict:
        """
        Import portfolio data from Robinhood CSV export
        Expected columns: Symbol, Quantity, Average Buy Price, Current Price, Equity, etc.
        """
        try:
            # Read CSV with more flexible parsing
            df = pd.read_csv(file_path)
        except Exception as e:
            logger.error(f"Failed to read CSV file: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to read CSV file: {str(e)}',
                'broker': 'robinhood'
            }
        
        try:
            # Validate required columns
            required_columns = ['symbol', 'quantity']
            available_columns = [col.lower() for col in df.columns]
            missing_columns = [col for col in required_columns if col not in available_columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Missing required columns: {missing_columns}. Found columns: {available_columns}',
                    'broker': 'robinhood'
                }
            
            # Normalize column names (handle spaces and case)
            df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
            
            portfolio = []
            for index, row in df.iterrows():
                try:
                    # Skip rows without essential data
                    symbol = row.get('symbol')
                    quantity = row.get('quantity')
                    
                    if pd.isna(symbol) or pd.isna(quantity) or quantity <= 0:
                        continue
                    
                    # Clean symbol
                    symbol = str(symbol).upper().strip()
                    if not symbol:
                        continue
                    
                    # Get default values properly to avoid nested parentheses
                    avg_cost_default = row.get('average_cost', row.get('cost_basis', 0))
                    price_default = row.get('price', 0)
                    equity_default = row.get('total_value', row.get('value', 0))
                    gain_loss_default = row.get('unrealized_gain_loss', 0)
                    gain_pct_default = row.get('gain_loss_percent', 0)
                    
                    holding = {
                        'symbol': symbol,
                        'quantity': float(quantity),
                        'average_cost': float(row.get('average_buy_price', avg_cost_default)),
                        'current_price': float(row.get('current_price', price_default)),
                        'equity_value': float(row.get('equity', equity_default)),
                        'gain_loss': float(row.get('gain_loss', gain_loss_default)),
                        'gain_loss_pct': float(row.get('gain_loss_pct', gain_pct_default)),
                        'broker': 'robinhood',
                        'import_date': datetime.now().isoformat()
                    }
                    portfolio.append(holding)
                    
                except Exception as row_error:
                    logger.warning(f"Skipping row {index} due to error: {str(row_error)}")
                    continue
            
            if not portfolio:
                return {
                    'success': False,
                    'error': 'No valid portfolio data found in CSV. Check file format.',
                    'broker': 'robinhood'
                }
            
            return {
                'success': True,
                'portfolio': portfolio,
                'broker': 'robinhood',
                'total_holdings': len(portfolio)
            }
            
        except Exception as e:
            logger.error(f"Error importing Robinhood data: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to import Robinhood data: {str(e)}',
                'broker': 'robinhood'
            }
    
    def import_from_etrade(self, file_path: str) -> Dict:
        """
        Import portfolio data from E-Trade CSV export
        Expected columns: Symbol, Quantity, Price, Value, Cost Basis, etc.
        """
        try:
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_columns = ['Symbol', 'Quantity']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    'success': False,
                    'error': f'Missing required columns: {missing_columns}',
                    'broker': 'etrade'
                }
            
            portfolio = []
            for _, row in df.iterrows():
                if pd.notna(row.get('Symbol')) and row.get('Quantity', 0) > 0:
                    holding = {
                        'symbol': row['Symbol'].upper(),
                        'quantity': float(row.get('Quantity', 0)),
                        'average_cost': float(row.get('Cost Basis', 0)) / float(row.get('Quantity', 1)) if row.get('Quantity', 0) > 0 else 0,
                        'current_price': float(row.get('Price', 0)),
                        'equity_value': float(row.get('Value', 0)),
                        'gain_loss': float(row.get('Unrealized Gain/Loss', 0)),
                        'broker': 'etrade',
                        'import_date': datetime.now().isoformat()
                    }
                    
                    # Calculate percentage if not provided
                    if holding['average_cost'] > 0:
                        holding['gain_loss_pct'] = ((holding['current_price'] - holding['average_cost']) / holding['average_cost']) * 100
                    else:
                        holding['gain_loss_pct'] = 0
                    
                    portfolio.append(holding)
            
            return {
                'success': True,
                'portfolio': portfolio,
                'broker': 'etrade',
                'total_holdings': len(portfolio)
            }
            
        except Exception as e:
            logger.error(f"Error importing E-Trade data: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to import E-Trade data: {str(e)}',
                'broker': 'etrade'
            }
    
    def import_from_csv(self, file_path: str, column_mapping: Dict[str, str] = None) -> Dict:
        """
        Import portfolio data from generic CSV with custom column mapping
        """
        try:
            df = pd.read_csv(file_path)
            
            # Default column mapping
            default_mapping = {
                'symbol': ['symbol', 'ticker', 'Symbol', 'Ticker'],
                'quantity': ['quantity', 'qty', 'Quantity', 'Shares'],
                'average_cost': ['average_cost', 'avg_cost', 'cost_basis', 'Average Cost'],
                'current_price': ['current_price', 'price', 'Price', 'Last Price']
            }
            
            if column_mapping:
                default_mapping.update(column_mapping)
            
            # Find actual column names
            actual_columns = {}
            for field, possible_names in default_mapping.items():
                for col in df.columns:
                    if col in possible_names:
                        actual_columns[field] = col
                        break
                
                if field not in actual_columns:
                    return {
                        'success': False,
                        'error': f'Could not find column for {field}. Expected one of: {possible_names}',
                        'broker': 'csv'
                    }
            
            portfolio = []
            for _, row in df.iterrows():
                if pd.notna(row.get(actual_columns['symbol'])) and row.get(actual_columns['quantity'], 0) > 0:
                    holding = {
                        'symbol': str(row[actual_columns['symbol']]).upper(),
                        'quantity': float(row.get(actual_columns['quantity'], 0)),
                        'average_cost': float(row.get(actual_columns.get('average_cost', ''), 0)),
                        'current_price': float(row.get(actual_columns.get('current_price', ''), 0)),
                        'broker': 'csv',
                        'import_date': datetime.now().isoformat()
                    }
                    
                    # Calculate derived values
                    if holding['current_price'] > 0:
                        holding['equity_value'] = holding['quantity'] * holding['current_price']
                    else:
                        holding['equity_value'] = 0
                    
                    if holding['average_cost'] > 0:
                        holding['gain_loss'] = (holding['current_price'] - holding['average_cost']) * holding['quantity']
                        holding['gain_loss_pct'] = ((holding['current_price'] - holding['average_cost']) / holding['average_cost']) * 100
                    else:
                        holding['gain_loss'] = 0
                        holding['gain_loss_pct'] = 0
                    
                    portfolio.append(holding)
            
            return {
                'success': True,
                'portfolio': portfolio,
                'broker': 'csv',
                'total_holdings': len(portfolio)
            }
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to import CSV data: {str(e)}',
                'broker': 'csv'
            }
    
    def validate_portfolio_data(self, portfolio_data: List[Dict]) -> Dict:
        """Validate and clean portfolio data"""
        if not portfolio_data:
            return {
                'valid': False,
                'error': 'No portfolio data to validate'
            }
        
        validated_data = []
        errors = []
        
        for i, holding in enumerate(portfolio_data):
            try:
                # Required fields
                if not holding.get('symbol'):
                    errors.append(f"Holding {i+1}: Missing symbol")
                    continue
                
                if holding.get('quantity', 0) <= 0:
                    errors.append(f"Holding {i+1}: Invalid quantity for {holding['symbol']}")
                    continue
                
                # Clean and standardize
                clean_holding = {
                    'symbol': holding['symbol'].upper().strip(),
                    'quantity': float(holding['quantity']),
                    'average_cost': float(holding.get('average_cost', 0)),
                    'current_price': float(holding.get('current_price', 0)),
                    'equity_value': float(holding.get('equity_value', 0)),
                    'gain_loss': float(holding.get('gain_loss', 0)),
                    'gain_loss_pct': float(holding.get('gain_loss_pct', 0)),
                    'broker': holding.get('broker', 'unknown'),
                    'import_date': holding.get('import_date', datetime.now().isoformat())
                }
                
                # Recalculate if needed
                if clean_holding['current_price'] > 0 and clean_holding['equity_value'] == 0:
                    clean_holding['equity_value'] = clean_holding['quantity'] * clean_holding['current_price']
                
                if clean_holding['average_cost'] > 0 and clean_holding['gain_loss'] == 0:
                    clean_holding['gain_loss'] = (clean_holding['current_price'] - clean_holding['average_cost']) * clean_holding['quantity']
                    clean_holding['gain_loss_pct'] = ((clean_holding['current_price'] - clean_holding['average_cost']) / clean_holding['average_cost']) * 100
                
                validated_data.append(clean_holding)
                
            except Exception as e:
                errors.append(f"Holding {i+1}: {str(e)}")
        
        return {
            'valid': len(errors) == 0,
            'validated_data': validated_data,
            'errors': errors,
            'total_processed': len(portfolio_data),
            'total_valid': len(validated_data)
        }
    
    def save_portfolio_to_config(self, portfolio_data: List[Dict], config_file: str = 'input/config_portfolio.txt') -> Dict:
        """Save imported portfolio symbols to config file"""
        try:
            # Extract unique symbols
            symbols = list(set([holding['symbol'] for holding in portfolio_data if holding.get('symbol')]))
            symbols.sort()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # Write to config file
            with open(config_file, 'w') as f:
                f.write("# Portfolio stocks imported from brokerage\n")
                f.write(f"# Import date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                for symbol in symbols:
                    f.write(f"{symbol}\n")
            
            return {
                'success': True,
                'symbols_saved': len(symbols),
                'config_file': config_file,
                'symbols': symbols
            }
            
        except Exception as e:
            logger.error(f"Error saving portfolio to config: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to save portfolio: {str(e)}'
            }
    
    def get_portfolio_summary(self, portfolio_data: List[Dict]) -> Dict:
        """Generate summary statistics for imported portfolio"""
        if not portfolio_data:
            return {'error': 'No portfolio data available'}
        
        total_equity = sum(h.get('equity_value', 0) for h in portfolio_data)
        total_cost = sum(h.get('average_cost', 0) * h.get('quantity', 0) for h in portfolio_data)
        total_gain_loss = sum(h.get('gain_loss', 0) for h in portfolio_data)
        
        # Top holdings by value
        top_holdings = sorted(portfolio_data, key=lambda x: x.get('equity_value', 0), reverse=True)[:10]
        
        # Performance distribution
        gainers = [h for h in portfolio_data if h.get('gain_loss', 0) > 0]
        losers = [h for h in portfolio_data if h.get('gain_loss', 0) < 0]
        
        return {
            'total_holdings': len(portfolio_data),
            'total_equity_value': round(total_equity, 2),
            'total_cost_basis': round(total_cost, 2),
            'total_gain_loss': round(total_gain_loss, 2),
            'overall_return_pct': round((total_gain_loss / total_cost * 100) if total_cost > 0 else 0, 2),
            'gainers_count': len(gainers),
            'losers_count': len(losers),
            'top_holdings': top_holdings,
            'best_performer': max(portfolio_data, key=lambda x: x.get('gain_loss_pct', 0)) if portfolio_data else None,
            'worst_performer': min(portfolio_data, key=lambda x: x.get('gain_loss_pct', 0)) if portfolio_data else None
        }
    
    def auto_detect_broker(self, file_path: str) -> str:
        """Auto-detect broker based on file content and naming"""
        filename = os.path.basename(file_path).lower()
        
        # Check filename patterns
        if 'robinhood' in filename or 'rh' in filename:
            return 'robinhood'
        elif 'etrade' in filename or 'e-trade' in filename:
            return 'etrade'
        elif 'fidelity' in filename:
            return 'fidelity'
        elif 'schwab' in filename:
            return 'schwab'
        
        # Check CSV headers
        try:
            df = pd.read_csv(file_path, nrows=1)
            columns = [col.lower() for col in df.columns]
            
            if 'symbol' in columns and 'quantity' in columns:
                if 'average_buy_price' in columns:
                    return 'robinhood'
                elif 'cost basis' in columns:
                    return 'etrade'
                else:
                    return 'csv'
        except:
            pass
        
        return 'csv'  # Default to generic CSV
    
    def import_portfolio(self, file_path: str, broker: str = None, column_mapping: Dict[str, str] = None) -> Dict:
        """Main method to import portfolio from file"""
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': f'File not found: {file_path}'
            }
        
        # Auto-detect broker if not specified
        if not broker:
            broker = self.auto_detect_broker(file_path)
        
        # Import based on broker
        if broker == 'robinhood':
            result = self.import_from_robinhood(file_path)
        elif broker == 'etrade':
            result = self.import_from_etrade(file_path)
        else:
            result = self.import_from_csv(file_path, column_mapping)
        
        if result['success']:
            # Validate the imported data
            validation = self.validate_portfolio_data(result['portfolio'])
            
            if validation['valid']:
                result['validated_portfolio'] = validation['validated_data']
                result['summary'] = self.get_portfolio_summary(validation['validated_data'])
            else:
                result['validation_errors'] = validation['errors']
        
        return result
