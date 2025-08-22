#!/usr/bin/env python3
"""
Load sanctions data from OpenSanctions daily datasets and other sources

Fallback hierarchy:
1. Prefetched data stored in database (primary)
2. Daily OpenSanctions datasets with date fallback (secondary)  
3. Dummy data (last resort)

Focused datasets:
- Debarred Companies and Individuals (updated daily)
- Politically Exposed Persons (PEPs) Core Data (updated daily)
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from database import AMLDatabase
from supabase_sanctions import SupabaseSanctionsDB
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SanctionsLoader:
    def __init__(self, db: AMLDatabase):
        self.db = db  # Keep local DB for transactions/alerts
        
        # Initialize Supabase for sanctions if enabled
        self.use_supabase = os.getenv('USE_SUPABASE_FOR_SANCTIONS', 'false').lower() == 'true'
        self.supabase_db = None
        
        if self.use_supabase:
            try:
                self.supabase_db = SupabaseSanctionsDB()
                print("✅ Supabase sanctions database initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize Supabase, falling back to local DB: {e}")
                self.use_supabase = False
        # OpenSanctions daily datasets base URL
        self.opensanctions_base = "https://data.opensanctions.org/datasets"
        
        # Dataset configurations
        self.datasets = {
            'debarment': {
                'name': 'Debarred Companies and Individuals',
                'path': 'debarment/senzing.json',
                'update_frequency': 'daily'
            },
            'peps': {
                'name': 'Politically Exposed Persons Core Data', 
                'path': 'peps/senzing.json',
                'update_frequency': 'daily'
            }
        }
        
        # Maximum days to look back for datasets
        self.max_days_lookback = 7
    
    def get_dataset_url(self, dataset_key: str, target_date: datetime = None) -> str:
        """Generate dataset URL for a specific date"""
        if target_date is None:
            target_date = datetime.now()
        
        date_str = target_date.strftime('%Y%m%d')
        dataset_path = self.datasets[dataset_key]['path']
        
        return f"{self.opensanctions_base}/{date_str}/{dataset_path}"
    
    def load_daily_dataset(self, dataset_key: str, target_date: datetime = None) -> Dict:
        """Load a specific dataset with date fallback"""
        if target_date is None:
            target_date = datetime.now()
            
        dataset_name = self.datasets[dataset_key]['name']
        print(f"🔄 Loading {dataset_name} dataset...")
        
        # Try multiple dates going backwards
        for days_back in range(self.max_days_lookback):
            attempt_date = target_date - timedelta(days=days_back)
            dataset_url = self.get_dataset_url(dataset_key, attempt_date)
            
            try:
                print(f"📅 Attempting {dataset_name} for {attempt_date.strftime('%Y-%m-%d')}")
                response = requests.get(dataset_url, timeout=30)
                
                if response.status_code == 200:
                    # Parse NDJSON format (newline-delimited JSON)
                    entities = []
                    lines = response.text.strip().split('\n')
                    
                    # Apply batch limit if set (prefer per-dataset limit, then global limit)
                    per_dataset_limit = getattr(self, '_dataset_batch_limit', None)
                    global_batch_limit = getattr(self, '_batch_limit', None)
                    
                    print(f"🔍 DEBUG: {dataset_key} - per_dataset_limit={per_dataset_limit}, global_batch_limit={global_batch_limit}")
                    print(f"🔍 DEBUG: {dataset_key} - total lines available: {len(lines)}")
                    
                    effective_limit = per_dataset_limit or global_batch_limit
                    if effective_limit:
                        original_line_count = len(lines)
                        lines = lines[:effective_limit]
                        print(f"📦 Applying batch limit: {effective_limit} records for {dataset_key} (reduced from {original_line_count} to {len(lines)})")
                    else:
                        print(f"⚠️ DEBUG: No effective limit for {dataset_key} - processing all {len(lines)} lines")
                    
                    for line in lines:
                        if line.strip():
                            try:
                                entity = json.loads(line)
                                entities.append(entity)
                            except json.JSONDecodeError as e:
                                print(f"⚠️ Failed to parse line: {e}")
                                continue
                    
                    print(f"📥 Retrieved {len(entities)} entities from {dataset_name} ({attempt_date.strftime('%Y-%m-%d')})")
                    
                    # Process entities for database storage
                    processed_entities = []
                    for entity in entities:
                        processed_entity = self._process_senzing_entity(entity, dataset_key, attempt_date)
                        if processed_entity:  # Only add valid entities
                            processed_entities.append(processed_entity)
                    
                    return {
                        'success': True,
                        'count': len(processed_entities),
                        'source': f'{dataset_name}',
                        'date': attempt_date.strftime('%Y-%m-%d'),
                        'entities': processed_entities
                    }
                else:
                    print(f"❌ Dataset not available for {attempt_date.strftime('%Y-%m-%d')} (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"❌ Error loading {dataset_name} for {attempt_date.strftime('%Y-%m-%d')}: {e}")
                
        print(f"❌ Failed to load {dataset_name} for last {self.max_days_lookback} days")
        return {'success': False, 'error': f'No {dataset_name} data available'}
    
    def _process_senzing_entity(self, entity: Dict, dataset_key: str, load_date: datetime) -> Dict:
        """Process raw entity data from OpenSanctions Senzing format"""
        try:
            # Get primary name from NAMES array
            names = entity.get('NAMES', [])
            primary_name = ''
            for name_obj in names:
                if name_obj.get('NAME_TYPE') == 'PRIMARY':
                    primary_name = name_obj.get('NAME_FULL', '')
                    break
            
            if not primary_name and names:
                # Fallback to first available name
                primary_name = names[0].get('NAME_FULL', '')
            
            if not primary_name:
                return None  # Skip entities without names
            
            # Get countries/nationalities
            countries = []
            country_data = entity.get('COUNTRIES', [])
            for country_obj in country_data:
                if country_obj.get('NATIONALITY'):
                    countries.append(country_obj['NATIONALITY'])
            
            # Get addresses for additional country info
            addresses = entity.get('ADDRESSES', [])
            for addr_obj in addresses:
                addr_full = addr_obj.get('ADDR_FULL', '')
                if addr_full:
                    # Extract country code from address (simplified)
                    addr_parts = addr_full.split(', ')
                    if len(addr_parts) > 1:
                        potential_country = addr_parts[-1].strip().lower()
                        if len(potential_country) <= 3:  # Likely country code
                            countries.append(potential_country)
            
            # Determine entity type based on record type
            schema = 'Person' if entity.get('RECORD_TYPE') == 'PERSON' else 'Organization'
            
            # Get risk topics
            risks = entity.get('RISKS', [])
            topics = []
            for risk in risks:
                topic = risk.get('TOPIC', '')
                if topic:
                    topics.append(topic)
            
            # Add dataset-specific topic
            if dataset_key not in topics:
                topics.append(dataset_key)
            
            return {
                'id': f"{dataset_key}_{entity.get('RECORD_ID', '')}",
                'caption': primary_name,
                'schema': schema,
                'countries': list(set(countries)),  # Remove duplicates
                'topics': topics,
                'datasets': [dataset_key],
                'first_seen': load_date.strftime('%Y-%m-%d'),
                'last_seen': load_date.strftime('%Y-%m-%d'),
                'properties': {
                    'dataset': dataset_key,
                    'load_date': load_date.strftime('%Y-%m-%d'),
                    'source': 'OpenSanctions_Daily_Senzing',
                    'record_id': entity.get('RECORD_ID'),
                    'record_type': entity.get('RECORD_TYPE'),
                    'last_change': entity.get('LAST_CHANGE'),
                    'url': entity.get('URL'),
                    'names': names,
                    'risks': risks
                }
            }
        except Exception as e:
            print(f"⚠️ Error processing entity: {e}")
            return None
    
    def _process_entity(self, entity: Dict, dataset_key: str, load_date: datetime) -> Dict:
        """Process raw entity data from OpenSanctions dataset"""
        # Extract entity properties
        properties = entity.get('properties', {})
        
        # Get name from various possible fields
        name = (
            properties.get('name', [''])[0] if properties.get('name') else
            properties.get('alias', [''])[0] if properties.get('alias') else  
            entity.get('id', '').replace('_', ' ')
        )
        
        # Get countries
        countries = []
        if properties.get('country'):
            countries.extend(properties['country'])
        if properties.get('nationality'):
            countries.extend(properties['nationality'])
        
        # Determine schema/type
        schema = entity.get('schema', 'Person')
        
        return {
            'id': f"{dataset_key}_{entity.get('id', '')}",
            'caption': name,
            'schema': schema,
            'countries': list(set(countries)),  # Remove duplicates
            'topics': [dataset_key, 'sanction'] if dataset_key == 'debarment' else [dataset_key, 'pep'],
            'datasets': [dataset_key],
            'first_seen': load_date.strftime('%Y-%m-%d'),
            'last_seen': load_date.strftime('%Y-%m-%d'),
            'properties': {
                'dataset': dataset_key,
                'load_date': load_date.strftime('%Y-%m-%d'),
                'source': 'OpenSanctions_Daily',
                'raw_properties': properties
            }
        }
    
    def force_refresh_sanctions_data(self) -> Dict:
        """Force refresh of sanctions data (bypasses prefetched data check)"""
        return self.refresh_sanctions_data(force_refresh=True)
    
    def _load_fallback_sanctions(self) -> Dict:
        """Load hardcoded sanctions data as fallback"""
        print("🔄 Loading fallback sanctions data...")
        
        fallback_entities = [
            {
                'id': 'fallback-001',
                'caption': 'Vladimir Vladimirovich PUTIN',
                'schema': 'Person',
                'countries': ['ru'],
                'topics': ['sanction'],
                'datasets': ['us_ofac_sdn'],
                'first_seen': '2022-02-26',
                'last_seen': '2024-12-01',
                'properties': {
                    'programs': ['RUSSIA-EO14024'],
                    'source': 'FALLBACK'
                }
            },
            {
                'id': 'fallback-002',
                'caption': 'Dmitri Kozlov',
                'schema': 'Person',
                'countries': ['ru'],
                'topics': ['sanction'],
                'datasets': ['us_ofac_sdn'],
                'first_seen': '2022-03-15',
                'last_seen': '2024-12-01',
                'properties': {
                    'programs': ['RUSSIA-EO14024'],
                    'source': 'FALLBACK'
                }
            },
            {
                'id': 'fallback-003',
                'caption': 'Hassan Bin Rashid',
                'schema': 'Person',
                'countries': ['ir'],
                'topics': ['sanction'],
                'datasets': ['us_ofac_sdn'],
                'first_seen': '2020-01-15',
                'last_seen': '2024-12-01',
                'properties': {
                    'programs': ['IRAN'],
                    'source': 'FALLBACK'
                }
            },
            {
                'id': 'fallback-004',
                'caption': 'Anna Volkov',
                'schema': 'Person',
                'countries': ['ru'],
                'topics': ['sanction'],
                'datasets': ['us_ofac_sdn'],
                'first_seen': '2022-04-08',
                'last_seen': '2024-12-01',
                'properties': {
                    'programs': ['RUSSIA-EO14024'],
                    'source': 'FALLBACK'
                }
            },
            {
                'id': 'fallback-005',
                'caption': 'Kim Jong Un',
                'schema': 'Person',
                'countries': ['kp'],
                'topics': ['sanction'],
                'datasets': ['us_ofac_sdn'],
                'first_seen': '2018-08-15',
                'last_seen': '2024-12-01',
                'properties': {
                    'programs': ['NORTH_KOREA'],
                    'source': 'FALLBACK'
                }
            }
        ]
        
        # Store in database
        self.db.add_sanctions_data(fallback_entities)
        
        return {
            'success': True,
            'count': len(fallback_entities),
            'source': 'FALLBACK'
        }
    
    def has_recent_sanctions_data(self, max_age_days: int = 1) -> bool:
        """Check if database has recent sanctions data"""
        try:
            if self.use_supabase and self.supabase_db:
                sanctions_count = self.supabase_db.get_sanctions_count()
            else:
                stats = self.db.get_statistics()
                sanctions_count = stats.get('total_sanctions', 0)
            
            if sanctions_count == 0:
                return False
                
            # For now, we'll assume data exists if count > 5 (more than just dummy data)
            # TODO: Add last_updated field to database schema
            return sanctions_count > 5
        except:
            return False
    
    def load_all_datasets(self) -> Dict:
        """Load all configured datasets"""
        results = {}
        all_entities = []
        total_loaded = 0
        
        print("🔄 Loading OpenSanctions daily datasets...")
        
        # Apply batch limit distribution if set
        batch_limit = getattr(self, '_batch_limit', None)
        print(f"🔍 DEBUG: _batch_limit attribute = {batch_limit}")
        if batch_limit:
            # Distribute batch limit across datasets
            dataset_count = len(self.datasets)
            per_dataset_limit = max(1, batch_limit // dataset_count)
            print(f"📦 Distributing batch limit: {batch_limit} total → {per_dataset_limit} records per dataset ({dataset_count} datasets)")
            
            # Temporarily set per-dataset limit
            original_limit = getattr(self, '_dataset_batch_limit', None)
            self._dataset_batch_limit = per_dataset_limit
            print(f"🔍 DEBUG: Set _dataset_batch_limit = {per_dataset_limit}")
        else:
            print("⚠️ DEBUG: No batch limit found - will load full datasets")
        
        # Load each dataset
        for dataset_key in self.datasets.keys():
            dataset_result = self.load_daily_dataset(dataset_key)
            results[dataset_key] = dataset_result
            
            if dataset_result.get('success'):
                entities = dataset_result.get('entities', [])
                all_entities.extend(entities)
                total_loaded += dataset_result.get('count', 0)
        
        # Restore original per-dataset limit if it was set
        if batch_limit:
            if original_limit is not None:
                self._dataset_batch_limit = original_limit
            elif hasattr(self, '_dataset_batch_limit'):
                delattr(self, '_dataset_batch_limit')
        
        # Store all entities in database if any were loaded
        if all_entities:
            print(f"💾 Storing {len(all_entities)} entities in database...")
            if self.use_supabase and self.supabase_db:
                storage_result = self.supabase_db.add_sanctions_data(all_entities)
                if not storage_result.get('success'):
                    print(f"⚠️ Supabase storage failed, falling back to local DB")
                    self.db.add_sanctions_data(all_entities)
            else:
                self.db.add_sanctions_data(all_entities)
            
        return {
            'success': total_loaded > 0,
            'total_count': total_loaded,
            'datasets': results,
            'source': 'OpenSanctions_Daily'
        }
    
    def refresh_sanctions_data(self, force_refresh: bool = False) -> Dict:
        """Refresh sanctions data using proper fallback hierarchy"""
        print("📥 Starting sanctions data refresh...")
        
        # 1. Check if we have recent prefetched data (primary)
        if not force_refresh and self.has_recent_sanctions_data():
            print("✅ Using existing prefetched sanctions data")
            stats = self.db.get_statistics()
            return {
                'success': True,
                'count': stats.get('total_sanctions', 0),
                'source': 'Database_Prefetched',
                'message': 'Using existing data'
            }
        
        # 2. Try to load fresh daily datasets (secondary)  
        daily_result = self.load_all_datasets()
        if daily_result.get('success'):
            print("✅ Successfully loaded fresh OpenSanctions datasets")
            return daily_result
        
        # 3. Fall back to dummy data (last resort)
        print("🔄 Falling back to dummy sanctions data...")
        fallback_result = self._load_fallback_sanctions()
        
        return fallback_result

if __name__ == "__main__":
    # Test sanctions loading
    db = AMLDatabase()
    loader = SanctionsLoader(db)
    
    print("🚀 Starting sanctions data loading...")
    results = loader.refresh_sanctions_data()
    print(f"✅ Loading complete: {results}")
    
    # Show statistics
    stats = db.get_statistics()
    print(f"📊 Database statistics: {stats}")