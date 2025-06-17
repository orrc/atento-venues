#!/usr/bin/env python3
"""
Simple HTTP server to test the web UI locally
"""

import http.server
import socketserver
import webbrowser
import threading
import time

def start_server():
    """Start the HTTP server"""
    PORT = 8001
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        print(f"Open your browser to view the Atento Voucher Venues interface")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{PORT}')
        
        threading.Thread(target=open_browser, daemon=True).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    start_server()
