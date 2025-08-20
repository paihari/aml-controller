#!/usr/bin/env python3
"""
Flask Web API for Dynamic AML System
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import json
import os
from database import AMLDatabase
from dynamic_aml_engine import DynamicAMLEngine
from transaction_generator import TransactionGenerator
from sanctions_loader import SanctionsLoader

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
        if not db:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 503
            
        stats = db.get_statistics()
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
    """Get recent transactions"""
    try:
        limit = request.args.get('limit', 100, type=int)
        transactions = db.get_recent_transactions(limit=limit)
        
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
    """Generate transactions and process them through AML engine"""
    try:
        if request.method == 'GET':
            count = request.args.get('count', 20, type=int)
        else:
            params = request.get_json() or {}
            count = params.get('count', 20)
        
        # Generate transactions
        transactions = transaction_generator.generate_mixed_batch(count)
        
        # Process through AML engine
        results = aml_engine.process_batch(transactions)
        
        return jsonify({
            'success': True,
            'generated_count': len(transactions),
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
        # Get statistics
        stats = db.get_statistics()
        
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

@app.route('/api/transactions/process', methods=['POST'])
def process_pending_transactions():
    """Process pending transactions and update their status"""
    try:
        if not db:
            return jsonify({
                'success': False,
                'error': 'Database not initialized'
            }), 503
        
        # Get all pending transactions
        conn = db.get_connection()
        cursor = conn.execute("""
            SELECT * FROM transactions 
            WHERE status = 'PENDING' 
            ORDER BY created_at DESC
            LIMIT 50
        """)
        pending_transactions = [dict(row) for row in cursor.fetchall()]
        
        if not pending_transactions:
            return jsonify({
                'success': True,
                'message': 'No pending transactions to process',
                'processed_count': 0,
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        # Process transactions - simulate different outcomes
        import random
        processed_count = 0
        completed_count = 0
        failed_count = 0
        under_review_count = 0
        
        for tx in pending_transactions:
            # Simulate processing with different outcomes
            outcome = random.choices(
                ['COMPLETED', 'FAILED', 'UNDER_REVIEW'], 
                weights=[0.85, 0.10, 0.05]  # 85% complete, 10% fail, 5% review
            )[0]
            
            # Update transaction status
            conn.execute("""
                UPDATE transactions 
                SET status = ?, created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (outcome, tx['id']))
            
            processed_count += 1
            if outcome == 'COMPLETED':
                completed_count += 1
            elif outcome == 'FAILED':
                failed_count += 1
            else:
                under_review_count += 1
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'Processed {processed_count} pending transactions',
            'processed_count': processed_count,
            'results': {
                'completed': completed_count,
                'failed': failed_count,
                'under_review': under_review_count
            },
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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