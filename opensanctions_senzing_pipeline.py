#!/usr/bin/env python3
"""
OpenSanctions Senzing Format Data Ingestion Pipeline
Handles the actual Senzing JSON format from OpenSanctions
"""

import os
import sys
import json
import requests
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from dotenv import load_dotenv
from aml_logger import AMLLogger

class OpenSanctionsSenzingPipeline:
    """Pipeline to fetch and process OpenSanctions Senzing format data"""
    
    def __init__(self):
        """Initialize the pipeline"""
        load_dotenv()
        self.logger = AMLLogger.get_logger('senzing_pipeline', 'sanctions')
        
        # Supabase setup
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise Exception("Supabase credentials not found in environment")
            
        self.supabase = create_client(supabase_url, supabase_key)
        self.logger.info("✅ Supabase client initialized")
        
        # OpenSanctions configuration
        self.base_url = "https://data.opensanctions.org/datasets"
        self.dataset_name = "sanctions"
        self.format = "senzing.json"
        
        # Senzing record type mappings to our entity types
        self.record_type_mapping = {
            'PERSON': 'person',
            'ORGANIZATION': 'organization',
            'COMPANY': 'company',
            'ADDRESS': 'address',
            'VESSEL': 'vessel',
            'AIRCRAFT': 'aircraft'
        }
        
    def get_latest_dataset_url(self) -> str:
        """Get the URL for the latest available OpenSanctions dataset"""
        import requests
        from datetime import timedelta
        
        # Try current date and previous few days
        for days_back in range(5):
            date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
            url = f"{self.base_url}/{date}/{self.dataset_name}/{self.format}"
            
            # Test if URL exists
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    self.logger.info(f"✅ Found latest dataset URL: {url}")
                    return url
                else:
                    self.logger.debug(f"Dataset not available for {date} (status: {response.status_code})")
            except Exception as e:
                self.logger.debug(f"Dataset not available for {date}: {e}")
        
        # Fallback to today's URL if nothing found
        today = datetime.now().strftime("%Y%m%d")
        url = f"{self.base_url}/{today}/{self.dataset_name}/{self.format}"
        self.logger.warning(f"⚠️ No recent datasets found, trying today's URL: {url}")
        return url
    
    def fetch_opensanctions_data(self, url: str) -> List[Dict]:
        """Fetch and parse OpenSanctions Senzing JSON data"""
        self.logger.info(f"🔄 Fetching OpenSanctions Senzing data from: {url}")
        
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            # Parse newline-delimited JSON
            entities = []
            for line_num, line in enumerate(response.text.strip().split('\n'), 1):
                if line.strip():
                    try:
                        entity = json.loads(line)
                        entities.append(entity)
                        
                        # Progress indicator
                        if line_num % 10000 == 0:
                            self.logger.info(f"📥 Parsed {line_num:,} entities...")
                            
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"⚠️ JSON decode error on line {line_num}: {e}")
                        continue
            
            self.logger.info(f"✅ Successfully fetched {len(entities):,} entities")
            return entities
            
        except requests.RequestException as e:
            self.logger.error(f"❌ Failed to fetch data: {e}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Error processing data: {e}")
            raise
    
    def normalize_name_for_matching(self, name: str) -> str:
        """Normalize name for exact matching"""
        if not name:
            return ""
            
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common prefixes/suffixes
        prefixes = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sir', 'lady', 'llc', 'inc', 'ltd', 'corp']
        suffixes = ['jr.', 'sr.', 'iii', 'iv', 'phd', 'md', 'llc', 'inc', 'ltd', 'corp']
        
        words = normalized.split()
        filtered_words = []
        
        for word in words:
            word = word.strip('.,\"')
            if word not in prefixes and word not in suffixes:
                filtered_words.append(word)
        
        # Remove extra spaces and special characters
        normalized = ' '.join(filtered_words)
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_names_from_senzing(self, entity: Dict) -> Dict[str, Any]:
        """Extract names from Senzing format"""
        names_data = entity.get('NAMES', [])
        
        primary_name = ""
        search_names = set()
        
        for name_entry in names_data:
            name_type = name_entry.get('NAME_TYPE', '')
            
            # Extract name based on record type
            if entity.get('RECORD_TYPE') == 'PERSON':
                # Person names
                name_full = name_entry.get('NAME_FULL', '')
                name_first = name_entry.get('NAME_FIRST', '')
                name_last = name_entry.get('NAME_LAST', '')
                name_middle = name_entry.get('NAME_MIDDLE', '')
                
                if name_full:
                    if name_type == 'PRIMARY' and not primary_name:
                        primary_name = name_full
                    search_names.add(name_full)
                
                # Construct full names from parts
                if name_first and name_last:
                    full_name = f"{name_first} {name_last}"
                    if name_middle:
                        full_name_with_middle = f"{name_first} {name_middle} {name_last}"
                        search_names.add(full_name_with_middle)
                    search_names.add(full_name)
                    search_names.add(f"{name_last}, {name_first}")
                    
            else:
                # Organization/Company names
                name_org = name_entry.get('NAME_ORG', '')
                if name_org:
                    if name_type == 'PRIMARY' and not primary_name:
                        primary_name = name_org
                    search_names.add(name_org)
        
        # Clean and limit search names
        cleaned_search_names = []
        for name in search_names:
            if name and len(name.strip()) > 1:
                normalized = self.normalize_name_for_matching(name)
                if normalized and normalized not in cleaned_search_names:
                    cleaned_search_names.append(normalized)
        
        return {
            'primary_name': primary_name,
            'search_names': cleaned_search_names[:20]  # Limit to 20 variations
        }
    
    def extract_identifiers_from_senzing(self, entity: Dict) -> Dict[str, Any]:
        """Extract identifiers from Senzing format"""
        identifiers_data = entity.get('IDENTIFIERS', [])
        
        identifiers = {
            'passport_numbers': [],
            'national_ids': [],
            'tax_numbers': [],
            'registration_numbers': [],
            'crypto_addresses': [],
            'vessel_imo': None,
            'aircraft_tail': None
        }
        
        for id_entry in identifiers_data:
            id_type = id_entry.get('IDENTIFIER_TYPE', '').upper()
            id_number = id_entry.get('IDENTIFIER_NUMBER', '')
            
            if not id_number:
                continue
            
            # Map identifier types
            if id_type in ['PASSPORT', 'PASSPORT_NUMBER']:
                identifiers['passport_numbers'].append(id_number)
            elif id_type in ['NATIONAL_ID', 'ID_NUMBER', 'CITIZENSHIP_ID']:
                identifiers['national_ids'].append(id_number)
            elif id_type in ['TAX_NUMBER', 'VAT_CODE', 'INN_CODE', 'FISCAL_CODE']:
                identifiers['tax_numbers'].append(id_number)
            elif id_type in ['REGISTRATION_NUMBER', 'COMPANY_NUMBER', 'INCORPORATION_NUMBER']:
                identifiers['registration_numbers'].append(id_number)
            elif id_type in ['CRYPTO_WALLET', 'WALLET_ADDRESS', 'BITCOIN_ADDRESS']:
                identifiers['crypto_addresses'].append(id_number)
            elif id_type in ['IMO_NUMBER', 'IMO'] and entity.get('RECORD_TYPE') == 'VESSEL':
                identifiers['vessel_imo'] = id_number
            elif id_type in ['TAIL_NUMBER', 'REGISTRATION_NUMBER'] and entity.get('RECORD_TYPE') == 'AIRCRAFT':
                identifiers['aircraft_tail'] = id_number
        
        return identifiers
    
    def extract_countries_from_senzing(self, entity: Dict) -> List[str]:
        """Extract countries from Senzing format"""
        countries_data = entity.get('COUNTRIES', [])
        countries = []
        
        for country_entry in countries_data:
            country_code = country_entry.get('COUNTRY_OF_ASSOCIATION', '')
            if country_code and len(country_code) == 2:  # ISO 2-letter codes
                countries.append(country_code.lower())
        
        return list(set(countries))  # Remove duplicates
    
    def calculate_risk_level_senzing(self, entity: Dict) -> str:
        """Calculate risk level based on Senzing entity characteristics"""
        risks = entity.get('RISKS', [])
        data_source = entity.get('DATA_SOURCE', '')
        
        # Check for high-risk indicators
        high_risk_sources = ['OFAC', 'UN_SANCTIONS', 'EU_SANCTIONS']
        if any(source in data_source.upper() for source in high_risk_sources):
            return 'CRITICAL'
        
        # Check risk entries
        for risk_entry in risks:
            risk_type = risk_entry.get('RISK_TYPE', '').upper()
            
            if risk_type in ['SANCTIONS', 'TERRORISM', 'CRIME']:
                return 'CRITICAL'
            elif risk_type in ['PEP', 'ADVERSE_MEDIA']:
                return 'HIGH'
            elif risk_type in ['WARNING', 'INVESTIGATION']:
                return 'MEDIUM'
        
        return 'HIGH'  # Default for sanctions list
    
    def transform_senzing_entity(self, entity: Dict) -> Optional[Dict]:
        """Transform Senzing entity to AML schema format"""
        try:
            # Basic validation
            record_id = entity.get('RECORD_ID')
            record_type = entity.get('RECORD_TYPE')
            
            if not record_id or not record_type:
                return None
            
            # Map record type
            entity_type = self.record_type_mapping.get(record_type, 'unknown')
            if entity_type == 'unknown':
                self.logger.warning(f"⚠️ Unknown record type: {record_type}")
                return None
            
            # Extract names
            names_data = self.extract_names_from_senzing(entity)
            if not names_data['primary_name']:
                return None  # Skip entities without primary name
            
            # Extract identifiers
            identifiers = self.extract_identifiers_from_senzing(entity)
            
            # Extract countries
            countries = self.extract_countries_from_senzing(entity)
            
            # Calculate risk level
            risk_level = self.calculate_risk_level_senzing(entity)
            
            # Parse last change date
            last_change_str = entity.get('LAST_CHANGE', '')
            try:
                if last_change_str:
                    # Parse ISO format: 2025-05-28T12:22:03
                    last_updated = datetime.fromisoformat(last_change_str.replace('Z', '')).date()
                else:
                    last_updated = date.today()
            except ValueError:
                last_updated = date.today()
            
            return {
                'entity_id': record_id,
                'entity_type': entity_type,
                'primary_name': names_data['primary_name'],
                'normalized_name': self.normalize_name_for_matching(names_data['primary_name']),
                'search_names': names_data['search_names'],
                'passport_numbers': identifiers['passport_numbers'],
                'national_ids': identifiers['national_ids'],
                'tax_numbers': identifiers['tax_numbers'],
                'registration_numbers': identifiers['registration_numbers'],
                'crypto_addresses': identifiers['crypto_addresses'],
                'vessel_imo': identifiers['vessel_imo'],
                'aircraft_tail': identifiers['aircraft_tail'],
                'countries': countries,
                'risk_level': risk_level,
                'is_active': True,
                'data_sources': [entity.get('DATA_SOURCE', 'OPEN_SANCTIONS')],
                'last_updated': last_updated.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error transforming entity {entity.get('RECORD_ID', 'unknown')}: {e}")
            return None
    
    def batch_insert_entities(self, entities: List[Dict], batch_size: int = 1000) -> bool:
        """Insert entities into Supabase in batches"""
        self.logger.info(f"💾 Inserting {len(entities):,} entities in batches of {batch_size}")
        
        # Clear existing data
        try:
            self.logger.info("🗑️ Clearing existing sanctions data...")
            self.supabase.table('sanctions_entities').delete().gte('id', 1).execute()
            self.logger.info("✅ Existing data cleared")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not clear existing data: {e}")
        
        # Insert in batches
        total_inserted = 0
        
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                self.logger.info(f"📤 Inserting batch {batch_num}: {len(batch)} entities")
                
                result = self.supabase.table('sanctions_entities').insert(batch).execute()
                
                if result.data:
                    total_inserted += len(result.data)
                    self.logger.info(f"✅ Batch {batch_num} inserted successfully")
                else:
                    self.logger.error(f"❌ Batch {batch_num} failed: no data returned")
                
                # Progress update
                if batch_num % 10 == 0:
                    self.logger.info(f"📊 Progress: {total_inserted:,}/{len(entities):,} entities inserted")
                    
            except Exception as e:
                self.logger.error(f"❌ Batch {batch_num} failed: {e}")
                return False
        
        self.logger.info(f"🎉 Successfully inserted {total_inserted:,} entities")
        return total_inserted == len(entities)
    
    def run_pipeline(self) -> bool:
        """Run the complete OpenSanctions Senzing ingestion pipeline"""
        self.logger.info("🚀 Starting OpenSanctions Senzing AML Pipeline")
        
        try:
            # Step 1: Get latest dataset URL
            dataset_url = self.get_latest_dataset_url()
            
            # Step 2: Fetch data
            raw_entities = self.fetch_opensanctions_data(dataset_url)
            
            # Step 3: Transform entities
            self.logger.info("🔄 Transforming Senzing entities to AML schema...")
            transformed_entities = []
            
            for i, entity in enumerate(raw_entities, 1):
                transformed = self.transform_senzing_entity(entity)
                if transformed:
                    transformed_entities.append(transformed)
                
                # Progress indicator
                if i % 5000 == 0:
                    self.logger.info(f"🔄 Transformed {i:,}/{len(raw_entities):,} entities...")
            
            self.logger.info(f"✅ Transformed {len(transformed_entities):,} entities successfully")
            
            # Step 4: Insert into database
            success = self.batch_insert_entities(transformed_entities)
            
            if success:
                self.logger.info("🎉 OpenSanctions Senzing AML Pipeline completed successfully!")
                
                # Summary statistics
                entity_types = {}
                risk_levels = {}
                
                for entity in transformed_entities:
                    entity_type = entity['entity_type']
                    risk_level = entity['risk_level']
                    
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                    risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
                
                self.logger.info("📊 Summary Statistics:")
                self.logger.info(f"   Total entities: {len(transformed_entities):,}")
                self.logger.info("   Entity types:")
                for etype, count in sorted(entity_types.items()):
                    self.logger.info(f"     {etype}: {count:,}")
                self.logger.info("   Risk levels:")
                for risk, count in sorted(risk_levels.items()):
                    self.logger.info(f"     {risk}: {count:,}")
                
                return True
            else:
                self.logger.error("❌ Pipeline failed during data insertion")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Pipeline failed: {e}")
            return False

def main():
    """Main entry point"""
    try:
        pipeline = OpenSanctionsSenzingPipeline()
        success = pipeline.run_pipeline()
        
        if success:
            print("🎉 OpenSanctions Senzing AML Pipeline completed successfully!")
            return 0
        else:
            print("❌ Pipeline failed")
            return 1
            
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())