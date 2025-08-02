#!/usr/bin/env python3
"""
Comprehensive Urbit group discovery using multiple methods and authentication approaches
"""
import requests
import json
import re
import time
import uuid
from typing import List, Dict, Set
from urllib.parse import urljoin, urlparse

# User's configuration
SHIP_URL = "http://100.90.185.114:8080"
SESSION_COOKIE = "0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4"

def try_different_ship_names() -> List[str]:
    """Try to determine possible ship names from various sources"""
    possible_ships = [
        "~halbex-palheb",  # From the example URL
    ]
    
    # Try to extract from cookie or other sources
    return possible_ships

def setup_session_with_ship(ship_name: str) -> requests.Session:
    """Setup session with specific ship name"""
    session = requests.Session()
    cookie_name = f"urbauth-{ship_name}"
    session.cookies.set(cookie_name, SESSION_COOKIE)
    
    # Also try without the ~ prefix in case it's needed
    if ship_name.startswith('~'):
        alt_cookie_name = f"urbauth-{ship_name[1:]}"
        session.cookies.set(alt_cookie_name, SESSION_COOKIE)
    
    return session

def discover_via_channel_subscription(session: requests.Session) -> Set[str]:
    """Try to discover groups via channel subscriptions"""
    print("🔗 Trying channel subscription method...")
    groups = set()
    
    try:
        # Create a channel
        timestamp = int(time.time())
        channel_id = f"{timestamp}-{str(uuid.uuid4())[:8]}"
        channel_url = f"{SHIP_URL}/~/channel/{channel_id}"
        
        # Subscribe to various apps that might contain group info
        subscriptions = [
            {"app": "groups", "path": "/all"},
            {"app": "graph-store", "path": "/updates"},
            {"app": "metadata-store", "path": "/updates"},
            {"app": "contact-store", "path": "/all"},
        ]
        
        for i, sub in enumerate(subscriptions):
            action = {
                "id": i,
                "action": "subscribe", 
                "ship": "our",
                "app": sub["app"],
                "path": sub["path"]
            }
            
            print(f"   Subscribing to {sub['app']}{sub['path']}")
            response = session.put(channel_url, json=[action], timeout=10)
            
            if response.status_code == 204:
                print(f"   ✅ Subscribed to {sub['app']}")
                
                # Try to read initial state
                try:
                    sse_response = session.get(channel_url, timeout=3, stream=True)
                    if sse_response.status_code == 200:
                        for line in sse_response.iter_lines(decode_unicode=True):
                            if line and line.startswith('data:'):
                                try:
                                    data = json.loads(line[5:])
                                    data_str = json.dumps(data)
                                    matches = re.findall(r'/ship/~[\w-]+/[\w-]+', data_str)
                                    for match in matches:
                                        groups.add(match)
                                        print(f"      📁 Found: {match}")
                                except:
                                    continue
                            # Don't wait too long
                            break  
                except:
                    pass
            else:
                print(f"   ❌ Failed to subscribe to {sub['app']}: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Channel subscription failed: {e}")
    
    return groups

def discover_via_poke_scry(session: requests.Session) -> Set[str]:
    """Try alternative scry paths with different authentication"""
    print("🔍 Trying alternative scry methods...")
    groups = set()
    
    # Alternative scry patterns to try
    scry_patterns = [
        "/~/scry/gx/groups.json",
        "/~/scry/groups.json", 
        "/~/scry/gx/groups/groups",
        "/~/scry/gx/graph-store/keys",
        "/~/scry/gx/graph-store/graphs",
        "/~/scry/g/groups/groups.json",
        "/~/scry/g/graph-store/keys.json",
        # Try without the gx prefix
        "/~/scry/groups/groups.json",
        "/~/scry/graph-store/keys.json",
    ]
    
    for pattern in scry_patterns:
        try:
            url = f"{SHIP_URL}{pattern}"
            print(f"   Trying: {pattern}")
            response = session.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ Success: {pattern}")
                try:
                    data = response.json()
                    data_str = json.dumps(data)
                    matches = re.findall(r'/ship/~[\w-]+/[\w-]+', data_str)
                    for match in matches:
                        groups.add(match)
                        print(f"      📁 Found: {match}")
                except:
                    # Try text parsing too
                    text = response.text
                    matches = re.findall(r'/ship/~[\w-]+/[\w-]+', text)
                    for match in matches:
                        groups.add(match)
                        print(f"      📁 Found (text): {match}")
                        
            elif response.status_code == 404:
                print(f"   ❌ Not found: {pattern}")
            else:
                print(f"   ⚠️  HTTP {response.status_code}: {pattern}")
                
        except Exception as e:
            continue
    
    return groups

