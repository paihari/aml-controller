#!/bin/bash

echo "🚀 Starting Enhanced AML Dashboard..."
echo ""

# Kill any existing servers
pkill -f "python.*server.py" 2>/dev/null || true

# Start the enhanced dashboard server
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📊 Starting dashboard server on port 8081..."
python3 public_server.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

echo ""
echo "✅ AML Dashboard is now running!"
echo ""
echo "🌐 Dashboard URLs:"
echo "   📋 Standard Dashboard: http://localhost:8081"
echo "   ✨ Enhanced Dashboard: http://localhost:8081/index_enhanced.html"
echo "   📡 API Endpoint: http://localhost:8081/api/alerts"
echo ""
echo "📊 Current Data:"
echo "   • 10 Active Alerts"
echo "   • 4 Critical OFAC Sanctions Matches"
echo "   • 5 High-Risk Geography Transactions"
echo "   • 1 Structuring Pattern Detection"
echo ""
echo "⏹️  To stop: kill $SERVER_PID or press Ctrl+C"
echo ""

# Test the server
if curl -s http://localhost:8081 > /dev/null; then
    echo "🎉 Server is responding successfully!"
    
    # Open the enhanced dashboard
    echo "🔓 Opening enhanced dashboard in browser..."
    open http://localhost:8081/index_enhanced.html
    
    echo ""
    echo "Dashboard is ready! Press any key to stop..."
    read -n 1
    
    echo ""
    echo "🛑 Stopping dashboard server..."
    kill $SERVER_PID 2>/dev/null || true
    echo "✅ Dashboard stopped."
else
    echo "❌ Server failed to start properly"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi