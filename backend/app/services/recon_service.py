"""
Reconciliation service for tracking recommendation performance
"""

import boto3
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import yfinance as yf
import logging
from app.models import ReconData, Recommendation

logger = logging.getLogger(__name__)

class ReconService:
    """Service for reconciling recommendations with actual performance"""
    
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
    
    def run_daily_recon(self) -> Dict[str, Any]:
        """Run daily reconciliation for all active recommendations"""
        try:
            # Get latest recommendations
            latest_data = self._get_latest_recommendations()
            if not latest_data:
                return {'success': False, 'error': 'No latest recommendations found'}
            
            recon_results = []
            
            for recommendation in latest_data.get('recommendations', []):
                recon_data = self._reconcile_recommendation(recommendation)
                if recon_data:
                    recon_results.append(recon_data)
            
            # Save recon results to both API and website paths
            self._save_recon_results(recon_results)
            self._save_recon_to_website(recon_results)
            
            return {
                'success': True,
                'reconciled_count': len(recon_results),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Daily recon failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _reconcile_recommendation(self, recommendation: Dict) -> ReconData:
        """Reconcile a single recommendation with current market data"""
        try:
            # Get current market data
            ticker = yf.Ticker(recommendation['symbol'])
            current_data = ticker.history(period="1d")
            
            if current_data.empty:
                logger.warning(f"No current data for {recommendation['symbol']}")
                return None
            
            current_price = current_data['Close'].iloc[-1]
            
            # Calculate days elapsed
            original_date = datetime.fromisoformat(recommendation['timestamp'].replace('Z', '+00:00'))
            days_elapsed = (datetime.utcnow() - original_date).days
            
            # Check if target or stop loss was hit
            target_met = False
            stop_loss_hit = False
            result_status = "in_transit"
            days_to_target = None
            
            if recommendation.get('target_price'):
                target_met = current_price >= recommendation['target_price']
                if target_met:
                    result_status = "target_met"
                    days_to_target = days_elapsed
            
            if recommendation.get('stop_loss'):
                stop_loss_hit = current_price <= recommendation['stop_loss']
                if stop_loss_hit and not target_met:  # Stop loss takes precedence
                    result_status = "stop_loss_hit"
            
            return ReconData(
                symbol=recommendation['symbol'],
                original_recommendation=recommendation['recommendation'],
                original_price=recommendation['price'],
                target_price=recommendation.get('target_price'),
                stop_loss=recommendation.get('stop_loss'),
                current_price=current_price,
                days_elapsed=days_elapsed,
                target_met=target_met,
                stop_loss_hit=stop_loss_hit,
                recon_date=datetime.utcnow().isoformat(),
                original_timestamp=recommendation['timestamp'],
                result_status=result_status,
                days_to_target=days_to_target
            )
            
        except Exception as e:
            logger.error(f"Error reconciling {recommendation['symbol']}: {str(e)}")
            return None
    
    def _get_latest_recommendations(self) -> Dict[str, Any]:
        """Get latest recommendations from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key='data/latest.json'
            )
            return json.loads(response['Body'].read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Error getting latest recommendations: {str(e)}")
            return None
    
    def _save_recon_results(self, recon_results: List[ReconData]):
        """Save reconciliation results to S3"""
        try:
            # Save to daily recon file
            today = datetime.utcnow().strftime('%Y-%m-%d')
            recon_key = f'recon/daily/{today}.json'
            
            recon_data = {
                'date': today,
                'timestamp': datetime.utcnow().isoformat(),
                'count': len(recon_results),
                'reconciliations': [recon.__dict__ for recon in recon_results]
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=recon_key,
                Body=json.dumps(recon_data, indent=2),
                ContentType='application/json'
            )
            
            # Update recommendations with recon data
            self._update_recommendations_with_recon(recon_results)
            
        except Exception as e:
            logger.error(f"Error saving recon results: {str(e)}")
            raise
    
    def _update_recommendations_with_recon(self, recon_results: List[ReconData]):
        """Update latest recommendations with reconciliation data"""
        try:
            # Get current latest recommendations
            latest_data = self._get_latest_recommendations()
            if not latest_data:
                return
            
            # Update recommendations with recon data
            updated_recommendations = []
            for rec in latest_data.get('recommendations', []):
                # Find matching recon data
                matching_recon = next(
                    (r for r in recon_results if r.symbol == rec['symbol']),
                    None
                )
                
                if matching_recon:
                    rec['days_to_target'] = matching_recon.days_elapsed
                    rec['target_met'] = matching_recon.target_met
                    rec['stop_loss_hit'] = matching_recon.stop_loss_hit
                    rec['result_status'] = matching_recon.result_status
                    rec['days_to_target_result'] = matching_recon.days_to_target
                
                updated_recommendations.append(rec)
            
            # Save updated recommendations
            updated_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'date': datetime.utcnow().strftime('%Y-%m-%d'),
                'count': len(updated_recommendations),
                'recommendations': updated_recommendations
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key='data/latest.json',
                Body=json.dumps(updated_data, indent=2),
                ContentType='application/json'
            )
            
        except Exception as e:
            logger.error(f"Error updating recommendations with recon: {str(e)}")
            raise
    
    def _save_recon_to_website(self, recon_results: List[ReconData]):
        """Save reconciliation data to S3 website path for direct access"""
        try:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Save daily recon data to website path
            daily_website_key = f'recon/daily/{today}.json'
            
            recon_data = {
                'date': today,
                'timestamp': datetime.utcnow().isoformat(),
                'count': len(recon_results),
                'reconciliations': [recon.__dict__ for recon in recon_results],
                'data_type': 'daily_reconciliation',
                'version': '2.0'
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=daily_website_key,
                Body=json.dumps(recon_data, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            logger.info(f"Saved daily recon to website path: s3://{self.bucket_name}/{daily_website_key}")
            
            # Update and save recon summary to website path
            self._update_recon_summary_website(recon_results)
            
        except Exception as e:
            logger.error(f"Error saving recon to website: {str(e)}")
            # Don't raise - website path is secondary access method
    
    def _update_recon_summary_website(self, recon_results: List[ReconData]):
        """Update reconciliation summary on website path"""
        try:
            # Get current summary or create new
            summary_key = 'recon/summary.json'
            
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=summary_key
                )
                current_summary = json.loads(response['Body'].read().decode('utf-8'))
            except self.s3_client.exceptions.NoSuchKey:
                current_summary = {
                    'total_reconciled': 0,
                    'targets_met': 0,
                    'stop_losses_hit': 0,
                    'avg_days_to_target': 0,
                    'performance_by_recommendation': {},
                    'last_updated': None
                }
            
            # Update summary with new results
            for recon in recon_results:
                current_summary['total_reconciled'] += 1
                
                if recon.target_met:
                    current_summary['targets_met'] += 1
                
                if recon.stop_loss_hit:
                    current_summary['stop_losses_hit'] += 1
                
                # Track by recommendation type
                rec_type = recon.original_recommendation
                if rec_type not in current_summary['performance_by_recommendation']:
                    current_summary['performance_by_recommendation'][rec_type] = {
                        'count': 0,
                        'targets_met': 0,
                        'stop_losses_hit': 0
                    }
                
                current_summary['performance_by_recommendation'][rec_type]['count'] += 1
                if recon.target_met:
                    current_summary['performance_by_recommendation'][rec_type]['targets_met'] += 1
                if recon.stop_loss_hit:
                    current_summary['performance_by_recommendation'][rec_type]['stop_losses_hit'] += 1
            
            # Update timestamp
            current_summary['last_updated'] = datetime.utcnow().isoformat()
            current_summary['data_type'] = 'reconciliation_summary'
            current_summary['version'] = '2.0'
            
            # Save updated summary
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=summary_key,
                Body=json.dumps(current_summary, indent=2),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            logger.info(f"Updated recon summary on website path: s3://{self.bucket_name}/{summary_key}")
            
        except Exception as e:
            logger.error(f"Error updating recon summary website: {str(e)}")
            # Don't raise - website path is secondary access method
    
    def get_recon_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get reconciliation summary for the last N days"""
        try:
            summary = {
                'total_reconciled': 0,
                'targets_met': 0,
                'stop_losses_hit': 0,
                'avg_days_to_target': 0,
                'performance_by_recommendation': {}
            }
            
            target_days = []
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
                recon_key = f'recon/daily/{date}.json'
                
                try:
                    response = self.s3_client.get_object(
                        Bucket=self.bucket_name,
                        Key=recon_key
                    )
                    recon_data = json.loads(response['Body'].read().decode('utf-8'))
                    
                    for recon in recon_data.get('reconciliations', []):
                        summary['total_reconciled'] += 1
                        
                        if recon['target_met']:
                            summary['targets_met'] += 1
                            target_days.append(recon['days_elapsed'])
                        
                        if recon['stop_loss_hit']:
                            summary['stop_losses_hit'] += 1
                        
                        # Track by recommendation type
                        rec_type = recon['original_recommendation']
                        if rec_type not in summary['performance_by_recommendation']:
                            summary['performance_by_recommendation'][rec_type] = {
                                'count': 0,
                                'targets_met': 0,
                                'stop_losses_hit': 0
                            }
                        
                        summary['performance_by_recommendation'][rec_type]['count'] += 1
                        if recon['target_met']:
                            summary['performance_by_recommendation'][rec_type]['targets_met'] += 1
                        if recon['stop_loss_hit']:
                            summary['performance_by_recommendation'][rec_type]['stop_losses_hit'] += 1
                
                except self.s3_client.exceptions.NoSuchKey:
                    continue  # File doesn't exist for this date
            
            # Calculate averages
            if target_days:
                summary['avg_days_to_target'] = sum(target_days) / len(target_days)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting recon summary: {str(e)}")
            return {'error': str(e)}

def run_daily_reconciliation() -> Dict[str, Any]:
    """Main function to run daily reconciliation"""
    recon_service = ReconService()
    return recon_service.run_daily_recon()