def discover_via_direct_group_access(session: requests.Session) -> Set[str]:
    """Try to discover groups by testing common group patterns"""
    print("🎯 Testing common group patterns...")
    groups = set()
    
    # Common group name patterns to test
    ship_name = "~halbex-palheb"
    common_groups = [
        "general", "random", "help", "chat", "dev", "testing", 
        "announcements", "updates", "public", "main", "lobby",
        "uf-public", "urbit-public", "community", "discussion"
    ]
    
    for group_name in common_groups:
        test_group = f"/ship/{ship_name}/{group_name}"
        print(f"   Testing: {test_group}")
        
        # Try different ways to access the group
        test_urls = [
            f"/~/scry/gx/graph-store/graph{test_group}/newest/1/noun",
            f"/~/scry/gx/groups/group{test_group}.json",
            f"/apps/groups/groups{test_group}"
        ]
        
        for test_url in test_urls:
            try:
                response = session.get(f"{SHIP_URL}{test_url}", timeout=3)
                if response.status_code in [200, 403]:  # 403 means exists but no access
                    groups.add(test_group)
                    print(f"   ✅ Found: {test_group}")
                    break
            except:
                continue
    
    return groups

def discover_via_html_parsing(session: requests.Session) -> Set[str]:
    """Enhanced HTML parsing with better patterns"""
    print("🌐 Enhanced web interface analysis...")
    groups = set()
    
    # URLs to analyze
    urls_to_check = [
        "/",
        "/apps/landscape",
        "/apps/groups",
        "/apps/groups/groups",
        "/apps/graph",
        "/apps/talk",
        "/apps/links"
    ]
    
    for url_path in urls_to_check:
        try:
            url = f"{SHIP_URL}{url_path}"
            print(f"   Analyzing: {url_path}")
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                print(f"   ✅ Got content ({len(content)} chars)")
                
                # Multiple pattern approaches
                patterns = [
                    # Direct group paths
                    r'/ship/~[\w-]+/[\w-]+',
                    # JSON embedded in HTML
                    r'"resource":\s*"/ship/~[\w-]+/[\w-]+"',
                    r'"group":\s*"/ship/~[\w-]+/[\w-]+"',
                    # URL paths in hrefs
                    r'href="[^"]*groups[^"]*~[\w-]+/[\w-]+[^"]*"',
                    # JavaScript variables
                    r'group[s]?.*?=.*?["\'/]ship/~[\w-]+/[\w-]+',
                    # Data attributes
                    r'data-[\w-]*group[s]?.*?["\'/]ship/~[\w-]+/[\w-]+',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Clean up the match
                        clean_match = re.search(r'/ship/~[\w-]+/[\w-]+', match)
                        if clean_match:
                            group_path = clean_match.group(0)
                            groups.add(group_path)
                            print(f"      📁 Found: {group_path}")
                            
            else:
                print(f"   ❌ HTTP {response.status_code}: {url_path}")
                
        except Exception as e:
            print(f"   ❌ Error with {url_path}: {e}")
            continue
    
    return groups

def comprehensive_discovery():
    """Run comprehensive discovery using all methods"""
    print("🚀 Comprehensive Urbit Group Discovery")
    print("=" * 60)
    
    all_groups = set()
    ship_names = try_different_ship_names()
    
    for ship_name in ship_names:
        print(f"\n🚢 Trying with ship: {ship_name}")
        session = setup_session_with_ship(ship_name)
        
        # Test authentication
        try:
            response = session.get(f"{SHIP_URL}/~/login", timeout=5)
            if response.status_code == 200:
                print(f"✅ Authentication successful for {ship_name}")
            else:
                print(f"⚠️  Auth status {response.status_code} for {ship_name}")
        except:
            print(f"❌ Auth failed for {ship_name}")
            continue
        
        # Try all discovery methods
        methods = [
            ("Channel Subscription", discover_via_channel_subscription),
            ("Alternative Scry", discover_via_poke_scry), 
            ("Direct Group Access", discover_via_direct_group_access),
            ("HTML Parsing", discover_via_html_parsing),
        ]
        
        for method_name, method_func in methods:
            print(f"\n--- {method_name} ---")
            try:
                groups = method_func(session)
                all_groups.update(groups)
                print(f"Found {len(groups)} groups via {method_name}")
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
    
    # Add the known group from the example
    known_group = "/ship/~halbex-palheb/uf-public"
    all_groups.add(known_group)
    print(f"\n➕ Added known group: {known_group}")
    
    return list(all_groups)

def main():
    groups = comprehensive_discovery()
    
    print(f"\n📊 Final Discovery Results:")
    print(f"Total unique groups found: {len(groups)}")
    
    if groups:
        print(f"\n📋 All Groups:")
        for i, group in enumerate(sorted(groups), 1):
            print(f"{i:2d}. {group}")
        
        # Update config
        try:
            from updated_group_discovery import update_config_file
            update_config_file(groups) 
            print(f"\n✅ Configuration updated with {len(groups)} groups!")
        except Exception as e:
            print(f"❌ Failed to update config: {e}")
    else:
        print(f"\n⚠️  No groups discovered")

if __name__ == "__main__":
    main()