#!/usr/bin/env python3
"""
Supabase database adapter for sanctions data storage
"""

import os
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import json
from src.utils.logger import AMLLogger, log_function_entry, log_function_exit, log_error_with_context

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
        self.table_name = 'sanctions_entities'
        
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
            # Fix: Use proper numeric comparison for bigint id field instead of empty string
            delete_result = self.supabase.table(self.table_name).delete().gte('id', 1).execute()
            
            print(f"💾 Inserting {len(sanctions)} sanctions records to Supabase...")
            
            # Debug: Check what fields we're getting from the source data
            if sanctions:
                sample_sanction = sanctions[0]
                print(f"🔍 DEBUG: Source sanction keys: {list(sample_sanction.keys())}")
            
            # Prepare data for Supabase - map to sanctions_entities schema
            processed_sanctions = []
            for sanction in sanctions:
                # Clean and validate data to avoid bigint errors
                processed_sanction = {
                    'entity_id': sanction.get('id', ''),
                    'entity_type': sanction.get('schema', 'Person'),
                    'primary_name': sanction.get('caption', ''),
                    'normalized_name': self._normalize_name(sanction.get('caption', '')),
                    'search_names': sanction.get('aliases', []),
                    'countries': sanction.get('countries', []),
                    'risk_level': 'HIGH',  # Default risk level
                    'is_active': True,
                    'data_sources': sanction.get('datasets', []),
                    'last_updated': sanction.get('last_seen'),
                    'passport_numbers': [],
                    'national_ids': [],
                    'tax_numbers': [],
                    'registration_numbers': [],
                    'crypto_addresses': [],
                    'vessel_imo': None,
                    'aircraft_tail': None
                }
                
                # Handle date fields - convert empty strings to None for proper date fields
                if processed_sanction['last_updated'] == '':
                    processed_sanction['last_updated'] = None
                    
                # CRITICAL: Remove 'id' field completely to let bigserial auto-increment handle it
                # The error "invalid input syntax for type bigint" is caused by trying to insert 
                # an empty string into the auto-increment id field
                processed_sanction.pop('id', None)
                
                processed_sanctions.append(processed_sanction)
            
            # Insert in batches to avoid payload size limits
            batch_size = 1000
            total_inserted = 0
            
            for i in range(0, len(processed_sanctions), batch_size):
                batch = processed_sanctions[i:i + batch_size]
                print(f"📤 Inserting batch {i//batch_size + 1}: {len(batch)} records")
                
                try:
                    result = self.supabase.table(self.table_name).insert(batch).execute()
                    total_inserted += len(batch)
                except Exception as e:
                    print(f"❌ Supabase insert error: {e}")
                    if batch:
                        sample_record = batch[0]
                        print(f"🔍 Sample record keys: {list(sample_record.keys())}")
                        print(f"🔍 Sample record values with empty strings:")
                        for key, value in sample_record.items():
                            if value == "":
                                print(f"   - {key}: '{value}' (empty string)")
                    raise e
                
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
                .or_(f"normalized_name.ilike.%{normalized_name}%,primary_name.ilike.%{name}%")\
                .limit(50)\
                .execute()
            
            # Convert to compatible format
            sanctions = []
            for row in result.data:
                sanction = {
                    'id': len(sanctions) + 1,  # Sequential ID for compatibility
                    'entity_id': row['entity_id'],
                    'name': row['primary_name'],
                    'name_normalized': row['normalized_name'],
                    'schema': row['entity_type'],
                    'countries': row['countries'] if row['countries'] else [],
                    'datasets': row['data_sources'] if row['data_sources'] else [],
                    'last_seen': row['last_updated'],
                    'risk_level': row['risk_level'],
                    'is_active': row['is_active'],
                    'created_at': row.get('created_at'),
                    'country': row['countries'][0] if row['countries'] and len(row['countries']) > 0 else None
                }
                sanctions.append(sanction)
            
            return sanctions
            
        except Exception as e:
            print(f"❌ Error searching sanctions in Supabase: {e}")
            return []
    
    def get_sanctions_count(self) -> int:
        """Get total count of sanctions records"""
        logger = AMLLogger.get_logger('supabase_count', 'supabase')
        log_function_entry(logger, 'get_sanctions_count', table=self.table_name)
        
        try:
            logger.info(f"Executing count query on table: {self.table_name}")
            # Use head request for count only (more efficient)
            result = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .limit(1)\
                .execute()
            
            count = result.count or 0
            data_length = len(result.data) if result.data else 0
            
            AMLLogger.log_supabase_operation('COUNT_QUERY', self.table_name, True, f"count={count}")
            logger.info(f"Supabase count query successful: count={count}, data_length={data_length}")
            
            log_function_exit(logger, 'get_sanctions_count', result=count)
            return count
            
        except Exception as e:
            AMLLogger.log_supabase_operation('COUNT_QUERY', self.table_name, False, f"error={str(e)}")
            log_error_with_context(logger, e, 'get_sanctions_count', table=self.table_name)
            return 0
    
    def get_sanctions_statistics(self) -> Dict:
        """Get sanctions statistics from Supabase"""
        try:
            count = self.get_sanctions_count()
            
            # Get entity type breakdown
            result = self.supabase.table(self.table_name)\
                .select("entity_type")\
                .execute()
            
            entity_types = {}
            for row in result.data:
                entity_type = row['entity_type']
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            return {
                'total_sanctions': count,
                'entity_types': entity_types,
                'source': 'Supabase'
            }
            
        except Exception as e:
            print(f"❌ Error getting sanctions statistics from Supabase: {e}")
            return {
                'total_sanctions': 0,
                'entity_types': {},
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