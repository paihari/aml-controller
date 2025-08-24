#!/usr/bin/env python3
"""
Dynamic AML System Launcher
"""

import os
import subprocess
import sys
import webbrowser
import time
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['flask', 'requests', 'faker', 'pandas']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
    
    return True

def initialize_system():
    """Initialize the AML system components"""
    print("🚀 Initializing Dynamic AML System...")
    
    try:
        # Initialize database and load initial data
        from database import AMLDatabase
        from sanctions_loader import SanctionsLoader
        from transaction_generator import TransactionGenerator
        from dynamic_aml_engine import DynamicAMLEngine
        
        print("📊 Setting up database...")
        db = AMLDatabase()
        
        print("📥 Loading sanctions data...")
        sanctions_loader = SanctionsLoader()
        sanctions_result = sanctions_loader.refresh_sanctions_data()
        print(f"   ✅ Sanctions loaded: {sanctions_result}")
        
        print("🎲 Generating initial transaction data...")
        generator = TransactionGenerator(db)
        transactions = generator.generate_mixed_batch(25)
        stored = generator.store_transactions(transactions)
        print(f"   ✅ Generated and stored {stored} transactions")
        
        print("⚡ Processing transactions through AML engine...")
        engine = DynamicAMLEngine(db)
        results = engine.process_batch(transactions)
        print(f"   ✅ Processed {results['processed_count']} transactions, generated {results['alert_count']} alerts")
        
        # Show statistics
        stats = db.get_statistics()
        print(f"📈 System Statistics:")
        print(f"   • Sanctions Records: {stats.get('total_sanctions', 0)}")
        print(f"   • Total Transactions: {stats.get('total_transactions', 0)}")
        print(f"   • Active Alerts: {stats.get('active_alerts', 0)}")
        print(f"   • Alerts by Risk: {stats.get('alerts_by_risk', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return False

def start_api_server():
    """Start the Flask API server"""
    print("🌐 Starting Flask API server...")
    
    try:
        # Start the Flask app
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_ENV'] = 'development'
        
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return None

def open_dashboard():
    """Open the dynamic dashboard in browser"""
    dashboard_path = Path(__file__).parent / 'dashboard' / 'dynamic.html'
    
    if dashboard_path.exists():
        print("🌍 Opening dynamic dashboard...")
        webbrowser.open(f'file://{dashboard_path.absolute()}')
        return True
    else:
        print("❌ Dashboard file not found")
        return False

def main():
    print("🛡️  Dynamic AML Agentic Platform Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Initialize system
    if not initialize_system():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎯 System Ready! Starting services...")
    
    # Start API server
    api_process = start_api_server()
    if not api_process:
        sys.exit(1)
    
    # Wait a bit for server to start
    print("⏳ Waiting for API server to start...")
    time.sleep(3)
    
    # Open dashboard
    open_dashboard()
    
    print("\n" + "=" * 50)
    print("✅ Dynamic AML System is running!")
    print("📍 API Endpoint: http://localhost:5000/api")
    print("🌐 Dashboard: file://dashboard/dynamic.html")
    print("📊 Health Check: http://localhost:5000/api/health")
    print("\n💡 Available API Endpoints:")
    print("   • GET  /api/statistics - System statistics")
    print("   • GET  /api/alerts - Active alerts")
    print("   • GET  /api/transactions - Recent transactions")
    print("   • POST /api/generate/process - Generate and process transactions")
    print("   • POST /api/sanctions/refresh - Refresh sanctions data")
    print("   • GET  /api/dashboard/data - All dashboard data")
    print("\n🔥 Press Ctrl+C to stop the system")
    
    try:
        # Keep running until interrupted
        api_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Dynamic AML System...")
        api_process.terminate()
        api_process.wait()
        print("✅ System stopped successfully")

if __name__ == '__main__':
    main()