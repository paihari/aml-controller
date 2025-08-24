#!/usr/bin/env python3
"""
Web-accessible Sanctions Data Loader
Integrates OpenSanctions pipeline with web dashboard
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any
from pipelines.opensanctions_senzing_pipeline import OpenSanctionsSenzingPipeline
from src.utils.logger import AMLLogger

class SanctionsWebLoader:
    """Web-accessible interface for sanctions data loading"""
    
    def __init__(self):
        """Initialize the web loader"""
        self.logger = AMLLogger.get_logger('sanctions_web_loader', 'sanctions')
        self.pipeline = None
        
    def initialize_pipeline(self) -> bool:
        """Initialize the OpenSanctions pipeline"""
        try:
            self.pipeline = OpenSanctionsSenzingPipeline()
            self.logger.info("✅ OpenSanctions pipeline initialized")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize pipeline: {e}")
            return False
    
    def refresh_sanctions_data(self, user_confirmed: bool = False) -> Dict[str, Any]:
        """
        Refresh sanctions data from OpenSanctions
        
        Args:
            user_confirmed: Whether user has confirmed they want to clear existing data
        
        Returns:
            Dict with operation results
        """
        self.logger.info("🚀 Starting web-triggered sanctions refresh")
        
        if not user_confirmed:
            return {
                'success': False,
                'error': 'User confirmation required',
                'requires_confirmation': True,
                'message': 'This will clear all existing sanctions data and reload from OpenSanctions. Continue?'
            }
        
        if not self.pipeline:
            if not self.initialize_pipeline():
                return {
                    'success': False,
                    'error': 'Failed to initialize OpenSanctions pipeline',
                    'requires_confirmation': False
                }
        
        try:
            # Run the pipeline
            success = self.pipeline.run_pipeline()
            
            if success:
                # Get summary statistics
                stats = self.get_sanctions_statistics()
                
                return {
                    'success': True,
                    'message': 'Sanctions data refreshed successfully',
                    'timestamp': datetime.now().isoformat(),
                    'statistics': stats,
                    'requires_confirmation': False
                }
            else:
                return {
                    'success': False,
                    'error': 'Pipeline execution failed',
                    'message': 'Check logs for detailed error information',
                    'requires_confirmation': False
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error during sanctions refresh: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Unexpected error during sanctions refresh',
                'requires_confirmation': False
            }
    
    def get_sanctions_statistics(self) -> Dict[str, Any]:
        """Get current sanctions database statistics"""
        try:
            from supabase import create_client
            from dotenv import load_dotenv
            
            load_dotenv()
            supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
            
            # Get total count
            total_result = supabase.table('sanctions_entities').select('*', count='exact').execute()
            total_count = total_result.count or 0
            
            # Get counts by entity type using count queries (more efficient for large datasets)
            entity_types = {}
            risk_levels = {}
            
            # Count by entity type
            for entity_type in ['person', 'organization', 'vessel', 'aircraft', 'company', 'address', 'crypto']:
                try:
                    count_result = supabase.table('sanctions_entities')\
                        .select('*', count='exact')\
                        .eq('entity_type', entity_type)\
                        .limit(1)\
                        .execute()
                    count = count_result.count or 0
                    if count > 0:
                        entity_types[entity_type] = count
                except:
                    pass
            
            # Count by risk level  
            for risk_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                try:
                    count_result = supabase.table('sanctions_entities')\
                        .select('*', count='exact')\
                        .eq('risk_level', risk_level)\
                        .limit(1)\
                        .execute()
                    count = count_result.count or 0
                    if count > 0:
                        risk_levels[risk_level] = count
                except:
                    pass
            
            return {
                'total_entities': total_count,
                'entity_types': entity_types,
                'risk_levels': risk_levels,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting statistics: {e}")
            return {
                'total_entities': 0,
                'entity_types': {},
                'risk_levels': {},
                'error': str(e)
            }
    
    def check_data_status(self) -> Dict[str, Any]:
        """Check current status of sanctions data"""
        try:
            stats = self.get_sanctions_statistics()
            
            # Determine status
            if stats['total_entities'] == 0:
                status = 'empty'
                message = 'No sanctions data loaded'
            elif stats['total_entities'] < 10000:
                status = 'partial'
                message = f'Partial data loaded ({stats["total_entities"]:,} entities)'
            else:
                status = 'loaded'
                message = f'Full dataset loaded ({stats["total_entities"]:,} entities)'
            
            return {
                'success': True,
                'status': status,
                'message': message,
                'statistics': stats
            }
            
        except Exception as e:
            return {
                'success': False,
                'status': 'error',
                'message': f'Error checking data status: {e}',
                'statistics': {}
            }

# Global instance for web integration
sanctions_web_loader = SanctionsWebLoader()

def refresh_sanctions_web(user_confirmed: bool = False) -> Dict[str, Any]:
    """Web endpoint function for sanctions refresh"""
    return sanctions_web_loader.refresh_sanctions_data(user_confirmed)

def get_sanctions_status() -> Dict[str, Any]:
    """Web endpoint function for sanctions status"""
    return sanctions_web_loader.check_data_status()

def get_sanctions_stats() -> Dict[str, Any]:
    """Web endpoint function for sanctions statistics"""
    return sanctions_web_loader.get_sanctions_statistics()

if __name__ == '__main__':
    # Test the web loader
    loader = SanctionsWebLoader()
    
    print("🔍 Checking sanctions data status...")
    status = loader.check_data_status()
    print(f"Status: {status}")
    
    print("\n📊 Getting sanctions statistics...")
    stats = loader.get_sanctions_statistics()
    print(f"Statistics: {stats}")