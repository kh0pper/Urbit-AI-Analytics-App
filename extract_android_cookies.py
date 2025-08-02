#!/usr/bin/env python3
"""
Helper to extract cookies from Android browser files
"""
import sqlite3
import json
import os
from typing import Dict, List

def extract_from_cookie_db(db_path: str) -> List[Dict]:
    """Extract cookies from Chrome/Brave cookie database"""
    cookies = []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query for Urbit cookies
        query = """
        SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
        FROM cookies 
        WHERE host_key LIKE '%100.90.185.114%' 
        OR name LIKE '%urbauth%' 
        OR name LIKE '%litmyl-nopmet%'
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            cookie = {
                'name': row[0],
                'value': row[1], 
                'domain': row[2],
                'path': row[3],
                'expires': row[4],
                'secure': row[5],
                'httponly': row[6]
            }
            cookies.append(cookie)
            
        conn.close()
        print(f"✅ Found {len(cookies)} cookies in {db_path}")
        
    except Exception as e:
        print(f"❌ Error reading {db_path}: {e}")
        
    return cookies

def search_for_cookie_files(search_paths: List[str]) -> List[str]:
    """Search for cookie database files"""
    found_files = []
    
    for path in search_paths:
        if os.path.exists(path):
            print(f"✅ Found path: {path}")
            
            # Look for cookie files
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower() in ['cookies', 'cookies-journal', 'web data']:
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
                        print(f"   📄 Found cookie file: {full_path}")
        else:
            print(f"❌ Path not found: {path}")
    
    return found_files

def parse_cookie_text_file(file_path: str) -> List[str]:
    """Parse text-based cookie files"""
    cookies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Look for Urbit-related patterns
            if 'urbauth' in content or 'litmyl-nopmet' in content or '100.90.185.114' in content:
                print(f"✅ Found Urbit-related content in {file_path}")
                
                # Extract potential cookie values
                lines = content.split('\n')
                for line in lines:
                    if 'urbauth' in line or 'litmyl-nopmet' in line:
                        cookies.append(line.strip())
                        print(f"   🔑 Potential cookie: {line[:50]}...")
                        
    except Exception as e:
        print(f"❌ Error reading text file {file_path}: {e}")
        
    return cookies

def main():
    print("🔍 Android Cookie Extractor")
    print("=" * 30)
    
    # Common Android browser data paths
    search_paths = [
        "/data/data/com.brave.browser/app_chrome/Default/",
        "/data/data/com.brave.browser/",
        "/storage/emulated/0/Android/data/com.brave.browser/",
        "/sdcard/Android/data/com.brave.browser/",
        # Chrome paths as backup
        "/data/data/com.android.chrome/app_chrome/Default/",
        "/storage/emulated/0/Android/data/com.android.chrome/",
    ]
    
    print("🔍 Searching for cookie files...")
    cookie_files = search_for_cookie_files(search_paths)
    
    if not cookie_files:
        print("\n❌ No cookie files found")
        print("This could mean:")
        print("- Files are in a different location")
        print("- Root access required")
        print("- Browser stores cookies differently")
        return
    
    print(f"\n📂 Found {len(cookie_files)} cookie files")
    
    all_cookies = []
    
    for file_path in cookie_files:
        print(f"\n🔍 Processing {file_path}")
        
        if file_path.endswith(('Cookies', 'cookies')):
            # Try as SQLite database
            db_cookies = extract_from_cookie_db(file_path)
            all_cookies.extend(db_cookies)
        else:
            # Try as text file
            text_cookies = parse_cookie_text_file(file_path)
            for cookie in text_cookies:
                all_cookies.append({'raw': cookie})
    
    # Look for Urbit auth cookie
    urbit_cookie = None
    for cookie in all_cookies:
        if isinstance(cookie, dict):
            if 'name' in cookie and cookie['name'] == 'urbauth-~litmyl-nopmet':
                urbit_cookie = cookie['value']
                print(f"\n🎉 Found Urbit auth cookie!")
                print(f"Value: {urbit_cookie}")
                break
            elif 'raw' in cookie and 'urbauth-~litmyl-nopmet' in cookie['raw']:
                # Extract from raw text
                raw = cookie['raw']
                if '=' in raw:
                    urbit_cookie = raw.split('=', 1)[1].split(';')[0].strip()
                    print(f"\n🎉 Found Urbit auth cookie from raw text!")
                    print(f"Value: {urbit_cookie}")
                    break
    
    if urbit_cookie:
        print(f"\n✅ SUCCESS!")
        print(f"Cookie to use: {urbit_cookie}")
        
        # Test the cookie
        print(f"\n🧪 Testing cookie...")
        import requests
        session = requests.Session()
        session.cookies.set('urbauth-~litmyl-nopmet', urbit_cookie)
        
        try:
            response = session.get("http://100.90.185.114:8080/~/login", timeout=10)
            if response.status_code == 200:
                print("✅ Cookie works!")
                
                # Update config
                try:
                    with open('.env', 'r') as f:
                        content = f.read()
                    
                    content = content.replace(
                        'URBIT_SESSION_COOKIE=your_session_cookie_here',
                        f'URBIT_SESSION_COOKIE={urbit_cookie}'
                    )
                    
                    with open('.env', 'w') as f:
                        f.write(content)
                    
                    print("✅ Configuration updated!")
                    
                except Exception as e:
                    print(f"❌ Error updating config: {e}")
            else:
                print(f"❌ Cookie test failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Cookie test error: {e}")
    else:
        print(f"\n❌ No Urbit auth cookie found")
        print(f"Found {len(all_cookies)} total cookies, but none for Urbit")

if __name__ == "__main__":
    main()