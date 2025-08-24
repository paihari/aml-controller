#!/usr/bin/env python3
"""
Create a simple hosting solution using Python's built-in server
with public access via ngrok if available
"""

import http.server
import socketserver
import os
import sys
import webbrowser
import threading
import time
import subprocess
import json

class AMLDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        # Serve API data
        if self.path == '/api/alerts' or self.path == '/api.json':
            try:
                with open('api.json', 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
                return
            except FileNotFoundError:
                pass
        
        # Default file serving
        super().do_GET()

def check_ngrok():
    """Check if ngrok is available and start tunnel"""
    try:
        result = subprocess.run(['which', 'ngrok'], capture_output=True, text=True)
        if result.returncode == 0:
            print("🚇 Starting ngrok tunnel...")
            # Start ngrok in background
            subprocess.Popen(['ngrok', 'http', '8080'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Wait a bit for ngrok to start
            time.sleep(4)
            
            # Try to get the public URL
            try:
                result = subprocess.run(['curl', '-s', 'localhost:4040/api/tunnels'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get('tunnels'):
                        public_url = data['tunnels'][0]['public_url']
                        return public_url
            except:
                pass
    except:
        pass
    
    return None

def main():
    PORT = 8080
    
    # Change to deployment directory
    os.chdir('online_deploy')
    
    print("🚀 Starting AML Dashboard Server...")
    print(f"📂 Serving from: {os.getcwd()}")
    print(f"📊 Files: {', '.join(os.listdir('.'))}")
    
    # Check for ngrok
    public_url = check_ngrok()
    
    print(f"\n🌐 AML Dashboard URLs:")
    print(f"   📊 Local Enhanced: http://localhost:{PORT}/index.html")
    print(f"   📋 Local Standard: http://localhost:{PORT}/standard.html")
    print(f"   📡 API Endpoint: http://localhost:{PORT}/api.json")
    
    if public_url:
        print(f"\n🌍 PUBLIC URLS (accessible from anywhere):")
        print(f"   📊 Enhanced Dashboard: {public_url}/index.html")
        print(f"   📋 Standard Dashboard: {public_url}/standard.html")
        print(f"   📡 API Endpoint: {public_url}/api.json")
        print(f"\n   🎉 SHARE THESE URLS WITH ANYONE!")
    else:
        print(f"\n💡 For public access, install ngrok:")
        print(f"   brew install ngrok  # macOS")
        print(f"   Then restart this server")
    
    # Start server
    try:
        with socketserver.TCPServer(("", PORT), AMLDashboardHandler) as httpd:
            print(f"\n✅ Server running on port {PORT}")
            print(f"⏹️  Press Ctrl+C to stop")
            
            # Open local browser
            def open_browser():
                time.sleep(2)
                webbrowser.open(f'http://localhost:{PORT}/index.html')
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n✅ Server stopped")
        # Kill ngrok if running
        subprocess.run(['pkill', '-f', 'ngrok'], capture_output=True)

if __name__ == "__main__":
    main()