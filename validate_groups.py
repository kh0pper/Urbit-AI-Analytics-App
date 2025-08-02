#!/usr/bin/env python3
"""
Validate discovered groups to ensure they are actually accessible and active
"""
import requests
import json
import time
from typing import List, Dict, Tuple

# Configuration
SHIP_URL = "http://100.90.185.114:8080"
SESSION_COOKIE = "0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4"
SHIP_NAME = "~halbex-palheb"

def setup_session() -> requests.Session:
    """Setup authenticated session"""
    session = requests.Session()
    cookie_name = f"urbauth-{SHIP_NAME}"
    session.cookies.set(cookie_name, SESSION_COOKIE)
    return session

def validate_group_access(session: requests.Session, group_path: str) -> Dict:
    """
    Validate if a group is accessible and get information about it
    Returns dict with status, accessibility, and any discovered info
    """
    result = {
        'group': group_path,
        'accessible': False,
        'exists': False,
        'has_content': False,
        'error': None,
        'status_codes': [],
        'info': {}
    }
    
    # Try different endpoints to validate the group
    test_endpoints = [
        # Graph store endpoints
        f"/~/scry/gx/graph-store/graph{group_path}/newest/10/noun",
        f"/~/scry/gx/graph-store/graph{group_path}/keys.json", 
        f"/~/scry/gx/graph-store/graph{group_path}.json",
        
        # Group store endpoints  
        f"/~/scry/gx/groups/group{group_path}.json",
        f"/~/scry/gx/groups{group_path}.json",
        
        # Metadata endpoints
        f"/~/scry/gx/metadata-store/resource{group_path}.json",
        f"/~/scry/gx/metadata-store/association{group_path}.json",
        
        # Direct web access
        f"/apps/groups/groups{group_path}",
    ]
    
    for endpoint in test_endpoints:
        try:
            url = f"{SHIP_URL}{endpoint}"
            response = session.get(url, timeout=5)
            result['status_codes'].append((endpoint, response.status_code))
            
            if response.status_code == 200:
                result['accessible'] = True
                result['exists'] = True
                
                # Try to parse content
                try:
                    if 'json' in endpoint:
                        data = response.json()
                        result['has_content'] = bool(data)
                        result['info']['json_data'] = str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                    else:
                        content = response.text
                        result['has_content'] = len(content) > 100  # Arbitrary threshold
                        result['info']['content_length'] = len(content)
                        
                except Exception as e:
                    result['info']['parse_error'] = str(e)
                    
            elif response.status_code == 403:
                result['exists'] = True  # Exists but no permission
                result['accessible'] = False
                
            elif response.status_code == 404:
                continue  # Try next endpoint
                
        except Exception as e:
            result['error'] = str(e)
            continue
    
    # If we got any non-404 responses, the group likely exists
    non_404_codes = [code for endpoint, code in result['status_codes'] if code != 404]
    if non_404_codes:
        result['exists'] = True
    
    return result

def get_groups_from_config() -> List[str]:
    """Read groups from the current config"""
    try:
        with open('/home/userland/urbit/urbit-urbit-f170eb9/urbit-ai-analytics/config.py', 'r') as f:
            content = f.read()
        
        # Extract MONITORED_GROUPS list
        import re
        pattern = r'MONITORED_GROUPS = \[(.*?)\]'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            groups_text = match.group(1)
            groups = re.findall(r'"([^"]+)"', groups_text)
            return groups
        
        return []
        
    except Exception as e:
        print(f"Error reading config: {e}")
        return []

def main():
    print("🧪 Validating Urbit Groups")
    print("=" * 40)
    
    session = setup_session()
    groups = get_groups_from_config()
    
    if not groups:
        print("❌ No groups found in config")
        return
    
    print(f"🔍 Validating {len(groups)} groups...")
    print()
    
    valid_groups = []
    invalid_groups = []
    
    for i, group in enumerate(groups, 1):
        print(f"[{i:2d}/{len(groups)}] Testing: {group}")
        result = validate_group_access(session, group)
        
        if result['accessible']:
            print(f"   ✅ ACCESSIBLE - Can read content")
            valid_groups.append(group)
        elif result['exists']:
            print(f"   🔒 EXISTS - No access permissions")
            valid_groups.append(group)  # Still include for monitoring attempts
        else:
            print(f"   ❌ NOT FOUND - No evidence of existence")
            invalid_groups.append(group)
        
        # Show additional info
        if result['has_content']:
            print(f"   📄 Has content")
        if result['info']:
            for key, value in result['info'].items():
                if key != 'json_data':  # Don't spam with long data
                    print(f"   ℹ️  {key}: {value}")
        
        # Show status codes for debugging
        status_summary = {}
        for endpoint, code in result['status_codes']:
            status_summary[code] = status_summary.get(code, 0) + 1
        
        if status_summary:
            status_str = ", ".join([f"{code}({count})" for code, count in status_summary.items()])
            print(f"   📊 Status codes: {status_str}")
        
        print()
        time.sleep(0.5)  # Be nice to the server
    
    # Summary
    print("📊 Validation Summary")
    print("=" * 30)
    print(f"✅ Valid groups: {len(valid_groups)}")
    print(f"❌ Invalid groups: {len(invalid_groups)}")
    
    if valid_groups:
        print(f"\n📋 Valid Groups:")
        for group in valid_groups:
            print(f"   {group}")
    
    if invalid_groups:
        print(f"\n🗑️  Invalid Groups (consider removing):")
        for group in invalid_groups:
            print(f"   {group}")
        
        # Offer to update config
        if invalid_groups:
            print(f"\n🔧 Update config to remove invalid groups? (y/n)")
            choice = input().strip().lower()
            if choice == 'y':
                update_config_with_valid_groups(valid_groups)

def update_config_with_valid_groups(valid_groups: List[str]):
    """Update config.py to only include valid groups"""
    try:
        with open('/home/userland/urbit/urbit-urbit-f170eb9/urbit-ai-analytics/config.py', 'r') as f:
            content = f.read()
        
        # Format groups for Python list
        groups_str = '[\n'
        for group in valid_groups:
            groups_str += f'    "{group}",\n'
        groups_str += ']'
        
        # Replace MONITORED_GROUPS
        import re
        pattern = r'MONITORED_GROUPS = \[.*?\]'
        replacement = f'MONITORED_GROUPS = {groups_str}'
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open('/home/userland/urbit/urbit-urbit-f170eb9/urbit-ai-analytics/config.py', 'w') as f:
            f.write(new_content)
        
        print(f"✅ Config updated with {len(valid_groups)} valid groups")
        
    except Exception as e:
        print(f"❌ Error updating config: {e}")

if __name__ == "__main__":
    main()