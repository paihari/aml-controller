#!/usr/bin/env python3
"""
Flask Web API for Dynamic AML System
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import json
import os
from typing import Dict, List, Tuple, Optional
from database import AMLDatabase
from dynamic_aml_engine import DynamicAMLEngine
from transaction_generator import TransactionGenerator
from sanctions_loader import SanctionsLoader
from plane_integration import PlaneIntegration

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    """Root endpoint - redirect to dashboard"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>syntropAI - AML Detection Platform</title>
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
            .brand { display: flex; align-items: center; justify-content: center; gap: 15px; margin-bottom: 40px; }
            .brand img { 
                height: 120px; 
                border: 2px solid #e8e1d6; 
                border-radius: 12px; 
                padding: 16px; 
                background: #ffffff;
            }
            .brand-text { font-size: 32px; font-weight: 600; color: #2d2d2d; }
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
                <img src="/images/brand.png" alt="syntropAI" />
            </div>
            <div class="subtitle">Real-time Anti-Money Laundering Detection Platform</div>
            
            <div class="nav-grid">
                <a href="/dashboard/minimalist.html" class="nav-card">
                    <div class="nav-title">📊 AML Dashboard</div>
                    <div class="nav-desc">Minimalist real-time dashboard</div>
                </a>
                <a href="/dashboard/dynamic.html" class="nav-card">
                    <div class="nav-title">🔧 Dynamic Dashboard</div>
                    <div class="nav-desc">Feature-rich dashboard</div>
                </a>
                <a href="/api/health" class="nav-card">
                    <div class="nav-title">💚 Health Check</div>
                    <div class="nav-desc">System status and version</div>
                </a>
                <a href="/api/statistics" class="nav-card">
                    <div class="nav-title">📈 Statistics</div>
                    <div class="nav-desc">System metrics and counts</div>
                </a>
                <a href="/api/alerts" class="nav-card">
                    <div class="nav-title">🚨 Alerts</div>
                    <div class="nav-desc">Active AML alerts</div>
                </a>
                <a href="/api/initialize" class="nav-card">
                    <div class="nav-title">🎲 Generate Data</div>
                    <div class="nav-desc">Create sample data</div>
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
    return send_from_directory('dashboard', filename)

@app.route('/images/<path:filename>')
def image_files(filename):
    """Serve image files"""
    return send_from_directory('images', filename)

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
    sanctions_loader = SanctionsLoader(db)
    plane = PlaneIntegration()
    print("✅ AML components initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize AML components: {e}")
    # Create minimal fallback components
    db = None
    aml_engine = None
    transaction_generator = None
    sanctions_loader = None
    plane = None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'version': '1.0.0'
    })

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
    """Refresh sanctions data from external sources"""
    try:
        # Load sanctions data
        results = sanctions_loader.refresh_sanctions_data()
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sanctions/refresh', methods=['POST'])
def refresh_sanctions_manually():
    """Manually refresh sanctions data from OpenSanctions daily datasets"""
    try:
        if not sanctions_loader:
            return jsonify({
                'success': False,
                'error': 'Sanctions loader not initialized'
            }), 503
        
        # Force refresh to get latest data
        results = sanctions_loader.force_refresh_sanctions_data()
        
        return jsonify({
            'success': results.get('success', False),
            'count': results.get('total_count', results.get('count', 0)),
            'source': results.get('source', 'Unknown'),
            'datasets': results.get('datasets', {}),
            'message': f"Loaded {results.get('total_count', results.get('count', 0))} sanctions records",
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
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
        
        # Use Supabase as the authoritative source for sanctions data
        if hasattr(aml_engine, 'supabase_db') and aml_engine.supabase_db:
            sanctions = aml_engine.supabase_db.get_sanctions_by_name(name)
        else:
            # Fallback to local DB only if Supabase is not available
            sanctions = db.get_sanctions_by_name(name)
        
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
        
        # Initialize Plane.so integration
        from plane_integration import PlaneIntegration
        plane = PlaneIntegration()
        
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
        plane_items_created = 0
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
                plane_item = None
                
                # Handle manual review cases
                if requires_manual_review and plane.is_configured():
                    plane_item = _create_plane_work_item(plane, transaction_data, alerts)
                    if plane_item:
                        plane_items_created += 1
                
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
                    'plane_work_item': plane_item['work_item_id'] if plane_item else None,
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
                'plane_work_items_created': plane_items_created
            },
            'plane_integration': {
                'configured': plane.is_configured(),
                'workspace': plane.workspace_slug if plane.is_configured() else None,
                'items_created': plane_items_created
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

def _create_plane_work_item(plane: 'PlaneIntegration', transaction_data: Dict, alerts: List[Dict]) -> Optional[Dict]:
    """Create appropriate Plane.so work item based on alert type"""
    
    # Find the highest priority alert
    sanctions_alerts = [a for a in alerts if a.get('typology') == 'R1_SANCTIONS_MATCH']
    geography_alerts = [a for a in alerts if a.get('typology') == 'R3_HIGH_RISK_CORRIDOR']
    structuring_alerts = [a for a in alerts if a.get('typology') == 'R2_STRUCTURING']
    
    # Create work item based on most critical alert type
    if sanctions_alerts:
        # Sanctions match - highest priority
        evidence = sanctions_alerts[0].get('evidence', {})
        sanctions_match = {
            'name': evidence.get('watchlist_name', 'Unknown'),
            'match_confidence': evidence.get('match_confidence', 0),
            'program': evidence.get('source', 'Unknown'),
            'data_source': evidence.get('source', 'Unknown')
        }
        return plane.create_sanctions_match_item(transaction_data, sanctions_match)
    
    elif geography_alerts:
        # High-risk geography
        evidence = geography_alerts[0].get('evidence', {})
        risk_details = {
            'country_risk': evidence.get('country_risk', 'Unknown'),
            'corridor_risk_score': evidence.get('corridor_risk_score', 0)
        }
        return plane.create_high_risk_geography_item(transaction_data, risk_details)
    
    elif structuring_alerts:
        # Structuring pattern
        evidence = structuring_alerts[0].get('evidence', {})
        pattern_details = {
            'transaction_count': evidence.get('transaction_count', 0),
            'total_amount': evidence.get('total_amount', 0),
            'pattern': evidence.get('pattern', 'Unknown'),
            'date': evidence.get('date', 'Unknown')
        }
        return plane.create_structuring_pattern_item(transaction_data, pattern_details)
    
    else:
        # Generic high-risk case
        max_risk_alert = max(alerts, key=lambda x: x.get('risk_score', 0))
        title = f"🚨 HIGH-RISK TRANSACTION: {transaction_data.get('transaction_id')}"
        description = f"High-risk transaction detected with {len(alerts)} AML alerts requiring manual review."
        
        return plane.create_work_item(
            title=title,
            description=description,
            transaction_data=transaction_data,
            alert_data=alerts,
            priority="high"
        )

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
        print(f"⚠️  Warning: Could not load sanctions data: {e}")
        # Load fallback data instead
        try:
            sanctions_loader._load_fallback_sanctions()
            print("✅ Fallback sanctions data loaded")
        except Exception as e2:
            print(f"⚠️  Warning: Could not load fallback data: {e2}")
    
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