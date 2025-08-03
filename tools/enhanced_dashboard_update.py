#!/usr/bin/env python3
"""
Enhanced Dashboard Update for Real-time Activity Monitoring
Shows group activity, AI analysis, and monitoring stats
"""
import json
import os
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.data_collector import DataCollector

def create_enhanced_dashboard():
    """Create enhanced dashboard with real-time activity data"""
    
    # Create dashboard directory
    os.makedirs('dashboard', exist_ok=True)
    
    # Load data
    data_collector = DataCollector(config.DATA_DIR)
    
    # Get current activity data
    activity_data = data_collector.activity_data
    network_stats = data_collector.get_network_overview()
    
    # Load discovery data
    try:
        with open('data/latest_discovery.json', 'r') as f:
            discovery_data = json.load(f)
    except FileNotFoundError:
        discovery_data = {"new_groups": 0, "total_discovered": 0}
    
    # Analyze recent activity
    recent_activity = analyze_recent_activity(activity_data)
    active_groups = get_active_groups(activity_data)
    ai_insights = get_latest_ai_insights(activity_data)
    
    # Create main dashboard
    create_main_dashboard_html(network_stats, recent_activity, active_groups, ai_insights, discovery_data)
    
    # Create API endpoints
    create_activity_api(recent_activity, active_groups, ai_insights)
    create_stats_api(network_stats, discovery_data)
    
    print("✅ Enhanced dashboard created successfully!")
    print("📊 Dashboard shows:")
    print(f"  - {network_stats.get('active_groups_24h', 0)} active groups")
    print(f"  - {network_stats.get('total_activities_collected', 0)} total activities")
    print(f"  - {len(ai_insights)} AI analysis results")
    print("🌐 View at: https://kh0pper.github.io/urbit-analytics/dashboard/")

def analyze_recent_activity(activity_data):
    """Analyze recent activity across all groups"""
    recent_activities = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for group_path, group_data in activity_data.get('groups', {}).items():
        for log_entry in group_data.get('activity_log', []):
            entry_time = datetime.fromisoformat(log_entry['timestamp'])
            if entry_time > cutoff_time:
                for activity in log_entry.get('activities', []):
                    recent_activities.append({
                        'group': group_path,
                        'timestamp': activity.get('timestamp', log_entry['timestamp']),
                        'author': activity.get('author', 'unknown'),
                        'content': activity.get('content', '')[:100] + '...' if len(activity.get('content', '')) > 100 else activity.get('content', ''),
                        'type': activity.get('type', 'message')
                    })
    
    # Sort by timestamp (newest first)
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    return recent_activities[:50]  # Last 50 activities

def get_active_groups(activity_data):
    """Get list of active groups with statistics"""
    active_groups = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for group_path, group_data in activity_data.get('groups', {}).items():
        recent_messages = 0
        unique_users = set()
        last_activity = None
        
        for log_entry in group_data.get('activity_log', []):
            entry_time = datetime.fromisoformat(log_entry['timestamp'])
            if entry_time > cutoff_time:
                recent_messages += log_entry.get('message_count', 0)
                for activity in log_entry.get('activities', []):
                    unique_users.add(activity.get('author', 'unknown'))
                    if not last_activity or activity.get('timestamp', '') > last_activity:
                        last_activity = activity.get('timestamp', log_entry['timestamp'])
        
        if recent_messages > 0:
            active_groups.append({
                'group': group_path,
                'group_name': group_path.split('/')[-1],
                'ship': group_path.split('/')[2] if len(group_path.split('/')) > 2 else 'unknown',
                'recent_messages': recent_messages,
                'unique_users': len(unique_users),
                'last_activity': last_activity,
                'activity_level': 'High' if recent_messages > 20 else 'Medium' if recent_messages > 5 else 'Low'
            })
    
    # Sort by activity level
    active_groups.sort(key=lambda x: x['recent_messages'], reverse=True)
    return active_groups

