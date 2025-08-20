#!/usr/bin/env python3
"""
Simple HTTP server to serve the AML dashboard with CORS support
"""

import http.server
import socketserver
import json
import os
from urllib.parse import urlparse

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'x-api-key,Content-Type')
        super().end_headers()

    def do_GET(self):
        # Serve the alerts JSON data
        if self.path == '/test_results_alerts.json':
            try:
                # Load the actual test results
                with open('../test_results_alerts.json', 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
                return
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Alert data not found')
                return
        
        # Default file serving
        super().do_GET()

if __name__ == '__main__':
    PORT = 8080
    
    # Change to dashboard directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"🚀 AML Dashboard server starting...")
        print(f"📊 Dashboard URL: http://localhost:{PORT}/aml_dashboard.html")
        print(f"🔍 API Endpoint: http://localhost:{PORT}/test_results_alerts.json")
        print(f"⏹️  Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n✅ Dashboard server stopped")