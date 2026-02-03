"""
Data Loader Module - Fetches OHLCV data from Yahoo Finance with S3 caching
"""

import yfinance as yf
import pandas as pd
import boto3
import os
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DataLoader:
    """Optimized data loader with S3 caching and batch processing"""
    
    def __init__(self, s3_bucket: str = None, use_s3_cache: bool = True):
        self.s3_bucket = s3_bucket or os.getenv('S3_BUCKET_NAME', '7h-stock-analyzer-dev')
        self.use_s3_cache = use_s3_cache
        self.s3_client = boto3.client('s3') if use_s3_cache else None
        self.cache_ttl_days = 1  # Cache data for 1 day
        
    def fetch_single_ticker(self, ticker: str, period: str = "1y") -> pd.DataFrame:
        """Fetch data for a single ticker with S3 cache check"""
        ticker = ticker.upper().strip()
        
        # Check S3 cache first
        if self.use_s3_cache:
            cached_data = self._get_from_cache(ticker)
            if cached_data is not None:
                logger.info(f"Cache hit for {ticker}")
                return cached_data
        
        # Fetch from Yahoo Finance
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=False)
            
            if df.empty:
                logger.warning(f"No data found for {ticker}")
                return pd.DataFrame()
            
            # Handle MultiIndex columns (newer yfinance versions)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            
            # Clean and validate data
            df = self._clean_data(df, ticker)
            
            # Save to S3 cache
            if self.use_s3_cache and not df.empty:
                self._save_to_cache(ticker, df)
            
            logger.info(f"Fetched {len(df)} rows for {ticker}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch data for {ticker}: {str(e)}")
            return pd.DataFrame()
    
    def fetch_batch(self, tickers: List[str], period: str = "1y", 
                   batch_size: int = 50, max_workers: int = 5) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple tickers with batch processing and rate limiting"""
        results = {}
        
        # Process in batches to avoid rate limits
        for i in range(0, len(tickers), batch_size):
            batch_tickers = tickers[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {batch_tickers}")
            
            # Use ThreadPoolExecutor for parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_ticker = {
                    executor.submit(self.fetch_single_ticker, ticker, period): ticker 
                    for ticker in batch_tickers
                }
                
                for future in as_completed(future_to_ticker):
                    ticker = future_to_ticker[future]
                    try:
                        df = future.result()
                        if not df.empty:
                            results[ticker] = df
                    except Exception as e:
                        logger.error(f"Error processing {ticker}: {str(e)}")
            
            # Rate limiting - delay between batches
            if i + batch_size < len(tickers):
                delay = random.uniform(1.0, 2.0)
                logger.info(f"Delaying {delay:.2f}s before next batch...")
                time.sleep(delay)
        
        logger.info(f"Successfully fetched data for {len(results)}/{len(tickers)} tickers")
        return results
    
    def fetch_universe(self, tickers: List[str], period: str = "1y") -> Dict[str, pd.DataFrame]:
        """Fetch data for entire universe with optimization for large sets"""
        if len(tickers) <= 50:
            return self.fetch_batch(tickers, period, batch_size=len(tickers))
        else:
            return self.fetch_batch(tickers, period, batch_size=50, max_workers=10)
    
    def _get_from_cache(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get data from S3 cache if available and fresh"""
        try:
            cache_key = f"{ticker}/data.json"
            
            # Check if object exists and get metadata
            response = self.s3_client.head_object(Bucket=self.s3_bucket, Key=cache_key)
            last_modified = response['LastModified']
            age_days = (datetime.now(last_modified.tzinfo) - last_modified).days
            
            if age_days > self.cache_ttl_days:
                logger.info(f"Cache expired for {ticker} ({age_days} days old)")
                return None
            
            # Load cached data
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=cache_key)
            import json
            data = json.loads(response['Body'].read())
            df = pd.DataFrame(data['data'], columns=data['columns'], index=pd.to_datetime(data['index']))
            
            # Validate cache integrity
            if self._validate_cached_data(df):
                return df
            else:
                logger.warning(f"Invalid cache data for {ticker}, will refetch")
                return None
                
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.debug(f"No cache found for {ticker}")
            else:
                logger.error(f"Cache error for {ticker}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected cache error for {ticker}: {str(e)}")
            return None
    
    def _save_to_cache(self, ticker: str, df: pd.DataFrame):
        """Save data to S3 cache"""
        try:
            cache_key = f"{ticker}/data.json"
            
            # Convert DataFrame to JSON
            data = {
                'columns': df.columns.tolist(),
                'index': df.index.strftime('%Y-%m-%d').tolist(),
                'data': df.values.tolist()
            }
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=cache_key,
                Body=json.dumps(data),
                ContentType='application/json'
            )
            
            logger.debug(f"Saved {ticker} data to cache")
            
        except Exception as e:
            logger.error(f"Failed to save {ticker} to cache: {str(e)}")
    
    def _clean_data(self, df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Clean and validate OHLCV data"""
        if df.empty:
            return df
        
        # Remove any duplicate rows
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by date
        df = df.sort_index()
        
        # Handle missing values
        df = df.ffill().bfill()
        
        # Remove any remaining NaN rows
        df = df.dropna()
        
        # Validate required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns for {ticker}: {missing_cols}")
            return pd.DataFrame()
        
        # Validate data ranges
        if (df['High'] < df['Low']).any():
            logger.warning(f"Invalid High/Low values for {ticker}")
            return pd.DataFrame()
        
        if (df['Close'] > df['High']).any() or (df['Close'] < df['Low']).any():
            logger.warning(f"Invalid Close values for {ticker}")
            return pd.DataFrame()
        
        return df
    
    def _validate_cached_data(self, df: pd.DataFrame) -> bool:
        """Validate cached data integrity"""
        if df.empty:
            return False
        
        # Check required columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        if not all(col in df.columns for col in required_cols):
            return False
        
        # Check for valid data ranges
        if df['Volume'].min() < 0:
            return False
        
        return True
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        if not self.use_s3_cache:
            return {'cached_tickers': 0, 'total_size_mb': 0}
        
        try:
            # List all cached tickers
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix='',
                Delimiter='/'
            )
            
            cached_tickers = []
            total_size = 0
            
            for obj in response.get('Contents', []):
                if obj['Key'].endswith('/data.parquet'):
                    ticker = obj['Key'].split('/')[0]
                    cached_tickers.append(ticker)
                    total_size += obj['Size']
            
            return {
                'cached_tickers': len(cached_tickers),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'tickers': cached_tickers
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {str(e)}")
            return {'cached_tickers': 0, 'total_size_mb': 0}
    
    def clear_cache(self, ticker: str = None) -> bool:
        """Clear cache for specific ticker or all cache"""
        try:
            if ticker:
                # Clear specific ticker
                cache_key = f"{ticker}/data.parquet"
                self.s3_client.delete_object(Bucket=self.s3_bucket, Key=cache_key)
                logger.info(f"Cleared cache for {ticker}")
            else:
                # Clear all cache
                response = self.s3_client.list_objects_v2(Bucket=self.s3_bucket)
                if 'Contents' in response:
                    delete_keys = [{'Key': obj['Key']} for obj in response['Contents']]
                    self.s3_client.delete_objects(
                        Bucket=self.s3_bucket,
                        Delete={'Objects': delete_keys}
                    )
                    logger.info("Cleared all cache")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False