def get_latest_ai_insights(activity_data):
    """Get latest AI analysis insights"""
    ai_insights = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    for group_path, group_data in activity_data.get('groups', {}).items():
        for analysis_entry in group_data.get('stats_history', []):
            entry_time = datetime.fromisoformat(analysis_entry['timestamp'])
            if entry_time > cutoff_time:
                analysis = analysis_entry.get('analysis', {})
                if analysis.get('ai_analysis'):
                    ai_insights.append({
                        'group': group_path,
                        'timestamp': analysis_entry['timestamp'],
                        'insight': analysis['ai_analysis'][:200] + '...' if len(analysis.get('ai_analysis', '')) > 200 else analysis.get('ai_analysis', ''),
                        'sentiment': analysis.get('sentiment', 'neutral'),
                        'key_topics': analysis.get('key_topics', []),
                        'stats': analysis_entry.get('stats', {})
                    })
    
    # Sort by timestamp (newest first)
    ai_insights.sort(key=lambda x: x['timestamp'], reverse=True)
    return ai_insights[:10]  # Latest 10 insights

def create_main_dashboard_html(network_stats, recent_activity, active_groups, ai_insights, discovery_data):
    """Create the main enhanced dashboard HTML"""
    
    total_messages = sum(group['recent_messages'] for group in active_groups)
    total_users = len(set(activity['author'] for activity in recent_activity))
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urbit AI Analytics Dashboard - Live Activity</title>
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
            max-width: 1400px;
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
        .live-indicator {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
            margin-right: 8px;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
            font-size: 2.2em;
            font-weight: bold;
            color: #4f46e5;
            margin: 0;
        }}
        .stat-label {{
            color: #64748b;
            margin: 5px 0 0 0;
            font-size: 1em;
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
        .activity-feed {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
        }}
        .activity-item {{
            padding: 15px;
            border-bottom: 1px solid #f1f5f9;
            transition: background 0.2s;
        }}
        .activity-item:hover {{
            background: #f8fafc;
        }}
        .activity-item:last-child {{
            border-bottom: none;
        }}
        .activity-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .activity-author {{
            font-weight: bold;
            color: #4f46e5;
        }}
        .activity-group {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.8em;
            color: #64748b;
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .activity-time {{
            color: #94a3b8;
            font-size: 0.8em;
        }}
        .activity-content {{
            color: #475569;
            line-height: 1.4;
        }}
        .groups-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }}
        .group-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            transition: transform 0.2s;
        }}
        .group-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .group-name {{
            font-weight: bold;
            color: #1e293b;
            margin-bottom: 8px;
            font-family: 'Monaco', 'Menlo', monospace;
        }}
        .group-stats {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .activity-level {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .activity-high {{ background: #fecaca; color: #dc2626; }}
        .activity-medium {{ background: #fed7aa; color: #ea580c; }}
        .activity-low {{ background: #d1fae5; color: #059669; }}
        .ai-insights {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}
        .insight-card {{
            background: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 8px;
            padding: 20px;
        }}
        .insight-group {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.8em;
            color: #0c4a6e;
            margin-bottom: 10px;
        }}
        .insight-text {{
            color: #0f172a;
            line-height: 1.4;
            margin-bottom: 10px;
        }}
        .insight-topics {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .topic-tag {{
            background: #dbeafe;
            color: #1d4ed8;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
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
        .footer {{
            background: #f8fafc;
            padding: 20px 30px;
            text-align: center;
            color: #64748b;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => {{
            window.location.reload();
        }}, 300000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Urbit AI Analytics</h1>
            <p><span class="live-indicator"></span>Live Network Monitoring & Activity Dashboard</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{len(active_groups)}</div>
                <div class="stat-label">Active Groups (24h)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_messages}</div>
                <div class="stat-label">Messages Collected</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_users}</div>
                <div class="stat-label">Active Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(ai_insights)}</div>
                <div class="stat-label">AI Insights</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(config.MONITORED_GROUPS)}</div>
                <div class="stat-label">Total Monitored</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{discovery_data.get('new_groups', 0)}</div>
                <div class="stat-label">New Groups Found</div>
            </div>
        </div>
        
        <div class="last-updated">
            <strong>📅 Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
            <span style="margin-left: 20px;"><strong>🔄 Auto-refresh:</strong> Every 5 minutes</span>
        </div>"""
    
    # Recent Activity Section
    if recent_activity:
        html_content += f"""
        <div class="section">
            <h2>📊 Recent Activity (Last 24 Hours)</h2>
            <div class="activity-feed">"""
        
        for activity in recent_activity[:20]:  # Show last 20 activities
            # Convert timestamp to readable format
            try:
                activity_time = datetime.fromisoformat(activity['timestamp']).strftime('%H:%M')
            except:
                activity_time = 'Unknown'
            
            html_content += f"""
                <div class="activity-item">
                    <div class="activity-header">
                        <span class="activity-author">{activity['author']}</span>
                        <div>
                            <span class="activity-group">{activity['group'].split('/')[-1]}</span>
                            <span class="activity-time">{activity_time}</span>
                        </div>
                    </div>
                    <div class="activity-content">{activity['content']}</div>
                </div>"""
        
        html_content += """
            </div>
        </div>"""
    else:
        html_content += """
        <div class="section">
            <h2>📊 Recent Activity</h2>
            <p style="text-align: center; color: #64748b; padding: 40px;">No recent activity detected in monitored groups</p>
        </div>"""
    
    # Active Groups Section
    if active_groups:
        html_content += f"""
        <div class="section">
            <h2>🔥 Most Active Groups</h2>
            <div class="groups-grid">"""
        
        for group in active_groups[:12]:  # Show top 12 active groups
            activity_class = f"activity-{group['activity_level'].lower()}"
            
            html_content += f"""
                <div class="group-card">
                    <div class="group-name">{group['group']}</div>
                    <div class="group-stats">
                        <span>{group['recent_messages']} messages • {group['unique_users']} users</span>
                        <span class="activity-level {activity_class}">{group['activity_level']}</span>
                    </div>
                    <div style="color: #64748b; font-size: 0.9em;">
                        Ship: {group['ship']}
                    </div>
                </div>"""
        
        html_content += """
            </div>
        </div>"""
    
    # AI Insights Section
    if ai_insights:
        html_content += f"""
        <div class="section">
            <h2>🧠 Latest AI Insights</h2>
            <div class="ai-insights">"""
        
        for insight in ai_insights:
            html_content += f"""
                <div class="insight-card">
                    <div class="insight-group">{insight['group']}</div>
                    <div class="insight-text">{insight['insight']}</div>"""
            
            if insight.get('key_topics'):
                html_content += f"""
                    <div class="insight-topics">
                        {''.join(f'<span class="topic-tag">{topic}</span>' for topic in insight['key_topics'][:3])}
                    </div>"""
            
            html_content += """
                </div>"""
        
        html_content += """
            </div>
        </div>"""
    
    # Current Monitoring Section
    html_content += f"""
        <div class="section">
            <h2>📈 Currently Monitoring ({len(config.MONITORED_GROUPS)} Groups)</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 10px;">"""
    
    for group in config.MONITORED_GROUPS:
        is_active = any(ag['group'] == group for ag in active_groups)
        status_class = "activity-high" if is_active else "activity-low"
        status_text = "Active" if is_active else "Monitoring"
        
        html_content += f"""
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; font-family: 'Monaco', 'Menlo', monospace; font-size: 0.85em;">
                    {group}
                    <span class="activity-level {status_class}" style="float: right;">{status_text}</span>
                </div>"""
    
    html_content += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 Urbit AI Analytics Dashboard | 
            <a href="https://github.com/kh0pper/urbit-analytics" target="_blank">View on GitHub</a> | 
            Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Monitoring {len(config.MONITORED_GROUPS)} groups • Discovered {discovery_data.get('total_discovered', 0)} total groups</p>
        </div>
    </div>
</body>
</html>"""
    
    with open('dashboard/index.html', 'w') as f:
        f.write(html_content)

def create_activity_api(recent_activity, active_groups, ai_insights):
    """Create API endpoint for activity data"""
    
    activity_api = {
        "recent_activity": recent_activity,
        "active_groups": active_groups,
        "ai_insights": ai_insights,
        "last_updated": datetime.now().isoformat(),
        "total_activities": len(recent_activity),
        "total_active_groups": len(active_groups)
    }
    
    with open('dashboard/activity.json', 'w') as f:
        json.dump(activity_api, f, indent=2)

def create_stats_api(network_stats, discovery_data):
    """Create API endpoint for statistics"""
    
    stats_api = {
        "network_stats": network_stats,
        "discovery_stats": discovery_data,
        "monitoring": {
            "total_groups": len(config.MONITORED_GROUPS),
            "groups": config.MONITORED_GROUPS
        },
        "system_status": "operational",
        "last_updated": datetime.now().isoformat()
    }
    
    with open('dashboard/stats.json', 'w') as f:
        json.dump(stats_api, f, indent=2)

if __name__ == "__main__":
    create_enhanced_dashboard()