#!/usr/bin/env python3
"""
Smart Group Discovery System - Practical approach for finding new Urbit groups
Uses working methods and avoids broken API endpoints
"""
import requests
import re
import json
import time
from typing import Set, List, Dict
import config

class SmartGroupDiscovery:
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.set('urbauth-~litmyl-nopmet', config.URBIT_SESSION_COOKIE)
        self.base_url = config.URBIT_SHIP_URL
        
    def discover_via_web_interface(self) -> Set[str]:
        """Scrape Groups app web interface for group patterns"""
        groups = set()
        
        try:
            # Get the main groups page
            response = self.session.get(f"{self.base_url}/apps/groups", timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # Look for group patterns in the HTML/JS
                patterns = [
                    r'/ship/~[\w-]+/[\w-]+(?:/[\w-]+)*',  # Full group paths
                    r'groups/~[\w-]+/[\w-]+',             # Groups in URLs
                    r'"~[\w-]+/[\w-]+(?:/[\w-]+)*"',      # Quoted ship/group patterns
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        clean_match = self._normalize_group_path(match)
                        if clean_match and self._is_valid_group_path(clean_match):
                            groups.add(clean_match)
                            
                print(f"Web interface discovery found {len(groups)} groups")
                
        except Exception as e:
            print(f"Web interface discovery failed: {e}")
            
        return groups
    
    def discover_via_known_patterns(self) -> Set[str]:
        """Test common group patterns based on existing groups"""
        groups = set()
        
        # Extract known ships from current groups
        known_ships = set()
        for group in config.MONITORED_GROUPS:
            if group.startswith('/ship/'):
                parts = group.split('/')
                if len(parts) >= 3:
                    known_ships.add(parts[2])
        
        # Common group/channel names to test
        common_names = [
            'general', 'chat', 'announcements', 'random', 'dev', 'help',
            'main', 'public', 'discussion', 'links', 'intro', 'welcome',
            'testing', 'lobby', 'community', 'updates', 'news', 'lounge'
        ]
        
        print(f"Testing patterns with {len(known_ships)} known ships...")
        
        for ship in known_ships:
            for name in common_names:
                test_group = f'/ship/{ship}/{name}'
                if test_group not in config.MONITORED_GROUPS:
                    if self._test_group_accessibility(test_group):
                        groups.add(test_group)
                        print(f"  Found: {test_group}")
        
        return groups
    
    def discover_via_community_hubs(self) -> Set[str]:
        """Check well-known community hubs for new groups"""
        groups = set()
        
        # Well-known Urbit community groups/ships
        community_hubs = [
            '/ship/~bitbet-bolbel/urbit-community',
            '/ship/~darrux-landes/the-forge', 
            '/ship/~libset-rirbep/landscape',
            '/ship/~dister-dozzod-basbys/urbitfoundation',
            '/ship/~sogryp-dister-dozzod-dozzod/network-states',
            '/ship/~pindet-timmut/hackroom',
            '/ship/~haddef-sigwen/tlon',
            '/ship/~nattyv/urbit',
            '/ship/~solfer-magfed/foundation'
        ]
        
        print("Testing community hubs...")
        
        for hub in community_hubs:
            if hub not in config.MONITORED_GROUPS:
                if self._test_group_accessibility(hub):
                    groups.add(hub)
                    print(f"  Accessible: {hub}")
                    
                    # Also test common subchannels
                    base_path = hub
                    subchannels = ['general', 'chat', 'announcements', 'dev']
                    for subchannel in subchannels:
                        subchannel_path = f"{base_path}/{subchannel}"
                        if self._test_group_accessibility(subchannel_path):
                            groups.add(subchannel_path)
                            print(f"  Subchannel: {subchannel_path}")
        
        return groups
    
    def discover_via_ship_exploration(self) -> Set[str]:
        """Explore individual ships to find their public groups"""
        groups = set()
        
        # Extract unique ships from known groups
        ships = set()
        for group in config.MONITORED_GROUPS:
            if group.startswith('/ship/'):
                parts = group.split('/')
                if len(parts) >= 3:
                    ships.add(parts[2])
        
        # Add some well-known ships
        ships.update([
            '~bitbet-bolbel', '~darrux-landes', '~libset-rirbep',
            '~haddef-sigwen', '~nattyv', '~solfer-magfed'
        ])
        
        print(f"Exploring {len(ships)} ships for public groups...")
        
        for ship in ships:
            ship_groups = self._explore_ship_groups(ship)
            groups.update(ship_groups)
            if ship_groups:
                print(f"  {ship}: found {len(ship_groups)} groups")
        
        return groups
    
    def _explore_ship_groups(self, ship: str) -> Set[str]:
        """Explore a specific ship for public groups"""
        groups = set()
        
        # Common public group names
        public_names = [
            'public', 'general', 'community', 'chat', 'main', 'lobby',
            'announcements', 'welcome', 'intro', 'discussion', 'random'
        ]
        
        for name in public_names:
            test_path = f'/ship/{ship}/{name}'
            if self._test_group_accessibility(test_path):
                groups.add(test_path)
        
        return groups
    
    def _test_group_accessibility(self, group_path: str) -> bool:
        """Test if a group is accessible"""
        try:
            # Try the web interface approach
            url = f"{self.base_url}/apps/groups/groups{group_path}"
            response = self.session.get(url, timeout=5)
            
            # 200 = accessible, 403 = exists but restricted, 404 = doesn't exist
            if response.status_code in [200, 403]:
                return True
                
        except Exception:
            pass
            
        return False
    
    def _normalize_group_path(self, path: str) -> str:
        """Normalize a group path to standard format"""
        path = path.strip('\'"')
        
        if path.startswith('groups/'):
            path = path[7:]  # Remove 'groups/' prefix
            
        if path.startswith('~') and not path.startswith('/ship/'):
            path = f'/ship/{path}'
            
        if not path.startswith('/ship/'):
            return None
            
        return path
    
    def _is_valid_group_path(self, path: str) -> bool:
        """Check if a group path looks valid"""
        if not path.startswith('/ship/~'):
            return False
            
        parts = path.split('/')
        if len(parts) < 3:
            return False
            
        # Check ship name format
        ship = parts[2]
        if not re.match(r'^~[\w-]+$', ship):
            return False
            
        return True
    
    def run_discovery(self) -> Dict[str, Set[str]]:
        """Run all discovery methods"""
        print("🔍 Running Smart Group Discovery")
        print("=" * 40)
        
        methods = {
            'web_interface': self.discover_via_web_interface,
            'known_patterns': self.discover_via_known_patterns,
            'community_hubs': self.discover_via_community_hubs,
            'ship_exploration': self.discover_via_ship_exploration
        }
        
        results = {}
        all_groups = set()
        
        for method_name, method_func in methods.items():
            print(f"\n🔎 {method_name.replace('_', ' ').title()}...")
            try:
                groups = method_func()
                results[method_name] = groups
                all_groups.update(groups)
                print(f"Found {len(groups)} groups via {method_name}")
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                results[method_name] = set()
        
        results['all_groups'] = all_groups
        return results
    
    def save_and_update_config(self, results: Dict[str, Set[str]]):
        """Save results and optionally update config"""
        all_groups = results.get('all_groups', set())
        new_groups = [g for g in all_groups if g not in config.MONITORED_GROUPS]
        
        # Save discovery results
        discovery_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_discovered': len(all_groups),
            'new_groups': len(new_groups),
            'groups_by_method': {k: list(v) for k, v in results.items() if isinstance(v, set)},
            'new_groups_list': new_groups
        }
        
        with open('data/latest_discovery.json', 'w') as f:
            json.dump(discovery_data, f, indent=2)
        
        print(f"\n📊 Discovery Summary:")
        print(f"  Total groups found: {len(all_groups)}")
        print(f"  New groups: {len(new_groups)}")
        print(f"  Results saved to: data/latest_discovery.json")
        
        if new_groups:
            print(f"\n🎯 New groups to consider adding:")
            for group in new_groups[:15]:  # Show first 15
                print(f"    \"{group}\",")
            
            if len(new_groups) > 15:
                print(f"    ... and {len(new_groups) - 15} more")

def main():
    discovery = SmartGroupDiscovery()
    results = discovery.run_discovery()
    discovery.save_and_update_config(results)
    
    print(f"\n✅ Discovery complete!")

if __name__ == "__main__":
    main()