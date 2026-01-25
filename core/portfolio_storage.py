#!/usr/bin/env python3
"""
Portfolio Data Storage Module
Handles persistent storage of imported portfolio data
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional


class PortfolioStorage:
    """Manages persistent storage of portfolio data"""
    
    def __init__(self, storage_dir: str = 'input'):
        self.storage_dir = storage_dir
        self.portfolio_file = os.path.join(storage_dir, 'portfolio_data.json')
        self.portfolio_csv_file = os.path.join(storage_dir, 'imported_portfolio.csv')
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_portfolio_data(self, portfolio_data: List[Dict], broker: str = 'unknown', 
                         source_file: str = None) -> Dict:
        """Save portfolio data to persistent storage"""
        try:
            # Create storage record
            storage_record = {
                'import_date': datetime.now().isoformat(),
                'broker': broker,
                'source_file': source_file,
                'total_holdings': len(portfolio_data),
                'portfolio_data': portfolio_data
            }
            
            # Save as JSON for programmatic access
            with open(self.portfolio_file, 'w') as f:
                json.dump(storage_record, f, indent=2, default=str)
            
            # Save as CSV for human readability and backup
            if portfolio_data:
                df = pd.DataFrame(portfolio_data)
                df.to_csv(self.portfolio_csv_file, index=False)
            
            return {
                'success': True,
                'message': f'Portfolio data saved to {self.portfolio_file}',
                'storage_file': self.portfolio_file,
                'csv_file': self.portfolio_csv_file
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to save portfolio data: {str(e)}'
            }
    
    def load_portfolio_data(self) -> Dict:
        """Load portfolio data from persistent storage"""
        try:
            if not os.path.exists(self.portfolio_file):
                return {
                    'success': False,
                    'error': 'No saved portfolio data found',
                    'portfolio_data': []
                }
            
            with open(self.portfolio_file, 'r') as f:
                storage_record = json.load(f)
            
            return {
                'success': True,
                'portfolio_data': storage_record.get('portfolio_data', []),
                'import_date': storage_record.get('import_date'),
                'broker': storage_record.get('broker'),
                'total_holdings': storage_record.get('total_holdings', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to load portfolio data: {str(e)}',
                'portfolio_data': []
            }
    
    def get_portfolio_symbols(self) -> List[str]:
        """Get list of symbols from stored portfolio"""
        result = self.load_portfolio_data()
        if result['success']:
            return list(set([holding.get('symbol', '').upper() 
                          for holding in result['portfolio_data'] 
                          if holding.get('symbol')]))
        return []
    
    def update_portfolio_config(self, config_file: str = 'input/config_portfolio.txt') -> Dict:
        """Update the portfolio config file with symbols from stored data"""
        try:
            symbols = self.get_portfolio_symbols()
            
            if not symbols:
                return {
                    'success': False,
                    'error': 'No portfolio symbols found'
                }
            
            symbols.sort()
            
            # Write to config file
            with open(config_file, 'w') as f:
                f.write("# Portfolio stocks from imported data\n")
                f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                for symbol in symbols:
                    f.write(f"{symbol}\n")
            
            return {
                'success': True,
                'symbols_updated': len(symbols),
                'config_file': config_file,
                'symbols': symbols
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update config file: {str(e)}'
            }
    
    def clear_portfolio_data(self) -> Dict:
        """Clear stored portfolio data"""
        try:
            files_to_remove = [self.portfolio_file, self.portfolio_csv_file]
            removed_files = []
            
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed_files.append(file_path)
            
            return {
                'success': True,
                'message': f'Portfolio data cleared',
                'removed_files': removed_files
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clear portfolio data: {str(e)}'
            }
    
    def get_storage_info(self) -> Dict:
        """Get information about stored portfolio data"""
        try:
            if not os.path.exists(self.portfolio_file):
                return {
                    'has_data': False,
                    'message': 'No portfolio data stored'
                }
            
            stat = os.stat(self.portfolio_file)
            result = self.load_portfolio_data()
            
            return {
                'has_data': True,
                'file_size': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'import_date': result.get('import_date'),
                'broker': result.get('broker'),
                'total_holdings': result.get('total_holdings', 0),
                'storage_file': self.portfolio_file,
                'csv_file': self.portfolio_csv_file if os.path.exists(self.portfolio_csv_file) else None
            }
            
        except Exception as e:
            return {
                'has_data': False,
                'error': str(e)
            }
