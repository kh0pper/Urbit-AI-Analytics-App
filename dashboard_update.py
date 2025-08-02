#!/usr/bin/env python3
"""
Update the dashboard with latest discovery data
"""
import json
import os
from datetime import datetime
import config

def create_dashboard_files():
    """Create/update dashboard files with latest discovery data"""
    
    # Create dashboard directory if it doesn't exist
    os.makedirs('dashboard', exist_ok=True)
    
    # Load latest discovery data
    try:
        with open('data/latest_discovery.json', 'r') as f:
            discovery_data = json.load(f)
    except FileNotFoundError:
        print("❌ No discovery data found. Run smart_group_discovery.py first.")
        return
    
    # Load discovery history
    try:
        with open('data/discovery_log.json', 'r') as f:
            history_data = json.load(f)
    except FileNotFoundError:
        history_data = {"discoveries": []}
    
    # Create main dashboard HTML
    create_main_dashboard(discovery_data, history_data)
    
    # Create data JSON files for the dashboard
    create_dashboard_data_files(discovery_data, history_data)
    
    # Update README with dashboard info
    update_dashboard_readme(discovery_data)
    
    print("✅ Dashboard updated successfully!")
    print("📊 Dashboard files created in ./dashboard/")
    print("🌐 View at: https://kh0pper.github.io/urbit-analytics/dashboard/")

