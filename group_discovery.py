#!/usr/bin/env python3
"""
Comprehensive Urbit Group and Channel Discovery System
Automatically discovers all groups, channels, and joins new ones
"""
import json
import requests
import time
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
from urbit_client import UrbitClient
import config

logger = logging.getLogger(__name__)

class GroupDiscovery:
    def __init__(self):
        self.client = UrbitClient(config.URBIT_SHIP_URL, config.URBIT_SESSION_COOKIE)
        self.session = requests.Session()
        self.session.cookies.set(f'urbauth-{self.client.ship_name}', config.URBIT_SESSION_COOKIE)
        self.discovered_groups = set()
        self.discovered_channels = {}
        
    def discover_all_groups(self) -> List[Dict]:
        """Discover all groups the user is a member of using multiple methods"""
        groups = []
        
        # Method 1: Try groups app API
        groups.extend(self._discover_via_groups_app())
        
        # Method 2: Try graph-store API
        groups.extend(self._discover_via_graph_store())
        
        # Method 3: Try chat API
        groups.extend(self._discover_via_chat())
        
        # Method 4: Scrape from web interface
        groups.extend(self._discover_via_web_scraping())
        
        # Deduplicate
        unique_groups = {}
        for group in groups:
            key = group.get('path', group.get('name', str(group)))
            unique_groups[key] = group
            
        logger.info(f"Discovered {len(unique_groups)} unique groups")
        return list(unique_groups.values())
    
    def _discover_via_groups_app(self) -> List[Dict]:
        """Try to discover groups via the groups app"""
        groups = []
        endpoints_to_try = [
            '/~/scry/j/groups/all.json',
            '/~/scry/j/our/groups/all.json', 
            '/~/scry/groups/all',
            '/apps/groups/api/groups',
            '/api/groups/all'
        ]
        
        for endpoint in endpoints_to_try:
            try:
                url = f"{config.URBIT_SHIP_URL}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Groups endpoint {endpoint} returned data")
                    
                    # Parse different response formats
                    if isinstance(data, dict):
                        if 'groups' in data:
                            groups.extend(self._parse_groups_data(data['groups']))
                        elif 'scry' in data:
                            groups.extend(self._parse_groups_data(data['scry']))
                        else:
                            groups.extend(self._parse_groups_data(data))
                    elif isinstance(data, list):
                        groups.extend(self._parse_groups_data(data))
                        
                    break  # Success, stop trying other endpoints
                    
            except Exception as e:
                logger.debug(f"Groups endpoint {endpoint} failed: {e}")
                continue
        
        return groups
    
    def _discover_via_graph_store(self) -> List[Dict]:
        """Try to discover groups via graph-store"""
        groups = []
        endpoints_to_try = [
            '/~/scry/j/graph-store/keys.json',
            '/~/scry/j/our/graph-store/keys.json',
            '/~/scry/graph-store/graph-update.json'
        ]
        
        for endpoint in endpoints_to_try:
            try:
                url = f"{config.URBIT_SHIP_URL}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Graph-store endpoint {endpoint} returned data")
                    
                    # Extract group information from graph-store keys
                    if isinstance(data, dict) and 'graph-update' in data:
                        for key, value in data['graph-update'].items():
                            if 'resource' in value:
                                resource = value['resource']
                                groups.append({
                                    'path': f"/ship/{resource.get('ship', '')}/{resource.get('name', '')}",
                                    'name': resource.get('name', ''),
                                    'host_ship': resource.get('ship', ''),
                                    'type': 'graph-store'
                                })
                    break
                    
            except Exception as e:
                logger.debug(f"Graph-store endpoint {endpoint} failed: {e}")
                continue
                
        return groups
    
    def _discover_via_chat(self) -> List[Dict]:
        """Try to discover groups via chat systems"""
        groups = []
        endpoints_to_try = [
            '/~/scry/j/chat-store/all.json',
            '/~/scry/j/our/chat/all.json',
            '/~/scry/chat/inbox.json'
        ]
        
        for endpoint in endpoints_to_try:
            try:
                url = f"{config.URBIT_SHIP_URL}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"Chat endpoint {endpoint} returned data")
                    
                    # Parse chat data for group information
                    if isinstance(data, dict):
                        for key, chat_data in data.items():
                            if isinstance(chat_data, dict) and 'path' in chat_data:
                                groups.append({
                                    'path': chat_data['path'],
                                    'name': key,
                                    'type': 'chat'
                                })
                    break
                    
            except Exception as e:
                logger.debug(f"Chat endpoint {endpoint} failed: {e}")
                continue
                
        return groups
    
    def _discover_via_web_scraping(self) -> List[Dict]:
        """Discover groups by parsing the web interface and channel content"""
        groups = []
        
        try:
            # Method 1: Get the main groups page
            url = f"{config.URBIT_SHIP_URL}/apps/groups"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                groups.extend(self._parse_content_for_groups(content, 'main-page'))
                        
            # Method 2: Parse known directory/announcement channels for group links
            directory_channels = [
                "~nibset-napwyn/tlon/channels/heap/~nibset-napwyn/local-directory",
                "~halbex-palheb/uf-public/announcements", 
                "~bitbet-bolbel/urbit-community",
                "~darrux-landes/the-forge"
            ]
            
            for channel_path in directory_channels:
                channel_groups = self._discover_from_channel_content(channel_path)
                groups.extend(channel_groups)
                        
            logger.info(f"Web scraping found {len(groups)} groups")
                
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            
        return groups
    
    def _parse_content_for_groups(self, content: str, source: str) -> List[Dict]:
        """Parse HTML/text content for group references"""
        groups = []
        import re
        
        # Pattern 1: Look for /ship/~ship/group-name patterns
        ship_patterns = re.findall(r'/ship/(~[\w-]+)/([\w-]+)', content)
        for ship, group_name in ship_patterns:
            groups.append({
                'path': f'/ship/{ship}/{group_name}',
                'name': group_name,
                'host_ship': ship,
                'type': f'web-scraped-{source}'
            })
        
        # Pattern 2: Look for ~ship/group patterns (without /ship/ prefix)
        simple_patterns = re.findall(r'(~[\w-]+)/([\w-]+)', content)
        for ship, group_name in simple_patterns:
            # Avoid duplicates and filter out non-group patterns
            if not any(g['path'] == f'/ship/{ship}/{group_name}' for g in groups):
                # Basic validation - ship names should start with ~ and be reasonable length
                if ship.startswith('~') and len(ship) > 3 and len(group_name) > 0:
                    groups.append({
                        'path': f'/ship/{ship}/{group_name}',
                        'name': group_name,
                        'host_ship': ship,
                        'type': f'pattern-{source}'
                    })
        
        # Pattern 3: Look for group metadata in JSON
        json_patterns = re.findall(r'\{[^}]*"resource"[^}]*\}', content)
        for json_str in json_patterns:
            try:
                data = json.loads(json_str)
                if 'resource' in data:
                    resource = data['resource']
                    if resource.get('ship') and resource.get('name'):
                        groups.append({
                            'path': f"/ship/{resource.get('ship', '')}/{resource.get('name', '')}",
                            'name': resource.get('name', ''),
                            'host_ship': resource.get('ship', ''),
                            'type': f'json-{source}'
                        })
            except:
                continue
        
        # Pattern 4: Look for URLs with group references
        url_patterns = re.findall(r'groups/(~[\w-]+)/([\w-]+)', content)
        for ship, group_name in url_patterns:
            if not any(g['path'] == f'/ship/{ship}/{group_name}' for g in groups):
                groups.append({
                    'path': f'/ship/{ship}/{group_name}',
                    'name': group_name,
                    'host_ship': ship,
                    'type': f'url-{source}'
                })
        
        return groups
    
    def _discover_from_channel_content(self, channel_path: str) -> List[Dict]:
        """Discover groups by parsing specific channel content for posted group links"""
        groups = []
        
        try:
            # Build URL for the channel
            url = f"{config.URBIT_SHIP_URL}/apps/groups/groups/{channel_path}"
            logger.info(f"Scanning channel for group links: {channel_path}")
            
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Parse content for group references
                channel_groups = self._parse_content_for_groups(content, f'channel-{channel_path.split("/")[-1]}')
                
                # Additional patterns specific to message/heap content
                import re
                
                # Look for text that mentions groups/communities
                community_patterns = re.findall(r'(community|group|chat|public|general|main)[:\s]*(~[\w-]+)/([\w-]+)', content, re.IGNORECASE)
                for _, ship, group_name in community_patterns:
                    if not any(g['path'] == f'/ship/{ship}/{group_name}' for g in channel_groups):
                        channel_groups.append({
                            'path': f'/ship/{ship}/{group_name}',
                            'name': group_name,
                            'host_ship': ship,
                            'type': 'community-mention'
                        })
                
                # Look for Urbit-style mentions in text content
                mention_patterns = re.findall(r'join\s+(~[\w-]+)/([\w-]+)', content, re.IGNORECASE)
                for ship, group_name in mention_patterns:
                    if not any(g['path'] == f'/ship/{ship}/{group_name}' for g in channel_groups):
                        channel_groups.append({
                            'path': f'/ship/{ship}/{group_name}',
                            'name': group_name,
                            'host_ship': ship,
                            'type': 'join-mention'
                        })
                
                groups.extend(channel_groups)
                logger.info(f"Found {len(channel_groups)} groups in channel {channel_path}")
                
            else:
                logger.debug(f"Could not access channel {channel_path}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error parsing channel {channel_path}: {e}")
            
        return groups
    
    def _parse_groups_data(self, data) -> List[Dict]:
        """Parse different formats of group data"""
        groups = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    group = {
                        'path': key,
                        'name': value.get('name', key.split('/')[-1] if '/' in key else key),
                        'type': 'parsed'
                    }
                    if 'ship' in value:
                        group['host_ship'] = value['ship']
                    groups.append(group)
                else:
                    groups.append({
                        'path': key,
                        'name': key.split('/')[-1] if '/' in key else key,
                        'type': 'simple'
                    })
                    
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    groups.append({
                        'path': item,
                        'name': item.split('/')[-1] if '/' in item else item,
                        'type': 'list-item'
                    })
                elif isinstance(item, dict):
                    groups.append(item)
                    
        return groups
    
    def discover_channels_in_group(self, group_path: str) -> List[Dict]:
        """Discover all channels within a specific group"""
        channels = []
        
        # Extract ship and group name from path
        parts = group_path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'ship':
            ship = parts[1]
            group_name = parts[2]
            
            # Try different methods to get channels
            channels.extend(self._get_channels_via_api(ship, group_name))
            channels.extend(self._get_channels_via_web(ship, group_name))
            
        logger.info(f"Discovered {len(channels)} channels in {group_path}")
        return channels
    
    def _get_channels_via_api(self, ship: str, group_name: str) -> List[Dict]:
        """Get channels via API endpoints"""
        channels = []
        endpoints_to_try = [
            f"/~/scry/j/groups/group{ship}/{group_name}/channels.json",
            f"/~/scry/j/our/groups/{ship}/{group_name}.json",
            f"/~/scry/groups/{ship}/{group_name}/channels"
        ]
        
        for endpoint in endpoints_to_try:
            try:
                url = f"{config.URBIT_SHIP_URL}{endpoint}"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse channel data
                    if isinstance(data, dict):
                        if 'channels' in data:
                            for channel_id, channel_data in data['channels'].items():
                                channels.append({
                                    'path': f"/ship/{ship}/{group_name}/{channel_id}",
                                    'name': channel_data.get('title', channel_id),
                                    'type': channel_data.get('type', 'unknown'),
                                    'group_path': f"/ship/{ship}/{group_name}"
                                })
                    break
                    
            except Exception as e:
                logger.debug(f"Channel API endpoint {endpoint} failed: {e}")
                continue
                
        return channels
    
    def _get_channels_via_web(self, ship: str, group_name: str) -> List[Dict]:
        """Get channels by parsing the group's web page"""
        channels = []
        
        try:
            url = f"{config.URBIT_SHIP_URL}/apps/groups/groups/{ship}/{group_name}/channels"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                content = response.text
                
                # Look for channel patterns
                import re
                channel_patterns = re.findall(r'/channels/([\w-]+)', content)
                
                for channel_id in set(channel_patterns):  # Remove duplicates
                    channels.append({
                        'path': f"/ship/{ship}/{group_name}/{channel_id}",
                        'name': channel_id,
                        'type': 'web-discovered',
                        'group_path': f"/ship/{ship}/{group_name}"
                    })
                    
                logger.info(f"Web discovery found {len(channels)} channels in {ship}/{group_name}")
                
        except Exception as e:
            logger.error(f"Web channel discovery failed for {ship}/{group_name}: {e}")
            
        return channels
    
    def attempt_join_group(self, group_path: str) -> bool:
        """Attempt to join a discovered group"""
        try:
            # Extract ship and group name
            parts = group_path.strip('/').split('/')
            if len(parts) < 3 or parts[0] != 'ship':
                return False
                
            ship = parts[1]
            group_name = parts[2]
            
            # Try to join via groups app
            join_data = {
                "action": "join",
                "resource": {
                    "ship": ship,
                    "name": group_name
                },
                "app": "groups"
            }
            
            # Create channel for the join request
            channel_id = f"join-{int(time.time())}"
            channel_url = f"{config.URBIT_SHIP_URL}/~/channel/{channel_id}"
            
            poke_data = {
                "id": 1,
                "action": "poke",
                "ship": "our",
                "app": "group-store", 
                "mark": "group-action",
                "json": join_data
            }
            
            response = self.session.put(channel_url, json=[poke_data], timeout=10)
            
            if response.status_code == 204:
                logger.info(f"Successfully joined group: {group_path}")
                return True
            else:
                logger.warning(f"Failed to join group {group_path}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error joining group {group_path}: {e}")
            return False
    
    def get_all_monitorable_targets(self) -> List[str]:
        """Get all groups and channels that should be monitored"""
        targets = []
        
        # Discover all groups
        groups = self.discover_all_groups()
        
        for group in groups:
            group_path = group.get('path', '')
            if group_path:
                # Add the group itself
                targets.append(group_path)
                
                # Discover and add all channels in the group
                channels = self.discover_channels_in_group(group_path)
                for channel in channels:
                    channel_path = channel.get('path', '')
                    if channel_path:
                        targets.append(channel_path)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_targets = []
        for target in targets:
            if target not in seen:
                seen.add(target)
                unique_targets.append(target)
                
        logger.info(f"Found {len(unique_targets)} total monitoring targets")
        return unique_targets
    
    def save_discovery_results(self, filename: str = "discovered_groups.json"):
        """Save discovery results to file"""
        groups = self.discover_all_groups()
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "groups": groups,
            "channels": {}
        }
        
        # Get channels for each group
        for group in groups:
            group_path = group.get('path', '')
            if group_path:
                channels = self.discover_channels_in_group(group_path)
                results["channels"][group_path] = channels
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Discovery results saved to {filename}")
        return filename

def main():
    """Test the group discovery system"""
    print("🔍 Urbit Group Discovery System")
    print("=" * 50)
    
    discovery = GroupDiscovery()
    
    print("1️⃣ Discovering all groups...")
    groups = discovery.discover_all_groups()
    
    print(f"\n📊 Found {len(groups)} groups:")
    for i, group in enumerate(groups, 1):
        print(f"   {i}. {group.get('path', 'Unknown')} ({group.get('type', 'unknown')})")
    
    print(f"\n2️⃣ Discovering channels in groups...")
    all_targets = discovery.get_all_monitorable_targets()
    
    print(f"\n📊 Total monitoring targets: {len(all_targets)}")
    for i, target in enumerate(all_targets[:10], 1):  # Show first 10
        print(f"   {i}. {target}")
    
    if len(all_targets) > 10:
        print(f"   ... and {len(all_targets) - 10} more")
    
    print(f"\n3️⃣ Saving results...")
    filename = discovery.save_discovery_results()
    print(f"   ✅ Results saved to: {filename}")
    
    print(f"\n🚀 Discovery complete!")
    return all_targets

if __name__ == "__main__":
    main()