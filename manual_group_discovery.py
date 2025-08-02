#!/usr/bin/env python3
"""
Manual group discovery by trying common endpoints and exploring the ship
"""
import requests
import json
import re
from urllib.parse import urljoin

def explore_ship_endpoints(cookie_value: str):
    """Explore various ship endpoints to find groups"""
    ship_url = "http://100.90.185.114:8080"
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    print("🔍 Exploring ship endpoints for groups...")
    print("=" * 40)
    
    # Try various scry endpoints
    scry_endpoints = [
        "/~/scry/gx/graph-store/keys.json",
        "/~/scry/gx/graph-store/graphs.json", 
        "/~/scry/gx/group-store/groups.json",
        "/~/scry/gx/group-store/keys.json",
        "/~/scry/gx/metadata-store/associations.json",
        "/~/scry/gx/chat-store/keys.json",
        "/~/scry/gx/chat-store/inbox.json",
        "/~/scry/gx/landscape/apps.json",
        "/~/scry/j/our/life.json",
        "/~/channel",
        "/apps/landscape",
        "/apps/groups",
        "/apps/talk"
    ]
    
    successful_endpoints = []
    
    for endpoint in scry_endpoints:
        try:
            print(f"📡 Trying: {endpoint}")
            response = session.get(f"{ship_url}{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                successful_endpoints.append(endpoint)
                content = response.text
                print(f"   ✅ Success! Content length: {len(content)}")
                
                # Try to parse as JSON
                try:
                    data = response.json()
                    print(f"   📊 JSON data type: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"   📋 Keys: {list(data.keys())[:10]}")
                        
                        # Look for group-like patterns
                        for key, value in data.items():
                            if isinstance(key, str) and ('/ship/' in key or key.startswith('~')):
                                print(f"      🏷️  Potential group: {key}")
                    
                    elif isinstance(data, list):
                        print(f"   📋 List with {len(data)} items")
                        for i, item in enumerate(data[:5]):
                            if isinstance(item, str) and ('/ship/' in item or item.startswith('~')):
                                print(f"      🏷️  Potential group: {item}")
                                
                except json.JSONDecodeError:
                    print("   📄 Non-JSON response")
                    # Look for patterns in HTML/text
                    if '/ship/' in content:
                        matches = re.findall(r'/ship/[~\w-]+/[\w-]+', content)
                        for match in matches[:10]:
                            print(f"      🏷️  Found pattern: {match}")
                
            elif response.status_code == 404:
                print("   ❌ Not found")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Summary: {len(successful_endpoints)} successful endpoints")
    return successful_endpoints

def try_common_groups(cookie_value: str):
    """Try to access some common group patterns"""
    ship_url = "http://100.90.185.114:8080"
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    print("\n🎯 Trying common group patterns...")
    
    # Common group patterns - these are guesses based on popular Urbit groups
    common_groups = [
        "/ship/~bitbet-bolbel/urbit-community", 
        "/ship/~darrux-landes/the-forge",
        "/ship/~bollug-worlus/urbit-index",
        "/ship/~haddef-sigwen/tlon",
        "/ship/~nattyv/urbit",
        "/ship/~solfer-magfed/foundation",
        # Your own ship groups
        "/ship/~litmyl-nopmet/general",
        "/ship/~litmyl-nopmet/chat",
        "/ship/~litmyl-nopmet/test"
    ]
    
    valid_groups = []
    
    for group in common_groups:
        try:
            print(f"🔍 Testing group: {group}")
            
            # Try to scry for the group
            scry_url = f"{ship_url}/~/scry/gx/graph-store/graph{group}/newest/10/noun"
            response = session.get(scry_url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Group exists and accessible!")
                valid_groups.append(group)
            elif response.status_code == 404:
                print(f"   ❌ Group not found")
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return valid_groups

def main():
    cookie_value = "0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4"
    
    print("🕵️ Manual Urbit Group Discovery")
    print("=" * 35)
    
    # First, explore endpoints
    successful_endpoints = explore_ship_endpoints(cookie_value)
    
    # Then try common groups
    valid_groups = try_common_groups(cookie_value)
    
    print(f"\n📋 Results:")
    print(f"✅ Found {len(successful_endpoints)} working endpoints")
    print(f"✅ Found {len(valid_groups)} accessible groups")
    
    if valid_groups:
        print(f"\n🎯 Valid groups found:")
        for group in valid_groups:
            print(f"   - {group}")
            
        # Update config.py
        try:
            with open('config.py', 'r') as f:
                content = f.read()
            
            # Format groups for Python list
            groups_str = '[\n'
            for group in valid_groups:
                groups_str += f'    "{group}",\n'
            groups_str += ']'
            
            # Replace the MONITORED_GROUPS section
            import re
            pattern = r'MONITORED_GROUPS = \[.*?\]'
            replacement = f'MONITORED_GROUPS = {groups_str}'
            
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            with open('config.py', 'w') as f:
                f.write(content)
            
            print(f"✅ Updated config.py with {len(valid_groups)} groups")
            
        except Exception as e:
            print(f"❌ Error updating config: {e}")
    else:
        print(f"\n⚠️  No groups found automatically")
        print(f"You may need to manually add group paths to config.py")
        print(f"Example format: /ship/~host-ship/group-name")

if __name__ == "__main__":
    main()