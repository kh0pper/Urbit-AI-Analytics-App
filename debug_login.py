#!/usr/bin/env python3
"""
Debug Urbit login to understand the exact authentication flow
"""
import requests
import json
import re
from urllib.parse import urljoin

def debug_urbit_login(access_code: str):
    """Debug the Urbit login process"""
    ship_url = "http://100.90.185.114:8080"
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
    })
    
    print("🔍 Debugging Urbit login process...")
    print(f"Ship URL: {ship_url}")
    print(f"Access Code: {access_code}")
    print("=" * 50)
    
    # Step 1: Get the main page
    print("1️⃣ Checking main page...")
    try:
        response = session.get(ship_url, timeout=15)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        if 'password' in response.text.lower():
            print("   ✅ Found login form on main page")
        else:
            print("   ⚠️  No obvious login form on main page")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 2: Check /~/login endpoint
    print("\n2️⃣ Checking /~/login endpoint...")
    try:
        login_url = f"{ship_url}/~/login"
        response = session.get(login_url, timeout=15)
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)}")
        
        # Look for form elements
        html = response.text.lower()
        if 'form' in html:
            print("   ✅ Found form element")
        if 'password' in html:
            print("   ✅ Found password field")
        if 'input' in html:
            print("   ✅ Found input elements")
            
        # Extract form details
        form_action_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', response.text, re.IGNORECASE)
        if form_action_match:
            print(f"   📋 Form action: {form_action_match.group(1)}")
            
        # Look for input fields
        input_matches = re.findall(r'<input[^>]*>', response.text, re.IGNORECASE)
        print(f"   📋 Found {len(input_matches)} input fields")
        
        for i, inp in enumerate(input_matches[:5]):  # Show first 5
            print(f"      {i+1}. {inp[:100]}...")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Step 3: Try Urbit-specific authentication
    print("\n3️⃣ Trying Urbit-specific auth methods...")
    
    # Method A: Direct password POST to login
    try:
        print("   Method A: POST password to /~/login")
        response = session.post(
            f"{ship_url}/~/login",
            data={'password': access_code},
            timeout=15
        )
        print(f"      Status: {response.status_code}")
        print(f"      Response length: {len(response.text)}")
        
        # Check cookies after this request
        cookies = {cookie.name: cookie.value for cookie in session.cookies}
        print(f"      Cookies: {list(cookies.keys())}")
        
        if any('urbauth' in cookie for cookie in cookies):
            print("      ✅ Found urbauth cookie!")
            for name, value in cookies.items():
                if 'urbauth' in name:
                    print(f"      🍪 {name}: {value[:30]}...")
                    return value
                    
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Method B: Try PUT method (some Urbit endpoints use PUT)
    try:
        print("   Method B: PUT password to /~/login")
        response = session.put(
            f"{ship_url}/~/login",
            data={'password': access_code},
            timeout=15
        )
        print(f"      Status: {response.status_code}")
        
        cookies = {cookie.name: cookie.value for cookie in session.cookies}
        if any('urbauth' in cookie for cookie in cookies):
            print("      ✅ Found urbauth cookie with PUT!")
            for name, value in cookies.items():
                if 'urbauth' in name:
                    print(f"      🍪 {name}: {value[:30]}...")
                    return value
                    
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Method C: JSON authentication
    try:
        print("   Method C: JSON authentication")
        response = session.post(
            f"{ship_url}/~/login",
            json={'password': access_code},
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        print(f"      Status: {response.status_code}")
        
        cookies = {cookie.name: cookie.value for cookie in session.cookies}
        if any('urbauth' in cookie for cookie in cookies):
            print("      ✅ Found urbauth cookie with JSON!")
            for name, value in cookies.items():
                if 'urbauth' in name:
                    print(f"      🍪 {name}: {value[:30]}...")
                    return value
                    
    except Exception as e:
        print(f"      ❌ Error: {e}")
    
    # Method D: Try different endpoints
    endpoints_to_try = [
        '/~/channel/login',
        '/auth',
        '/authenticate', 
        '/api/login'
    ]
    
    for endpoint in endpoints_to_try:
        try:
            print(f"   Method D: POST to {endpoint}")
            response = session.post(
                f"{ship_url}{endpoint}",
                data={'password': access_code},
                timeout=10
            )
            print(f"      Status: {response.status_code}")
            
            cookies = {cookie.name: cookie.value for cookie in session.cookies}
            if any('urbauth' in cookie for cookie in cookies):
                print(f"      ✅ Found urbauth cookie at {endpoint}!")
                for name, value in cookies.items():
                    if 'urbauth' in name:
                        print(f"      🍪 {name}: {value[:30]}...")
                        return value
                        
        except Exception as e:
            continue
    
    print("\n❌ No authentication method worked")
    print("💡 Possible issues:")
    print("   - Access code might be incorrect")
    print("   - Ship might use a different auth method")
    print("   - Ship might be behind additional authentication")
    print("   - Network connectivity issues")
    
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 debug_login.py ACCESS_CODE")
        sys.exit(1)
    
    access_code = sys.argv[1]
    cookie = debug_urbit_login(access_code)
    
    if cookie:
        print(f"\n🎉 SUCCESS! Found cookie: {cookie}")
        
        # Update .env file
        try:
            with open('.env', 'r') as f:
                content = f.read()
            
            content = content.replace(
                'URBIT_SESSION_COOKIE=your_session_cookie_here',
                f'URBIT_SESSION_COOKIE={cookie}'
            )
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✅ Configuration updated!")
            
        except Exception as e:
            print(f"❌ Error updating config: {e}")
    else:
        print(f"\n❌ Could not authenticate with the provided access code")