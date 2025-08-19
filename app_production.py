#!/usr/bin/env python3
"""
Flask Web API for Dynamic AML System - Production Version
"""

import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import datetime
import json
from database import AMLDatabase
from dynamic_aml_engine import DynamicAMLEngine
from transaction_generator import TransactionGenerator
from sanctions_loader import SanctionsLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Production CORS configuration
CORS(app, origins=[
    "https://*.herokuapp.com",
    "https://*.railway.app", 
    "https://*.render.com",
    "https://*.vercel.app",
    "https://*.netlify.app",
    "http://localhost:*",
    "https://localhost:*"
])

# Database path for production
db_path = os.environ.get('DATABASE_PATH', '/app/data/aml_database.db')
db = None
aml_engine = None
transaction_generator = None
sanctions_loader = None

def initialize_components():
    """Initialize all components with error handling"""
    global db, aml_engine, transaction_generator, sanctions_loader
    
    try:
        logger.info("Initializing AML system components...")
        
        # Initialize database
        db = AMLDatabase(db_path=db_path)
        logger.info("Database initialized")
        
        # Initialize other components
        aml_engine = DynamicAMLEngine(db)
        transaction_generator = TransactionGenerator(db)
        sanctions_loader = SanctionsLoader(db)
        
        logger.info("All components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        return False

def ensure_initial_data():
    """Ensure system has initial data"""
    try:
        stats = db.get_statistics()
        
        # Load sanctions if none exist
        if stats.get('total_sanctions', 0) == 0:
            logger.info("Loading initial sanctions data...")
            sanctions_loader._load_fallback_sanctions()
        
        # Generate transactions if none exist  
        if stats.get('total_transactions', 0) == 0:
            logger.info("Generating initial transaction data...")
            transactions = transaction_generator.generate_mixed_batch(20)
            transaction_generator.store_transactions(transactions)
            
            # Process through AML engine
            results = aml_engine.process_batch(transactions)
            logger.info(f"Generated {results['alert_count']} alerts from {results['processed_count']} transactions")
        
        # Log final stats
        final_stats = db.get_statistics()
        logger.info(f"System ready: {final_stats}")
        
    except Exception as e:
        logger.error(f"Error ensuring initial data: {e}")

# Initialize components at module level for production
initialize_components()
ensure_initial_data()

@app.route('/')
def index():
    """Serve the dashboard"""
    return send_from_directory('dashboard', 'dynamic.html')

@app.route('/dashboard')
def dashboard():
    """Serve the dashboard"""
    return send_from_directory('dashboard', 'dynamic.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        stats = db.get_statistics() if db else {}
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'database': 'connected',
            'statistics': stats
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get system statistics"""
    try:
        stats = db.get_statistics()
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Statistics error: {e}")
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
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Alerts error: {e}")
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
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Transactions error: {e}")
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
        
        logger.info(f"Processed transaction {transaction_data.get('transaction_id')}, generated {len(alerts)} alerts")
        
        return jsonify({
            'success': True,
            'transaction_id': transaction_data.get('transaction_id'),
            'alerts_generated': len(alerts),
            'alerts': alerts,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Transaction processing error: {e}")
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
        
        logger.info(f"Processed {results['processed_count']} transactions, generated {results['alert_count']} alerts")
        
        return jsonify({
            'success': True,
            'processed_count': results['processed_count'],
            'alert_count': results['alert_count'],
            'alerts': results['alerts'],
            'processing_time': results['processing_time'].isoformat(),
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/transactions', methods=['POST'])
def generate_transactions():
    """Generate sample transactions for testing"""
    try:
        params = request.get_json() or {}
        count = min(params.get('count', 20), 100)  # Limit to 100 for production
        
        # Generate mixed batch of transactions
        transactions = transaction_generator.generate_mixed_batch(count)
        
        # Store transactions in database
        stored_count = transaction_generator.store_transactions(transactions)
        
        logger.info(f"Generated {len(transactions)} transactions, stored {stored_count}")
        
        return jsonify({
            'success': True,
            'generated_count': len(transactions),
            'stored_count': stored_count,
            'transactions': transactions[:5],  # Return first 5 as sample
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Transaction generation error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate/process', methods=['POST'])
def generate_and_process():
    """Generate transactions and process them through AML engine"""
    try:
        params = request.get_json() or {}
        count = min(params.get('count', 20), 50)  # Limit for production
        
        # Generate transactions
        transactions = transaction_generator.generate_mixed_batch(count)
        
        # Process through AML engine
        results = aml_engine.process_batch(transactions)
        
        logger.info(f"Generated and processed {count} transactions, created {results['alert_count']} alerts")
        
        return jsonify({
            'success': True,
            'generated_count': len(transactions),
            'processed_count': results['processed_count'],
            'alert_count': results['alert_count'],
            'alerts': results['alerts'],
            'processing_time': results['processing_time'].isoformat(),
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Generate and process error: {e}")
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
        
        logger.info(f"Sanctions refresh completed: {results}")
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Sanctions refresh error: {e}")
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
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Sanctions search error: {e}")
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
            'timestamp': datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Dashboard data error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }), 500

if __name__ == '__main__':
    # Initialize components on startup
    if not initialize_components():
        logger.error("Failed to initialize system, exiting...")
        exit(1)
    
    # Ensure initial data exists
    ensure_initial_data()
    
    # Get port from environment variable
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting AML API server on port {port}")
    logger.info("🛡️ Dynamic AML System - Production Mode")
    logger.info(f"📍 Health Check: http://localhost:{port}/api/health")
    logger.info(f"🌐 Dashboard: http://localhost:{port}/dashboard")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )