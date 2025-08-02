#!/usr/bin/env python3
"""
Urbit Login Automation - Generate session cookie from access code
"""
import requests
import json
import re
import time
from typing import Optional

class UrbitLoginBot:
    def __init__(self, ship_url: str):
        self.ship_url = ship_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        })
    
    def login_with_code(self, access_code: str) -> Optional[str]:
        """Login to Urbit ship using access code and return session cookie"""
        print(f"🚀 Attempting to login to {self.ship_url}")
        print(f"🔑 Using access code: {access_code[:8]}...")
        
        try:
            # Step 1: Get the login page to understand the form structure
            print("📄 Getting login page...")
            login_url = f"{self.ship_url}/~/login"
            response = self.session.get(login_url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Failed to access login page: HTTP {response.status_code}")
                return None
            
            print("✅ Got login page")
            
            # Step 2: Extract any CSRF tokens or hidden fields
            html_content = response.text
            csrf_token = None
            
            # Look for CSRF token patterns
            csrf_patterns = [
                r'name=["\']_csrf["\'] value=["\']([^"\']+)["\']',
                r'csrf["\']:\s*["\']([^"\']+)["\']',
                r'_token["\'] value=["\']([^"\']+)["\']'
            ]
            
            for pattern in csrf_patterns:
                match = re.search(pattern, html_content)
                if match:
                    csrf_token = match.group(1)
                    print(f"🔒 Found CSRF token: {csrf_token[:10]}...")
                    break
            
            # Step 3: Attempt login with different possible form structures
            login_attempts = [
                # Standard password field
                {"password": access_code},
                
                # With CSRF token
                {"password": access_code, "_csrf": csrf_token} if csrf_token else None,
                
                # Alternative field names
                {"code": access_code},
                {"access_code": access_code},
                {"login_code": access_code},
                
                # JSON format
                None  # Will be handled separately
            ]
            
            login_attempts = [attempt for attempt in login_attempts if attempt is not None]
            
            for i, form_data in enumerate(login_attempts):
                print(f"🔄 Login attempt {i+1}/{len(login_attempts)}")
                
                # Try POST to login endpoint
                response = self.session.post(
                    login_url,
                    data=form_data,
                    timeout=15,
                    allow_redirects=True
                )
                
                print(f"   Response: HTTP {response.status_code}")
                
                # Check if login was successful
                if self._check_login_success(response):
                    print("✅ Login successful!")
                    return self._extract_session_cookie()
                
                # Wait between attempts
                time.sleep(1)
            
            # Step 4: Try JSON-based login
            print("🔄 Trying JSON login...")
            json_data = {"password": access_code}
            if csrf_token:
                json_data["_csrf"] = csrf_token
            
            response = self.session.post(
                login_url,
                json=json_data,
                headers={'Content-Type': 'application/json'},
                timeout=15
            )
            
            print(f"   JSON Response: HTTP {response.status_code}")
            
            if self._check_login_success(response):
                print("✅ JSON login successful!")
                return self._extract_session_cookie()
            
            # Step 5: Try alternative endpoints
            alt_endpoints = [
                f"{self.ship_url}/~/auth",
                f"{self.ship_url}/auth",
                f"{self.ship_url}/login"
            ]
            
            for endpoint in alt_endpoints:
                print(f"🔄 Trying endpoint: {endpoint}")
                try:
                    response = self.session.post(
                        endpoint,
                        data={"password": access_code},
                        timeout=10
                    )
                    
                    if self._check_login_success(response):
                        print("✅ Alternative endpoint login successful!")
                        return self._extract_session_cookie()
                except:
                    continue
            
            print("❌ All login attempts failed")
            print("💡 This could mean:")
            print("   - Access code is incorrect")
            print("   - Ship requires different authentication method")
            print("   - Ship is not accessible")
            print("   - Login form structure is different than expected")
            
            return None
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            return None
    
    def _check_login_success(self, response) -> bool:
        """Check if login was successful"""
        # Check status codes
        if response.status_code in [200, 302, 303]:
            # Check for redirect to dashboard/main page
            if 'location' in response.headers:
                location = response.headers['location']
                if any(path in location.lower() for path in ['/apps', '/landscape', '/dashboard', '/home']):
                    return True
            
            # Check response content for success indicators
            content = response.text.lower()
            success_indicators = [
                'landscape',
                'dashboard',
                'apps',
                'welcome',
                'grid',
                '"ship":', 
                'urbauth-'
            ]
            
            if any(indicator in content for indicator in success_indicators):
                return True
            
            # Check for absence of login form
            if 'password' not in content and 'login' not in content:
                return True
        
        return False
    
    def _extract_session_cookie(self) -> Optional[str]:
        """Extract the session cookie from the current session"""
        print("🍪 Extracting session cookie...")
        
        # Look through all cookies for Urbit auth cookie
        for cookie in self.session.cookies:
            if cookie.name.startswith('urbauth-'):
                print(f"✅ Found session cookie: {cookie.name}")
                print(f"   Value: {cookie.value[:20]}...")
                return cookie.value
        
        print("❌ No session cookie found")
        return None
    
    def test_cookie(self, cookie_value: str) -> bool:
        """Test if a cookie value works"""
        print(f"🧪 Testing cookie...")
        
        test_session = requests.Session()
        
        # Set the cookie for the ship domain
        ship_domain = self.ship_url.replace('http://', '').replace('https://', '').split(':')[0]
        test_session.cookies.set('urbauth-~litmyl-nopmet', cookie_value, domain=ship_domain)
        
        try:
            # Test access to a protected endpoint
            response = test_session.get(f"{self.ship_url}/~/login", timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                # If we get the main interface (not login form), cookie works
                if 'landscape' in content or 'apps' in content or '"ship":' in content:
                    print("✅ Cookie works!")
                    return True
                elif 'password' in content:
                    print("❌ Cookie invalid - still seeing login form")
                    return False
            
            print(f"⚠️  Unclear result: HTTP {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Cookie test error: {e}")
            return False

def main():
    print("🤖 Urbit Login Bot")
    print("=" * 25)
    
    ship_url = "http://100.90.185.114:8080"
    
    # Get access code from user
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 urbit_login.py YOUR_ACCESS_CODE")
        print()
        print("Your access code is the +code from your ship")
        print("(the one you use to login from new devices)")
        return
    
    access_code = sys.argv[1]
    
    # Create login bot
    bot = UrbitLoginBot(ship_url)
    
    # Attempt login
    session_cookie = bot.login_with_code(access_code)
    
    if session_cookie:
        print(f"\n🎉 SUCCESS!")
        print(f"Session Cookie: {session_cookie}")
        
        # Test the cookie
        if bot.test_cookie(session_cookie):
            # Update .env file
            try:
                with open('.env', 'r') as f:
                    content = f.read()
                
                content = content.replace(
                    'URBIT_SESSION_COOKIE=your_session_cookie_here',
                    f'URBIT_SESSION_COOKIE={session_cookie}'
                )
                
                with open('.env', 'w') as f:
                    f.write(content)
                
                print("✅ Configuration updated!")
                print("\n🚀 Next step: python3 discover_groups.py --cookie " + session_cookie)
                
            except Exception as e:
                print(f"❌ Error updating config: {e}")
                print(f"Manual update needed: {session_cookie}")
        else:
            print("⚠️  Cookie generated but may not be working properly")
    else:
        print(f"\n❌ Login failed")
        print("Please check your access code and try again")

if __name__ == "__main__":
    main()