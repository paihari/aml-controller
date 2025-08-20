#!/usr/bin/env python3
"""
Supabase database adapter for sanctions data storage
"""

import os
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

class SupabaseSanctionsDB:
    def __init__(self):
        """Initialize Supabase client for sanctions storage"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.table_name = 'sanctions'
        
        # Initialize table if needed
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Ensure the sanctions table exists in Supabase"""
        # Table creation is handled via Supabase dashboard or migration scripts
        # This is a placeholder for future table initialization logic
        pass
    
    def add_sanctions_data(self, sanctions: List[Dict]) -> Dict:
        """Add sanctions data to Supabase"""
        try:
            # Clear existing data first (for fresh loads)
            print(f"🗑️ Clearing existing sanctions data...")
            delete_result = self.supabase.table(self.table_name).delete().neq('id', '').execute()
            
            print(f"💾 Inserting {len(sanctions)} sanctions records to Supabase...")
            
            # Prepare data for Supabase (convert arrays to JSON strings)
            processed_sanctions = []
            for sanction in sanctions:
                processed_sanction = {
                    'entity_id': sanction.get('id', ''),
                    'name': sanction.get('caption', ''),
                    'name_normalized': self._normalize_name(sanction.get('caption', '')),
                    'schema_type': sanction.get('schema', 'Person'),
                    'countries': json.dumps(sanction.get('countries', [])),
                    'topics': json.dumps(sanction.get('topics', [])),
                    'datasets': json.dumps(sanction.get('datasets', [])),
                    'first_seen': sanction.get('first_seen'),
                    'last_seen': sanction.get('last_seen'),
                    'properties': json.dumps(sanction.get('properties', {})),
                    'data_source': sanction.get('properties', {}).get('source', 'Unknown'),
                    'list_name': sanction.get('properties', {}).get('dataset', 'unknown'),
                    'program': sanction.get('properties', {}).get('dataset', 'unknown')
                }
                processed_sanctions.append(processed_sanction)
            
            # Insert in batches to avoid payload size limits
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(processed_sanctions), batch_size):
                batch = processed_sanctions[i:i + batch_size]
                print(f"📤 Inserting batch {i//batch_size + 1}: {len(batch)} records")
                
                result = self.supabase.table(self.table_name).insert(batch).execute()
                total_inserted += len(batch)
                
                if i % (batch_size * 10) == 0:  # Progress update every 10 batches
                    print(f"✅ Progress: {total_inserted}/{len(processed_sanctions)} records inserted")
            
            print(f"✅ Successfully inserted {total_inserted} sanctions records to Supabase")
            
            return {
                'success': True,
                'count': total_inserted,
                'message': f'Inserted {total_inserted} sanctions records'
            }
            
        except Exception as e:
            print(f"❌ Error inserting sanctions data to Supabase: {e}")
            return {
                'success': False,
                'error': str(e),
                'count': 0
            }
    
    def get_sanctions_by_name(self, name: str) -> List[Dict]:
        """Search sanctions by name (fuzzy matching)"""
        try:
            normalized_name = self._normalize_name(name)
            
            # Search using ilike for partial matching
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .or_(f"name_normalized.ilike.%{normalized_name}%,name.ilike.%{name}%")\
                .limit(50)\
                .execute()
            
            # Convert JSON strings back to objects
            sanctions = []
            for row in result.data:
                sanction = {
                    'id': len(sanctions) + 1,  # Sequential ID for compatibility
                    'entity_id': row['entity_id'],
                    'name': row['name'],
                    'name_normalized': row['name_normalized'],
                    'schema': row['schema_type'],
                    'countries': json.loads(row['countries']) if row['countries'] else [],
                    'topics': json.loads(row['topics']) if row['topics'] else [],
                    'datasets': json.loads(row['datasets']) if row['datasets'] else [],
                    'first_seen': row['first_seen'],
                    'last_seen': row['last_seen'],
                    'properties': json.loads(row['properties']) if row['properties'] else {},
                    'data_source': row['data_source'],
                    'list_name': row['list_name'],
                    'program': row['program'],
                    'created_at': row.get('created_at'),
                    'country': json.loads(row['countries'])[0] if row['countries'] and json.loads(row['countries']) else None
                }
                sanctions.append(sanction)
            
            return sanctions
            
        except Exception as e:
            print(f"❌ Error searching sanctions in Supabase: {e}")
            return []
    
    def get_sanctions_count(self) -> int:
        """Get total count of sanctions records"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*", count="exact")\
                .execute()
            return result.count or 0
        except Exception as e:
            print(f"❌ Error getting sanctions count from Supabase: {e}")
            return 0
    
    def get_sanctions_statistics(self) -> Dict:
        """Get sanctions statistics from Supabase"""
        try:
            count = self.get_sanctions_count()
            
            # Get dataset breakdown
            result = self.supabase.table(self.table_name)\
                .select("list_name")\
                .execute()
            
            datasets = {}
            for row in result.data:
                dataset = row['list_name']
                datasets[dataset] = datasets.get(dataset, 0) + 1
            
            return {
                'total_sanctions': count,
                'datasets': datasets,
                'source': 'Supabase'
            }
            
        except Exception as e:
            print(f"❌ Error getting sanctions statistics from Supabase: {e}")
            return {
                'total_sanctions': 0,
                'datasets': {},
                'source': 'Supabase_Error'
            }
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison (same as AML engine)"""
        if not name:
            return ""
        import re
        return re.sub(r'[^A-Z0-9]', '', name.upper().strip())

if __name__ == "__main__":
    # Test Supabase connection
    try:
        db = SupabaseSanctionsDB()
        print("✅ Supabase sanctions database connection successful")
        
        stats = db.get_sanctions_statistics()
        print(f"📊 Current sanctions count: {stats}")
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")