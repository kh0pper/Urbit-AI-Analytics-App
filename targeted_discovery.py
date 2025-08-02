#!/usr/bin/env python3
"""
Targeted discovery for the specific uf-public group and its channels
"""
import requests
import json
import re
from bs4 import BeautifulSoup
import config

def discover_uf_public_channels():
    """Discover channels in the uf-public group from ~halbex-palheb"""
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', config.URBIT_SESSION_COOKIE)
    
    print("🔍 Discovering channels in /ship/~halbex-palheb/uf-public")
    print("=" * 60)
    
    # Method 1: Direct web scraping of the channels page
    print("1️⃣ Method 1: Web scraping channels page...")
    try:
        url = f"{config.URBIT_SHIP_URL}/apps/groups/groups/~halbex-palheb/uf-public/channels"
        response = session.get(url, timeout=15)
        
        print(f"   Status: {response.status_code}")
        print(f"   Content length: {len(response.text)} chars")
        
        if response.status_code == 200:
            content = response.text
            
            # Look for channel links or patterns
            channel_patterns = [
                r'/channels/([\w-]+)',
                r'channel-(\w+)',
                r'"(\w+)"\s*:\s*{[^}]*"type"\s*:\s*"channel"',
                r'href="[^"]*/([\w-]+)/channels"',
            ]
            
            channels_found = set()
            
            for pattern in channel_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                channels_found.update(matches)
            
            print(f"   Found potential channels: {list(channels_found)}")
            
            # Also try parsing with BeautifulSoup for better HTML parsing
            try:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Look for links containing 'channel' or common channel names
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if 'channel' in href.lower():
                        print(f"   Channel link found: {href}")
                        
            except Exception as e:
                print(f"   BeautifulSoup parsing failed: {e}")
                
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 2: Try to access common channel names directly
    print(f"\n2️⃣ Method 2: Testing common channel names...")
    common_channels = [
        'general', 'chat', 'random', 'announcements', 'discussion',
        'dev', 'help', 'lobby', 'main', 'public', 'testing',
        'default', 'welcome', 'intro', 'links', 'resources'
    ]
    
    working_channels = []
    
    for channel in common_channels:
        try:
            # Try to access the channel directly
            channel_url = f"{config.URBIT_SHIP_URL}/apps/groups/groups/~halbex-palheb/uf-public/channels/{channel}"
            response = session.get(channel_url, timeout=5)
            
            print(f"   {channel}: {response.status_code}")
            
            if response.status_code == 200:
                working_channels.append(channel)
                print(f"     ✅ {channel} - ACCESSIBLE")
            
        except Exception as e:
            print(f"   {channel}: Error - {e}")
    
    # Method 3: Try API endpoints for the specific group
    print(f"\n3️⃣ Method 3: API endpoints...")
    api_endpoints = [
        f"/~/scry/j/groups/~halbex-palheb/uf-public.json",
        f"/~/scry/j/our/groups/~halbex-palheb/uf-public.json",
        f"/~/scry/groups/~halbex-palheb/uf-public/channels.json",
        f"/api/groups/~halbex-palheb/uf-public/channels"
    ]
    
    for endpoint in api_endpoints:
        try:
            url = f"{config.URBIT_SHIP_URL}{endpoint}"
            response = session.get(url, timeout=10)
            
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"     📄 JSON data: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"     📄 Text data: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    # Method 4: Graph-store queries for this specific group
    print(f"\n4️⃣ Method 4: Graph-store queries...")
    graph_endpoints = [
        f"/~/scry/j/graph-store/graph/~halbex-palheb/uf-public.json",
        f"/~/scry/j/graph-store/keys.json"
    ]
    
    for endpoint in graph_endpoints:
        try:
            url = f"{config.URBIT_SHIP_URL}{endpoint}"
            response = session.get(url, timeout=10)
            
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"     📄 Data keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                except:
                    print(f"     📄 Raw response: {response.text[:200]}...")
                    
        except Exception as e:
            print(f"   {endpoint}: Error - {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Working channels found: {working_channels}")
    
    # Create monitoring targets
    targets = ["/ship/~halbex-palheb/uf-public"]  # Base group
    
    for channel in working_channels:
        targets.append(f"/ship/~halbex-palheb/uf-public/{channel}")
    
    print(f"   Recommended monitoring targets: {targets}")
    
    return targets

def test_activity_retrieval(targets):
    """Test getting activity from discovered targets"""
    print(f"\n🧪 Testing activity retrieval...")
    
    from urbit_client import UrbitClient
    client = UrbitClient(config.URBIT_SHIP_URL, config.URBIT_SESSION_COOKIE)
    
    for target in targets:
        print(f"\n   Testing: {target}")
        try:
            activities = client.get_group_activity(target, 24)
            print(f"     ✅ Got {len(activities)} activities")
            
            if activities:
                sample = activities[0]
                print(f"     📄 Sample: {json.dumps(sample, indent=2)[:150]}...")
        except Exception as e:
            print(f"     ❌ Error: {e}")

if __name__ == "__main__":
    targets = discover_uf_public_channels()
    test_activity_retrieval(targets)