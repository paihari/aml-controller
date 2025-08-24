#!/usr/bin/env python3
"""
OpenSanctions Data Ingestion Pipeline
Fetches Consolidated Sanctions data and loads into minimalist AML schema
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

class OpenSanctionsAMLPipeline:
    """Pipeline to fetch and process OpenSanctions Consolidated Sanctions data"""
    
    def __init__(self):
        """Initialize the pipeline"""
        load_dotenv()
        self.logger = AMLLogger.get_logger('opensanctions_pipeline', 'sanctions')
        
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
        
        # Entity type mappings
        self.entity_type_mapping = {
            'Person': 'person',
            'Organization': 'organization',
            'Company': 'company', 
            'Address': 'address',
            'CryptoWallet': 'crypto',
            'Vessel': 'vessel',
            'Aircraft': 'aircraft',
            'LegalEntity': 'organization',  # Merge with organization
            'PublicBody': 'organization',   # Merge with organization
            'Security': 'company',          # Merge with company
            'Airplane': 'aircraft',         # Alternative name
            'Ship': 'vessel'               # Alternative name
        }
        
    def get_latest_dataset_url(self) -> str:
        """Get the URL for the latest OpenSanctions dataset"""
        today = datetime.now().strftime("%Y%m%d")
        url = f"{self.base_url}/{today}/{self.dataset_name}/{self.format}"
        self.logger.info(f"Latest dataset URL: {url}")
        return url
    
    def fetch_opensanctions_data(self, url: str) -> List[Dict]:
        """Fetch and parse OpenSanctions Senzing JSON data"""
        self.logger.info(f"🔄 Fetching OpenSanctions data from: {url}")
        
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
        prefixes = ['mr.', 'mrs.', 'ms.', 'dr.', 'prof.', 'sir', 'lady']
        suffixes = ['jr.', 'sr.', 'iii', 'iv', 'phd', 'md']
        
        words = normalized.split()
        filtered_words = []
        
        for word in words:
            word = word.strip('.,')
            if word not in prefixes and word not in suffixes:
                filtered_words.append(word)
        
        # Remove extra spaces and special characters
        normalized = ' '.join(filtered_words)
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_search_names(self, entity: Dict) -> List[str]:
        """Extract all name variations for fuzzy matching"""
        names = set()
        properties = entity.get('properties', {})
        
        # Primary name
        if entity.get('caption'):
            names.add(entity['caption'])
        
        # Property-based names
        name_fields = ['name', 'firstName', 'lastName', 'middleName', 'alias', 'weakAlias', 
                      'previousName', 'tradingName', 'fullName', 'title']
        
        for field in name_fields:
            if field in properties:
                values = properties[field]
                if isinstance(values, list):
                    names.update(values)
                elif isinstance(values, str):
                    names.add(values)
        
        # Generate name combinations for persons
        if entity.get('schema') == 'Person':
            first_names = properties.get('firstName', [])
            last_names = properties.get('lastName', [])
            middle_names = properties.get('middleName', [])
            
            for first in first_names:
                for last in last_names:
                    names.add(f"{first} {last}")
                    names.add(f"{last}, {first}")
                    
                    for middle in middle_names:
                        names.add(f"{first} {middle} {last}")
                        names.add(f"{last}, {first} {middle}")
        
        # Clean and normalize
        cleaned_names = []
        for name in names:
            if name and isinstance(name, str) and len(name.strip()) > 1:
                normalized = self.normalize_name_for_matching(name)
                if normalized and normalized not in cleaned_names:
                    cleaned_names.append(normalized)
        
        return cleaned_names[:20]  # Limit to 20 variations
    
    def extract_identifiers(self, entity: Dict) -> Dict[str, Any]:
        """Extract all identifiers based on entity type"""
        properties = entity.get('properties', {})
        entity_type = entity.get('schema', '')
        identifiers = {}
        
        # Passport numbers
        passport_fields = ['passportNumber', 'passport']
        passports = []
        for field in passport_fields:
            if field in properties:
                values = properties[field]
                if isinstance(values, list):
                    passports.extend(values)
                elif isinstance(values, str):
                    passports.append(values)
        identifiers['passport_numbers'] = passports
        
        # National IDs
        id_fields = ['idNumber', 'nationalId', 'citizenshipId', 'residenceId']
        national_ids = []
        for field in id_fields:
            if field in properties:
                values = properties[field]
                if isinstance(values, list):
                    national_ids.extend(values)
                elif isinstance(values, str):
                    national_ids.append(values)
        identifiers['national_ids'] = national_ids
        
        # Tax numbers
        tax_fields = ['taxNumber', 'vatCode', 'innCode', 'fiscalCode']
        tax_numbers = []
        for field in tax_fields:
            if field in properties:
                values = properties[field]
                if isinstance(values, list):
                    tax_numbers.extend(values)
                elif isinstance(values, str):
                    tax_numbers.append(values)
        identifiers['tax_numbers'] = tax_numbers
        
        # Registration numbers
        reg_fields = ['registrationNumber', 'incorporationNumber', 'companyNumber']
        registration_numbers = []
        for field in reg_fields:
            if field in properties:
                values = properties[field]
                if isinstance(values, list):
                    registration_numbers.extend(values)
                elif isinstance(values, str):
                    registration_numbers.append(values)
        identifiers['registration_numbers'] = registration_numbers
        
        # Crypto addresses
        crypto_fields = ['cryptoWalletAddress', 'walletAddress', 'address']
        crypto_addresses = []
        if entity_type == 'CryptoWallet':
            for field in crypto_fields:
                if field in properties:
                    values = properties[field]
                    if isinstance(values, list):
                        crypto_addresses.extend(values)
                    elif isinstance(values, str):
                        crypto_addresses.append(values)
        identifiers['crypto_addresses'] = crypto_addresses
        
        # Vessel IMO
        if entity_type in ['Vessel', 'Ship']:
            imo_fields = ['imoNumber', 'imo']
            for field in imo_fields:
                if field in properties:
                    imo_value = properties[field]
                    if isinstance(imo_value, list) and imo_value:
                        identifiers['vessel_imo'] = imo_value[0]
                    elif isinstance(imo_value, str):
                        identifiers['vessel_imo'] = imo_value
                    break
        
        # Aircraft tail number
        if entity_type in ['Aircraft', 'Airplane']:
            tail_fields = ['registrationNumber', 'tailNumber', 'callSign']
            for field in tail_fields:
                if field in properties:
                    tail_value = properties[field]
                    if isinstance(tail_value, list) and tail_value:
                        identifiers['aircraft_tail'] = tail_value[0]
                    elif isinstance(tail_value, str):
                        identifiers['aircraft_tail'] = tail_value
                    break
        
        return identifiers
    
    def calculate_risk_level(self, entity: Dict) -> str:
        """Calculate risk level based on entity characteristics"""
        topics = entity.get('topics', [])
        datasets = entity.get('datasets', [])
        
        # Critical: UN Security Council, OFAC SDN
        critical_sources = ['un_sc_sanctions', 'us_ofac_sdn', 'us_ofac_cons']
        if any(ds in critical_sources for ds in datasets):
            return 'CRITICAL'
        
        # High: Direct sanctions
        high_topics = ['sanction', 'crime', 'terror']
        if any(topic in high_topics for topic in topics):
            return 'HIGH'
        
        # Medium: PEP, adverse media
        medium_topics = ['pep', 'adverse', 'warning']
        if any(topic in medium_topics for topic in topics):
            return 'MEDIUM'
        
        return 'LOW'
    
    def transform_entity(self, entity: Dict) -> Optional[Dict]:
        """Transform OpenSanctions entity to AML schema format"""
        try:
            # Basic validation
            if not entity.get('id') or not entity.get('caption'):
                return None
            
            # Map entity type
            os_schema = entity.get('schema', 'Unknown')
            entity_type = self.entity_type_mapping.get(os_schema, 'unknown')
            
            if entity_type == 'unknown':
                self.logger.warning(f"⚠️ Unknown entity schema: {os_schema}")
                return None
            
            # Extract core data
            entity_id = entity['id']
            primary_name = entity['caption']
            normalized_name = self.normalize_name_for_matching(primary_name)
            search_names = self.extract_search_names(entity)
            
            # Extract identifiers
            identifiers = self.extract_identifiers(entity)
            
            # Geographic and risk data
            countries = entity.get('countries', [])
            risk_level = self.calculate_risk_level(entity)
            
            # Source tracking
            data_sources = entity.get('datasets', [])
            last_updated_str = entity.get('last_seen')
            
            # Parse date
            try:
                if last_updated_str:
                    last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d').date()
                else:
                    last_updated = date.today()
            except ValueError:
                last_updated = date.today()
            
            return {
                'entity_id': entity_id,
                'entity_type': entity_type,
                'primary_name': primary_name,
                'normalized_name': normalized_name,
                'search_names': search_names,
                'passport_numbers': identifiers.get('passport_numbers', []),
                'national_ids': identifiers.get('national_ids', []),
                'tax_numbers': identifiers.get('tax_numbers', []),
                'registration_numbers': identifiers.get('registration_numbers', []),
                'crypto_addresses': identifiers.get('crypto_addresses', []),
                'vessel_imo': identifiers.get('vessel_imo'),
                'aircraft_tail': identifiers.get('aircraft_tail'),
                'countries': countries,
                'risk_level': risk_level,
                'is_active': True,
                'data_sources': data_sources,
                'last_updated': last_updated.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error transforming entity {entity.get('id', 'unknown')}: {e}")
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
        """Run the complete OpenSanctions ingestion pipeline"""
        self.logger.info("🚀 Starting OpenSanctions AML Pipeline")
        
        try:
            # Step 1: Get latest dataset URL
            dataset_url = self.get_latest_dataset_url()
            
            # Step 2: Fetch data
            raw_entities = self.fetch_opensanctions_data(dataset_url)
            
            # Step 3: Transform entities
            self.logger.info("🔄 Transforming entities to AML schema...")
            transformed_entities = []
            
            for i, entity in enumerate(raw_entities, 1):
                transformed = self.transform_entity(entity)
                if transformed:
                    transformed_entities.append(transformed)
                
                # Progress indicator
                if i % 5000 == 0:
                    self.logger.info(f"🔄 Transformed {i:,}/{len(raw_entities):,} entities...")
            
            self.logger.info(f"✅ Transformed {len(transformed_entities):,} entities successfully")
            
            # Step 4: Insert into database
            success = self.batch_insert_entities(transformed_entities)
            
            if success:
                self.logger.info("🎉 OpenSanctions AML Pipeline completed successfully!")
                
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
        pipeline = OpenSanctionsAMLPipeline()
        success = pipeline.run_pipeline()
        
        if success:
            print("🎉 OpenSanctions AML Pipeline completed successfully!")
            return 0
        else:
            print("❌ Pipeline failed")
            return 1
            
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())