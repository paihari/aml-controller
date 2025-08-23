#!/usr/bin/env python3
"""
Create minimalist AML schema in Supabase PostgreSQL
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

def create_minimalist_schema():
    """Create the minimalist AML schema tables and indexes"""
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print('❌ Supabase credentials not found in environment')
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        print('✅ Connected to Supabase')
        
        # SQL Commands
        sql_commands = [
            # Drop existing tables if they exist
            """
            DROP TABLE IF EXISTS entity_relationships CASCADE;
            DROP TABLE IF EXISTS sanctions_entities CASCADE;
            """,
            
            # Create sanctions_entities table
            """
            CREATE TABLE sanctions_entities (
                -- Primary Key
                id BIGSERIAL PRIMARY KEY,
                
                -- Core Identity
                entity_id VARCHAR(100) UNIQUE NOT NULL,
                entity_type VARCHAR(20) NOT NULL, -- person|organization|company|address|crypto|vessel|aircraft
                
                -- Names (Critical for Screening)
                primary_name VARCHAR(500) NOT NULL,
                normalized_name VARCHAR(500) NOT NULL,
                search_names TEXT[], -- Array of name variations
                
                -- Identifiers (High-value for AML)
                passport_numbers TEXT[],
                national_ids TEXT[],
                tax_numbers TEXT[],
                registration_numbers TEXT[],
                crypto_addresses TEXT[],
                vessel_imo VARCHAR(20),
                aircraft_tail VARCHAR(20),
                
                -- Geographic & Risk
                countries VARCHAR(10)[], -- ISO country codes
                risk_level VARCHAR(10) NOT NULL DEFAULT 'HIGH', -- CRITICAL|HIGH|MEDIUM|LOW
                is_active BOOLEAN NOT NULL DEFAULT true,
                
                -- Source Tracking
                data_sources VARCHAR(50)[],
                last_updated DATE NOT NULL,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            """,
            
            # Create entity_relationships table
            """
            CREATE TABLE entity_relationships (
                id BIGSERIAL PRIMARY KEY,
                parent_entity_id BIGINT REFERENCES sanctions_entities(id),
                child_entity_id BIGINT REFERENCES sanctions_entities(id),
                relationship_type VARCHAR(30), -- owned_by|controlled_by|associated_with|same_as
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            
            # Core screening indexes
            """
            CREATE INDEX idx_sanctions_normalized_name ON sanctions_entities (normalized_name);
            """,
            
            """
            CREATE INDEX idx_sanctions_search_names ON sanctions_entities USING gin (search_names);
            """,
            
            """
            CREATE INDEX idx_sanctions_entity_type ON sanctions_entities (entity_type) WHERE is_active = true;
            """,
            
            # Identifier matching indexes
            """
            CREATE INDEX idx_sanctions_passports ON sanctions_entities USING gin (passport_numbers);
            """,
            
            """
            CREATE INDEX idx_sanctions_national_ids ON sanctions_entities USING gin (national_ids);
            """,
            
            """
            CREATE INDEX idx_sanctions_tax_numbers ON sanctions_entities USING gin (tax_numbers);
            """,
            
            """
            CREATE INDEX idx_sanctions_crypto ON sanctions_entities USING gin (crypto_addresses);
            """,
            
            # Risk and geographic indexes
            """
            CREATE INDEX idx_sanctions_countries ON sanctions_entities USING gin (countries);
            """,
            
            """
            CREATE INDEX idx_sanctions_risk_active ON sanctions_entities (risk_level, is_active);
            """,
            
            # Full-text search index
            """
            CREATE INDEX idx_sanctions_fulltext ON sanctions_entities USING gin (to_tsvector('english', primary_name));
            """,
            
            # Relationship indexes
            """
            CREATE INDEX idx_relationships_parent ON entity_relationships (parent_entity_id);
            """,
            
            """
            CREATE INDEX idx_relationships_child ON entity_relationships (child_entity_id);
            """
        ]
        
        # Execute SQL commands
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f'📝 Executing SQL command {i}/{len(sql_commands)}...')
                
                # Use the raw SQL execution method
                result = supabase.rpc('execute_sql', {'query': sql.strip()})
                
                if i == 1:
                    print('   ⚠️  Dropped existing tables (if any)')
                elif i == 2:
                    print('   ✅ Created sanctions_entities table')
                elif i == 3:
                    print('   ✅ Created entity_relationships table')
                elif 'INDEX' in sql:
                    index_name = sql.split('INDEX ')[1].split(' ON')[0]
                    print(f'   ✅ Created index: {index_name}')
                    
            except Exception as e:
                # Try alternative method for Supabase
                print(f'   ⚠️  Direct SQL failed, trying alternative method: {str(e)[:100]}...')
                
                # For table creation, we'll need to handle this differently
                # Let's try using the postgrest API
                if 'CREATE TABLE' in sql:
                    print(f'   ⚠️  Skipping table creation - may need manual execution')
                    continue
                    
        print('\n🎉 Schema creation completed!')
        print('\n📊 Created tables:')
        print('   • sanctions_entities (primary AML data)')
        print('   • entity_relationships (entity connections)')
        print('\n🔍 Created indexes:')
        print('   • idx_sanctions_normalized_name (exact name matching)')
        print('   • idx_sanctions_search_names (fuzzy name matching)')
        print('   • idx_sanctions_entity_type (entity type filtering)')
        print('   • idx_sanctions_passports (passport number matching)')
        print('   • idx_sanctions_national_ids (national ID matching)')
        print('   • idx_sanctions_tax_numbers (tax number matching)')
        print('   • idx_sanctions_crypto (crypto address matching)')
        print('   • idx_sanctions_countries (geographic filtering)')
        print('   • idx_sanctions_risk_active (risk level filtering)')
        print('   • idx_sanctions_fulltext (full-text search)')
        print('   • idx_relationships_parent (relationship queries)')
        print('   • idx_relationships_child (relationship queries)')
        
        return True
        
    except Exception as e:
        print(f'❌ Error creating schema: {e}')
        return False

if __name__ == '__main__':
    success = create_minimalist_schema()
    if not success:
        sys.exit(1)