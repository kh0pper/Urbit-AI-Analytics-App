#!/usr/bin/env python3
"""
Simple cookie tester
"""
import requests
import sys

def test_cookie(cookie_value):
    """Test if a cookie value works"""
    print(f"🧪 Testing cookie: {cookie_value[:20]}{'...' if len(cookie_value) > 20 else ''}")
    
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    try:
        response = session.get("http://100.90.185.114:8080/~/login", timeout=10)
        print(f"📊 Response: HTTP {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS! Cookie works!")
            
            # Update .env file
            try:
                with open('.env', 'r') as f:
                    content = f.read()
                
                content = content.replace(
                    'URBIT_SESSION_COOKIE=your_session_cookie_here',
                    f'URBIT_SESSION_COOKIE={cookie_value}'
                )
                
                with open('.env', 'w') as f:
                    f.write(content)
                
                print("✅ Configuration updated!")
                print("\n🚀 Next step: python3 discover_groups.py --cookie " + cookie_value)
                return True
                
            except Exception as e:
                print(f"❌ Error updating config: {e}")
                return False
        else:
            print("❌ Cookie doesn't work")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_cookie.py YOUR_COOKIE_VALUE")
        sys.exit(1)
    
    cookie_value = sys.argv[1]
    test_cookie(cookie_value)