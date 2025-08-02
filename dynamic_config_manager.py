#!/usr/bin/env python3
"""
Dynamic Configuration Manager
Automatically updates monitoring lists when new groups are discovered
"""
import os
import json
import time
from typing import List, Set
from datetime import datetime
import config

class DynamicConfigManager:
    def __init__(self):
        self.config_file_path = os.path.join(os.path.dirname(__file__), 'config.py')
        self.discovery_log_path = 'data/discovery_log.json'
        self.current_monitored = set(config.MONITORED_GROUPS)
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
    def load_discovery_log(self) -> dict:
        """Load the discovery log to track what we've found"""
        try:
            if os.path.exists(self.discovery_log_path):
                with open(self.discovery_log_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading discovery log: {e}")
        
        return {
            "last_discovery": None,
            "discovered_groups": [],
            "auto_added_groups": [],
            "discovery_history": []
        }
    
    def save_discovery_log(self, log_data: dict):
        """Save the discovery log"""
        try:
            with open(self.discovery_log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Error saving discovery log: {e}")
    
    def add_groups_to_config(self, new_groups: List[str]) -> bool:
        """Dynamically add new groups to the config file"""
        if not new_groups:
            return True
        
        print(f"📝 Adding {len(new_groups)} new groups to configuration...")
        
        try:
            # Read current config file
            with open(self.config_file_path, 'r') as f:
                config_content = f.read()
            
            # Find the MONITORED_GROUPS section
            import re
            
            # Pattern to match the MONITORED_GROUPS list
            pattern = r'(MONITORED_GROUPS\s*=\s*\[)(.*?)(\])'
            match = re.search(pattern, config_content, re.DOTALL)
            
            if not match:
                print("❌ Could not find MONITORED_GROUPS in config file")
                return False
            
            start_bracket = match.group(1)
            current_list = match.group(2)
            end_bracket = match.group(3)
            
            # Parse existing groups from the config
            existing_groups = []
            for line in current_list.split('\n'):
                line = line.strip()
                if line.startswith('"') and line.endswith('",'):
                    group = line[1:-2]  # Remove quotes and comma
                    existing_groups.append(group)
                elif line.startswith('"') and line.endswith('"'):
                    group = line[1:-1]  # Remove quotes
                    existing_groups.append(group)
            
            # Add new groups that aren't already present
            all_groups = list(set(existing_groups + new_groups))
            all_groups.sort()  # Sort for better organization
            
            # Create new list content
            new_list_content = "\n"
            for i, group in enumerate(all_groups):
                if group.strip():  # Skip empty groups
                    # Add comment for auto-discovered groups
                    if group in new_groups:
                        new_list_content += f"    # Auto-discovered: {datetime.now().strftime('%Y-%m-%d')}\n"
                    
                    comma = "," if i < len(all_groups) - 1 else ""
                    new_list_content += f'    "{group}"{comma}\n'
            
            # Replace the MONITORED_GROUPS section
            new_config_content = re.sub(
                pattern,
                f"{start_bracket}{new_list_content}{end_bracket}",
                config_content,
                flags=re.DOTALL
            )
            
            # Write back to config file
            with open(self.config_file_path, 'w') as f:
                f.write(new_config_content)
            
            print(f"✅ Successfully added {len(new_groups)} groups to config")
            for group in new_groups:
                print(f"   + {group}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating config file: {e}")
            return False
    
    def filter_and_add_promising_groups(self, discovered_groups: List[dict]) -> List[str]:
        """Filter discovered groups and add promising ones automatically"""
        log_data = self.load_discovery_log()
        
        # Get groups we've already considered
        previously_discovered = set(log_data.get("discovered_groups", []))
        auto_added = set(log_data.get("auto_added_groups", []))
        
        # Filter for new, promising groups
        promising_groups = []
        all_discovered = []
        
        for group in discovered_groups:
            group_path = group.get('path', '')
            group_name = group.get('name', '').lower()
            
            if not group_path:
                continue
                
            all_discovered.append(group_path)
            
            # Skip if already monitored or previously considered
            if group_path in self.current_monitored or group_path in previously_discovered:
                continue
            
            # Auto-add criteria: public/open groups that seem active
            promising_keywords = [
                'public', 'general', 'chat', 'community', 'welcome', 
                'open', 'main', 'lobby', 'announcements', 'discussion',
                'help', 'intro', 'random'
            ]
            
            # Skip private/restricted groups
            restricted_keywords = [
                'private', 'admin', 'mod', 'restricted', 'secret',
                'internal', 'staff', 'dev-private'
            ]
            
            # Check if group name suggests it's public/open
            is_promising = any(keyword in group_name for keyword in promising_keywords)
            is_restricted = any(keyword in group_name for keyword in restricted_keywords)
            
            # Special handling for known good hosts
            known_good_hosts = ['~halbex-palheb', '~bitbet-bolbel', '~darrux-landes', '~zod']
            host_ship = group.get('host_ship', '')
            from_good_host = host_ship in known_good_hosts
            
            if (is_promising or from_good_host) and not is_restricted:
                promising_groups.append(group_path)
                print(f"🎯 Identified promising group: {group_path}")
        
        # Update discovery log
        current_time = datetime.now().isoformat()
        log_data["last_discovery"] = current_time
        log_data["discovered_groups"] = list(set(log_data.get("discovered_groups", []) + all_discovered))
        
        # Add promising groups to config
        if promising_groups:
            if self.add_groups_to_config(promising_groups):
                log_data["auto_added_groups"] = list(set(log_data.get("auto_added_groups", []) + promising_groups))
        
        # Add to discovery history
        if "discovery_history" not in log_data:
            log_data["discovery_history"] = []
        
        log_data["discovery_history"].append({
            "timestamp": current_time,
            "total_discovered": len(all_discovered),
            "new_groups": len([g for g in all_discovered if g not in previously_discovered]),
            "auto_added": len(promising_groups)
        })
        
        # Keep only last 10 history entries
        log_data["discovery_history"] = log_data["discovery_history"][-10:]
        
        self.save_discovery_log(log_data)
        
        return promising_groups
    
    def get_discovery_stats(self) -> dict:
        """Get statistics about discovery and auto-adding"""
        log_data = self.load_discovery_log()
        
        return {
            "total_discovered": len(log_data.get("discovered_groups", [])),
            "auto_added": len(log_data.get("auto_added_groups", [])),
            "currently_monitoring": len(config.MONITORED_GROUPS),
            "last_discovery": log_data.get("last_discovery"),
            "discovery_history": log_data.get("discovery_history", [])
        }
    
    def manual_add_groups(self, groups_to_add: List[str]) -> bool:
        """Manually add specific groups to monitoring"""
        print(f"🔧 Manually adding {len(groups_to_add)} groups...")
        
        # Filter out groups already being monitored
        new_groups = [g for g in groups_to_add if g not in self.current_monitored]
        
        if not new_groups:
            print("ℹ️ All specified groups are already being monitored")
            return True
        
        success = self.add_groups_to_config(new_groups)
        
        if success:
            # Update discovery log
            log_data = self.load_discovery_log()
            log_data["auto_added_groups"] = list(set(log_data.get("auto_added_groups", []) + new_groups))
            self.save_discovery_log(log_data)
        
        return success

def test_dynamic_config():
    """Test the dynamic configuration manager"""
    print("🧪 TESTING DYNAMIC CONFIGURATION MANAGER")
    print("=" * 50)
    
    manager = DynamicConfigManager()
    
    # Test 1: Get current stats
    print("\n1️⃣ Current discovery statistics:")
    stats = manager.get_discovery_stats()
    
    for key, value in stats.items():
        if key == "discovery_history":
            print(f"   📊 {key}: {len(value)} entries")
        else:
            print(f"   📊 {key}: {value}")
    
    # Test 2: Simulate discovering new groups
    print("\n2️⃣ Simulating discovery of new groups...")
    
    sample_discovered_groups = [
        {
            'path': '/ship/~bitbet-bolbel/urbit-community',
            'name': 'urbit-community',
            'host_ship': '~bitbet-bolbel',
            'type': 'discovered'
        },
        {
            'path': '/ship/~darrux-landes/the-forge',
            'name': 'the-forge', 
            'host_ship': '~darrux-landes',
            'type': 'discovered'
        },
        {
            'path': '/ship/~zod/general',
            'name': 'general',
            'host_ship': '~zod',
            'type': 'discovered'
        }
    ]
    
    added_groups = manager.filter_and_add_promising_groups(sample_discovered_groups)
    
    print(f"\n3️⃣ Results:")
    print(f"   ✅ Processed {len(sample_discovered_groups)} discovered groups")
    print(f"   ➕ Auto-added {len(added_groups)} promising groups")
    
    # Test 3: Show updated stats
    print("\n4️⃣ Updated statistics:")
    updated_stats = manager.get_discovery_stats()
    
    for key, value in updated_stats.items():
        if key == "discovery_history":
            print(f"   📊 {key}: {len(value)} entries")
            if value:
                latest = value[-1]
                print(f"      Latest: {latest.get('total_discovered', 0)} discovered, {latest.get('auto_added', 0)} added")
        else:
            print(f"   📊 {key}: {value}")
    
    print(f"\n🏁 Dynamic configuration test complete!")
    return len(added_groups)

if __name__ == "__main__":
    test_dynamic_config()