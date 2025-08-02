#!/usr/bin/env python3
"""
Enhanced Group Discovery System for Urbit Analytics
Implements multiple discovery methods and automated joining
"""
import requests
import json
import re
import time
import uuid
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
import logging
import config
from urbit_client import UrbitClient

logger = logging.getLogger(__name__)

class EnhancedGroupDiscovery:
    def __init__(self):
        self.client = UrbitClient(config.URBIT_SHIP_URL, config.URBIT_SESSION_COOKIE)
        self.session = requests.Session()
        self.session.cookies.set('urbauth-~litmyl-nopmet', config.URBIT_SESSION_COOKIE)
        self.discovered_groups = set()
        
    def discover_via_web_scraping(self) -> Set[str]:
        """Scrape web interface for group references"""
        groups = set()
        
        # URLs to scrape for group mentions
        urls_to_scrape = [
            "/apps/groups",
            "/apps/landscape", 
            "/",
            "/apps/talk"
        ]
        
        for url_path in urls_to_scrape:
            try:
                url = f"{config.URBIT_SHIP_URL}{url_path}"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Multiple patterns to find groups
                    patterns = [
                        r'/ship/~[\w-]+/[\w-]+',
                        r'"resource":\s*"/ship/~[\w-]+/[\w-]+"',
                        r'groups[^"]*~[\w-]+/[\w-]+',
                        r'~[\w-]+/[\w-]+(?=/|"|\s)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            # Extract clean group path
                            clean_match = re.search(r'/ship/~[\w-]+/[\w-]+', match)
                            if clean_match:
                                groups.add(clean_match.group(0))
                            else:
                                # Try to convert ~ship/group to /ship/~ship/group
                                ship_match = re.search(r'~[\w-]+/[\w-]+', match)
                                if ship_match:
                                    groups.add(f"/ship/{ship_match.group(0)}")
                                    
            except Exception as e:
                logger.debug(f"Web scraping failed for {url_path}: {e}")
                
        return groups
    
    def discover_via_message_analysis(self) -> Set[str]:
        """Analyze message content in monitored groups for group mentions"""
        groups = set()
        
        # Analyze messages in current groups for mentions of other groups
        for group_path in config.MONITORED_GROUPS:
            try:
                activity = self.client.get_group_activity(group_path, hours_back=72)
                
                if activity:
                    for message in activity:
                        content = str(message.get('content', ''))
                        
                        # Look for direct group path mentions
                        group_patterns = re.findall(r'/ship/~[\w-]+/[\w-]+', content)
                        for pattern in group_patterns:
                            if pattern not in config.MONITORED_GROUPS:
                                groups.add(pattern)
                        
                        # Look for ship/group patterns without /ship/ prefix
                        ship_patterns = re.findall(r'~[\w-]+/[\w-]+', content)
                        for pattern in ship_patterns:
                            full_path = f'/ship/{pattern}'
                            if full_path not in config.MONITORED_GROUPS:
                                groups.add(full_path)
                        
                        # Look for community/group keywords
                        if any(keyword in content.lower() for keyword in ['join', 'group', 'community', 'channel']):
                            # Extract potential group references near these keywords
                            context_patterns = re.findall(r'(?i)(join|group|community|channel)[^.]*?~[\w-]+/[\w-]+', content)
                            for context_match in context_patterns:
                                ship_match = re.search(r'~[\w-]+/[\w-]+', context_match)
                                if ship_match:
                                    groups.add(f'/ship/{ship_match.group(0)}')
                                    
            except Exception as e:
                logger.debug(f"Message analysis failed for {group_path}: {e}")
                
        return groups
    
    def discover_via_common_patterns(self) -> Set[str]:
        """Test common group naming patterns"""
        groups = set()
        
        # Extract ships from current groups to find other groups they host
        known_ships = set()
        for group_path in config.MONITORED_GROUPS:
            if group_path.startswith('/ship/'):
                parts = group_path.split('/')
                if len(parts) >= 3:
                    known_ships.add(parts[2])
        
        # Common group names to test with known ships
        common_names = [
            'general', 'chat', 'random', 'dev', 'help', 'announcements',
            'main', 'public', 'discussion', 'links', 'intro', 'welcome',
            'testing', 'lobby', 'community', 'updates', 'news'
        ]
        
        for ship in known_ships:
            for name in common_names:
                test_group = f'/ship/{ship}/{name}'
                if test_group not in config.MONITORED_GROUPS:
                    # Quick test to see if group exists
                    if self.test_group_exists(test_group):
                        groups.add(test_group)
        
        return groups
    
    def discover_via_network_exploration(self) -> Set[str]:
        """Explore network by following connections"""
        groups = set()
        
        # Well-known community hubs to explore
        hub_groups = [
            '/ship/~bitbet-bolbel/urbit-community',
            '/ship/~darrux-landes/the-forge',
            '/ship/~halbex-palheb/uf-public',
            '/ship/~libset-rirbep/landscape',
            '/ship/~dister-dozzod-basbys/urbitfoundation'
        ]
        
        for hub in hub_groups:
            if hub not in config.MONITORED_GROUPS:
                # Test if hub is accessible
                if self.test_group_exists(hub):
                    groups.add(hub)
                    
                    # Try to find channels within the hub
                    channels = self.discover_channels_in_group(hub)
                    groups.update(channels)
        
        return groups
    
    def discover_channels_in_group(self, group_path: str) -> Set[str]:
        """Discover channels within a specific group"""
        channels = set()
        
        # Extract ship and group name
        parts = group_path.strip('/').split('/')
        if len(parts) >= 3 and parts[0] == 'ship':
            ship = parts[1]
            group_name = parts[2]
            
            # Common channel names
            channel_names = [
                'general', 'chat', 'announcements', 'dev', 'help', 'random',
                'discussion', 'links', 'intro', 'welcome', 'main', 'lobby'
            ]
            
            for channel in channel_names:
                channel_path = f'/ship/{ship}/{group_name}/{channel}'
                if self.test_group_exists(channel_path):
                    channels.add(channel_path)
        
        return channels
    
    def test_group_exists(self, group_path: str) -> bool:
        """Test if a group exists and is accessible"""
        try:
            # Try multiple endpoints to test group existence
            test_urls = [
                f"{config.URBIT_SHIP_URL}/~/scry/gx/graph-store/graph{group_path}/newest/1/noun",
                f"{config.URBIT_SHIP_URL}/~/scry/gx/groups/group{group_path}.json",
                f"{config.URBIT_SHIP_URL}/apps/groups/groups{group_path}"
            ]
            
            for url in test_urls:
                response = self.session.get(url, timeout=5)
                if response.status_code in [200, 403]:  # 200 = accessible, 403 = exists but no access
                    return True
                    
        except Exception:
            pass
            
        return False
    
    def attempt_join_group(self, group_path: str) -> bool:
        """Attempt to join a group automatically"""
        try:
            # Extract ship and group name
            parts = group_path.strip('/').split('/')
            if len(parts) < 3 or parts[0] != 'ship':
                return False
                
            ship = parts[1]
            group_name = '/'.join(parts[2:])  # Handle nested paths
            
            # Create channel for join request
            channel_id = f"join-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            channel_url = f"{config.URBIT_SHIP_URL}/~/channel/{channel_id}"
            
            # Join request data
            join_data = {
                "action": "join",
                "resource": {
                    "ship": ship,
                    "name": group_name
                }
            }
            
            poke_action = {
                "id": 1,
                "action": "poke",
                "ship": "our",
                "app": "group-store",
                "mark": "group-action", 
                "json": join_data
            }
            
            response = self.session.put(channel_url, json=[poke_action], timeout=10)
            
            if response.status_code == 204:
                logger.info(f"Successfully joined group: {group_path}")
                return True
            else:
                logger.warning(f"Failed to join group {group_path}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error joining group {group_path}: {e}")
            return False
    
    def run_comprehensive_discovery(self) -> Dict[str, Set[str]]:
        """Run all discovery methods and return results"""
        discovery_methods = {
            'web_scraping': self.discover_via_web_scraping,
            'message_analysis': self.discover_via_message_analysis,
            'common_patterns': self.discover_via_common_patterns,
            'network_exploration': self.discover_via_network_exploration
        }
        
        results = {}
        all_groups = set()
        
        for method_name, method_func in discovery_methods.items():
            try:
                groups = method_func()
                results[method_name] = groups
                all_groups.update(groups)
                logger.info(f"{method_name}: found {len(groups)} groups")
            except Exception as e:
                logger.error(f"{method_name} failed: {e}")
                results[method_name] = set()
        
        results['all_groups'] = all_groups
        return results
    
    def save_discovery_results(self, results: Dict[str, Set[str]], filename: str = "data/latest_discovery.json"):
        """Save discovery results to file"""
        # Convert sets to lists for JSON serialization
        json_results = {}
        for key, value in results.items():
            if isinstance(value, set):
                json_results[key] = list(value)
            else:
                json_results[key] = value
        
        json_results['timestamp'] = datetime.now().isoformat()
        json_results['total_discovered'] = len(results.get('all_groups', set()))
        
        with open(filename, 'w') as f:
            json.dump(json_results, f, indent=2)
        
        logger.info(f"Discovery results saved to {filename}")
        return filename

def main():
    """Test the enhanced discovery system"""
    print("🚀 Enhanced Urbit Group Discovery System")
    print("=" * 50)
    
    discovery = EnhancedGroupDiscovery()
    
    print("Running comprehensive discovery...")
    results = discovery.run_comprehensive_discovery()
    
    print(f"\n📊 Discovery Results:")
    for method, groups in results.items():
        if method != 'all_groups':
            print(f"  {method}: {len(groups)} groups")
    
    all_groups = results.get('all_groups', set())
    print(f"\n📋 Total unique groups discovered: {len(all_groups)}")
    
    if all_groups:
        print("\nDiscovered groups:")
        for i, group in enumerate(sorted(all_groups), 1):
            print(f"  {i:2d}. {group}")
        
        # Save results
        filename = discovery.save_discovery_results(results)
        print(f"\n✅ Results saved to: {filename}")
        
        # Ask about joining new groups
        new_groups = [g for g in all_groups if g not in config.MONITORED_GROUPS]
        if new_groups:
            print(f"\n🎯 Found {len(new_groups)} new groups not in config")
            print("These could be added to MONITORED_GROUPS in config.py:")
            for group in new_groups[:10]:  # Show first 10
                print(f"    \"{group}\",")
    else:
        print("\nNo new groups discovered.")

if __name__ == "__main__":
    main()