def create_main_dashboard(discovery_data, history_data):
    """Create the main dashboard HTML file"""
    
    new_groups_count = discovery_data.get('new_groups', 0)
    total_groups = discovery_data.get('total_discovered', 0)
    current_monitoring = len(config.MONITORED_GROUPS)
    
    # Get high-priority groups
    new_groups_list = discovery_data.get('new_groups_list', [])
    priority_groups = [g for g in new_groups_list if any(ship in g for ship in [
        'haddef-sigwen', 'nattyv', 'solfer-magfed', 'bitbet-bolbel'
    ])][:10]
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urbit AI Analytics Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
        }}
        .stat-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #4f46e5;
            margin: 0;
        }}
        .stat-label {{
            color: #64748b;
            margin: 5px 0 0 0;
            font-size: 1.1em;
        }}
        .section {{
            padding: 30px;
            border-top: 1px solid #e2e8f0;
        }}
        .section h2 {{
            margin: 0 0 20px 0;
            color: #1e293b;
            font-size: 1.5em;
        }}
        .groups-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        .group-card {{
            background: #f1f5f9;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9em;
        }}
        .priority-group {{
            background: #fef3c7;
            border-color: #f59e0b;
        }}
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-operational {{
            background: #dcfce7;
            color: #166534;
        }}
        .status-new {{
            background: #dbeafe;
            color: #1d4ed8;
        }}
        .footer {{
            background: #f8fafc;
            padding: 20px 30px;
            text-align: center;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
        .last-updated {{
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
            color: #0c4a6e;
        }}
        .methods-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .method-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 15px;
            text-align: center;
        }}
        .method-count {{
            font-size: 1.8em;
            font-weight: bold;
            color: #7c3aed;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Urbit AI Analytics</h1>
            <p>Real-time Network Monitoring & Group Discovery Dashboard</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{total_groups}</div>
                <div class="stat-label">Total Groups Discovered</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{new_groups_count}</div>
                <div class="stat-label">New Groups Found</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{current_monitoring}</div>
                <div class="stat-label">Currently Monitoring</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(priority_groups)}</div>
                <div class="stat-label">High-Priority Groups</div>
            </div>
        </div>
        
        <div class="last-updated">
            <strong>📅 Last Discovery:</strong> {discovery_data.get('timestamp', 'Unknown')}
            <span class="status-badge status-operational">System Operational</span>
        </div>
        
        <div class="section">
            <h2>🔥 High-Priority Community Groups</h2>
            <p>These groups represent major Urbit community hubs and official channels:</p>
            <div class="groups-grid">"""
    
    for group in priority_groups:
        html_content += f"""
                <div class="group-card priority-group">
                    {group}
                    <span class="status-badge status-new">New</span>
                </div>"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Discovery Methods Performance</h2>
            <div class="methods-grid">"""
    
    methods = discovery_data.get('groups_by_method', {})
    for method, groups in methods.items():
        if isinstance(groups, list) and method != 'all_groups':
            method_name = method.replace('_', ' ').title()
            html_content += f"""
                <div class="method-card">
                    <div class="method-count">{len(groups)}</div>
                    <div>{method_name}</div>
                </div>"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="section">
            <h2>📋 Recently Discovered Groups</h2>
            <p>Latest groups found by the discovery system (showing first 20):</p>
            <div class="groups-grid">"""
    
    for group in new_groups_list[:20]:
        html_content += f"""
                <div class="group-card">
                    {group}
                </div>"""
    
    if len(new_groups_list) > 20:
        html_content += f"""
                <div class="group-card" style="text-align: center; font-style: italic; background: #e2e8f0;">
                    ... and {len(new_groups_list) - 20} more groups
                </div>"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="section">
            <h2>📈 Currently Monitoring</h2>
            <p>Groups actively monitored by the AI analytics system:</p>
            <div class="groups-grid">"""
    
    for group in config.MONITORED_GROUPS:
        html_content += f"""
                <div class="group-card">
                    {group}
                    <span class="status-badge status-operational">Active</span>
                </div>"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 Urbit AI Analytics Dashboard | 
            <a href="https://github.com/kh0pper/urbit-analytics" target="_blank">View on GitHub</a> | 
            Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>System Status: <span class="status-badge status-operational">Operational</span></p>
        </div>
    </div>
</body>
</html>"""
    
    with open('dashboard/index.html', 'w') as f:
        f.write(html_content)

def create_dashboard_data_files(discovery_data, history_data):
    """Create JSON data files for dashboard API"""
    
    # Dashboard stats API
    stats = {
        "total_discovered": discovery_data.get('total_discovered', 0),
        "new_groups": discovery_data.get('new_groups', 0),
        "currently_monitoring": len(config.MONITORED_GROUPS),
        "last_discovery": discovery_data.get('timestamp', ''),
        "system_status": "operational",
        "discovery_methods": len(discovery_data.get('groups_by_method', {})),
        "high_priority_count": len([g for g in discovery_data.get('new_groups_list', []) 
                                  if any(ship in g for ship in ['haddef-sigwen', 'nattyv', 'solfer-magfed', 'bitbet-bolbel'])]),
        "last_updated": datetime.now().isoformat()
    }
    
    with open('dashboard/stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Groups data API
    groups_data = {
        "monitored_groups": config.MONITORED_GROUPS,
        "new_groups": discovery_data.get('new_groups_list', []),
        "priority_groups": [g for g in discovery_data.get('new_groups_list', []) 
                          if any(ship in g for ship in ['haddef-sigwen', 'nattyv', 'solfer-magfed', 'bitbet-bolbel'])],
        "methods_breakdown": discovery_data.get('groups_by_method', {}),
        "last_updated": datetime.now().isoformat()
    }
    
    with open('dashboard/groups.json', 'w') as f:
        json.dump(groups_data, f, indent=2)

def update_dashboard_readme(discovery_data):
    """Create a README for the dashboard"""
    
    readme_content = f"""# 📊 Urbit AI Analytics Dashboard

## Live Dashboard
🌐 **View Live**: https://kh0pper.github.io/urbit-analytics/dashboard/

## Latest Statistics

- **Total Groups Discovered**: {discovery_data.get('total_discovered', 0)}
- **New Groups Found**: {discovery_data.get('new_groups', 0)} 
- **Currently Monitoring**: {len(config.MONITORED_GROUPS)}
- **Last Discovery**: {discovery_data.get('timestamp', 'Unknown')}

## Dashboard Features

- 📊 **Real-time Statistics**: Current monitoring and discovery stats
- 🔥 **Priority Groups**: High-value community groups to join
- 📋 **Discovery Results**: Complete list of newly found groups
- 📈 **Monitoring Status**: Current groups being tracked
- 🔍 **Method Breakdown**: Performance of different discovery methods

## API Endpoints

- `/dashboard/stats.json` - Current statistics
- `/dashboard/groups.json` - Groups data and discovery results
- `/data/latest_discovery.json` - Full discovery data
- `/data/discovery_log.json` - Historical discovery log

## System Status

✅ **Operational** - All systems running normally

Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('dashboard/README.md', 'w') as f:
        f.write(readme_content)

if __name__ == "__main__":
    create_dashboard_files()