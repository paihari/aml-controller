#!/usr/bin/env python3
"""
Test the OpenSanctions pipeline with a small sample
"""

import json
from opensanctions_pipeline import OpenSanctionsAMLPipeline

def test_pipeline():
    """Test the pipeline with sample data"""
    
    # Sample OpenSanctions entity (realistic format)
    sample_entity = {
        "id": "NK-vladimir-putin",
        "caption": "Vladimir Vladimirovich PUTIN",
        "schema": "Person",
        "countries": ["ru"],
        "topics": ["sanction", "pep"],
        "datasets": ["us_ofac_sdn", "eu_sanctions"],
        "first_seen": "2022-02-26",
        "last_seen": "2024-12-01",
        "properties": {
            "name": ["Vladimir Vladimirovich PUTIN"],
            "firstName": ["Vladimir"],
            "lastName": ["PUTIN"],
            "middleName": ["Vladimirovich"],
            "birthDate": ["1952-10-07"],
            "birthPlace": ["Leningrad, USSR"],
            "nationality": ["ru"],
            "passportNumber": ["123456789"],
            "position": ["President of Russia"]
        }
    }
    
    try:
        # Initialize pipeline
        pipeline = OpenSanctionsAMLPipeline()
        print("✅ Pipeline initialized successfully")
        
        # Test entity transformation
        transformed = pipeline.transform_entity(sample_entity)
        
        if transformed:
            print("✅ Entity transformation successful")
            print("📋 Transformed entity:")
            for key, value in transformed.items():
                print(f"   {key}: {value}")
            
            # Test name normalization
            normalized = pipeline.normalize_name_for_matching("Vladimir Vladimirovich PUTIN")
            print(f"\n🔤 Normalized name: '{normalized}'")
            
            # Test search names extraction
            search_names = pipeline.extract_search_names(sample_entity)
            print(f"🔍 Search names: {search_names}")
            
            # Test identifiers extraction
            identifiers = pipeline.extract_identifiers(sample_entity)
            print(f"🆔 Identifiers: {identifiers}")
            
            return True
        else:
            print("❌ Entity transformation failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == '__main__':
    test_pipeline()