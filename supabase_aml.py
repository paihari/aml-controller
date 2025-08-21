#!/usr/bin/env python3
"""
Supabase client for AML transactions and alerts storage
"""

import os
import json
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, date

# Load environment variables
load_dotenv()

class SupabaseAMLDB:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise Exception("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        print("✅ Supabase AML database initialized")
    
    def _serialize_data(self, data: Dict) -> Dict:
        """Convert date objects to ISO format strings for JSON serialization"""
        # Define valid columns for each table
        valid_transaction_fields = {
            'transaction_id', 'account_id', 'amount', 'currency', 'transaction_type',
            'transaction_date', 'beneficiary_account', 'beneficiary_name', 
            'beneficiary_bank', 'beneficiary_country', 'origin_country', 
            'purpose', 'status', 'created_at', 'updated_at'
        }
        
        valid_alert_fields = {
            'alert_id', 'subject_id', 'subject_type', 'typology', 'risk_score', 
            'evidence', 'status', 'assigned_to', 'resolution', 'created_at', 'updated_at'
        }
        
        serialized = {}
        for key, value in data.items():
            # Filter out invalid fields (like risk_factors)
            if key in valid_transaction_fields or key in valid_alert_fields:
                if isinstance(value, (date, datetime)):
                    serialized[key] = value.isoformat()
                else:
                    serialized[key] = value
        
        return serialized
    
    # Transaction methods
    def add_transaction(self, transaction_data: Dict) -> Optional[str]:
        """Add a new transaction and return transaction ID"""
        try:
            # Serialize date objects to ISO format
            serialized_data = self._serialize_data(transaction_data)
            result = self.supabase.table('aml_transactions').insert(serialized_data).execute()
            if result.data:
                return transaction_data.get('transaction_id')
            return None
        except Exception as e:
            print(f"Error inserting transaction to Supabase: {e}")
            return None
    
    def get_transactions(self, limit: int = 100, status: str = None) -> List[Dict]:
        """Get transactions with optional status filter"""
        try:
            query = self.supabase.table('aml_transactions').select("*").order('created_at', desc=True)
            
            if status:
                query = query.eq('status', status)
            
            result = query.limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting transactions from Supabase: {e}")
            return []
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict]:
        """Get a specific transaction by ID"""
        try:
            result = self.supabase.table('aml_transactions').select("*").eq('transaction_id', transaction_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting transaction from Supabase: {e}")
            return None
    
    def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction status"""
        try:
            result = self.supabase.table('aml_transactions').update({'status': status}).eq('transaction_id', transaction_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error updating transaction status in Supabase: {e}")
            return False
    
    def get_pending_transactions(self) -> List[Dict]:
        """Get all pending transactions"""
        return self.get_transactions(status='PENDING', limit=1000)
    
    def delete_all_transactions(self) -> Dict:
        """Delete all transactions"""
        try:
            # Get counts before deletion
            all_transactions = self.supabase.table('aml_transactions').select("id").execute()
            transaction_count = len(all_transactions.data) if all_transactions.data else 0
            
            # Delete all transactions
            self.supabase.table('aml_transactions').delete().gte('id', 0).execute()
            
            return {
                'success': True,
                'deleted_transactions': transaction_count
            }
        except Exception as e:
            print(f"Error deleting transactions from Supabase: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # Alert methods
    def add_alert(self, alert_data: Dict) -> Optional[str]:
        """Add a new alert and return alert ID"""
        try:
            # Serialize date objects and handle evidence JSON
            serialized_data = self._serialize_data(alert_data)
            
            # Convert evidence dict to JSONB
            if 'evidence' in serialized_data and isinstance(serialized_data['evidence'], dict):
                serialized_data['evidence'] = json.dumps(serialized_data['evidence'])
            
            result = self.supabase.table('aml_alerts').insert(serialized_data).execute()
            if result.data:
                return alert_data.get('alert_id')
            return None
        except Exception as e:
            print(f"Error inserting alert to Supabase: {e}")
            return None
    
    def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        """Get active alerts"""
        try:
            result = self.supabase.table('aml_alerts').select("*").eq('status', 'ACTIVE').order('created_at', desc=True).limit(limit).execute()
            
            alerts = result.data or []
            # Parse evidence JSON
            for alert in alerts:
                if alert.get('evidence'):
                    try:
                        if isinstance(alert['evidence'], str):
                            alert['evidence'] = json.loads(alert['evidence'])
                    except json.JSONDecodeError:
                        alert['evidence'] = {}
            
            return alerts
        except Exception as e:
            print(f"Error getting alerts from Supabase: {e}")
            return []
    
    def delete_all_alerts(self) -> Dict:
        """Delete all alerts"""
        try:
            # Get counts before deletion
            all_alerts = self.supabase.table('aml_alerts').select("id").execute()
            alert_count = len(all_alerts.data) if all_alerts.data else 0
            
            # Delete all alerts
            self.supabase.table('aml_alerts').delete().gte('id', 0).execute()
            
            return {
                'success': True,
                'deleted_alerts': alert_count
            }
        except Exception as e:
            print(f"Error deleting alerts from Supabase: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            # Get transaction counts
            all_transactions = self.supabase.table('aml_transactions').select("status").execute()
            transactions_data = all_transactions.data or []
            
            transaction_stats = {}
            for tx in transactions_data:
                status = tx.get('status', 'UNKNOWN')
                transaction_stats[status] = transaction_stats.get(status, 0) + 1
            
            # Get alert counts
            all_alerts = self.supabase.table('aml_alerts').select("typology,risk_score,status").execute()
            alerts_data = all_alerts.data or []
            
            alert_stats = {}
            alerts_by_risk = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
            
            for alert in alerts_data:
                if alert.get('status') == 'ACTIVE':
                    typology = alert.get('typology', 'UNKNOWN')
                    alert_stats[typology] = alert_stats.get(typology, 0) + 1
                    
                    # Categorize by risk score
                    risk_score = alert.get('risk_score', 0)
                    if risk_score >= 0.9:
                        alerts_by_risk['Critical'] += 1
                    elif risk_score >= 0.8:
                        alerts_by_risk['High'] += 1
                    elif risk_score >= 0.5:
                        alerts_by_risk['Medium'] += 1
                    else:
                        alerts_by_risk['Low'] += 1
            
            return {
                'total_transactions': len(transactions_data),
                'active_alerts': len([a for a in alerts_data if a.get('status') == 'ACTIVE']),
                'transaction_status': transaction_stats,
                'alert_typologies': alert_stats,
                'alerts_by_risk': alerts_by_risk
            }
            
        except Exception as e:
            print(f"Error getting statistics from Supabase: {e}")
            return {
                'total_transactions': 0,
                'active_alerts': 0,
                'transaction_status': {},
                'alert_typologies': {},
                'alerts_by_risk': {}
            }

if __name__ == "__main__":
    # Test the Supabase AML connection
    try:
        db = SupabaseAMLDB()
        print("✅ Supabase AML database connection successful")
        
        # Test getting statistics
        stats = db.get_statistics()
        print(f"📊 Current statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Supabase AML database connection failed: {e}")