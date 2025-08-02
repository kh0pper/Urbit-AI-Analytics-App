#!/usr/bin/env python3
"""
Update the discovery log with latest findings
"""
import json
from datetime import datetime
import config

def update_discovery_log():
    """Update discovery_log.md with latest findings"""
    
    # Read the latest discovery results
    try:
        with open('data/latest_discovery.json', 'r') as f:
            latest_data = json.load(f)
    except FileNotFoundError:
        print("❌ No latest discovery data found. Run smart_group_discovery.py first.")
        return
    
    # Read existing discovery log if it exists
    try:
        with open('data/discovery_log.json', 'r') as f:
            history = json.load(f)
            if "discoveries" not in history:
                history["discoveries"] = []
    except FileNotFoundError:
        history = {"discoveries": []}
    
    # Add latest discovery to history
    discovery_entry = {
        "timestamp": latest_data.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        "total_discovered": latest_data.get("total_discovered", 0),
        "new_groups": latest_data.get("new_groups", 0),
        "methods_used": list(latest_data.get("groups_by_method", {}).keys()),
        "top_new_groups": latest_data.get("new_groups_list", [])[:20]  # Top 20
    }
    
    history["discoveries"].append(discovery_entry)
    history["last_updated"] = datetime.now().isoformat()
    
    # Save updated history
    with open('data/discovery_log.json', 'w') as f:
        json.dump(history, f, indent=2)
    
    # Create readable markdown log
    create_markdown_log(history, latest_data)
    
    print(f"✅ Discovery log updated with {latest_data.get('new_groups', 0)} new groups")

def create_markdown_log(history, latest_data):
    """Create a readable markdown discovery log"""
    
    latest_discovery = history["discoveries"][-1] if history["discoveries"] else {}
    
    md_content = f"""# Urbit Group Discovery Log

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Latest Discovery Summary

- **Discovery Date**: {latest_discovery.get('timestamp', 'Unknown')}
- **Total Groups Found**: {latest_discovery.get('total_discovered', 0)}
- **New Groups**: {latest_discovery.get('new_groups', 0)}
- **Methods Used**: {', '.join(latest_discovery.get('methods_used', []))}

## 🎯 Top New Groups Discovered

"""
    
    new_groups = latest_data.get("new_groups_list", [])
    
    # High-priority groups (community hubs)
    priority_groups = [g for g in new_groups if any(ship in g for ship in [
        'haddef-sigwen', 'nattyv', 'solfer-magfed', 'bitbet-bolbel'
    ])]
    
    if priority_groups:
        md_content += "### 🔥 High-Priority Community Groups\n\n"
        for i, group in enumerate(priority_groups[:10], 1):
            md_content += f"{i:2d}. `{group}`\n"
        md_content += "\n"
    
    # All new groups
    md_content += "### 📋 All New Groups\n\n"
    for i, group in enumerate(new_groups[:30], 1):  # Show first 30
        md_content += f"{i:2d}. `{group}`\n"
    
    if len(new_groups) > 30:
        md_content += f"\n... and {len(new_groups) - 30} more groups\n"
    
    # Discovery methods breakdown
    md_content += f"\n## 🔍 Discovery Methods Breakdown\n\n"
    
    methods = latest_data.get("groups_by_method", {})
    for method, groups in methods.items():
        if isinstance(groups, list) and groups:
            md_content += f"### {method.replace('_', ' ').title()}\n"
            md_content += f"Found {len(groups)} groups\n\n"
    
    # History
    md_content += "\n## 📈 Discovery History\n\n"
    
    for discovery in history["discoveries"][-5:]:  # Last 5 discoveries
        md_content += f"- **{discovery.get('timestamp', 'Unknown')}**: {discovery.get('total_discovered', 0)} total, {discovery.get('new_groups', 0)} new\n"
    
    # Current monitoring status
    md_content += f"\n## 📊 Current Monitoring Status\n\n"
    md_content += f"- **Currently Monitoring**: {len(config.MONITORED_GROUPS)} groups\n"
    md_content += f"- **Potential New Groups**: {len(new_groups)}\n"
    md_content += f"- **Discovery Coverage**: {len(methods)} methods used\n"
    
    # Recommendations
    md_content += f"\n## 💡 Recommendations\n\n"
    
    if priority_groups:
        md_content += "### Immediate Action\n"
        md_content += "Consider adding these high-priority community groups to config.py:\n\n"
        md_content += "```python\n"
        for group in priority_groups[:5]:
            md_content += f'    "{group}",\n'
        md_content += "```\n\n"
    
    md_content += "### Next Steps\n"
    md_content += "1. Review the high-priority groups above\n"
    md_content += "2. Test accessibility of interesting groups\n"
    md_content += "3. Add promising groups to MONITORED_GROUPS in config.py\n"
    md_content += "4. Run discovery again in 1-2 weeks\n"
    
    md_content += f"\n---\n*Auto-generated discovery log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
    
    # Save markdown log
    with open('data/discovery_log.md', 'w') as f:
        f.write(md_content)

if __name__ == "__main__":
    update_discovery_log()