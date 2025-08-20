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
    <h1>🛡️ Dynamic AML System</h1>
    <p>Welcome to the Anti-Money Laundering Detection System</p>
    <ul>
        <li><a href="/dashboard/dynamic.html">📊 AML Dashboard</a></li>
        <li><a href="/api/health">💚 Health Check</a></li>
        <li><a href="/api/statistics">📈 Statistics</a></li>
        <li><a href="/api/alerts">🚨 Alerts</a></li>
    </ul>
    '''

@app.route('/dashboard/<path:filename>')
def dashboard_files(filename):
    """Serve dashboard files"""
    return send_from_directory('dashboard', filename)

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

@app.route('/api/generate/process', methods=['POST'])
def generate_and_process():
    """Generate transactions and process them through AML engine"""
    try:
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