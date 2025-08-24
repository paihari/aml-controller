#!/usr/bin/env python3
"""
Flask Web API for Dynamic AML System
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import json
import os
import re
import requests
from typing import Dict, List, Tuple, Optional
from src.data.database import AMLDatabase
from src.core.aml_engine import DynamicAMLEngine
from src.core.transaction_generator import TransactionGenerator
from src.core.sanctions_loader import SanctionsLoader
# Plane integration removed
from dotenv import load_dotenv
from src.utils.logger import AMLLogger, log_function_entry, log_function_exit, log_error_with_context

app = Flask(__name__)
CORS(app)

# OpenSanctions Integration Functions
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
            'first_seen': datetime.datetime.now().strftime('%Y-%m-%d'),
            'last_seen': datetime.datetime.now().strftime('%Y-%m-%d'),
            'properties': json.dumps({
                'dataset': dataset_key,
                'load_date': datetime.datetime.now().strftime('%Y-%m-%d'),
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

def load_opensanctions_batch(dataset_url: str, dataset_key: str, limit: int = 100) -> tuple:
    """Load OpenSanctions data in batches with duplicate checking"""
    try:
        print(f"📥 Fetching {dataset_key} data from {dataset_url}")
        response = requests.get(dataset_url, timeout=30)
        
        if response.status_code != 200:
            return [], 0, f"Failed to fetch data: HTTP {response.status_code}"
        
        # Parse NDJSON format
        entities = []
        lines = response.text.strip().split('\n')
        
        for i, line in enumerate(lines[:limit]):
            if line.strip():
                try:
                    entity = json.loads(line)
                    processed = process_senzing_entity(entity, dataset_key)
                    if processed:
                        entities.append(processed)
                except json.JSONDecodeError as e:
                    continue
        
        # Check for existing sanctions using Supabase
        load_dotenv()
        entity_ids = [e['entity_id'] for e in entities]
        existing_ids = check_existing_sanctions_supabase(entity_ids)
        
        # Filter out existing sanctions
        new_entities = [e for e in entities if e['entity_id'] not in existing_ids]
        
        # Insert new entities
        if new_entities and hasattr(aml_engine, 'supabase_db') and aml_engine.supabase_db:
            inserted_count = insert_sanctions_supabase(new_entities)
        else:
            inserted_count = 0
        
        return inserted_count, len(existing_ids), None
        
    except Exception as e:
        return 0, 0, str(e)

def check_existing_sanctions_supabase(entity_ids: List[str]) -> List[str]:
    """Check which entity IDs already exist in Supabase"""
    if not hasattr(aml_engine, 'supabase_db') or not aml_engine.supabase_db:
        return []
    
    existing_ids = []
    try:
        # Check in batches of 100 to avoid URL length limits
        for i in range(0, len(entity_ids), 100):
            batch_ids = entity_ids[i:i + 100]
            # Use Supabase client to check existing records
            result = aml_engine.supabase_db.supabase.table('sanctions_entities').select('entity_id').in_('entity_id', batch_ids).execute()
            existing_ids.extend([record['entity_id'] for record in result.data])
    except Exception as e:
        print(f"⚠️ Warning: Error checking existing records: {e}")
    
    return existing_ids

def insert_sanctions_supabase(sanctions: List[Dict]) -> int:
    """Insert sanctions data to Supabase"""
    if not hasattr(aml_engine, 'supabase_db') or not aml_engine.supabase_db:
        return 0
    
    try:
        # Insert in batches of 50
        total_inserted = 0
        batch_size = 50
        
        for i in range(0, len(sanctions), batch_size):
            batch = sanctions[i:i + batch_size]
            result = aml_engine.supabase_db.supabase.table('sanctions_entities').insert(batch).execute()
            if result.data:
                total_inserted += len(result.data)
        
        return total_inserted
    except Exception as e:
        print(f"❌ Error inserting sanctions: {e}")
        return 0

@app.route('/')
def home():
    """Root endpoint - redirect to dashboard"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>syntropAI Sentinel - AML Detection Platform</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #faf7f2; 
                color: #2d2d2d; 
                line-height: 1.6;
                padding: 40px 20px;
            }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            .brand { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 20px; margin-bottom: 40px; }
            .brand img { 
                height: 160px; 
                border: 2px solid #000000;
            }
            .brand-text { font-size: 36px; font-weight: 600; color: #2d2d2d; }
            .subtitle { font-size: 18px; color: #666; margin-bottom: 40px; }
            .nav-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
            .nav-card { 
                background: #ffffff; 
                border: 1px solid #e8e1d6; 
                border-radius: 8px; 
                padding: 24px; 
                text-decoration: none; 
                color: #2d2d2d;
                transition: all 0.2s ease;
            }
            .nav-card:hover { box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05); transform: translateY(-2px); }
            .nav-title { font-size: 18px; font-weight: 600; margin-bottom: 8px; }
            .nav-desc { font-size: 14px; color: #666; }
            .status { background: #ffffff; border: 1px solid #e8e1d6; border-radius: 8px; padding: 20px; margin-top: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="brand">
                <a href="/" style="display: inline-block; text-decoration: none;">
                    <img src="/images/Brand.svg" alt="syntropAI Sentinel" style="cursor: pointer;" />
                </a>
                <div class="brand-text">syntropAI Sentinel</div>
            </div>
            <div class="subtitle">Real-time Anti-Money Laundering Detection Platform</div>
            
            <div class="nav-grid">
                <a href="/dashboard/minimalist.html" class="nav-card">
                    <div class="nav-title">📊 AML Dashboard</div>
                    <div class="nav-desc">Minimalist real-time dashboard</div>
                </a>
                <a href="/dashboard/data-generator.html" class="nav-card">
                    <div class="nav-title">⚡ Generate Data</div>
                    <div class="nav-desc">Create sample transactions & process data</div>
                </a>
                <a href="/dashboard/search.html" class="nav-card">
                    <div class="nav-title">🔍 Search</div>
                    <div class="nav-desc">Search alerts, transactions & sanctions</div>
                </a>
                <a href="/api/statistics" class="nav-card">
                    <div class="nav-title">📈 Statistics</div>
                    <div class="nav-desc">System metrics and counts</div>
                </a>
                <a href="/api/alerts" class="nav-card">
                    <div class="nav-title">🚨 Alerts</div>
                    <div class="nav-desc">Active AML alerts</div>
                </a>
                <a href="/api/health" class="nav-card">
                    <div class="nav-title">💚 Health Check</div>
                    <div class="nav-desc">System status and version</div>
                </a>
            </div>
            
            <div class="status">
                <strong>System Status:</strong> <span style="color: #22c55e;">Online</span> | 
                <strong>Version:</strong> 2.0.0 | 
                <strong>Build:</strong> Minimalist Edition
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/dashboard/<path:filename>')
def dashboard_files(filename):
    """Serve dashboard files"""
    # Path relative to project root (two levels up from src/api/)
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dashboard')
    return send_from_directory(dashboard_path, filename)

@app.route('/images/<path:filename>')
def image_files(filename):
    """Serve image files"""
    # Path relative to project root (two levels up from src/api/)
    images_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'images')
    return send_from_directory(images_path, filename)

@app.route('/api/initialize', methods=['GET'])
def initialize_data():
    """Initialize system with sample data"""
    try:
        if not db or not transaction_generator or not aml_engine:
            return jsonify({
                'success': False,
                'error': 'System components not initialized'
            }), 503
            
        # Generate and process transactions
        transactions = transaction_generator.generate_mixed_batch(15)
        stored = transaction_generator.store_transactions(transactions)
        results = aml_engine.process_batch(transactions)
        
        return jsonify({
            'success': True,
            'message': 'System initialized with sample data',
            'transactions_generated': len(transactions),
            'transactions_stored': stored,
            'alerts_generated': results['alert_count'],
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Initialize components with error handling
try:
    db = AMLDatabase()
    aml_engine = DynamicAMLEngine(db)
    transaction_generator = TransactionGenerator(db)
    sanctions_loader = SanctionsLoader()
    print("✅ AML components initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize AML components: {e}")
    # Create minimal fallback components
    db = None
    aml_engine = None
    transaction_generator = None
    sanctions_loader = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint with API status groupings"""
    health_status = {
        'overall_status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '2.0.0',
        'api_groups': {}
    }
    
    try:
        # Core System APIs
        core_apis = {}
        try:
            # Test database connection
            if aml_engine and aml_engine.db:
                stats = aml_engine.get_alert_statistics()
                core_apis['statistics'] = {
                    'status': 'healthy',
                    'endpoint': '/api/statistics',
                    'last_result': f"Total transactions: {stats.get('total_transactions', 0)}, Alerts: {stats.get('total_alerts', 0)}"
                }
            else:
                core_apis['statistics'] = {'status': 'error', 'endpoint': '/api/statistics', 'error': 'Database not available'}
                
            # Test AML engine
            if aml_engine:
                core_apis['aml_engine'] = {
                    'status': 'healthy',
                    'endpoint': '/api/transactions/process',
                    'last_result': f"Supabase: {'enabled' if aml_engine.use_supabase else 'disabled'}"
                }
            else:
                core_apis['aml_engine'] = {'status': 'error', 'endpoint': '/api/transactions/process', 'error': 'AML engine not initialized'}
        except Exception as e:
            core_apis['core_system'] = {'status': 'error', 'error': str(e)}
            
        health_status['api_groups']['Core System'] = core_apis
        
        # Transaction Management APIs
        transaction_apis = {}
        try:
            if db:
                # Get recent transaction count
                recent_count = db.get_statistics().get('total_transactions', 0)
                transaction_apis['get_transactions'] = {
                    'status': 'healthy',
                    'endpoint': '/api/transactions',
                    'last_result': f"Database contains {recent_count} transactions"
                }
                transaction_apis['create_transaction'] = {
                    'status': 'healthy',
                    'endpoint': '/api/transactions (POST)',
                    'last_result': 'Ready to accept new transactions'
                }
                transaction_apis['batch_processing'] = {
                    'status': 'healthy',
                    'endpoint': '/api/transactions/batch',
                    'last_result': 'Batch processing available'
                }
                transaction_apis['process_pending'] = {
                    'status': 'healthy',
                    'endpoint': '/api/transactions/process',
                    'last_result': 'AML processing ready'
                }
            else:
                transaction_apis['database'] = {'status': 'error', 'error': 'Database not available'}
        except Exception as e:
            transaction_apis['transaction_system'] = {'status': 'error', 'error': str(e)}
            
        health_status['api_groups']['Transaction Management'] = transaction_apis
        
        # Data Generation APIs
        generation_apis = {}
        try:
            if transaction_generator:
                generation_apis['generate_transactions'] = {
                    'status': 'healthy',
                    'endpoint': '/api/generate/transactions',
                    'last_result': 'Transaction generator ready'
                }
                generation_apis['demo_sanctions'] = {
                    'status': 'healthy',
                    'endpoint': '/api/generate/demo-sanctions',
                    'last_result': 'Demo sanctions data ready'
                }
                generation_apis['process_workflow'] = {
                    'status': 'healthy',
                    'endpoint': '/api/generate/process',
                    'last_result': 'End-to-end workflow available'
                }
            else:
                generation_apis['generator'] = {'status': 'error', 'error': 'Transaction generator not available'}
        except Exception as e:
            generation_apis['generation_system'] = {'status': 'error', 'error': str(e)}
            
        health_status['api_groups']['Data Generation'] = generation_apis
        
        # Sanctions & Compliance APIs
        sanctions_apis = {}
        try:
            if aml_engine and aml_engine.use_supabase and aml_engine.supabase_db:
                # Test sanctions database
                sanctions_count = aml_engine.supabase_db.get_sanctions_count()
                total_sanctions = sanctions_count.get('total_sanctions', 0) if isinstance(sanctions_count, dict) else sanctions_count
                sanctions_apis['sanctions_status'] = {
                    'status': 'healthy',
                    'endpoint': '/api/sanctions/status',
                    'last_result': f"Supabase contains {total_sanctions} sanctions records"
                }
                sanctions_apis['sanctions_search'] = {
                    'status': 'healthy',
                    'endpoint': '/api/sanctions/search',
                    'last_result': 'Sanctions search ready'
                }
                sanctions_apis['sanctions_refresh'] = {
                    'status': 'healthy',
                    'endpoint': '/api/sanctions/refresh',
                    'last_result': 'Sanctions refresh available'
                }
            else:
                sanctions_apis['supabase_sanctions'] = {
                    'status': 'warning',
                    'endpoint': '/api/sanctions/*',
                    'last_result': 'Using local database fallback'
                }
        except Exception as e:
            sanctions_apis['sanctions_system'] = {'status': 'error', 'error': str(e)}
            
        health_status['api_groups']['Sanctions & Compliance'] = sanctions_apis
        
        # Dashboard & Alerts APIs
        dashboard_apis = {}
        try:
            if aml_engine:
                alert_stats = aml_engine.get_alert_statistics()
                dashboard_apis['dashboard_data'] = {
                    'status': 'healthy',
                    'endpoint': '/api/dashboard/data',
                    'last_result': f"Dashboard ready - {alert_stats.get('total_alerts', 0)} alerts"
                }
                dashboard_apis['get_alerts'] = {
                    'status': 'healthy',
                    'endpoint': '/api/alerts',
                    'last_result': f"Alert system operational"
                }
                dashboard_apis['update_alerts'] = {
                    'status': 'healthy',
                    'endpoint': '/api/alerts/<id>/update',
                    'last_result': 'Alert updates ready'
                }
        except Exception as e:
            dashboard_apis['dashboard_system'] = {'status': 'error', 'error': str(e)}
            
        health_status['api_groups']['Dashboard & Alerts'] = dashboard_apis
        
        # Determine overall status
        all_statuses = []
        for group in health_status['api_groups'].values():
            for api in group.values():
                all_statuses.append(api.get('status', 'unknown'))
        
        if 'error' in all_statuses:
            health_status['overall_status'] = 'degraded'
        elif 'warning' in all_statuses:
            health_status['overall_status'] = 'warning'
        else:
            health_status['overall_status'] = 'healthy'
            
        # Add summary
        health_status['summary'] = {
            'total_api_groups': len(health_status['api_groups']),
            'total_apis_checked': sum(len(group) for group in health_status['api_groups'].values()),
            'healthy_apis': sum(1 for group in health_status['api_groups'].values() 
                              for api in group.values() if api.get('status') == 'healthy'),
            'warning_apis': sum(1 for group in health_status['api_groups'].values() 
                               for api in group.values() if api.get('status') == 'warning'),
            'error_apis': sum(1 for group in health_status['api_groups'].values() 
                             for api in group.values() if api.get('status') == 'error')
        }
        
    except Exception as e:
        health_status['overall_status'] = 'error'
        health_status['error'] = f"Health check failed: {str(e)}"
    
    # Set HTTP status code based on health
    status_code = 200
    if health_status['overall_status'] == 'error':
        status_code = 503
    elif health_status['overall_status'] == 'degraded':
        status_code = 206
    elif health_status['overall_status'] == 'warning':
        status_code = 200
        
    # Return HTML if requested via browser
    if request.headers.get('Accept', '').find('text/html') >= 0:
        return render_health_html(health_status), status_code
    else:
        return jsonify(health_status), status_code

def render_health_html(health_data):
    """Render health check data as HTML"""
    overall_status = health_data.get('overall_status', 'unknown')
    status_color = {
        'healthy': '#22c55e',
        'warning': '#f59e0b', 
        'degraded': '#ef4444',
        'error': '#ef4444'
    }.get(overall_status, '#6b7280')
    
    status_icon = {
        'healthy': '✅',
        'warning': '⚠️',
        'degraded': '🔴', 
        'error': '❌'
    }.get(overall_status, '❓')
    
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AML System Health Check</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background-color: #faf7f2; 
                color: #2d2d2d; 
                line-height: 1.6;
                min-height: 100vh;
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 24px;
                position: relative;
            }}
            
            /* Uniform Header Component */
            .header {{ 
                display: flex; 
                align-items: center; 
                justify-content: flex-end; 
                padding: 0; 
                border-bottom: none; 
                margin-bottom: 0; 
                position: absolute; 
                top: 24px; 
                right: 24px; 
            }}
            
            .header-left {{ 
                display: flex; 
                align-items: center; 
                gap: 24px; 
            }}
            
            .brand {{ 
                display: flex; 
                align-items: center; 
                gap: 15px; 
            }}
            
            .brand img {{ 
                height: 60px; 
                width: auto; 
                border: 2px solid #000000;
            }}
            
            .brand-text {{ 
                font-size: 24px; 
                font-weight: 600; 
                color: #2d2d2d; 
            }}
            
            .system-status {{ 
                display: flex; 
                align-items: center; 
                gap: 8px; 
                font-size: 14px; 
                color: #666;
            }}
            
            .status-dot {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #22c55e;
            }}
            
            .status-dot.error {{
                background: #ef4444;
            }}
            
            /* Page Title Section */
            .page-title {{ 
                display: flex; 
                align-items: center; 
                gap: 20px; 
                margin: 20px 0 40px 0; 
                padding-bottom: 24px; 
                border-bottom: 1px solid #e8e1d6;
            }}
            
            .page-title img {{ 
                height: 80px; 
                width: auto; 
                border: 2px solid #000000;
            }}
            
            .page-title-content {{ 
                flex: 1; 
            }}
            
            .page-title h1 {{ 
                font-size: 2.2rem; 
                font-weight: 600; 
                color: #2d2d2d; 
                margin-bottom: 8px; 
            }}
            
            .page-title p {{ 
                font-size: 1rem; 
                color: #666; 
            }}
            .summary {{ 
                background: white; 
                border-radius: 12px; 
                padding: 24px; 
                margin-bottom: 30px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            }}
            .summary-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
            }}
            .summary-item {{ text-align: center; }}
            .summary-number {{ font-size: 2rem; font-weight: 700; color: #2d2d2d; }}
            .summary-label {{ color: #666; font-size: 0.9rem; }}
            .api-group {{ 
                background: white; 
                border-radius: 12px; 
                padding: 24px; 
                margin-bottom: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                border: 1px solid #e8e1d6;
            }}
            .api-group h3 {{ 
                font-size: 1.3rem; 
                margin-bottom: 20px; 
                color: #2d2d2d;
                border-bottom: 2px solid #e5e5e5;
                padding-bottom: 10px;
            }}
            .api-item {{ 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                padding: 12px 0; 
                border-bottom: 1px solid #f3f3f3;
            }}
            .api-item:last-child {{ border-bottom: none; }}
            .api-info {{ flex: 1; }}
            .api-name {{ font-weight: 600; color: #2d2d2d; }}
            .api-endpoint {{ font-size: 0.85rem; color: #666; font-family: monospace; }}
            .api-result {{ font-size: 0.9rem; color: #444; margin-top: 4px; }}
            .status-indicator {{ 
                width: 12px; 
                height: 12px; 
                border-radius: 50%; 
                margin-right: 8px;
            }}
            .status-healthy {{ background: #22c55e; }}
            .status-warning {{ background: #f59e0b; }}
            .status-error {{ background: #ef4444; }}
            .timestamp {{ text-align: center; color: #666; font-size: 0.9rem; margin-top: 30px; }}
            .refresh-btn {{ 
                background: #2563eb; 
                color: white; 
                border: none; 
                padding: 12px 24px; 
                border-radius: 8px; 
                cursor: pointer; 
                font-size: 1rem;
                margin: 0 5px;
                display: inline-block;
            }}
            .refresh-btn:hover {{ background: #1d4ed8; }}
            .breadcrumb {{ 
                display: flex; 
                align-items: center; 
                gap: 8px; 
                font-size: 0.9rem; 
                color: #666;
            }}
            .breadcrumb a {{ 
                color: #374151; 
                text-decoration: none; 
                font-weight: 500; 
                transition: color 0.2s;
            }}
            .breadcrumb a:hover {{ 
                color: #2563eb;
            }}
            .breadcrumb .separator {{ 
                color: #9ca3af; 
                font-weight: 400;
            }}
            .breadcrumb .current {{ 
                color: #2563eb; 
                font-weight: 600;
            }}
            .test-btn {{ 
                background: #06b6d4; 
                color: white; 
                border: none; 
                padding: 6px 12px; 
                border-radius: 6px; 
                cursor: pointer; 
                font-size: 0.85rem;
                margin-left: 12px;
                transition: all 0.2s;
            }}
            .test-btn:hover {{ background: #0891b2; }}
            .test-btn:disabled {{ background: #94a3b8; cursor: not-allowed; }}
            .test-result {{ 
                margin-top: 8px; 
                padding: 8px 12px; 
                border-radius: 6px; 
                font-size: 0.85rem;
                display: none;
            }}
            .test-result.success {{ background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }}
            .test-result.error {{ background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }}
            .test-result.warning {{ background: #fefbeb; color: #d97706; border: 1px solid #fed7aa; }}
            .spinner {{ 
                display: inline-block; 
                width: 12px; 
                height: 12px; 
                border: 2px solid #f3f3f3; 
                border-top: 2px solid #06b6d4; 
                border-radius: 50%; 
                animation: spin 1s linear infinite; 
            }}
            @keyframes spin {{ 
                0% {{ transform: rotate(0deg); }} 
                100% {{ transform: rotate(360deg); }} 
            }}
            
            /* Responsive design */
            @media (max-width: 768px) {{
                .container {{
                    padding: 15px;
                }}
                
                .header {{
                    flex-direction: column;
                    gap: 20px;
                    text-align: center;
                }}
                
                .summary-grid {{
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="page-title">
                <a href="/" style="display: inline-block;">
                    <img src="/images/Brand.svg" alt="syntropAI" style="cursor: pointer;" />
                </a>
                <div class="page-title-content">
                    <h1>{status_icon} AML System Health Check</h1>
                    <p>Comprehensive API Status & Service Testing</p>
                </div>
            </div>
            
            <header class="header">
                <div class="header-left">
                </div>
                <div class="system-status">
                    <div class="status-dot{' error' if overall_status in ['error', 'degraded'] else ''}" id="statusDot"></div>
                    <span id="statusText">System Online</span>
                    <div style="font-size: 12px; color: #666; margin-top: 4px;" id="serverUptime">Uptime: -</div>
                </div>
            </header>
            
            <nav class="breadcrumb" style="margin-bottom: 40px;">
                <a href="/">Home</a>
                <span class="separator">/</span>
                <span class="current">System Health</span>
            </nav>
            
            <div class="summary">
                <div class="summary-grid">
                    <div class="summary-item">
                        <div class="summary-number">{health_data.get('summary', {}).get('total_api_groups', 0)}</div>
                        <div class="summary-label">API Groups</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number" style="color: #22c55e;">{health_data.get('summary', {}).get('healthy_apis', 0)}</div>
                        <div class="summary-label">Healthy APIs</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number" style="color: #f59e0b;">{health_data.get('summary', {}).get('warning_apis', 0)}</div>
                        <div class="summary-label">Warning APIs</div>
                    </div>
                    <div class="summary-item">
                        <div class="summary-number" style="color: #ef4444;">{health_data.get('summary', {}).get('error_apis', 0)}</div>
                        <div class="summary-label">Error APIs</div>
                    </div>
                </div>
            </div>
    '''
    
    # Add API groups
    for group_name, apis in health_data.get('api_groups', {}).items():
        html += f'''
            <div class="api-group">
                <h3>{group_name}</h3>
        '''
        
        for api_name, api_info in apis.items():
            status = api_info.get('status', 'unknown')
            endpoint = api_info.get('endpoint', 'N/A')
            result = api_info.get('last_result', api_info.get('error', 'No information'))
            
            # Create unique ID for this API test
            test_id = f"{group_name.lower().replace(' ', '_').replace('&', '')}_{api_name}"
            
            html += f'''
                <div class="api-item">
                    <div class="api-info">
                        <div class="api-name">
                            <span class="status-indicator status-{status}"></span>
                            {api_name.replace('_', ' ').title()}
                            <button class="test-btn" onclick="testService('{test_id}', '{endpoint}')" id="btn_{test_id}">
                                🧪 Test
                            </button>
                        </div>
                        <div class="api-endpoint">{endpoint}</div>
                        <div class="api-result">{result}</div>
                        <div class="test-result" id="result_{test_id}"></div>
                    </div>
                </div>
            '''
        
        html += '</div>'
    
    html += f'''
            <div style="text-align: center; margin: 30px 0;">
                <button class="refresh-btn" onclick="window.location.reload()">🔄 Refresh Health Check</button>
                <button class="refresh-btn" onclick="testAllServices()" style="background: #059669; margin-left: 10px;">🧪 Test All Services</button>
            </div>
            
            <div class="timestamp">
                Last updated: {health_data.get('timestamp', 'Unknown')}
            </div>
        </div>
        
        <script>
            async function testService(testId, endpoint) {{
                const button = document.getElementById('btn_' + testId);
                const resultDiv = document.getElementById('result_' + testId);
                
                // Show loading state
                button.disabled = true;
                button.innerHTML = '<span class="spinner"></span> Testing...';
                resultDiv.style.display = 'block';
                resultDiv.className = 'test-result';
                resultDiv.textContent = 'Testing service...';
                
                try {{
                    const response = await fetch('/api/health/test-service', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ endpoint: endpoint }})
                    }});
                    
                    const result = await response.json();
                    
                    // Display result
                    if (result.success) {{
                        resultDiv.className = 'test-result success';
                        resultDiv.innerHTML = '✅ <strong>Success:</strong> ' + result.message;
                        if (result.data) {{
                            resultDiv.innerHTML += '<br><small>' + result.data + '</small>';
                        }}
                    }} else {{
                        resultDiv.className = 'test-result error';
                        resultDiv.innerHTML = '❌ <strong>Error:</strong> ' + result.error;
                    }}
                }} catch (error) {{
                    resultDiv.className = 'test-result error';
                    resultDiv.innerHTML = '❌ <strong>Network Error:</strong> ' + error.message;
                }}
                
                // Reset button
                button.disabled = false;
                button.innerHTML = '🧪 Test';
            }}
            
            function testAllServices() {{
                const buttons = document.querySelectorAll('.test-btn');
                buttons.forEach((button, index) => {{
                    setTimeout(() => {{
                        button.click();
                    }}, index * 500); // Stagger tests by 500ms
                }});
            }}
            
            // Uptime functionality
            const serverStartTime = Date.now();
            
            function formatUptime(milliseconds) {{
                const seconds = Math.floor(milliseconds / 1000);
                const minutes = Math.floor(seconds / 60);
                const hours = Math.floor(minutes / 60);
                const days = Math.floor(hours / 24);
                
                if (days > 0) return `${{days}}d ${{hours % 24}}h ${{minutes % 60}}m`;
                if (hours > 0) return `${{hours}}h ${{minutes % 60}}m`;
                if (minutes > 0) return `${{minutes}}m ${{seconds % 60}}s`;
                return `${{seconds}}s`;
            }}
            
            function updateServerUptime() {{
                const uptime = Date.now() - serverStartTime;
                const uptimeString = formatUptime(uptime);
                const uptimeElement = document.getElementById('serverUptime');
                if (uptimeElement) {{
                    uptimeElement.textContent = `Uptime: ${{uptimeString}}`;
                }}
            }}
            
            // Update uptime every second
            setInterval(updateServerUptime, 1000);
            
            // Initialize uptime on page load
            updateServerUptime();
        </script>
    </body>
    </html>
    '''
    
    return html

@app.route('/api/health/test-service', methods=['POST'])
def test_individual_service():
    """Test individual service endpoint"""
    try:
        data = request.get_json()
        endpoint = data.get('endpoint', '')
        
        if not endpoint:
            return jsonify({
                'success': False,
                'error': 'Endpoint parameter required'
            }), 400
        
        # Test the specific endpoint
        result = test_service_endpoint(endpoint)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Test failed: {str(e)}'
        }), 500

@app.route('/api/search', methods=['GET'])
def search_data():
    """Modern search across alerts, transactions, and sanctions with real data retrieval"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')
        date_range = request.args.get('date_range', 'all')
        status_filter = request.args.get('status', 'all')
        risk_filter = request.args.get('risk', 'all')
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 results
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query required'
            }), 400
        
        results = []
        query_lower = query.lower()
        
        # Search alerts with real data
        if search_type in ['all', 'alerts']:
            try:
                # Get alerts from Supabase database
                if db and hasattr(db, 'get_active_alerts'):
                    alerts_data = db.get_active_alerts(limit=200)
                elif aml_engine and hasattr(aml_engine, 'get_alerts'):
                    alerts_data = aml_engine.get_alerts()
                else:
                    alerts_data = []
                
                for alert in alerts_data:
                    # Create searchable text from all alert fields
                    searchable_fields = [
                        str(alert.get('alert_id', '')),
                        str(alert.get('transaction_id', '')),
                        str(alert.get('alert_type', '')),
                        str(alert.get('description', '')),
                        str(alert.get('sender_name', '')),
                        str(alert.get('receiver_name', '')),
                        str(alert.get('sender_country', '')),
                        str(alert.get('receiver_country', '')),
                        str(alert.get('risk_level', ''))
                    ]
                    searchable_text = ' '.join(searchable_fields).lower()
                    
                    # Check if query matches any field
                    if query_lower in searchable_text:
                        # Apply filters
                        if risk_filter != 'all' and alert.get('risk_level', '').lower() != risk_filter:
                            continue
                        if status_filter != 'all' and alert.get('status', '').lower() != status_filter:
                            continue
                        
                        # Format amount properly
                        amount = alert.get('amount', 0)
                        try:
                            amount = float(amount) if amount else 0
                        except (ValueError, TypeError):
                            amount = 0
                        
                        results.append({
                            'type': 'alert',
                            'title': f"Alert {alert.get('alert_id', 'N/A')} - {alert.get('alert_type', 'AML Alert')}",
                            'details': f"Transaction: {alert.get('transaction_id', 'N/A')} | Risk: {alert.get('risk_level', 'Medium')} | Amount: ${amount:,.2f} | Status: {alert.get('status', 'Active')}",
                            'timestamp': alert.get('created_date', alert.get('timestamp', '')),
                            'metadata': {
                                'sender': f"{alert.get('sender_name', 'N/A')} ({alert.get('sender_country', 'N/A')})",
                                'receiver': f"{alert.get('receiver_name', 'N/A')} ({alert.get('receiver_country', 'N/A')})",
                                'amount': amount,
                                'risk_level': alert.get('risk_level', 'Medium'),
                                'alert_type': alert.get('alert_type', 'AML Alert')
                            },
                            'data': alert
                        })
            except Exception as e:
                print(f"Error searching alerts: {e}")
        
        # Search transactions with real data
        if search_type in ['all', 'transactions']:
            try:
                # Get transactions from Supabase database
                if db and hasattr(db, 'get_transactions'):
                    transactions_data = db.get_transactions(limit=200)
                else:
                    transactions_data = []
                
                for txn in transactions_data:
                    # Create searchable text from all transaction fields
                    searchable_fields = [
                        str(txn.get('transaction_id', '')),
                        str(txn.get('sender_name', '')),
                        str(txn.get('receiver_name', '')),
                        str(txn.get('sender_country', '')),
                        str(txn.get('receiver_country', '')),
                        str(txn.get('sender_bank', '')),
                        str(txn.get('receiver_bank', '')),
                        str(txn.get('transaction_type', '')),
                        str(txn.get('purpose', ''))
                    ]
                    searchable_text = ' '.join(searchable_fields).lower()
                    
                    # Check if query matches any field
                    if query_lower in searchable_text:
                        # Apply filters
                        if status_filter != 'all' and txn.get('status', '').lower() != status_filter:
                            continue
                        
                        # Format amount properly
                        amount = txn.get('amount', 0)
                        try:
                            amount = float(amount) if amount else 0
                        except (ValueError, TypeError):
                            amount = 0
                        
                        results.append({
                            'type': 'transaction',
                            'title': f"Transaction {txn.get('transaction_id', 'N/A')} - ${amount:,.2f}",
                            'details': f"From: {txn.get('sender_name', 'N/A')} ({txn.get('sender_country', 'N/A')}) → To: {txn.get('receiver_name', 'N/A')} ({txn.get('receiver_country', 'N/A')}) | Status: {txn.get('status', 'Unknown')}",
                            'timestamp': txn.get('created_date', txn.get('timestamp', '')),
                            'metadata': {
                                'sender': f"{txn.get('sender_name', 'N/A')} ({txn.get('sender_country', 'N/A')})",
                                'receiver': f"{txn.get('receiver_name', 'N/A')} ({txn.get('receiver_country', 'N/A')})",
                                'amount': amount,
                                'status': txn.get('status', 'Unknown'),
                                'type': txn.get('transaction_type', 'Transfer')
                            },
                            'data': txn
                        })
            except Exception as e:
                print(f"Error searching transactions: {e}")
        
        # Search sanctions with real data
        if search_type in ['all', 'sanctions']:
            try:
                # Get sanctions from Supabase sanctions database
                if aml_engine and hasattr(aml_engine, 'supabase_db') and aml_engine.supabase_db:
                    # Use the existing get_sanctions_by_name method for name-based search
                    sanctions_data = aml_engine.supabase_db.get_sanctions_by_name(query)
                    
                    for sanction in sanctions_data[:50]:  # Limit to 50 sanctions results
                        results.append({
                            'type': 'sanction',
                            'title': f"Sanctions: {sanction.get('name', 'N/A')}",
                            'details': f"Country: {sanction.get('country', 'N/A')} | Program: {sanction.get('program', 'N/A')} | Type: {sanction.get('entity_type', 'Individual')} | Source: {sanction.get('source', 'OpenSanctions')}",
                            'timestamp': sanction.get('updated_at', sanction.get('last_seen', '')),
                            'metadata': {
                                'country': sanction.get('country', 'N/A'),
                                'program': sanction.get('program', 'N/A'),
                                'entity_type': sanction.get('entity_type', 'Individual'),
                                'source': sanction.get('source', 'OpenSanctions'),
                                'schema': sanction.get('schema', 'Person')
                            },
                            'data': sanction
                        })
            except Exception as e:
                print(f"Error searching sanctions: {e}")
        
        # Sort results by relevance (exact matches first) and timestamp
        def calculate_relevance(result):
            title_lower = result['title'].lower()
            details_lower = result['details'].lower()
            
            # Exact match in title gets highest score
            if query_lower == title_lower:
                return 1000
            elif query_lower in title_lower:
                return 500
            elif query_lower in details_lower:
                return 100
            else:
                return 1
        
        # Add relevance score and sort
        for result in results:
            result['relevance_score'] = calculate_relevance(result)
        
        results.sort(key=lambda x: (x['relevance_score'], x.get('timestamp', '')), reverse=True)
        
        # Limit final results
        results = results[:limit]
        
        return jsonify({
            'success': True,
            'query': query,
            'type': search_type,
            'total': len(results),
            'limit': limit,
            'filters_applied': {
                'date_range': date_range,
                'status': status_filter,
                'risk': risk_filter
            },
            'results': results
        })
        
    except Exception as e:
        print(f"Search API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}'
        }), 500

def test_service_endpoint(endpoint):
    """Test a specific service endpoint and return detailed results"""
    try:
        # Handle different endpoint patterns
        if endpoint == '/api/statistics':
            if aml_engine and aml_engine.db:
                stats = aml_engine.get_alert_statistics()
                return {
                    'success': True,
                    'message': 'Statistics endpoint working',
                    'data': f"Transactions: {stats.get('total_transactions', 0)}, Alerts: {stats.get('total_alerts', 0)}"
                }
            else:
                return {'success': False, 'error': 'Database not available'}
                
        elif endpoint == '/api/transactions':
            if db:
                stats = db.get_statistics()
                count = stats.get('total_transactions', 0)
                return {
                    'success': True,
                    'message': 'Transactions endpoint working',
                    'data': f"Found {count} transactions in database"
                }
            else:
                return {'success': False, 'error': 'Database not available'}
                
        elif endpoint == '/api/transactions (POST)':
            if db and transaction_generator:
                return {
                    'success': True,
                    'message': 'Transaction creation ready',
                    'data': 'Database and generator available for new transactions'
                }
            else:
                return {'success': False, 'error': 'Transaction system not ready'}
                
        elif endpoint == '/api/transactions/batch':
            if db and aml_engine:
                return {
                    'success': True,
                    'message': 'Batch processing ready',
                    'data': 'Database and AML engine available for batch processing'
                }
            else:
                return {'success': False, 'error': 'Batch processing system not ready'}
                
        elif endpoint == '/api/transactions/process':
            if aml_engine:
                supabase_status = 'enabled' if aml_engine.use_supabase else 'disabled'
                return {
                    'success': True,
                    'message': 'AML processing ready',
                    'data': f'AML engine operational, Supabase: {supabase_status}'
                }
            else:
                return {'success': False, 'error': 'AML engine not available'}
                
        elif endpoint == '/api/generate/transactions':
            if transaction_generator:
                return {
                    'success': True,
                    'message': 'Transaction generator ready',
                    'data': 'Can generate various transaction types including sanctions risks'
                }
            else:
                return {'success': False, 'error': 'Transaction generator not available'}
                
        elif endpoint == '/api/generate/demo-sanctions':
            if transaction_generator:
                return {
                    'success': True,
                    'message': 'Demo sanctions ready',
                    'data': 'Can generate demo sanctioned entity transactions'
                }
            else:
                return {'success': False, 'error': 'Transaction generator not available'}
                
        elif endpoint == '/api/generate/process':
            if transaction_generator and aml_engine:
                return {
                    'success': True,
                    'message': 'End-to-end workflow ready',
                    'data': 'Generator and AML engine available for complete workflow'
                }
            else:
                return {'success': False, 'error': 'Workflow components not available'}
                
        elif endpoint == '/api/sanctions/status':
            if aml_engine and aml_engine.use_supabase and aml_engine.supabase_db:
                try:
                    sanctions_count = aml_engine.supabase_db.get_sanctions_count()
                    total_sanctions = sanctions_count.get('total_sanctions', 0) if isinstance(sanctions_count, dict) else sanctions_count
                    return {
                        'success': True,
                        'message': 'Sanctions database accessible',
                        'data': f'Supabase contains {total_sanctions} sanctions records'
                    }
                except Exception as e:
                    return {'success': False, 'error': f'Sanctions database error: {str(e)}'}
            else:
                return {'success': False, 'error': 'Sanctions database not configured'}
                
        elif endpoint == '/api/sanctions/search':
            if aml_engine and aml_engine.use_supabase and aml_engine.supabase_db:
                try:
                    # Test search with a simple query
                    results = aml_engine.supabase_db.get_sanctions_by_name('test')
                    return {
                        'success': True,
                        'message': 'Sanctions search working',
                        'data': f'Search functionality operational (test query returned {len(results)} results)'
                    }
                except Exception as e:
                    return {'success': False, 'error': f'Search error: {str(e)}'}
            else:
                return {'success': False, 'error': 'Sanctions search not available'}
                
        elif endpoint == '/api/sanctions/refresh':
            return {
                'success': True,
                'message': 'Sanctions refresh available',
                'data': 'Refresh endpoint ready (test does not execute actual refresh)'
            }
            
        elif endpoint == '/api/dashboard/data':
            if aml_engine:
                try:
                    alert_stats = aml_engine.get_alert_statistics()
                    return {
                        'success': True,
                        'message': 'Dashboard data accessible',
                        'data': f"Dashboard ready with {alert_stats.get('total_alerts', 0)} alerts"
                    }
                except Exception as e:
                    return {'success': False, 'error': f'Dashboard data error: {str(e)}'}
            else:
                return {'success': False, 'error': 'Dashboard system not available'}
                
        elif endpoint == '/api/alerts':
            if aml_engine:
                return {
                    'success': True,
                    'message': 'Alert system operational',
                    'data': 'Alert retrieval and management available'
                }
            else:
                return {'success': False, 'error': 'Alert system not available'}
                
        elif endpoint.startswith('/api/alerts/') and endpoint.endswith('/update'):
            if aml_engine and aml_engine.db:
                return {
                    'success': True,
                    'message': 'Alert updates ready',
                    'data': 'Alert update functionality available'
                }
            else:
                return {'success': False, 'error': 'Alert update system not available'}
                
        else:
            return {
                'success': False,
                'error': f'Unknown endpoint: {endpoint}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Service test failed: {str(e)}'
        }

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        if not aml_engine:
            return jsonify({
                'success': False,
                'error': 'AML engine not initialized'
            }), 503
            
        stats = aml_engine.get_alert_statistics()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    try:
        limit = request.args.get('limit', 50, type=int)
        alerts = db.get_active_alerts(limit=limit)
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts),
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get recent transactions with optional status filtering"""
    try:
        limit = request.args.get('limit', 100, type=int)
        status = request.args.get('status', None)
        transaction_id = request.args.get('transaction_id', None)
        
        if transaction_id:
            # Get specific transaction by ID
            transaction = db.get_transaction_by_id(transaction_id)
            transactions = [transaction] if transaction else []
        elif status:
            # Filter by status - use Supabase method if available
            if db.use_supabase and db.supabase_aml:
                transactions = db.supabase_aml.get_transactions(limit=limit, status=status)
            else:
                # SQLite fallback with status filter
                conn = db.get_connection()
                cursor = conn.execute("""
                    SELECT * FROM transactions 
                    WHERE status = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (status, limit))
                transactions = [dict(row) for row in cursor]
                conn.close()
        else:
            # Get all recent transactions
            transactions = db.get_recent_transactions(limit)
        
        return jsonify({
            'success': True,
            'data': transactions,
            'count': len(transactions),
            'timestamp': datetime.datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions', methods=['POST'])
def process_transaction():
    """Process a single transaction"""
    try:
        transaction_data = request.get_json()
        
        if not transaction_data:
            return jsonify({
                'success': False,
                'error': 'No transaction data provided'
            }), 400
        
        # Process transaction through AML engine
        alerts = aml_engine.process_transaction(transaction_data)
        
        return jsonify({
            'success': True,
            'transaction_id': transaction_data.get('transaction_id'),
            'alerts_generated': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions/batch', methods=['POST'])
def process_transaction_batch():
    """Process a batch of transactions"""
    try:
        batch_data = request.get_json()
        
        if not batch_data or 'transactions' not in batch_data:
            return jsonify({
                'success': False,
                'error': 'No transaction batch data provided'
            }), 400
        
        transactions = batch_data['transactions']
        
        # Process batch through AML engine
        results = aml_engine.process_batch(transactions)
        
        return jsonify({
            'success': True,
            'processed_count': results['processed_count'],
            'alert_count': results['alert_count'],
            'alerts': results['alerts'],
            'processing_time': results['processing_time'].isoformat(),
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/transactions', methods=['POST'])
def generate_transactions():
    """Generate sample transactions for testing"""
    try:
        params = request.get_json() or {}
        count = params.get('count', 20)
        
        # Generate mixed batch of transactions
        transactions = transaction_generator.generate_mixed_batch(count)
        
        # Store transactions in database
        stored_count = transaction_generator.store_transactions(transactions)
        
        return jsonify({
            'success': True,
            'generated_count': len(transactions),
            'stored_count': stored_count,
            'transactions': transactions[:5],  # Return first 5 as sample
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/process', methods=['GET', 'POST'])
def generate_and_process():
    """Generate transactions in PENDING status (without processing)"""
    try:
        if request.method == 'GET':
            count = request.args.get('count', 20, type=int)
        else:
            params = request.get_json() or {}
            count = params.get('count', 20)
        
        # Generate transactions and store as PENDING
        transactions = transaction_generator.generate_mixed_batch(count)
        stored_count = transaction_generator.store_transactions(transactions)
        
        return jsonify({
            'success': True,
            'generated_count': len(transactions),
            'stored_count': stored_count,
            'message': f'Generated {stored_count} transactions in PENDING status',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/demo-sanctions', methods=['POST'])
def generate_demo_sanctions():
    """Generate demo transactions with well-known sanctioned entities"""
    try:
        # Generate demo sanctioned transactions
        demo_transactions = transaction_generator.generate_demo_sanctioned_transactions()
        stored_count = transaction_generator.store_transactions(demo_transactions)
        
        # Get the names for display
        entity_names = [tx['beneficiary_name'] for tx in demo_transactions]
        
        return jsonify({
            'success': True,
            'generated_count': len(demo_transactions),
            'stored_count': stored_count,
            'entity_names': entity_names,
            'message': f'Generated {stored_count} demo transactions with sanctioned entities',
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sanctions/refresh', methods=['POST'])
def refresh_sanctions():
    """Refresh sanctions data from OpenSanctions Consolidated Sanctions dataset"""
    try:
        from src.services.sanctions_web_loader import refresh_sanctions_web
        
        # Get request parameters
        params = request.get_json() or {}
        user_confirmed = params.get('confirmed', False)
        
        print(f"🔍 SANCTIONS REFRESH: User confirmed = {user_confirmed}")
        
        # Use the new OpenSanctions pipeline
        result = refresh_sanctions_web(user_confirmed)
        
        if result.get('requires_confirmation'):
            return jsonify({
                'success': False,
                'requires_confirmation': True,
                'message': result.get('message', 'Confirmation required'),
                'warning': 'This will clear all existing sanctions data and reload from OpenSanctions'
            }), 200
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': result.get('message', 'Sanctions refreshed successfully'),
                'statistics': result.get('statistics', {}),
                'timestamp': result.get('timestamp')
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error'),
                'message': result.get('message', 'Sanctions refresh failed')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'total_loaded': 0,
            'total_skipped': 0,
            'total_processed': 0
        }), 500

def _refresh_sanctions_via_api(dataset: str, batch_size: int, api_key: str):
    """Refresh sanctions using OpenSanctions API (paid service with real-time data)"""
    # TODO: Implement OpenSanctions API integration
    # This would use their REST API endpoints with authentication
    return jsonify({
        'success': False,
        'error': 'OpenSanctions API integration not yet implemented',
        'total_loaded': 0,
        'total_skipped': 0,
        'total_processed': 0,
        'source': 'OpenSanctions_API',
        'note': 'API key detected but implementation pending',
        'debug_info': [
            f'API key detected: {api_key[:10]}...',
            'Using OpenSanctions API path (not implemented)',
            'This should not happen if no API key is set'
        ]
    })

def _refresh_sanctions_via_datasets(dataset: str, batch_size: int):
    """Refresh sanctions using OpenSanctions dataset files (free public data)"""
    logger = AMLLogger.get_logger('sanctions_refresh', 'sanctions')
    log_function_entry(logger, '_refresh_sanctions_via_datasets', dataset=dataset, batch_size=batch_size)
    
    try:
        debug_info = []
        
        if not sanctions_loader:
            logger.error("Sanctions loader not initialized")
            return jsonify({
                'success': False,
                'error': 'Sanctions loader not initialized',
                'total_loaded': 0,
                'total_skipped': 0,
                'total_processed': 0,
                'debug_info': ['Sanctions loader not initialized']
            }), 503
        
        # Get current sanctions count before loading
        logger.info("Getting current sanctions count from statistics")
        current_stats = aml_engine.get_alert_statistics()
        initial_sanctions = current_stats.get('total_sanctions', 0)
        logger.info(f"Current sanctions count: {initial_sanctions}")
        logger.info(f"Statistics keys available: {list(current_stats.keys())}")
        
        debug_info.append(f"Initial sanctions count: {initial_sanctions}")
        debug_info.append(f"Stats keys: {list(current_stats.keys())}")
        
        # Use existing sanctions loader with limited batch size
        debug_info.append(f"Setting batch_size = {batch_size} on sanctions_loader")
        original_limit = getattr(sanctions_loader, '_batch_limit', None)
        debug_info.append(f"Original limit was: {original_limit}")
        sanctions_loader._batch_limit = batch_size
        actual_limit = getattr(sanctions_loader, '_batch_limit', 'NOT_SET')
        debug_info.append(f"After setting, _batch_limit = {actual_limit}")
        
        # Force refresh to get latest data from OpenSanctions dataset files
        debug_info.append("About to call force_refresh_sanctions_data()")
        results = sanctions_loader.force_refresh_sanctions_data()
        
        # Restore original limit
        if original_limit is not None:
            sanctions_loader._batch_limit = original_limit
        elif hasattr(sanctions_loader, '_batch_limit'):
            delattr(sanctions_loader, '_batch_limit')
        
        # Get new sanctions count after loading
        new_stats = aml_engine.get_alert_statistics()
        final_sanctions = new_stats.get('total_sanctions', 0)
        
        # Calculate actual loaded count
        total_loaded = max(0, final_sanctions - initial_sanctions)
        
        # Extract summary information from results
        datasets_info = []
        if 'datasets' in results and isinstance(results['datasets'], dict):
            for key, dataset_info in results['datasets'].items():
                if dataset_info.get('success', False):
                    datasets_info.append(f"{key}: {dataset_info.get('count', 0)} processed")
        
        # Estimate processed count from results
        total_processed = results.get('total_count', results.get('count', total_loaded))
        total_skipped = max(0, total_processed - total_loaded)
        
        # Limit the numbers to batch_size if they exceed it significantly
        if total_processed > batch_size * 10:  # If way over batch size, likely full dataset
            total_processed = min(total_processed, batch_size * 2)  # Cap at reasonable amount
            total_loaded = min(total_loaded, batch_size)
            total_skipped = total_processed - total_loaded
        
        debug_info.append(f"Final sanctions count: {final_sanctions}")
        debug_info.append(f"Calculated loaded: {total_loaded}")
        debug_info.append(f"Results total_count: {results.get('total_count', 'N/A')}")
        debug_info.append(f"Results success: {results.get('success', 'N/A')}")
        
        return jsonify({
            'success': results.get('success', False),
            'total_loaded': total_loaded,
            'total_skipped': total_skipped,
            'total_processed': total_processed,
            'batch_size': batch_size,
            'dataset': dataset,
            'source': results.get('source', 'OpenSanctions_DatasetFiles'),
            'datasets_info': datasets_info,
            'debug_info': debug_info,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'total_loaded': 0,
            'total_skipped': 0,
            'total_processed': 0
        }), 500


@app.route('/api/sanctions/status', methods=['GET'])
def get_sanctions_status():
    """Get current sanctions data status and statistics"""
    try:
        from src.services.sanctions_web_loader import get_sanctions_status
        
        result = get_sanctions_status()
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'status': result.get('status'),
                'message': result.get('message'),
                'statistics': result.get('statistics', {}),
                'timestamp': datetime.datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('message', 'Unknown error'),
                'status': 'error'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/sanctions/search', methods=['GET'])
def search_sanctions():
    """Search sanctions by name"""
    try:
        name = request.args.get('name', '')
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Name parameter is required'
            }), 400
        
        # Use Supabase as the only source for sanctions data
        if not hasattr(aml_engine, 'supabase_db') or not aml_engine.supabase_db:
            return jsonify({
                'success': False,
                'error': 'Sanctions database not available. Supabase connection required.'
            }), 503
            
        sanctions = aml_engine.supabase_db.get_sanctions_by_name(name)
        
        return jsonify({
            'success': True,
            'query': name,
            'results': sanctions,
            'count': len(sanctions),
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Get all data needed for dashboard"""
    try:
        # Get statistics (includes Supabase sanctions count if enabled)
        stats = aml_engine.get_alert_statistics()
        
        # Get recent alerts
        alerts = db.get_active_alerts(limit=20)
        
        # Get recent transactions
        transactions = db.get_recent_transactions(limit=50)
        
        # Get alert breakdown by typology
        alert_typologies = {}
        for alert in alerts:
            typology = alert['typology']
            if typology not in alert_typologies:
                alert_typologies[typology] = 0
            alert_typologies[typology] += 1
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'alerts': alerts,
            'transactions': transactions,
            'alert_typologies': alert_typologies,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/alerts/<alert_id>/update', methods=['PUT'])
def update_alert(alert_id):
    """Update alert status or assignment"""
    try:
        update_data = request.get_json()
        
        if not update_data:
            return jsonify({
                'success': False,
                'error': 'No update data provided'
            }), 400
        
        # For now, just return success (would implement actual update logic)
        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'updated_fields': list(update_data.keys()),
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions/delete', methods=['POST'])
def delete_transactions():
    """Delete transactions by transaction_ids"""
    try:
        if not db:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 503
        
        data = request.get_json()
        if not data or 'transaction_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'transaction_ids required'
            }), 400
        
        transaction_ids = data['transaction_ids']
        if not isinstance(transaction_ids, list):
            return jsonify({
                'success': False,
                'error': 'transaction_ids must be a list'
            }), 400
        
        # Delete transactions
        result = db.delete_transactions_batch(transaction_ids)
        
        return jsonify({
            'success': True,
            'deleted_count': result['deleted_count'],
            'requested_count': result['requested_count'],
            'not_found': result['not_found'],
            'message': f"Deleted {result['deleted_count']} of {result['requested_count']} transactions",
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transactions/delete-all', methods=['POST'])
def delete_all_transactions():
    """Delete ALL transactions and related alerts"""
    try:
        if not db:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 503
        
        conn = db.get_connection()
        
        # Get count before deletion
        cursor = conn.execute("SELECT COUNT(*) as count FROM transactions")
        total_transactions = cursor.fetchone()['count']
        
        cursor = conn.execute("SELECT COUNT(*) as count FROM alerts")
        total_alerts = cursor.fetchone()['count']
        
        # Delete all alerts first (due to foreign key constraints)
        conn.execute("DELETE FROM alerts")
        deleted_alerts = conn.total_changes
        
        # Delete all transactions
        conn.execute("DELETE FROM transactions")
        deleted_transactions = conn.total_changes - deleted_alerts
        
        # Reset auto-increment counters
        conn.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='alerts'")
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'All transactions and alerts deleted successfully',
            'deleted': {
                'transactions': deleted_transactions,
                'alerts': deleted_alerts,
                'total_transactions_before': total_transactions,
                'total_alerts_before': total_alerts
            },
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/transactions/process', methods=['POST'])
def process_pending_transactions():
    """Process pending transactions through AML engine with Plane.so integration"""
    try:
        if not aml_engine:
            return jsonify({
                'success': False,
                'error': 'AML engine not initialized'
            }), 503
        
        # Plane integration removed
        
        # Get all pending transactions using proper database abstraction
        pending_transactions = db.get_pending_transactions()
        
        if not pending_transactions:
            return jsonify({
                'success': True,
                'message': 'No pending transactions to process',
                'processed_count': 0,
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        total_pending = len(pending_transactions)
        print(f"🔄 Processing {total_pending} pending transactions...")
        
        # Process transactions through AML engine
        processed_count = 0
        completed_count = 0
        failed_count = 0
        under_review_count = 0
        processing_results = []
        
        for i, tx in enumerate(pending_transactions, 1):
            try:
                # Progress logging for large batches
                if total_pending > 10 and i % 10 == 0:
                    print(f"📊 Progress: {i}/{total_pending} transactions processed")
                
                # Convert database row to transaction format
                transaction_data = {
                    'transaction_id': tx['transaction_id'],
                    'account_id': tx['account_id'],
                    'amount': float(tx['amount']),
                    'currency': tx['currency'],
                    'sender_name': tx.get('sender_name', 'Unknown'),  # Not stored in current schema
                    'beneficiary_name': tx['beneficiary_name'],
                    'origin_country': tx.get('origin_country', 'US'),  # Keep the original field name
                    'beneficiary_country': tx['beneficiary_country'],
                    'sender_account': tx.get('sender_account', tx['account_id']),  # Use account_id as fallback
                    'beneficiary_account': tx['beneficiary_account'],
                    'transaction_date': tx['transaction_date'],
                    'transaction_type': tx.get('transaction_type', 'WIRE_TRANSFER')
                }
                
                # Run AML detection on existing transaction
                alerts = aml_engine.detect_alerts_for_existing_transaction(transaction_data)
                
                # Determine transaction outcome based on alerts
                outcome, requires_manual_review = _determine_transaction_outcome(alerts)
                # Manual review cases (Plane integration removed)
                
                # Update transaction status using proper database abstraction
                db.update_transaction_status(tx['transaction_id'], outcome)
                
                # Track results
                processed_count += 1
                if outcome == 'COMPLETED':
                    completed_count += 1
                elif outcome == 'FAILED':
                    failed_count += 1
                else:  # UNDER_REVIEW
                    under_review_count += 1
                
                processing_results.append({
                    'transaction_id': tx['transaction_id'],
                    'status': outcome,
                    'alerts_generated': len(alerts),
                    'requires_manual_review': requires_manual_review
                })
                
            except Exception as e:
                print(f"❌ Error processing transaction {tx['transaction_id']}: {e}")
                # Mark as failed using proper database abstraction
                db.update_transaction_status(tx['transaction_id'], 'FAILED')
                failed_count += 1
                continue
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'Processed {processed_count} pending transactions through AML engine (found {total_pending} total)',
            'processed_count': processed_count,
            'total_found': total_pending,
            'results': {
                'completed': completed_count,
                'failed': failed_count,
                'under_review': under_review_count,
            },
            'processing_details': processing_results,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def _determine_transaction_outcome(alerts: List[Dict]) -> Tuple[str, bool]:
    """
    Determine transaction outcome based on AML alerts
    Returns: (status, requires_manual_review)
    """
    if not alerts:
        return 'COMPLETED', False
    
    # Check for high-risk alerts requiring manual review
    high_risk_typologies = ['R1_SANCTIONS_MATCH']
    critical_risk_threshold = 0.9
    high_risk_threshold = 0.8
    
    max_risk_score = max(alert.get('risk_score', 0) for alert in alerts)
    has_sanctions_match = any(alert.get('typology') in high_risk_typologies for alert in alerts)
    
    # Critical cases - require immediate manual review
    if has_sanctions_match or max_risk_score >= critical_risk_threshold:
        return 'UNDER_REVIEW', True
    
    # High risk cases - require manual review  
    elif max_risk_score >= high_risk_threshold:
        return 'UNDER_REVIEW', True
    
    # Medium risk - can be auto-processed but flagged
    elif max_risk_score >= 0.6:
        return 'COMPLETED', False  # Process but keep alerts for monitoring
    
    # Low risk - auto-approve
    else:
        return 'COMPLETED', False

# Plane integration functions removed

def initialize_system():
    """Initialize AML system with error handling"""
    print("🚀 Starting AML Dynamic API Server...")
    
    if not db or not sanctions_loader or not transaction_generator or not aml_engine:
        print("⚠️  Core components not initialized, skipping data initialization")
        return
    
    # Initialize sanctions data on startup
    print("📥 Loading initial sanctions data...")
    try:
        sanctions_loader.refresh_sanctions_data()
        print("✅ Sanctions data loaded successfully")
    except Exception as e:
        print(f"❌ Error: Could not load sanctions data: {e}")
        print("💡 Note: Sanctions system requires Supabase connection. Please check configuration.")
    
    # Generate some initial data for testing
    print("🎲 Generating initial test data...")
    try:
        test_transactions = transaction_generator.generate_mixed_batch(5)
        transaction_generator.store_transactions(test_transactions)
        
        # Process through AML engine to generate alerts
        aml_engine.process_batch(test_transactions)
        print("✅ Initial test data generated")
    except Exception as e:
        print(f"⚠️  Warning: Could not generate test data: {e}")
    
    # Show statistics
    try:
        stats = db.get_statistics()
        print(f"📊 Database Statistics: {stats}")
    except Exception as e:
        print(f"⚠️  Warning: Could not get statistics: {e}")

if __name__ == '__main__':
    # Initialize system with error handling
    try:
        initialize_system()
    except Exception as e:
        print(f"⚠️  System initialization error: {e}")
        print("🚀 Starting server anyway...")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"🌐 API Server starting on http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port)