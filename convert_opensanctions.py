#!/usr/bin/env python3
"""
Convert OpenSanctions NDJSON data to Supabase format and insert via API
"""

import json
import re
import requests
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

def normalize_name(name: str) -> str:
    """Normalize name for comparison (same as AML engine)"""
    if not name:
        return ""
    return re.sub(r'[^A-Z0-9]', '', name.upper().strip())

def process_senzing_entity(entity: Dict, dataset_key: str) -> Dict:
    """Process raw entity data from OpenSanctions Senzing format"""
    try:
        # Get primary name from NAMES array
        names = entity.get('NAMES', [])
        primary_name = ''
        for name_obj in names:
            if name_obj.get('NAME_TYPE') == 'PRIMARY':
                primary_name = name_obj.get('NAME_FULL', '') or name_obj.get('NAME_ORG', '')
                break
        
        if not primary_name and names:
            # Fallback to first available name
            first_name = names[0]
            primary_name = first_name.get('NAME_FULL', '') or first_name.get('NAME_ORG', '')
        
        if not primary_name:
            return None  # Skip entities without names
        
        # Get countries/nationalities
        countries = []
        country_data = entity.get('COUNTRIES', [])
        for country_obj in country_data:
            if country_obj.get('NATIONALITY'):
                countries.append(country_obj['NATIONALITY'])
            if country_obj.get('COUNTRY_OF_ASSOCIATION'):
                countries.append(country_obj['COUNTRY_OF_ASSOCIATION'])
        
        # Determine entity type based on record type
        schema = entity.get('RECORD_TYPE', 'Person')
        if schema == 'ORGANIZATION':
            schema = 'Organization'
        elif schema == 'PERSON':
            schema = 'Person'
        else:
            schema = 'Person'  # Default
        
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
            'entity_id': f"{dataset_key}_{entity.get('RECORD_ID', '')}",
            'name': primary_name,
            'name_normalized': normalize_name(primary_name),
            'schema_type': schema,
            'countries': json.dumps(list(set(countries))),  # Remove duplicates
            'topics': json.dumps(topics),
            'datasets': json.dumps([dataset_key]),
            'first_seen': datetime.now().strftime('%Y-%m-%d'),
            'last_seen': datetime.now().strftime('%Y-%m-%d'),
            'properties': json.dumps({
                'dataset': dataset_key,
                'load_date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'OpenSanctions_Daily_Senzing',
                'record_id': entity.get('RECORD_ID'),
                'record_type': entity.get('RECORD_TYPE'),
                'last_change': entity.get('LAST_CHANGE'),
                'url': entity.get('URL'),
                'names': names,
                'risks': risks
            }),
            'data_source': 'OpenSanctions_Daily',
            'list_name': dataset_key,
            'program': dataset_key
        }
    except Exception as e:
        print(f"⚠️ Error processing entity: {e}")
        return None

def fetch_and_convert_data(dataset_url: str, dataset_key: str, limit: int = 100) -> List[Dict]:
    """Fetch OpenSanctions data and convert to Supabase format"""
    try:
        print(f"📥 Fetching {dataset_key} data from {dataset_url}")
        response = requests.get(dataset_url, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch data: HTTP {response.status_code}")
            return []
        
        # Parse NDJSON format
        entities = []
        lines = response.text.strip().split('\n')
        
        for i, line in enumerate(lines[:limit]):  # Limit for testing
            if line.strip():
                try:
                    entity = json.loads(line)
                    processed = process_senzing_entity(entity, dataset_key)
                    if processed:
                        entities.append(processed)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Failed to parse line {i}: {e}")
                    continue
        
        print(f"✅ Processed {len(entities)} entities")
        return entities
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return []

def insert_to_supabase(sanctions: List[Dict], batch_size: int = 100):
    """Insert sanctions data to Supabase in batches"""
    load_dotenv()
    
    supabase_url = os.getenv('SUPABASE_URL')
    api_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not api_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
        return 0
    
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    total_inserted = 0
    
    # Insert in batches
    for i in range(0, len(sanctions), batch_size):
        batch = sanctions[i:i + batch_size]
        
        try:
            response = requests.post(
                f"{supabase_url}/rest/v1/sanctions",
                headers=headers,
                json=batch
            )
            
            if response.status_code in [200, 201]:
                total_inserted += len(batch)
                print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} records")
            else:
                print(f"❌ Failed to insert batch {i//batch_size + 1}: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error inserting batch {i//batch_size + 1}: {e}")
    
    return total_inserted

if __name__ == "__main__":
    print("🚀 Starting OpenSanctions data loading...")
    
    # Load multiple datasets
    datasets = [
        ("https://data.opensanctions.org/datasets/20250819/debarment/senzing.json", "debarment", 1000),
        ("https://data.opensanctions.org/datasets/20250819/peps/senzing.json", "peps", 500),
        ("https://data.opensanctions.org/datasets/20250819/sanctions/senzing.json", "sanctions", 1000)
    ]
    
    total_inserted = 0
    
    for dataset_url, dataset_key, limit in datasets:
        print(f"\n📥 Loading {dataset_key} dataset...")
        sanctions_data = fetch_and_convert_data(dataset_url, dataset_key, limit=limit)
        
        if sanctions_data:
            print(f"💾 Inserting {len(sanctions_data)} {dataset_key} records to Supabase...")
            inserted_count = insert_to_supabase(sanctions_data, batch_size=50)
            total_inserted += inserted_count
            print(f"✅ Successfully inserted {inserted_count} {dataset_key} records")
        else:
            print(f"❌ No {dataset_key} data to insert")
    
    print(f"\n🎉 Total sanctions loaded: {total_inserted:,} records")