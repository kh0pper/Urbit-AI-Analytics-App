#!/usr/bin/env python3
"""
Updated Urbit group discovery script for the user's specific ship configuration
Ship URL: http://100.90.185.114:8080
Session Cookie: 0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4
"""
import requests
import json
import re
import time
import uuid
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

# User's specific configuration
SHIP_URL = "http://100.90.185.114:8080"
SESSION_COOKIE = "0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4"

def get_ship_name_from_cookie():
    """Extract ship name from the URL and context"""
    # From the example URL, we know the host ship is ~halbex-palheb
    # But we need to determine the user's own ship name for authentication
    return "~halbex-palheb"  # This may need adjustment based on actual user ship

def setup_session() -> requests.Session:
    """Setup authenticated session with proper cookie"""
    session = requests.Session()
    ship_name = get_ship_name_from_cookie()
    cookie_name = f"urbauth-{ship_name}"
    session.cookies.set(cookie_name, SESSION_COOKIE)
    return session

def test_authentication(session: requests.Session) -> bool:
    """Test if authentication works"""
    print("🔐 Testing authentication...")
    try:
        response = session.get(f"{SHIP_URL}/~/login", timeout=10)
        if response.status_code == 200:
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False

def extract_group_from_url(url: str) -> str:
    """
    Convert a group URL to API path format
    Example: http://100.90.185.114:8080/apps/groups/groups/~halbex-palheb/uf-public/channels
    Returns: /ship/~halbex-palheb/uf-public
    """
    # Parse the URL path
    path_parts = url.split('/')
    
    # Find the groups section
    if 'groups' in path_parts:
        groups_index = path_parts.index('groups')
        if len(path_parts) > groups_index + 3:  # groups/groups/~ship/group-name
            ship_name = path_parts[groups_index + 2]  # ~halbex-palheb
            group_name = path_parts[groups_index + 3]  # uf-public
            return f"/ship/{ship_name}/{group_name}"
    
    return None

