#!/usr/bin/env python3
"""
Database setup and management for dynamic AML system
"""

import sqlite3
import json
import datetime
from typing import Dict, List, Optional

class AMLDatabase:
    def __init__(self, db_path: str = "aml_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
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
            
        except Exception as e:
            print(f"Error inserting alert: {e}")
            return None
        finally:
            conn.close()
    
    def get_active_alerts(self, limit: int = 50) -> List[Dict]:
        """Get active alerts"""
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
        conn = self.get_connection()
        
        cursor = conn.execute("""
            SELECT * FROM transactions 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        transactions = [dict(row) for row in cursor]
        conn.close()
        return transactions
    
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
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = self.get_connection()
        
        stats = {}
        
        # Count total records
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