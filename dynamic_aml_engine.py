#!/usr/bin/env python3
"""
Dynamic AML Detection Engine with real-time processing
"""

import datetime
import uuid
from typing import Dict, List, Tuple
from database import AMLDatabase
from supabase_sanctions import SupabaseSanctionsDB
import re
import os
from dotenv import load_dotenv
from aml_logger import AMLLogger, log_function_entry, log_function_exit, log_error_with_context

# Load environment variables
load_dotenv()

class DynamicAMLEngine:
    def __init__(self, db: AMLDatabase):
        self.db = db
        
        # Initialize Supabase for sanctions if enabled
        self.use_supabase = os.getenv('USE_SUPABASE_FOR_SANCTIONS', 'false').lower() == 'true'
        self.supabase_db = None
        
        if self.use_supabase:
            try:
                self.supabase_db = SupabaseSanctionsDB()
                print("✅ AML Engine: Supabase sanctions database initialized")
            except Exception as e:
                print(f"⚠️ AML Engine: Failed to initialize Supabase, using local DB: {e}")
                self.use_supabase = False
        
        # Risk thresholds
        self.structuring_threshold = 10000
        self.velocity_threshold_count = 5
        self.velocity_threshold_hours = 24
        
        # High-risk corridors with risk scores
        self.high_risk_corridors = {
            ('US', 'IR'): 0.85,
            ('US', 'RU'): 0.80,
            ('US', 'KP'): 0.95,
            ('DE', 'RU'): 0.75,
            ('GB', 'RU'): 0.70,
            ('US', 'SY'): 0.90,
            ('US', 'KY'): 0.60,
            ('US', 'BVI'): 0.65,
            ('US', 'LI'): 0.55,
            ('US', 'CH'): 0.50
        }
    
    def process_transaction(self, transaction_data: Dict) -> List[Dict]:
        """Process a single transaction and generate alerts"""
        alerts = []
        
        # Store transaction first
        transaction_id = self.db.add_transaction(transaction_data)
        if not transaction_id:
            return alerts
        
        # Run all detection rules
        alerts.extend(self._check_sanctions_screening(transaction_data))
        alerts.extend(self._check_high_risk_geography(transaction_data))
        alerts.extend(self._check_structuring_patterns(transaction_data))
        alerts.extend(self._check_velocity_anomalies(transaction_data))
        alerts.extend(self._check_round_trip_transactions(transaction_data))
        
        # Store alerts in database
        for alert in alerts:
            self.db.add_alert(alert)
        
        return alerts
    
    def detect_alerts_for_existing_transaction(self, transaction_data: Dict) -> List[Dict]:
        """Run AML detection rules on existing transaction without storing it"""
        transaction_id = transaction_data.get('transaction_id', 'UNKNOWN')
        beneficiary_name = transaction_data.get('beneficiary_name', 'Unknown')
        
        print(f"🚀 DEBUG: Starting AML detection for existing transaction {transaction_id}")
        print(f"🚀 DEBUG: Transaction data: beneficiary='{beneficiary_name}', country={transaction_data.get('beneficiary_country')}")
        
        alerts = []
        
        # Run all detection rules (same as process_transaction but without storing)
        print(f"🚀 DEBUG: Running sanctions screening...")
        sanctions_alerts = self._check_sanctions_screening(transaction_data)
        alerts.extend(sanctions_alerts)
        print(f"🚀 DEBUG: Sanctions screening returned {len(sanctions_alerts)} alerts")
        
        print(f"🚀 DEBUG: Running other AML rules...")
        alerts.extend(self._check_high_risk_geography(transaction_data))
        alerts.extend(self._check_structuring_patterns(transaction_data))
        alerts.extend(self._check_velocity_anomalies(transaction_data))
        alerts.extend(self._check_round_trip_transactions(transaction_data))
        
        print(f"🚀 DEBUG: Total alerts generated: {len(alerts)}")
        
        # Store alerts in database
        print(f"🚀 DEBUG: Storing {len(alerts)} alerts in database...")
        for alert in alerts:
            result = self.db.add_alert(alert)
            print(f"🚀 DEBUG: Alert {alert['alert_id']} stored: {result}")
        
        print(f"🚀 DEBUG: AML detection completed for {transaction_id}")
        return alerts
    
    def process_batch(self, transactions: List[Dict]) -> Dict:
        """Process a batch of transactions"""
        results = {
            'processed_count': 0,
            'alert_count': 0,
            'alerts': [],
            'processing_time': datetime.datetime.now()
        }
        
        for transaction in transactions:
            try:
                alerts = self.process_transaction(transaction)
                results['alerts'].extend(alerts)
                results['alert_count'] += len(alerts)
                results['processed_count'] += 1
            except Exception as e:
                print(f"Error processing transaction {transaction.get('transaction_id', 'UNKNOWN')}: {e}")
                continue
        
        return results
    
    def _check_sanctions_screening(self, transaction: Dict) -> List[Dict]:
        """Check beneficiary against sanctions lists"""
        alerts = []
        
        beneficiary_name = transaction.get('beneficiary_name', '').strip()
        transaction_id = transaction.get('transaction_id', 'UNKNOWN')
        
        print(f"🔍 DEBUG: Starting sanctions screening for {transaction_id}")
        print(f"🔍 DEBUG: Beneficiary name: '{beneficiary_name}'")
        
        if not beneficiary_name:
            print(f"🔍 DEBUG: No beneficiary name, skipping sanctions check")
            return alerts
        
        # Search sanctions database (Supabase only as authoritative source)
        sanctions_matches = []
        if self.use_supabase and self.supabase_db:
            print(f"🔍 DEBUG: Using Supabase for sanctions lookup")
            try:
                sanctions_matches = self.supabase_db.get_sanctions_by_name(beneficiary_name)
                print(f"🔍 DEBUG: Supabase returned {len(sanctions_matches)} matches")
            except Exception as e:
                print(f"🔍 DEBUG: Supabase lookup failed: {e}")
        else:
            print(f"🔍 DEBUG: Using local DB for sanctions lookup (Supabase not available)")
            # Fallback to local DB only if Supabase is not available
            sanctions_matches = self.db.get_sanctions_by_name(beneficiary_name)
            print(f"🔍 DEBUG: Local DB returned {len(sanctions_matches)} matches")
        
        for i, match in enumerate(sanctions_matches):
            match_name = match.get('name', 'UNKNOWN')
            print(f"🔍 DEBUG: Processing match {i+1}: '{match_name}'")
            
            # Calculate match confidence
            confidence = self._calculate_name_similarity(beneficiary_name, match_name)
            print(f"🔍 DEBUG: Name similarity confidence: {confidence:.2f}")
            
            if confidence >= 0.8:  # High confidence match
                print(f"🔍 DEBUG: High confidence match found! Creating alert...")
                alert = {
                    'alert_id': f"ALERT-{str(uuid.uuid4())[:8].upper()}",
                    'subject_id': transaction['transaction_id'],
                    'subject_type': 'TRANSACTION',
                    'typology': 'R1_SANCTIONS_MATCH',
                    'risk_score': 0.95,
                    'evidence': {
                        'source': match.get('data_source', 'Unknown'),
                        'program': match.get('program', 'Unknown'),
                        'party_name': beneficiary_name,
                        'watchlist_name': match['name'],
                        'match_confidence': confidence,
                        'match_type': 'exact' if confidence >= 0.95 else 'fuzzy',
                        'entity_id': match.get('entity_id'),
                        'country': match.get('country'),
                        'transaction_amount': transaction['amount'],
                        'transaction_id': transaction['transaction_id']
                    }
                }
                alerts.append(alert)
                print(f"🔍 DEBUG: Alert created: {alert['alert_id']}")
            else:
                print(f"🔍 DEBUG: Low confidence match ({confidence:.2f}), skipping")
        
        print(f"🔍 DEBUG: Sanctions screening completed. Generated {len(alerts)} alerts")
        return alerts
    
    def _check_high_risk_geography(self, transaction: Dict) -> List[Dict]:
        """Check for high-risk geographic corridors"""
        alerts = []
        
        origin = transaction.get('origin_country')
        destination = transaction.get('beneficiary_country')
        
        if not origin or not destination:
            return alerts
        
        corridor = (origin, destination)
        risk_score = self.high_risk_corridors.get(corridor, 0)
        
        # Also check if destination is high-risk country
        high_risk_countries = ['IR', 'RU', 'KP', 'SY', 'AF', 'IQ', 'LY', 'SO', 'YE']
        if destination in high_risk_countries and risk_score == 0:
            risk_score = 0.75
        
        if risk_score >= 0.5:
            alert = {
                'alert_id': f"ALERT-{str(uuid.uuid4())[:8].upper()}",
                'subject_id': transaction['account_id'],
                'subject_type': 'ACCOUNT',
                'typology': 'R3_HIGH_RISK_CORRIDOR',
                'risk_score': risk_score,
                'evidence': {
                    'origin_country': origin,
                    'beneficiary_country': destination,
                    'transaction_id': transaction['transaction_id'],
                    'amount': transaction['amount'],
                    'country_risk': 'HIGH' if risk_score >= 0.8 else 'MEDIUM',
                    'corridor_risk_score': risk_score,
                    'beneficiary_name': transaction.get('beneficiary_name')
                }
            }
            alerts.append(alert)
        
        return alerts
    
    def _check_structuring_patterns(self, transaction: Dict) -> List[Dict]:
        """Check for structuring patterns (multiple transactions under reporting threshold)"""
        alerts = []
        
        account_id = transaction['account_id']
        transaction_date = transaction['transaction_date']
        
        # Get transactions from same account on same date
        recent_transactions = self.db.get_recent_transactions(limit=100)
        
        # Filter to same account and date
        same_day_transactions = [
            t for t in recent_transactions 
            if (t['account_id'] == account_id and 
                str(t['transaction_date']) == str(transaction_date) and
                t['amount'] < self.structuring_threshold)
        ]
        
        if len(same_day_transactions) >= 4:
            total_amount = sum(t['amount'] for t in same_day_transactions)
            avg_amount = total_amount / len(same_day_transactions)
            
            # Calculate risk score based on pattern
            base_risk = 0.6
            count_factor = min(0.2, (len(same_day_transactions) - 4) * 0.05)
            amount_factor = min(0.2, (avg_amount / self.structuring_threshold) * 0.1)
            risk_score = min(0.9, base_risk + count_factor + amount_factor)
            
            alert = {
                'alert_id': f"ALERT-{str(uuid.uuid4())[:8].upper()}",
                'subject_id': account_id,
                'subject_type': 'ACCOUNT',
                'typology': 'R2_STRUCTURING',
                'risk_score': risk_score,
                'evidence': {
                    'transaction_count': len(same_day_transactions),
                    'total_amount': total_amount,
                    'average_amount': avg_amount,
                    'date': str(transaction_date),
                    'pattern': f"{len(same_day_transactions)}_transactions_under_{self.structuring_threshold}",
                    'threshold': self.structuring_threshold,
                    'transaction_ids': [t['transaction_id'] for t in same_day_transactions[:5]]  # First 5
                }
            }
            alerts.append(alert)
        
        return alerts
    
    def _check_velocity_anomalies(self, transaction: Dict) -> List[Dict]:
        """Check for unusual transaction velocity"""
        alerts = []
        
        account_id = transaction['account_id']
        
        # Get recent transactions from same account
        recent_transactions = self.db.get_recent_transactions(limit=100)
        
        # Filter to same account in last 24 hours
        account_transactions = [
            t for t in recent_transactions 
            if t['account_id'] == account_id
        ]
        
        # Check if high volume in short period
        if len(account_transactions) >= self.velocity_threshold_count:
            total_volume = sum(t['amount'] for t in account_transactions)
            max_amount = max(t['amount'] for t in account_transactions)
            
            # Velocity risk scoring
            if total_volume > 500000 or len(account_transactions) > 10:
                base_risk = 0.5
                volume_factor = min(0.3, (total_volume / 1000000) * 0.3)
                count_factor = min(0.2, (len(account_transactions) / 20) * 0.2)
                risk_score = min(0.85, base_risk + volume_factor + count_factor)
                
                alert = {
                    'alert_id': f"ALERT-{str(uuid.uuid4())[:8].upper()}",
                    'subject_id': account_id,
                    'subject_type': 'ACCOUNT',
                    'typology': 'R4_VELOCITY_ANOMALY',
                    'risk_score': risk_score,
                    'evidence': {
                        'total_volume': total_volume,
                        'max_single_transaction': max_amount,
                        'transaction_count': len(account_transactions),
                        'time_period': f"{self.velocity_threshold_hours}_hours",
                        'anomaly_type': 'high_volume_high_frequency',
                        'average_amount': total_volume / len(account_transactions)
                    }
                }
                alerts.append(alert)
        
        return alerts
    
    def _check_round_trip_transactions(self, transaction: Dict) -> List[Dict]:
        """Check for round-trip transaction patterns"""
        alerts = []
        
        # Get recent transactions to look for patterns
        recent_transactions = self.db.get_recent_transactions(limit=200)
        
        current_account = transaction['account_id']
        current_beneficiary = transaction.get('beneficiary_account')
        current_amount = transaction['amount']
        
        # Look for reverse transactions (beneficiary sends money back)
        for recent_txn in recent_transactions:
            if (recent_txn['account_id'] == current_beneficiary and 
                recent_txn.get('beneficiary_account') == current_account and
                abs(recent_txn['amount'] - current_amount) / current_amount < 0.1):  # Within 10%
                
                # Found potential round trip
                alert = {
                    'alert_id': f"ALERT-{str(uuid.uuid4())[:8].upper()}",
                    'subject_id': current_account,
                    'subject_type': 'ACCOUNT',
                    'typology': 'R5_ROUND_TRIP',
                    'risk_score': 0.70,
                    'evidence': {
                        'outbound_txn': recent_txn['transaction_id'],
                        'return_txn': transaction['transaction_id'],
                        'amount_out': recent_txn['amount'],
                        'amount_in': current_amount,
                        'amount_difference': abs(recent_txn['amount'] - current_amount),
                        'pattern': 'round_trip_detected',
                        'time_gap_days': self._calculate_day_difference(
                            recent_txn['transaction_date'], 
                            transaction['transaction_date']
                        )
                    }
                }
                alerts.append(alert)
                break  # Only flag one round trip per transaction
        
        return alerts
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        if not name1 or not name2:
            return 0.0
        
        # Normalize names
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        # Simple similarity calculation
        if norm1 in norm2 or norm2 in norm1:
            return 0.9
        
        # Check word overlap
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if words1 and words2:
            overlap = len(words1.intersection(words2))
            total = len(words1.union(words2))
            return overlap / total if total > 0 else 0.0
        
        return 0.0
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""
        return re.sub(r'[^A-Z0-9]', '', name.upper().strip())
    
    def _calculate_day_difference(self, date1, date2) -> int:
        """Calculate difference in days between two dates"""
        try:
            if isinstance(date1, str):
                date1 = datetime.datetime.strptime(date1, '%Y-%m-%d').date()
            if isinstance(date2, str):
                date2 = datetime.datetime.strptime(date2, '%Y-%m-%d').date()
            
            return abs((date2 - date1).days)
        except:
            return 0
    
    def get_alert_statistics(self) -> Dict:
        """Get current alert statistics"""
        logger = AMLLogger.get_logger('alert_statistics', 'statistics')
        log_function_entry(logger, 'get_alert_statistics', use_supabase=self.use_supabase)
        
        # Include Supabase sanctions count if using Supabase
        supabase_count = None
        if self.use_supabase and self.supabase_db:
            try:
                logger.info("Attempting to get Supabase sanctions count")
                supabase_count = self.supabase_db.get_sanctions_count()
                AMLLogger.log_statistics('AML_Engine', 'supabase_sanctions_count', supabase_count, "Retrieved from Supabase")
                logger.info(f"Successfully retrieved Supabase count: {supabase_count}")
            except Exception as e:
                log_error_with_context(logger, e, 'get_supabase_sanctions_count', use_supabase=self.use_supabase)
                supabase_count = None
        else:
            logger.info(f"Skipping Supabase count - use_supabase={self.use_supabase}, supabase_db={bool(self.supabase_db)}")
        
        logger.info(f"Calling db.get_statistics with supabase_sanctions_count={supabase_count}")
        stats = self.db.get_statistics(supabase_sanctions_count=supabase_count)
        
        AMLLogger.log_statistics('AML_Engine', 'final_total_sanctions', stats.get('total_sanctions', 0), "Final statistics result")
        log_function_exit(logger, 'get_alert_statistics', result={'total_sanctions': stats.get('total_sanctions', 0)})
        
        return stats

if __name__ == "__main__":
    # Test the dynamic AML engine
    from transaction_generator import TransactionGenerator
    
    db = AMLDatabase()
    engine = DynamicAMLEngine(db)
    generator = TransactionGenerator(db)
    
    print("🚀 Testing Dynamic AML Engine...")
    
    # Generate some test transactions
    test_transactions = generator.generate_mixed_batch(10)
    
    # Process transactions
    results = engine.process_batch(test_transactions)
    
    print(f"✅ Processed {results['processed_count']} transactions")
    print(f"🚨 Generated {results['alert_count']} alerts")
    
    if results['alerts']:
        print("\n📊 Sample alerts:")
        for alert in results['alerts'][:3]:
            print(f"  • {alert['alert_id']}: {alert['typology']} (Risk: {alert['risk_score']:.0%})")
    
    # Show statistics
    stats = engine.get_alert_statistics()
    print(f"\n📈 System statistics: {stats}")