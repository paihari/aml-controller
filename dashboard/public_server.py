#!/usr/bin/env python3
"""
Public-accessible HTTP server for AML dashboard
Uses ngrok-like tunneling for public access
"""

import http.server
import socketserver
import json
import os
import subprocess
import threading
import time

class PublicCORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'x-api-key,Content-Type')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
            
        # Serve the alerts JSON data
        if self.path == '/test_results_alerts.json' or self.path == '/api/alerts':
            try:
                # Load the actual test results
                with open('../test_results_alerts.json', 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
                return
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Alert data not found')
                return
        
        # Default file serving
        super().do_GET()

def start_tunnel(port):
    """Start ngrok tunnel if available"""
    try:
        # Check if ngrok is available
        result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"🚇 Starting ngrok tunnel...")
            subprocess.Popen(['ngrok', 'http', str(port)], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(3)  # Give ngrok time to start
            
            # Get the public URL
            try:
                result = subprocess.run(['curl', '-s', 'http://localhost:4040/api/tunnels'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    tunnels = json.loads(result.stdout)
                    if tunnels.get('tunnels'):
                        public_url = tunnels['tunnels'][0]['public_url']
                        print(f"🌐 Public URL: {public_url}")
                        return public_url
            except:
                pass
    except:
        pass
    
    print(f"💡 To make publicly accessible, install ngrok:")
    print(f"   brew install ngrok  # macOS")
    print(f"   # Then restart this server")
    return None

if __name__ == '__main__':
    PORT = 8081
    
    # Change to dashboard directory
    os.chdir('/Users/bantwal/projects/my-cluse-code/dashboard')
    
    print(f"🚀 Starting AML Dashboard Public Server...")
    print(f"📂 Serving from: {os.getcwd()}")
    
    # Start tunnel in background
    threading.Thread(target=lambda: start_tunnel(PORT), daemon=True).start()
    
    with socketserver.TCPServer(("", PORT), PublicCORSRequestHandler) as httpd:
        print(f"📊 Local Dashboard: http://localhost:{PORT}")
        print(f"🔍 API Endpoint: http://localhost:{PORT}/api/alerts") 
        print(f"⏹️  Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n✅ Dashboard server stopped")