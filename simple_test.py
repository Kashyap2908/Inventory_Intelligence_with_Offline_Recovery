#!/usr/bin/env python3
"""
Simple test to check if server is running and accessible
"""

import requests

def test_server():
    """Test if the server is accessible"""
    
    print("🧪 Testing Server Accessibility")
    print("=" * 40)
    
    try:
        # Test login page
        response = requests.get('http://localhost:8000/')
        print(f"✅ Login page loads: {response.status_code}")
        
        if 'NeuroStock' in response.text:
            print("✅ NeuroStock branding found")
        
        if 'login' in response.text.lower():
            print("✅ Login form found")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 40)
    print("🏁 Server test completed!")
    print("\nManual testing steps:")
    print("1. Open http://localhost:8000/ in your browser")
    print("2. Login with username: admin, password: admin123")
    print("3. Navigate to Marketing Dashboard (Trends)")
    print("4. Click the 'Run Trend Analysis' button")
    print("5. Check if you see an alert popup")

if __name__ == "__main__":
    test_server()