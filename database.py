#!/usr/bin/env python3
"""
Database setup and management for dynamic AML system
"""

import sqlite3
import json
import datetime
import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Supabase AML client
try:
    from supabase_aml import SupabaseAMLDB
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class AMLDatabase:
    def __init__(self, db_path: str = "aml_database.db"):
        self.db_path = db_path
        self.use_supabase = os.getenv('USE_SUPABASE_AML', 'true').lower() == 'true'
        
        # Initialize Supabase AML client if available
        self.supabase_aml = None
        if self.use_supabase and SUPABASE_AVAILABLE:
            try:
                self.supabase_aml = SupabaseAMLDB()
                print("✅ Using Supabase for transactions and alerts storage")
            except Exception as e:
                print(f"⚠️ Failed to initialize Supabase AML, falling back to SQLite: {e}")
                self.use_supabase = False
        else:
            print("✅ Using SQLite for transactions and alerts storage")
        
        self.init_database()
    
    def get_connection(self):
        """Get database connection with proper configuration for concurrent access"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)  # 30 second timeout
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        # Enable WAL mode for better concurrent access
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')  # 30 second busy timeout
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        
        # Sanctions table (from OpenSanctions API)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sanctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT UNIQUE,
                name TEXT,
                name_normalized TEXT,
                type TEXT,
                schema TEXT,
                country TEXT,
                program TEXT,
                list_name TEXT,
                data_source TEXT,
                first_seen DATE,
                last_seen DATE,
                properties TEXT,  -- JSON
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Transactions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE,
                account_id TEXT,
                amount DECIMAL(15,2),
                currency TEXT DEFAULT 'USD',
                transaction_type TEXT,
                transaction_date DATE,
                beneficiary_account TEXT,
                beneficiary_name TEXT,
                beneficiary_bank TEXT,
                beneficiary_country TEXT,
                origin_country TEXT,
                purpose TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Parties table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS parties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_id TEXT UNIQUE,
                name TEXT,
                name_normalized TEXT,
                type TEXT,  -- INDIVIDUAL, CORPORATE
                date_of_birth DATE,
                nationality TEXT,
                address TEXT,
                id_number TEXT,
                occupation TEXT,
                risk_rating TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alerts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT UNIQUE,
                subject_id TEXT,
                subject_type TEXT,  -- PARTY, ACCOUNT, TRANSACTION
                typology TEXT,
                risk_score DECIMAL(3,2),
                evidence TEXT,  -- JSON
                status TEXT DEFAULT 'ACTIVE',
                assigned_to TEXT,
                resolution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alert history for audit trail
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT,
                action TEXT,
                old_status TEXT,
                new_status TEXT,
                notes TEXT,
                user_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sanctions_name ON sanctions(name_normalized)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_parties_name ON parties(name_normalized)")
        
        conn.commit()
        conn.close()
    
    def add_sanctions_data(self, sanctions_data: List[Dict]):
        """Add sanctions data from OpenSanctions API"""
        conn = self.get_connection()
        
        for entity in sanctions_data:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO sanctions 
                    (entity_id, name, name_normalized, type, schema, country, program, 
                     list_name, data_source, first_seen, last_seen, properties)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity.get('id'),
                    entity.get('caption'),
                    self._normalize_name(entity.get('caption', '')),
                    entity.get('schema'),
                    entity.get('schema'),
                    ','.join(entity.get('countries', [])),
                    ','.join(entity.get('topics', [])),
                    ','.join(entity.get('datasets', [])),
                    'OpenSanctions',
                    entity.get('first_seen'),
                    entity.get('last_seen'),
                    json.dumps(entity.get('properties', {}))
                ))
            except Exception as e:
                print(f"Error inserting sanctions data: {e}")
                continue
        
        conn.commit()
        conn.close()
    
    def add_transaction(self, transaction_data: Dict) -> str:
        """Add a new transaction and return transaction ID"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.add_transaction(transaction_data)
        
        # SQLite fallback
        conn = self.get_connection()
        
        try:
            conn.execute("""
                INSERT INTO transactions 
                (transaction_id, account_id, amount, currency, transaction_type,
                 transaction_date, beneficiary_account, beneficiary_name, beneficiary_bank,
                 beneficiary_country, origin_country, purpose)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_data.get('transaction_id'),
                transaction_data.get('account_id'),
                transaction_data.get('amount'),
                transaction_data.get('currency', 'USD'),
                transaction_data.get('transaction_type'),
                transaction_data.get('transaction_date'),
                transaction_data.get('beneficiary_account'),
                transaction_data.get('beneficiary_name'),
                transaction_data.get('beneficiary_bank'),
                transaction_data.get('beneficiary_country'),
                transaction_data.get('origin_country'),
                transaction_data.get('purpose')
            ))
            
            conn.commit()
            return transaction_data.get('transaction_id')
            
        except Exception as e:
            print(f"Error inserting transaction: {e}")
            return None
        finally:
            conn.close()
    
    def add_alert(self, alert_data: Dict) -> str:
        """Add a new alert and return alert ID"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.add_alert(alert_data)
        
        # SQLite fallback with retry logic
        import time
        
        max_retries = 3
        for attempt in range(max_retries):
            conn = self.get_connection()
            
            try:
                conn.execute("""
                    INSERT INTO alerts 
                    (alert_id, subject_id, subject_type, typology, risk_score, evidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    alert_data.get('alert_id'),
                    alert_data.get('subject_id'),
                    alert_data.get('subject_type', 'TRANSACTION'),
                    alert_data.get('typology'),
                    alert_data.get('risk_score'),
                    json.dumps(alert_data.get('evidence', {}))
                ))
                
                conn.commit()
                return alert_data.get('alert_id')
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    print(f"Database locked, retrying in {0.5 * (attempt + 1)} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    print(f"Error inserting alert after {attempt + 1} attempts: {e}")
                    return None
            except Exception as e:
                print(f"Error inserting alert: {e}")
                return None
            finally:
                conn.close()
        
        return None
    
    def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        """Get active alerts"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.get_active_alerts(limit)
        
        # SQLite fallback
        conn = self.get_connection()
        
        cursor = conn.execute("""
            SELECT * FROM alerts 
            WHERE status = 'ACTIVE' 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        alerts = []
        for row in cursor:
            alert = dict(row)
            alert['evidence'] = json.loads(alert['evidence']) if alert['evidence'] else {}
            alerts.append(alert)
        
        conn.close()
        return alerts
    
    def get_sanctions_by_name(self, name: str) -> List[Dict]:
        """Search sanctions by name (fuzzy matching)"""
        conn = self.get_connection()
        normalized_name = self._normalize_name(name)
        
        cursor = conn.execute("""
            SELECT * FROM sanctions 
            WHERE name_normalized LIKE ? OR name_normalized LIKE ?
        """, (f"%{normalized_name}%", f"%{normalized_name.split()[0] if normalized_name.split() else ''}%"))
        
        sanctions = [dict(row) for row in cursor]
        conn.close()
        return sanctions
    
    def get_recent_transactions(self, limit: int = 100) -> List[Dict]:
        """Get recent transactions"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.get_transactions(limit)
        
        # SQLite fallback
        conn = self.get_connection()
        
        cursor = conn.execute("""
            SELECT * FROM transactions 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        transactions = [dict(row) for row in cursor]
        conn.close()
        return transactions
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Dict]:
        """Get a specific transaction by ID"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.get_transaction_by_id(transaction_id)
        
        # SQLite fallback
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction status"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.update_transaction_status(transaction_id, status)
        
        # SQLite fallback
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "UPDATE transactions SET status = ? WHERE transaction_id = ?", 
                (status, transaction_id)
            )
            updated = cursor.rowcount > 0
            conn.commit()
            return updated
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_pending_transactions(self) -> List[Dict]:
        """Get all pending transactions"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            return self.supabase_aml.get_pending_transactions()
        
        # SQLite fallback
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT * FROM transactions WHERE status = 'PENDING' ORDER BY created_at")
            return [dict(row) for row in cursor]
        finally:
            conn.close()
    
    def delete_transaction(self, transaction_id: str) -> bool:
        """Delete a transaction by transaction_id"""
        conn = self.get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM transactions WHERE transaction_id = ?", 
                (transaction_id,)
            )
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_transactions_batch(self, transaction_ids: List[str]) -> Dict:
        """Delete multiple transactions by transaction_ids"""
        conn = self.get_connection()
        deleted_count = 0
        not_found = []
        
        try:
            for transaction_id in transaction_ids:
                cursor = conn.execute(
                    "DELETE FROM transactions WHERE transaction_id = ?", 
                    (transaction_id,)
                )
                if cursor.rowcount > 0:
                    deleted_count += 1
                else:
                    not_found.append(transaction_id)
            
            conn.commit()
            return {
                'deleted_count': deleted_count,
                'requested_count': len(transaction_ids),
                'not_found': not_found
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def clear_all_transactions_and_alerts(self) -> Dict:
        """Clear all transactions and alerts (for testing)"""
        # Use Supabase if available, otherwise fall back to SQLite
        if self.use_supabase and self.supabase_aml:
            try:
                tx_result = self.supabase_aml.delete_all_transactions()
                alert_result = self.supabase_aml.delete_all_alerts()
                
                return {
                    'success': True,
                    'deleted_transactions': tx_result.get('deleted_transactions', 0),
                    'deleted_alerts': alert_result.get('deleted_alerts', 0),
                    'source': 'Supabase'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'source': 'Supabase'
                }
        
        # SQLite fallback
        conn = self.get_connection()
        try:
            # Count before deletion
            tx_cursor = conn.execute("SELECT COUNT(*) as count FROM transactions")
            tx_count = tx_cursor.fetchone()['count']
            
            alert_cursor = conn.execute("SELECT COUNT(*) as count FROM alerts")
            alert_count = alert_cursor.fetchone()['count']
            
            # Delete all data
            conn.execute("DELETE FROM transactions")
            conn.execute("DELETE FROM alerts")
            conn.execute("DELETE FROM alert_history")
            
            conn.commit()
            
            return {
                'success': True,
                'deleted_transactions': tx_count,
                'deleted_alerts': alert_count,
                'source': 'SQLite'
            }
            
        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'error': str(e),
                'source': 'SQLite'
            }
        finally:
            conn.close()
    
    def get_statistics(self, supabase_sanctions_count: int = None) -> Dict:
        """Get database statistics"""
        # Use Supabase if available for transactions and alerts statistics
        if self.use_supabase and self.supabase_aml:
            supabase_stats = self.supabase_aml.get_statistics()
            
            # Add sanctions count (either provided or from SQLite)
            if supabase_sanctions_count is not None:
                supabase_stats['total_sanctions'] = supabase_sanctions_count
            else:
                conn = self.get_connection()
                cursor = conn.execute("SELECT COUNT(*) as count FROM sanctions")
                supabase_stats['total_sanctions'] = cursor.fetchone()['count']
                conn.close()
            
            return supabase_stats
        
        # SQLite fallback
        conn = self.get_connection()
        
        stats = {}
        
        # Count total records (use Supabase count if provided)
        if supabase_sanctions_count is not None:
            stats['total_sanctions'] = supabase_sanctions_count
        else:
            cursor = conn.execute("SELECT COUNT(*) as count FROM sanctions")
            stats['total_sanctions'] = cursor.fetchone()['count']
        
        cursor = conn.execute("SELECT COUNT(*) as count FROM transactions")
        stats['total_transactions'] = cursor.fetchone()['count']
        
        cursor = conn.execute("SELECT COUNT(*) as count FROM alerts WHERE status = 'ACTIVE'")
        stats['active_alerts'] = cursor.fetchone()['count']
        
        # Alert breakdown by risk level
        cursor = conn.execute("""
            SELECT 
                CASE 
                    WHEN risk_score >= 0.9 THEN 'Critical'
                    WHEN risk_score >= 0.8 THEN 'High'
                    WHEN risk_score >= 0.6 THEN 'Medium'
                    ELSE 'Low'
                END as risk_level,
                COUNT(*) as count
            FROM alerts 
            WHERE status = 'ACTIVE'
            GROUP BY risk_level
        """)
        
        stats['alerts_by_risk'] = {row['risk_level']: row['count'] for row in cursor}
        
        conn.close()
        return stats
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        if not name:
            return ""
        import re
        return re.sub(r'[^A-Z0-9]', '', name.upper().strip())

if __name__ == "__main__":
    # Test database setup
    db = AMLDatabase()
    print("✅ Database initialized successfully")
    print(f"📊 Statistics: {db.get_statistics()}")