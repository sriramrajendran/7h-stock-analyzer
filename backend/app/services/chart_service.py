"""
Chart generation service for price charts
"""

import boto3
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import io
import base64
import logging
from app.models import Recommendation

logger = logging.getLogger(__name__)

class ChartService:
    """Service for generating price charts"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        
        # Set matplotlib style
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
    
    def generate_price_chart(self, recommendation: Recommendation) -> str:
        """Generate price chart for a recommendation"""
        try:
            # Get historical data
            ticker = yf.Ticker(recommendation.symbol)
            data = ticker.history(period="3m")  # 3 months of data
            
            if data.empty:
                logger.warning(f"No historical data for {recommendation.symbol}")
                return None
            
            # Create the chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), 
                                          gridspec_kw={'height_ratios': [3, 1]})
            
            # Price chart
            ax1.plot(data.index, data['Close'], label='Close Price', linewidth=2, color='blue')
            
            # Add moving averages
            if len(data) >= 20:
                sma_20 = data['Close'].rolling(window=20).mean()
                ax1.plot(data.index, sma_20, label='20-day SMA', linewidth=1, color='orange', alpha=0.7)
            
            if len(data) >= 50:
                sma_50 = data['Close'].rolling(window=50).mean()
                ax1.plot(data.index, sma_50, label='50-day SMA', linewidth=1, color='red', alpha=0.7)
            
            # Add recommendation markers
            current_price = recommendation.price
            ax1.axhline(y=current_price, color='green', linestyle='--', alpha=0.7, label=f'Current: ${current_price:.2f}')
            
            # Add target and stop loss lines
            if recommendation.target_price:
                ax1.axhline(y=recommendation.target_price, color='green', linestyle='-', alpha=0.8, 
                           label=f'Target: ${recommendation.target_price:.2f}')
            
            if recommendation.stop_loss:
                ax1.axhline(y=recommendation.stop_loss, color='red', linestyle='-', alpha=0.8, 
                           label=f'Stop Loss: ${recommendation.stop_loss:.2f}')
            
            # Format price chart
            ax1.set_title(f'{recommendation.symbol} - {recommendation.company} Price Chart', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Price ($)', fontsize=12)
            ax1.legend(loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
            
            # Volume chart
            ax2.bar(data.index, data['Volume'], alpha=0.6, color='blue')
            ax2.set_ylabel('Volume', fontsize=12)
            ax2.set_xlabel('Date', fontsize=12)
            ax2.grid(True, alpha=0.3)
            
            # Format volume chart x-axis
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax2.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Add recommendation info as text
            info_text = f"Recommendation: {recommendation.recommendation}\\n"
            info_text += f"Score: {recommendation.score:.2f}\\n"
            info_text += f"RSI: {recommendation.rsi:.1f}\\n"
            info_text += f"Confidence: {recommendation.confidence_level}"
            
            ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes, fontsize=10,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to S3
            chart_url = self._save_chart_to_s3(fig, recommendation.symbol, recommendation.timestamp)
            
            # Close the figure to free memory
            plt.close(fig)
            
            return chart_url
            
        except Exception as e:
            logger.error(f"Error generating chart for {recommendation.symbol}: {str(e)}")
            return None
    
    def _save_chart_to_s3(self, fig, symbol: str, timestamp: str) -> str:
        """Save chart to S3 and return URL"""
        try:
            # Save figure to bytes
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            
            # Generate filename
            date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            filename = f'charts/{symbol}_{date_str}.png'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=img_buffer.getvalue(),
                ContentType='image/png',
                ACL='public-read'  # Make publicly accessible
            )
            
            # Generate URL
            chart_url = f"https://{self.bucket_name}.s3.{self.s3_client.meta.region_name}.amazonaws.com/{filename}"
            
            logger.info(f"Chart saved to S3: {filename}")
            return chart_url
            
        except Exception as e:
            logger.error(f"Error saving chart to S3: {str(e)}")
            raise
    
    def generate_comparison_chart(self, recommendations: List[Recommendation]) -> str:
        """Generate comparison chart for multiple recommendations"""
        try:
            if not recommendations:
                return None
            
            # Limit to top 10 recommendations to avoid clutter
            top_recommendations = recommendations[:10]
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            # Get data for each symbol
            for rec in top_recommendations:
                try:
                    ticker = yf.Ticker(rec.symbol)
                    data = ticker.history(period="1m")  # 1 month of data
                    
                    if not data.empty:
                        # Normalize prices to percentage change
                        normalized = (data['Close'] / data['Close'].iloc[0] - 1) * 100
                        ax.plot(data.index, normalized, label=f"{rec.symbol} ({rec.recommendation})", linewidth=2)
                
                except Exception as e:
                    logger.warning(f"Error getting data for {rec.symbol}: {str(e)}")
                    continue
            
            # Format chart
            ax.set_title('Stock Performance Comparison (1 Month)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Price Change (%)', fontsize=12)
            ax.set_xlabel('Date', fontsize=12)
            ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
            ax.grid(True, alpha=0.3)
            
            # Add horizontal line at 0%
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            # Adjust layout
            plt.tight_layout()
            
            # Save to S3
            chart_url = self._save_comparison_chart_to_s3(fig)
            
            # Close the figure
            plt.close(fig)
            
            return chart_url
            
        except Exception as e:
            logger.error(f"Error generating comparison chart: {str(e)}")
            return None
    
    def _save_comparison_chart_to_s3(self, fig) -> str:
        """Save comparison chart to S3"""
        try:
            # Save figure to bytes
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            
            # Generate filename
            date_str = datetime.utcnow().strftime('%Y-%m-%d')
            filename = f'charts/comparison_{date_str}.png'
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=img_buffer.getvalue(),
                ContentType='image/png',
                ACL='public-read'
            )
            
            # Generate URL
            chart_url = f"https://{self.bucket_name}.s3.{self.s3_client.meta.region_name}.amazonaws.com/{filename}"
            
            logger.info(f"Comparison chart saved to S3: {filename}")
            return chart_url
            
        except Exception as e:
            logger.error(f"Error saving comparison chart to S3: {str(e)}")
            raise
    
    def generate_charts_for_recommendations(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        """Generate charts for all recommendations"""
        try:
            chart_results = {}
            
            # Generate individual charts
            for rec in recommendations:
                chart_url = self.generate_price_chart(rec)
                if chart_url:
                    chart_results[rec.symbol] = chart_url
            
            # Generate comparison chart
            comparison_url = self.generate_comparison_chart(recommendations)
            if comparison_url:
                chart_results['comparison'] = comparison_url
            
            return {
                'success': True,
                'charts_generated': len(chart_results),
                'chart_urls': chart_results
            }
            
        except Exception as e:
            logger.error(f"Error generating charts: {str(e)}")
            return {'success': False, 'error': str(e)}

def generate_charts_for_recommendations(recommendations: List[Recommendation]) -> Dict[str, Any]:
    """Main function to generate charts for recommendations"""
    chart_service = ChartService()
    return chart_service.generate_charts_for_recommendations(recommendations)
