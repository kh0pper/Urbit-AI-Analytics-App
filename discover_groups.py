#!/usr/bin/env python3
"""
Helper script to discover groups and get session cookie from your Urbit ship
"""
import requests
import json
import re
from typing import List, Dict

def get_session_cookie_help():
    """Print instructions for getting session cookie"""
    print("🔑 To get your session cookie:")
    print("1. Open http://100.90.185.114:8080 in your browser")
    print("2. Log into your ship (~litmyl-nopmet)")
    print("3. Press F12 to open developer tools")
    print("4. Go to Application → Cookies")
    print("5. Look for cookie: urbauth-~litmyl-nopmet")
    print("6. Copy the value (long string)")
    print("7. Run: python3 discover_groups.py --cookie YOUR_COOKIE_VALUE")
    print()

def discover_groups_with_cookie(cookie_value: str) -> List[str]:
    """Discover groups you're a member of"""
    print(f"🔍 Discovering groups for ~litmyl-nopmet...")
    
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    ship_url = "http://100.90.185.114:8080"
    groups = []
    
    try:
        # Try to get groups from graph-store
        print("📊 Checking graph-store for groups...")
        scry_url = f"{ship_url}/~/scry/gx/graph-store/keys.json"
        response = session.get(scry_url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found graph data: {len(data) if isinstance(data, list) else 'unknown'} entries")
            
            # Parse group paths from graph keys
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str) and item.startswith('/ship/'):
                        groups.append(item)
                        print(f"   📁 Found group: {item}")
        else:
            print(f"⚠️  Graph-store scry failed: {response.status_code}")
            
        # Try to get groups from group-store
        print("👥 Checking group-store...")
        scry_url = f"{ship_url}/~/scry/gx/group-store/groups.json"
        response = session.get(scry_url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found group-store data")
            
            # Parse groups
            if isinstance(data, dict):
                for group_path in data.keys():
                    if group_path.startswith('/ship/') and group_path not in groups:
                        groups.append(group_path)
                        print(f"   👥 Found group: {group_path}")
        else:
            print(f"⚠️  Group-store scry failed: {response.status_code}")
            
        # Try alternative discovery methods
        if not groups:
            print("🔍 Trying alternative discovery...")
            
            # Check for landscape groups
            scry_url = f"{ship_url}/~/scry/gx/metadata-store/associations.json"
            response = session.get(scry_url)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Found metadata associations")
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key.startswith('/ship/'):
                            groups.append(key)
                            print(f"   🏷️  Found from metadata: {key}")
            
        if groups:
            print(f"\n🎉 Successfully discovered {len(groups)} groups!")
            return list(set(groups))  # Remove duplicates
        else:
            print("\n⚠️  No groups found. This could mean:")
            print("   - Cookie is invalid/expired")
            print("   - Ship is not accessible")
            print("   - No groups joined yet")
            print("   - Different API structure")
            return []
            
    except Exception as e:
        print(f"❌ Error discovering groups: {e}")
        return []

def test_connection(cookie_value: str) -> bool:
    """Test basic connection to the ship"""
    print("🧪 Testing connection to your ship...")
    
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    ship_url = "http://100.90.185.114:8080"
    
    try:
        # Test basic authentication
        response = session.get(f"{ship_url}/~/login")
        if response.status_code == 200:
            print("✅ Successfully connected to ship")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code}")
            print("   Check if cookie is valid and ship is accessible")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def update_config_file(groups: List[str], cookie_value: str):
    """Update the configuration files with discovered groups"""
    print("📝 Updating configuration files...")
    
    # Update .env file with cookie
    try:
        with open('.env', 'r') as f:
            env_content = f.read()
        
        env_content = env_content.replace(
            'URBIT_SESSION_COOKIE=your_session_cookie_here',
            f'URBIT_SESSION_COOKIE={cookie_value}'
        )
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Updated .env file with session cookie")
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")
    
    # Update config.py with groups
    try:
        with open('config.py', 'r') as f:
            config_content = f.read()
        
        # Format groups for Python list
        groups_str = '[\n'
        for group in groups:
            groups_str += f'    "{group}",\n'
        groups_str += ']'
        
        # Replace the MONITORED_GROUPS section
        import re
        pattern = r'MONITORED_GROUPS = \[.*?\]'
        replacement = f'MONITORED_GROUPS = {groups_str}'
        
        config_content = re.sub(pattern, replacement, config_content, flags=re.DOTALL)
        
        with open('config.py', 'w') as f:
            f.write(config_content)
        
        print(f"✅ Updated config.py with {len(groups)} groups")
        
    except Exception as e:
        print(f"❌ Error updating config.py: {e}")

def main():
    import sys
    
    print("🤖 Urbit Group Discovery Tool")
    print("=" * 40)
    
    if len(sys.argv) < 3 or sys.argv[1] != '--cookie':
        get_session_cookie_help()
        return
    
    cookie_value = sys.argv[2]
    print(f"🔑 Using provided session cookie")
    
    # Test connection first
    if not test_connection(cookie_value):
        print("\n❌ Setup cannot continue - fix connection issues first")
        return
    
    # Discover groups
    groups = discover_groups_with_cookie(cookie_value)
    
    if groups:
        print(f"\n📋 Discovered Groups:")
        for i, group in enumerate(groups, 1):
            print(f"{i:2d}. {group}")
        
        # Update configuration
        update_config_file(groups, cookie_value)
        
        print(f"\n🎉 Setup Complete!")
        print(f"✅ {len(groups)} groups configured for monitoring")
        print(f"✅ Session cookie saved")
        print(f"\n🚀 Next steps:")
        print(f"   python3 main.py test    # Test the system")
        print(f"   python3 main.py         # Start monitoring")
        
    else:
        print("\n❌ No groups discovered")
        print("Try manually adding groups to config.py")

if __name__ == "__main__":
    main()