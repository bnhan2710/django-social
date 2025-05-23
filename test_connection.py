#!/usr/bin/env python3

import http.client
import json
import sys

def test_connection():
    """Test if the server is running and check WebSocket debug endpoint"""
    host = "127.0.0.1"
    port = 8000
    
    print(f"Testing connection to http://{host}:{port}...")
    
    try:
        # Create HTTP connection
        conn = http.client.HTTPConnection(host, port)
        conn.request("GET", "/ws-debug/")
        
        # Get response
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        
        print(f"HTTP Status: {response.status}")
        print(f"Response: {data[:200]}...")  # Show first 200 chars
        
        if response.status == 200:
            print("✅ Server is running and responding!")
        else:
            print("❌ Server responded with an error status code")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    test_connection()
