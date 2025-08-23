#!/usr/bin/env python3
"""
Load sanctions data from OpenSanctions daily datasets

Supabase-only architecture:
- All sanctions data stored exclusively in Supabase
- No local SQLite fallback or dummy data
- Direct integration with OpenSanctions daily datasets

Focused datasets:
- Debarred Companies and Individuals (updated daily)
- Politically Exposed Persons (PEPs) Core Data (updated daily)
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from supabase_sanctions import SupabaseSanctionsDB
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SanctionsLoader:
    def __init__(self):
        """Initialize Supabase-only sanctions loader"""
        # Initialize Supabase sanctions database (required)
        try:
            self.supabase_db = SupabaseSanctionsDB()
            print("✅ Supabase sanctions database initialized")
        except Exception as e:
            raise Exception(f"❌ Failed to initialize Supabase sanctions database: {e}")
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
        from aml_logger import AMLLogger
        logger = AMLLogger.get_logger('sanctions_loader', 'sanctions')
        
        if target_date is None:
            target_date = datetime.now()
            
        dataset_name = self.datasets[dataset_key]['name']
        logger.info(f"Loading {dataset_name} dataset for {dataset_key}")
        print(f"🔄 Loading {dataset_name} dataset...")
        
        # Try multiple dates going backwards
        for days_back in range(self.max_days_lookback):
            attempt_date = target_date - timedelta(days=days_back)
            dataset_url = self.get_dataset_url(dataset_key, attempt_date)
            
            try:
                print(f"📅 Attempting {dataset_name} for {attempt_date.strftime('%Y-%m-%d')}")
                logger.info(f"Requesting URL: {dataset_url}")
                response = requests.get(dataset_url, timeout=120)  # Increased timeout to 2 minutes
                logger.info(f"HTTP response: {response.status_code}")
                
                if response.status_code == 200:
                    # Parse NDJSON format (newline-delimited JSON)
                    entities = []
                    lines = response.text.strip().split('\n')
                    
                    # Get current sanctions count to use as offset
                    current_sanctions_count = 0
                    if self.use_supabase and self.supabase_db:
                        current_sanctions_count = self.supabase_db.get_sanctions_count()
                        print(f"🔍 DEBUG: Current Supabase sanctions count: {current_sanctions_count}")
                    
                    # Calculate offset per dataset (divide total by number of datasets)
                    dataset_count = len(self.datasets)
                    offset_per_dataset = current_sanctions_count // dataset_count
                    print(f"🔍 DEBUG: Using offset {offset_per_dataset} for {dataset_key}")
                    
                    # Apply offset to skip existing records
                    if offset_per_dataset > 0 and offset_per_dataset < len(lines):
                        lines = lines[offset_per_dataset:]
                        print(f"📦 Applied offset: skipped first {offset_per_dataset} records")
                    
                    # Apply batch limit if set (prefer per-dataset limit, then global limit)
                    per_dataset_limit = getattr(self, '_dataset_batch_limit', None)
                    global_batch_limit = getattr(self, '_batch_limit', None)
                    
                    effective_limit = per_dataset_limit or global_batch_limit
                    if effective_limit:
                        original_line_count = len(lines)
                        lines = lines[:effective_limit]
                        print(f"📦 Applying batch limit: {effective_limit} records for {dataset_key} (reduced from {original_line_count} to {len(lines)})")
                    
                    print(f"🔍 DEBUG: Final processing count for {dataset_key}: {len(lines)} records")
                    
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
                    from aml_logger import AMLLogger
                    logger = AMLLogger.get_logger('sanctions_loader', 'sanctions')
                    
                    processed_entities = []
                    logger.info(f"Processing {len(entities)} raw entities for {dataset_key}")
                    
                    for entity in entities:
                        processed_entity = self._process_senzing_entity(entity, dataset_key, attempt_date)
                        if processed_entity:  # Only add valid entities
                            processed_entities.append(processed_entity)
                        else:
                            logger.info(f"Entity filtered out during processing - no valid data")
                    
                    logger.info(f"Processed entities: {len(entities)} raw -> {len(processed_entities)} valid")
                    
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
        from aml_logger import AMLLogger
        logger = AMLLogger.get_logger('sanctions_loader', 'sanctions')
        
        try:
            # Debug: Log the actual entity structure for first few entities
            entity_keys = list(entity.keys())
            logger.info(f"Entity keys: {entity_keys[:10]}...")  # First 10 keys
            
            # Get primary name from NAMES array
            names = entity.get('NAMES', [])
            logger.info(f"Names array length: {len(names)}, first few: {names[:2] if names else 'empty'}")
            
            primary_name = ''
            for name_obj in names:
                if name_obj.get('NAME_TYPE') == 'PRIMARY':
                    primary_name = name_obj.get('NAME_FULL', '')
                    break
            
            if not primary_name and names:
                # Fallback to first available name
                primary_name = names[0].get('NAME_FULL', '')
            
            logger.info(f"Final primary_name: '{primary_name}'")
            
            if not primary_name:
                logger.info(f"Skipping entity - no primary name found")
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
    
    
    def has_recent_sanctions_data(self, max_age_days: int = 1) -> bool:
        """Check if Supabase has recent sanctions data"""
        try:
            sanctions_count = self.supabase_db.get_sanctions_count()
            
            if sanctions_count == 0:
                return False
                
            # Return True if we have any sanctions data
            # TODO: Add last_updated field to database schema for time-based checks
            return sanctions_count > 0
        except Exception as e:
            print(f"⚠️ Error checking sanctions count: {e}")
            return False
    
    def load_all_datasets(self) -> Dict:
        """Load all configured datasets"""
        from aml_logger import AMLLogger
        logger = AMLLogger.get_logger('sanctions_loader', 'sanctions')
        
        logger.info("ENTRY load_all_datasets()")
        
        results = {}
        all_entities = []
        total_loaded = 0
        
        print("🔄 Loading OpenSanctions daily datasets...")
        logger.info(f"Configured datasets count: {len(self.datasets)}")
        
        # Apply batch limit distribution if set
        batch_limit = getattr(self, '_batch_limit', None)
        logger.info(f"Batch limit attribute: {batch_limit}")
        print(f"🔍 DEBUG: _batch_limit attribute = {batch_limit}")
        if batch_limit:
            # Distribute batch limit across datasets
            dataset_count = len(self.datasets)
            per_dataset_limit = max(1, batch_limit // dataset_count)
            logger.info(f"Distributing batch limit: {batch_limit} total → {per_dataset_limit} per dataset ({dataset_count} datasets)")
            print(f"📦 Distributing batch limit: {batch_limit} total → {per_dataset_limit} records per dataset ({dataset_count} datasets)")
            
            # Temporarily set per-dataset limit
            original_limit = getattr(self, '_dataset_batch_limit', None)
            self._dataset_batch_limit = per_dataset_limit
            print(f"🔍 DEBUG: Set _dataset_batch_limit = {per_dataset_limit}")
        else:
            print("⚠️ DEBUG: No batch limit found - will load full datasets")
        
        # Load each dataset
        for dataset_key in self.datasets.keys():
            logger.info(f"Processing dataset: {dataset_key}")
            try:
                dataset_result = self.load_daily_dataset(dataset_key)
                logger.info(f"Dataset {dataset_key} result: success={dataset_result.get('success')}, count={dataset_result.get('count', 0)}")
                results[dataset_key] = dataset_result
                
                if dataset_result.get('success'):
                    entities = dataset_result.get('entities', [])
                    logger.info(f"Dataset {dataset_key} returned {len(entities)} entities")
                    all_entities.extend(entities)
                    # Don't add to total_loaded yet - wait for successful storage
                else:
                    logger.info(f"Dataset {dataset_key} failed: {dataset_result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.info(f"Exception loading dataset {dataset_key}: {str(e)}")
                results[dataset_key] = {'success': False, 'error': str(e)}
        
        # Restore original per-dataset limit if it was set
        if batch_limit:
            if original_limit is not None:
                self._dataset_batch_limit = original_limit
            elif hasattr(self, '_dataset_batch_limit'):
                delattr(self, '_dataset_batch_limit')
        
        # Store all entities in Supabase (required)
        logger.info(f"About to store entities: all_entities count = {len(all_entities)}")
        if all_entities:
            logger.info(f"Storing {len(all_entities)} entities in Supabase")
            print(f"💾 Storing {len(all_entities)} entities in Supabase...")
            
            logger.info(f"Calling supabase_db.add_sanctions_data() with {len(all_entities)} entities")
            storage_result = self.supabase_db.add_sanctions_data(all_entities)
            logger.info(f"Supabase storage result: {storage_result}")
            
            if not storage_result.get('success'):
                error_msg = f"❌ Supabase storage failed: {storage_result.get('error', 'Unknown error')}"
                print(error_msg)
                logger.error(error_msg)
                # Don't fall back - fail fast and let caller handle the error
                return {
                    'success': False,
                    'total_count': 0,
                    'datasets': results,
                    'source': 'OpenSanctions_Daily',
                    'error': storage_result.get('error', 'Supabase storage failed')
                }
            else:
                stored_count = storage_result.get('count', len(all_entities))
                print(f"✅ Successfully stored {stored_count} entities in Supabase")
                logger.info(f"Successfully stored {stored_count} entities in Supabase")
                total_loaded = stored_count  # Use actual stored count
        else:
            print(f"⚠️ DEBUG: No entities to store (all_entities is empty)")
            logger.info("No entities to store - all_entities is empty")
            
        final_result = {
            'success': total_loaded > 0,
            'total_count': total_loaded,
            'datasets': results,
            'source': 'OpenSanctions_Daily'
        }
        
        logger.info(f"EXIT load_all_datasets() - success={final_result['success']}, total_count={final_result['total_count']}")
        return final_result
    
    def refresh_sanctions_data(self, force_refresh: bool = False) -> Dict:
        """Refresh sanctions data from OpenSanctions (Supabase-only)"""
        from aml_logger import AMLLogger
        logger = AMLLogger.get_logger('sanctions_refresh', 'sanctions')
        
        logger.info(f"ENTRY refresh_sanctions_data(force_refresh={force_refresh})")
        print("📥 Starting sanctions data refresh...")
        
        # Check if we should skip refresh (only if not forcing)
        if not force_refresh:
            has_recent_data = self.has_recent_sanctions_data()
            logger.info(f"Has recent data check: {has_recent_data}")
            
            if has_recent_data:
                logger.info("Using existing Supabase data - EARLY RETURN")
                print("✅ Using existing sanctions data from Supabase")
                count = self.supabase_db.get_sanctions_count()
                return {
                    'success': True,
                    'count': count,
                    'source': 'Supabase_Existing',
                    'message': 'Using existing data'
                }
        
        logger.info("Proceeding to load fresh datasets (force_refresh=True or no recent data)")
        
        # Load fresh daily datasets from OpenSanctions
        logger.info("About to call load_all_datasets()")
        daily_result = self.load_all_datasets()
        logger.info(f"load_all_datasets() returned: success={daily_result.get('success')}, count={daily_result.get('total_count', 0)}")
        
        if daily_result.get('success'):
            print("✅ Successfully loaded fresh OpenSanctions datasets")
            logger.info("Successfully loaded fresh datasets - RETURN")
            return daily_result
        else:
            # No fallback - return the error
            error_msg = f"❌ Failed to load OpenSanctions datasets: {daily_result.get('error', 'Unknown error')}"
            print(error_msg)
            logger.error(error_msg)
            return daily_result

if __name__ == "__main__":
    # Test sanctions loading (Supabase-only)
    loader = SanctionsLoader()
    
    print("🚀 Starting sanctions data loading...")
    results = loader.refresh_sanctions_data()
    print(f"✅ Loading complete: {results}")
    
    # Show Supabase statistics
    count = loader.supabase_db.get_sanctions_count()
    print(f"📊 Supabase sanctions count: {count}")