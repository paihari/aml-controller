#!/bin/bash

# Dynamic AML System Startup Script

echo "🛡️  Dynamic AML Agentic Platform"
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet

# Check if system is ready
echo "🔧 Testing system components..."
python3 -c "
from database import AMLDatabase
from sanctions_loader import SanctionsLoader  
from transaction_generator import TransactionGenerator
from dynamic_aml_engine import DynamicAMLEngine

print('   ✅ All components loaded successfully')
"

if [ $? -ne 0 ]; then
    echo "❌ System check failed"
    exit 1
fi

# Initialize system
echo "🚀 Initializing AML system..."
python3 -c "
from database import AMLDatabase
from sanctions_loader import SanctionsLoader
from transaction_generator import TransactionGenerator
from dynamic_aml_engine import DynamicAMLEngine

# Setup system
db = AMLDatabase()
loader = SanctionsLoader()
generator = TransactionGenerator(db)
engine = DynamicAMLEngine(db)

# Load initial data
print('📥 Loading sanctions data from OpenSanctions...')
try:
    loader.refresh_sanctions_data()
    print('✅ Sanctions data loaded successfully')
except Exception as e:
    print(f'❌ Error loading sanctions data: {e}')
    print('💡 Note: Requires Supabase connection for sanctions data')

print('🎲 Generating initial transactions...')
transactions = generator.generate_mixed_batch(15)
generator.store_transactions(transactions)

print('⚡ Processing through AML engine...')
results = engine.process_batch(transactions)
print(f'   Generated {results[\"alert_count\"]} alerts from {results[\"processed_count\"]} transactions')

stats = db.get_statistics()
print(f'📊 System ready with {stats[\"total_sanctions\"]} sanctions, {stats[\"total_transactions\"]} transactions, {stats[\"active_alerts\"]} alerts')
"

echo ""
echo "🌐 Starting Flask API server..."
echo "   API will be available at: http://localhost:5000/api"
echo "   Dashboard available at: dashboard/dynamic.html"
echo ""
echo "🔥 Press Ctrl+C to stop the system"
echo ""

# Start the Flask application
python3 app.py