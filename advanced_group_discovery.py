#!/usr/bin/env python3
"""
Advanced Urbit group discovery using ship interface analysis
"""
import requests
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def discover_groups_from_interface(cookie_value: str):
    """Discover groups by analyzing the ship's web interface"""
    ship_url = "http://100.90.185.114:8080"
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    print("🔍 Advanced Group Discovery")
    print("=" * 30)
    
    groups_found = []
    
    # Method 1: Analyze the main landscape page
    print("1️⃣ Analyzing landscape interface...")
    try:
        response = session.get(f"{ship_url}/apps/landscape", timeout=15)
        if response.status_code == 200:
            content = response.text
            print(f"   ✅ Got landscape page ({len(content)} chars)")
            
            # Look for group references in the HTML/JS
            group_patterns = [
                r'/ship/[~\w-]+/[\w-]+',
                r'"[~\w-]+/[\w-]+"',
                r'resource.*?/ship/[~\w-]+/[\w-]+',
                r'group.*?[~\w-]+/[\w-]+'
            ]
            
            for pattern in group_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if '/ship/' in match and match not in groups_found:
                        # Clean up the match
                        clean_match = match.strip('"').strip("'")
                        if clean_match.startswith('/ship/'):
                            groups_found.append(clean_match)
                            print(f"   📁 Found: {clean_match}")
        else:
            print(f"   ❌ Failed to get landscape page: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 2: Try Groups app specifically
    print("\n2️⃣ Analyzing groups app...")
    try:
        response = session.get(f"{ship_url}/apps/groups", timeout=15)
        if response.status_code == 200:
            content = response.text
            print(f"   ✅ Got groups page ({len(content)} chars)")
            
            # Parse with BeautifulSoup if possible
            try:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for data attributes or JavaScript with group info
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        script_content = script.string
                        group_matches = re.findall(r'/ship/[~\w-]+/[\w-]+', script_content)
                        for match in group_matches:
                            if match not in groups_found:
                                groups_found.append(match)
                                print(f"   📁 Found in script: {match}")
                                
            except ImportError:
                print("   ⚠️  BeautifulSoup not available, using regex")
                
            # Fallback to regex
            group_matches = re.findall(r'/ship/[~\w-]+/[\w-]+', content)
            for match in group_matches:
                if match not in groups_found:
                    groups_found.append(match)
                    print(f"   📁 Found: {match}")
        else:
            print(f"   ❌ Failed to get groups page: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 3: Try to access known API endpoints
    print("\n3️⃣ Trying API endpoints...")
    api_endpoints = [
        "/~/scry/gx/groups/groups.json",
        "/~/scry/gx/graph-store/graphs.json",
        "/~/scry/gx/metadata-store/resources.json",
        "/~/scry/gx/contact-store/contacts.json"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = session.get(f"{ship_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ {endpoint} works!")
                try:
                    data = response.json()
                    # Analyze the JSON structure for group references
                    json_str = json.dumps(data)
                    group_matches = re.findall(r'/ship/[~\w-]+/[\w-]+', json_str)
                    for match in group_matches:
                        if match not in groups_found:
                            groups_found.append(match)
                            print(f"   📁 Found in API: {match}")
                except json.JSONDecodeError:
                    print(f"   ⚠️  {endpoint} returned non-JSON")
        except Exception as e:
            continue
    
    # Method 4: Try channel subscriptions
    print("\n4️⃣ Testing channel subscriptions...")
    try:
        # Create a test channel
        import uuid
        import time
        
        timestamp = int(time.time())
        channel_id = f"{timestamp}-{str(uuid.uuid4())[:8]}"
        channel_url = f"{ship_url}/~/channel/{channel_id}"
        
        # Try to subscribe to metadata updates
        subscribe_action = {
            "id": 1,
            "action": "subscribe",
            "ship": "our",
            "app": "metadata-store",
            "path": "/all"
        }
        
        response = session.put(channel_url, json=[subscribe_action], timeout=10)
        if response.status_code == 204:
            print("   ✅ Channel subscription works!")
            
            # Listen for updates (briefly)
            sse_url = f"{channel_url}"
            response = session.get(sse_url, timeout=5, stream=True)
            
            if response.status_code == 200:
                for line in response.iter_lines(decode_unicode=True):
                    if line and line.startswith('data:'):
                        try:
                            data = json.loads(line[5:])  # Remove 'data:' prefix
                            data_str = json.dumps(data)
                            group_matches = re.findall(r'/ship/[~\w-]+/[\w-]+', data_str)
                            for match in group_matches:
                                if match not in groups_found:
                                    groups_found.append(match)
                                    print(f"   📁 Found via SSE: {match}")
                        except json.JSONDecodeError:
                            continue
                        except:
                            break
        
    except Exception as e:
        print(f"   ⚠️  Channel test failed: {e}")
    
    # Clean up and validate groups
    print(f"\n🔍 Validating discovered groups...")
    valid_groups = []
    
    for group in groups_found:
        # Basic validation
        if group.count('/') >= 3 and group.startswith('/ship/~'):
            print(f"   🧪 Testing: {group}")
            
            # Quick test to see if group is accessible
            try:
                test_url = f"{ship_url}/~/scry/gx/graph-store/graph{group}/newest/1/noun"
                response = session.get(test_url, timeout=5)
                
                if response.status_code == 200:
                    valid_groups.append(group)
                    print(f"   ✅ Valid: {group}")
                elif response.status_code == 404:
                    print(f"   ❌ Not found: {group}")
                else:
                    print(f"   ⚠️  Status {response.status_code}: {group}")
                    # Still add it as it might be valid
                    valid_groups.append(group)
                    
            except Exception as e:
                print(f"   ❌ Error testing {group}: {e}")
    
    return valid_groups

def update_config_with_groups(groups: list):
    """Update config.py with discovered groups"""
    if not groups:
        print("❌ No groups to add to config")
        return
    
    print(f"\n📝 Updating config with {len(groups)} groups...")
    
    try:
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Format groups for Python list
        groups_str = '[\n'
        for group in groups:
            groups_str += f'    "{group}",\n'
        groups_str += ']'
        
        # Replace the MONITORED_GROUPS section
        import re
        pattern = r'MONITORED_GROUPS = \[.*?\]'
        replacement = f'MONITORED_GROUPS = {groups_str}'
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open('config.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Config updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")

def main():
    cookie_value = "0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4"
    
    print("🚀 Advanced Urbit Group Discovery")
    print("=" * 40)
    
    groups = discover_groups_from_interface(cookie_value)
    
    print(f"\n📊 Discovery Results:")
    print(f"Found {len(groups)} valid groups:")
    
    for i, group in enumerate(groups, 1):
        print(f"{i:2d}. {group}")
    
    if groups:
        update_config_with_groups(groups)
        print(f"\n🎉 Setup complete!")
        print(f"✅ {len(groups)} groups configured for monitoring")
        print(f"\n🚀 Next step: python3 main.py test")
    else:
        print(f"\n⚠️  No groups discovered automatically")
        print(f"You may need to manually add groups to monitor")
        print(f"Check your ship's Groups app for group names")

if __name__ == "__main__":
    main()