def discover_groups_via_api(session: requests.Session) -> Set[str]:
    """Discover groups using various Urbit API endpoints"""
    print("🔍 Discovering groups via API endpoints...")
    groups = set()
    
    # List of API endpoints to try
    endpoints = [
        "/~/scry/gx/groups/groups.json",
        "/~/scry/gx/graph-store/keys.json", 
        "/~/scry/gx/graph-store/graphs.json",
        "/~/scry/gx/metadata-store/associations.json",
        "/~/scry/gx/metadata-store/resources.json",
        "/~/scry/gx/contact-store/contacts.json"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{SHIP_URL}{endpoint}"
            print(f"   Trying: {endpoint}")
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Success: {endpoint}")
                try:
                    data = response.json()
                    # Convert to string and search for group patterns
                    data_str = json.dumps(data)
                    
                    # Look for /ship/~shipname/groupname patterns
                    group_matches = re.findall(r'/ship/~[\w-]+/[\w-]+', data_str)
                    for match in group_matches:
                        groups.add(match)
                        print(f"      📁 Found: {match}")
                        
                    # Also look for resource patterns
                    resource_matches = re.findall(r'"resource":\s*"([^"]*)"', data_str)
                    for match in resource_matches:
                        if match.startswith('/ship/'):
                            groups.add(match)
                            print(f"      📁 Found resource: {match}")
                            
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON response from {endpoint}")
                    
            elif response.status_code == 404:
                print(f"   ❌ Not found: {endpoint}")
            else:
                print(f"   ⚠️  HTTP {response.status_code}: {endpoint}")
                
        except Exception as e:
            print(f"   ❌ Error with {endpoint}: {e}")
            continue
    
    return groups

def discover_groups_via_interface(session: requests.Session) -> Set[str]:
    """Discover groups by analyzing the web interface"""
    print("🌐 Discovering groups via web interface...")
    groups = set()
    
    # Pages to analyze
    pages = [
        "/apps/landscape",
        "/apps/groups", 
        "/apps/groups/groups"
    ]
    
    for page in pages:
        try:
            url = f"{SHIP_URL}{page}"
            print(f"   Analyzing: {page}")
            response = session.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                print(f"   ✅ Got page ({len(content)} chars)")
                
                # Look for group patterns in the content
                patterns = [
                    r'/ship/~[\w-]+/[\w-]+',
                    r'"resource":\s*"/ship/~[\w-]+/[\w-]+"',
                    r'groups/~[\w-]+/[\w-]+',
                    r'/groups/groups/~[\w-]+/[\w-]+'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        # Clean up the match
                        clean_match = match.strip('"').strip("'")
                        
                        # Convert groups/~ship/group format to /ship/~ship/group
                        if clean_match.startswith('groups/~'):
                            clean_match = '/ship/' + clean_match[7:]  # Remove 'groups/'
                        elif '/groups/groups/~' in clean_match:
                            # Extract from /groups/groups/~ship/group format
                            parts = clean_match.split('/groups/groups/')
                            if len(parts) > 1:
                                ship_group = parts[1].split('/')[0:2]  # ~ship/group
                                if len(ship_group) == 2:
                                    clean_match = f'/ship/{ship_group[0]}/{ship_group[1]}'
                        
                        if clean_match.startswith('/ship/~'):
                            groups.add(clean_match)
                            print(f"      📁 Found: {clean_match}")
                            
            else:
                print(f"   ❌ Failed to get {page}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {page}: {e}")
            continue
    
    return groups

def validate_groups(session: requests.Session, groups: Set[str]) -> List[str]:
    """Validate that discovered groups are accessible"""
    print(f"🧪 Validating {len(groups)} discovered groups...")
    valid_groups = []
    
    for group in groups:
        print(f"   Testing: {group}")
        
        # Try to access group data
        test_endpoints = [
            f"/~/scry/gx/graph-store/graph{group}/newest/1/noun",
            f"/~/scry/gx/groups/group{group}.json",
            f"/~/scry/gx/metadata-store/resource{group}.json"
        ]
        
        group_valid = False
        for endpoint in test_endpoints:
            try:
                url = f"{SHIP_URL}{endpoint}"
                response = session.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ Valid (via {endpoint.split('/')[-2]}): {group}")
                    group_valid = True
                    break
                elif response.status_code == 403:
                    print(f"   🔒 Access denied (still valid): {group}")
                    group_valid = True
                    break
                    
            except Exception:
                continue
        
        if group_valid:
            valid_groups.append(group)
        else:
            print(f"   ❌ Cannot access: {group}")
    
    return valid_groups

def update_config_file(groups: List[str]):
    """Update config.py with discovered groups"""
    if not groups:
        print("❌ No groups to update in config")
        return False
    
    print(f"📝 Updating config.py with {len(groups)} groups...")
    
    try:
        # Read current config
        with open('/home/userland/urbit/urbit-urbit-f170eb9/urbit-ai-analytics/config.py', 'r') as f:
            content = f.read()
        
        # Format groups for Python list
        groups_str = '[\n'
        for group in groups:
            groups_str += f'    "{group}",\n'
        groups_str += ']'
        
        # Update MONITORED_GROUPS
        pattern = r'MONITORED_GROUPS = \[.*?\]'
        replacement = f'MONITORED_GROUPS = {groups_str}'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Update URBIT_SHIP_URL and URBIT_SESSION_COOKIE
        new_content = re.sub(
            r'URBIT_SHIP_URL = os\.environ\.get\("URBIT_SHIP_URL", "[^"]*"\)',
            f'URBIT_SHIP_URL = os.environ.get("URBIT_SHIP_URL", "{SHIP_URL}")',
            new_content
        )
        
        # Write updated config
        with open('/home/userland/urbit/urbit-urbit-f170eb9/urbit-ai-analytics/config.py', 'w') as f:
            f.write(new_content)
        
        print("✅ config.py updated successfully!")
        
        # Update .env file if it exists
        try:
            env_content = f"""# Urbit Configuration
URBIT_SHIP_URL={SHIP_URL}
URBIT_SESSION_COOKIE={SESSION_COOKIE}

# Add your Llama API key here
LLAMA_API_KEY=your_api_key_here

# Ship to send reports to (your ship name)
URBIT_RECIPIENT_SHIP={get_ship_name_from_cookie()}
"""
            with open('/home/userland/urbit/urbit-urbit-f170eb9/urbit-ai-analytics/.env', 'w') as f:
                f.write(env_content)
            print("✅ .env file created/updated!")
            
        except Exception as e:
            print(f"⚠️  Could not update .env file: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

def add_known_group():
    """Add the known group from the example URL"""
    known_group = "/ship/~halbex-palheb/uf-public"
    print(f"➕ Adding known group from example URL: {known_group}")
    return [known_group]

def main():
    print("🚀 Updated Urbit Group Discovery")
    print("=" * 50)
    print(f"Ship URL: {SHIP_URL}")
    print(f"Cookie: {SESSION_COOKIE[:20]}...")
    print()
    
    # Setup session
    session = setup_session()
    
    # Test authentication
    if not test_authentication(session):
        print("❌ Cannot proceed without valid authentication")
        return
    
    # Start with known group
    all_groups = set(add_known_group())
    
    # Discover via API
    api_groups = discover_groups_via_api(session)
    all_groups.update(api_groups)
    
    # Discover via interface
    interface_groups = discover_groups_via_interface(session)
    all_groups.update(interface_groups)
    
    print(f"\n📊 Discovery Summary:")
    print(f"Total unique groups found: {len(all_groups)}")
    
    if all_groups:
        # Validate groups
        valid_groups = validate_groups(session, all_groups)
        
        print(f"\n📋 Valid Groups ({len(valid_groups)}):")
        for i, group in enumerate(valid_groups, 1):
            print(f"{i:2d}. {group}")
        
        # Update configuration
        if update_config_file(valid_groups):
            print(f"\n🎉 Setup Complete!")
            print(f"✅ {len(valid_groups)} groups configured for monitoring")
            print(f"✅ Configuration files updated")
            print(f"\n🚀 Next steps:")
            print(f"   python3 main.py test    # Test the configuration")
            print(f"   python3 main.py         # Start monitoring")
        else:
            print(f"\n❌ Failed to update configuration")
    else:
        print(f"\n⚠️  No groups discovered")
        print(f"Check ship accessibility and authentication")

if __name__ == "__main__":
    main()