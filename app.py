#!/usr/bin/env python3
"""
Main entry point for AML Dynamic API Server
"""

import sys
import os

# Add the project root to Python path so we can import from src/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the Flask app
from src.api.app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)