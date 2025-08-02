#!/usr/bin/env python3
"""
GitHub Repository Uploader for Urbit Analytics Reports
Automatically uploads reports to GitHub for remote viewing
"""
import os
import json
import base64
import requests
from datetime import datetime
from typing import Optional, Dict, List
import config

class GitHubUploader:
    def __init__(self, github_token: str = None, repo_owner: str = None, repo_name: str = None):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.repo_owner = repo_owner or os.environ.get("GITHUB_REPO_OWNER")
        self.repo_name = repo_name or os.environ.get("GITHUB_REPO_NAME", "urbit-analytics")
        
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        
        if self.github_token:
            self.session.headers.update({
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Urbit-AI-Analytics/1.0'
            })
    
    def check_setup(self) -> Dict[str, bool]:
        """Check if GitHub setup is complete"""
        setup_status = {
            'token_provided': bool(self.github_token),
            'repo_owner_provided': bool(self.repo_owner),
            'repo_name_provided': bool(self.repo_name),
            'repo_exists': False,
            'repo_accessible': False
        }
        
        if all([self.github_token, self.repo_owner, self.repo_name]):
            try:
                repo_url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}"
                response = self.session.get(repo_url)
                
                if response.status_code == 200:
                    setup_status['repo_exists'] = True
                    setup_status['repo_accessible'] = True
                elif response.status_code == 404:
                    setup_status['repo_exists'] = False
                    setup_status['repo_accessible'] = False
                else:
                    setup_status['repo_accessible'] = False
                    
            except Exception as e:
                print(f"Error checking repository: {e}")
        
        return setup_status
    
    def create_repository(self) -> bool:
        """Create a new GitHub repository for analytics"""
        if not self.github_token:
            print("❌ GitHub token required to create repository")
            return False
        
        print(f"🔧 Creating GitHub repository: {self.repo_name}")
        
        repo_data = {
            "name": self.repo_name,
            "description": "Urbit AI Analytics Reports - Automated analytics and insights from Urbit network monitoring",
            "private": False,  # Set to True if you want private repo
            "auto_init": True,
            "gitignore_template": "Python"
        }
        
        try:
            if self.repo_owner:
                # Creating in organization
                create_url = f"{self.base_url}/orgs/{self.repo_owner}/repos"
            else:
                # Creating in user account
                create_url = f"{self.base_url}/user/repos"
                # Get username for repo_owner
                user_response = self.session.get(f"{self.base_url}/user")
                if user_response.status_code == 200:
                    self.repo_owner = user_response.json()['login']
                else:
                    print("❌ Could not get user information")
                    return False
            
            response = self.session.post(create_url, json=repo_data)
            
            if response.status_code == 201:
                print(f"✅ Repository created: https://github.com/{self.repo_owner}/{self.repo_name}")
                
                # Create initial README
                self.create_initial_readme()
                return True
            else:
                print(f"❌ Failed to create repository: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error creating repository: {e}")
            return False
    
    def create_initial_readme(self):
        """Create an initial README for the repository"""
        readme_content = f"""# Urbit AI Analytics Reports

This repository contains automated analytics and insights from Urbit network monitoring.

## 📊 Analytics System

- **Real-time monitoring** of {len(config.MONITORED_GROUPS)} Urbit groups/channels
- **AI-powered analysis** using Llama API for intelligent insights
- **Automatic group discovery** and monitoring expansion
- **Comprehensive reporting** with network health assessments

## 📁 Repository Structure

```
/
├── reports/           # Analytics reports (Markdown format)
├── data/             # Raw data and statistics
├── insights/         # AI-generated insights and summaries
└── dashboard/        # Web dashboard files (coming soon)
```

## 🤖 Automated Updates

This repository is automatically updated by the Urbit AI Analytics system:
- New reports generated every hour
- AI insights uploaded when significant activity detected
- Network statistics updated daily
- Discovery logs maintained for transparency

## 📈 Latest Analytics

<!-- AUTO-GENERATED CONTENT BELOW -->
*Reports will appear here automatically as the system runs*

---
*Generated by Urbit AI Analytics System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        self.upload_file("README.md", readme_content, "Initialize Urbit Analytics repository")
    
    def upload_file(self, file_path: str, content: str, commit_message: str = None) -> bool:
        """Upload a file to the GitHub repository"""
        if not all([self.github_token, self.repo_owner, self.repo_name]):
            print("❌ GitHub configuration incomplete")
            return False
        
        if not commit_message:
            commit_message = f"Update {file_path} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        try:
            # Check if file exists to get SHA for update
            file_url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            existing_response = self.session.get(file_url)
            
            file_data = {
                "message": commit_message,
                "content": base64.b64encode(content.encode('utf-8')).decode('utf-8')
            }
            
            # If file exists, include SHA for update
            if existing_response.status_code == 200:
                existing_file = existing_response.json()
                file_data["sha"] = existing_file["sha"]
            
            response = self.session.put(file_url, json=file_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ Uploaded: {file_path}")
                return True
            else:
                print(f"❌ Failed to upload {file_path}: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            return False
    
    def upload_report(self, report_file_path: str, report_content: str = None) -> bool:
        """Upload an analytics report to GitHub"""
        try:
            # Read report content if not provided
            if report_content is None:
                with open(report_file_path, 'r') as f:
                    report_content = f.read()
            
            # Extract filename and create GitHub path
            filename = os.path.basename(report_file_path)
            github_path = f"reports/{filename}"
            
            # Create commit message
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            commit_message = f"📊 Analytics Report: {filename} - {timestamp}"
            
            return self.upload_file(github_path, report_content, commit_message)
            
        except Exception as e:
            print(f"❌ Error uploading report {report_file_path}: {e}")
            return False
    
    def upload_analytics_summary(self, stats: Dict) -> bool:
        """Upload current analytics statistics"""
        summary_content = f"""# Urbit Analytics Summary

**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Current Statistics

- **Groups Discovered**: {stats.get('total_discovered', 0)}
- **Groups Monitoring**: {stats.get('currently_monitoring', 0)}
- **Auto-Added Groups**: {stats.get('auto_added', 0)}
- **Total Activities**: {stats.get('total_activities_collected', 0)}
- **Active Groups (24h)**: {stats.get('active_groups_24h', 0)}

## 🔍 Latest Discovery

{stats.get('last_discovery', 'No discoveries yet')}

## 📈 Monitoring Targets

Currently monitoring **{len(config.MONITORED_GROUPS)}** channels:

"""
        
        # Add monitored groups list
        for i, group in enumerate(config.MONITORED_GROUPS[:10], 1):  # Show first 10
            summary_content += f"{i}. `{group}`\n"
        
        if len(config.MONITORED_GROUPS) > 10:
            summary_content += f"\n*...and {len(config.MONITORED_GROUPS) - 10} more groups*\n"
        
        summary_content += f"""
## 🤖 System Status

✅ **Operational** - All systems running normally

- AI Analysis: Llama API integrated
- Group Discovery: Active scanning
- Report Generation: Automated every 60 minutes
- Data Collection: Real-time monitoring

---
*Auto-generated by Urbit AI Analytics System*
"""
        
        commit_message = f"📈 Update analytics summary - {datetime.now().strftime('%H:%M:%S')}"
        return self.upload_file("data/analytics_summary.md", summary_content, commit_message)
    
    def upload_discovery_log(self, discovery_data: Dict) -> bool:
        """Upload discovery log data"""
        log_content = f"""# Group Discovery Log

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Discovery Statistics

```json
{json.dumps(discovery_data, indent=2, default=str)}
```

## Recent Discoveries

"""
        
        # Add discovery history
        history = discovery_data.get('discovery_history', [])
        for entry in history[-5:]:  # Last 5 entries
            timestamp = entry.get('timestamp', 'Unknown')
            total = entry.get('total_discovered', 0)
            new = entry.get('new_groups', 0)
            added = entry.get('auto_added', 0)
            
            log_content += f"- **{timestamp}**: {total} total, {new} new, {added} auto-added\n"
        
        log_content += "\n---\n*Auto-generated discovery log*"
        
        commit_message = f"🔍 Update discovery log - {datetime.now().strftime('%H:%M:%S')}"
        return self.upload_file("data/discovery_log.md", log_content, commit_message)
    
    def create_web_dashboard(self) -> bool:
        """Create a simple web dashboard for viewing reports"""
        dashboard_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Urbit AI Analytics Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; 
                     border-radius: 8px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
        .status {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                 gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007acc; }}
        .reports-list {{ margin-top: 30px; }}
        .report-item {{ background: #fff; border: 1px solid #ddd; padding: 10px; 
                       margin: 10px 0; border-radius: 5px; }}
        a {{ color: #007acc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Urbit AI Analytics Dashboard</h1>
        
        <div class="status">
            <strong>🚀 System Status:</strong> Operational | 
            <strong>📊 Last Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |
            <strong>🔍 Monitoring:</strong> {len(config.MONITORED_GROUPS)} channels
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">96+</div>
                <div>Groups Discovered</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(config.MONITORED_GROUPS)}</div>
                <div>Channels Monitored</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">24/7</div>
                <div>Monitoring Active</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">AI</div>
                <div>Powered Analysis</div>
            </div>
        </div>
        
        <h2>📊 Latest Reports</h2>
        <div class="reports-list">
            <div class="report-item">
                <strong><a href="https://github.com/{self.repo_owner}/{self.repo_name}/tree/main/reports" target="_blank">📁 View All Reports</a></strong> - 
                Complete analytics reports generated automatically
            </div>
            <div class="report-item">
                <strong><a href="https://github.com/{self.repo_owner}/{self.repo_name}/blob/main/data/analytics_summary.md" target="_blank">📈 Analytics Summary</a></strong> - 
                Current system statistics and status
            </div>
            <div class="report-item">
                <strong><a href="https://github.com/{self.repo_owner}/{self.repo_name}/blob/main/data/discovery_log.md" target="_blank">🔍 Discovery Log</a></strong> - 
                History of group discoveries and additions
            </div>
        </div>
        
        <h2>🤖 About This System</h2>
        <p>This dashboard shows real-time analytics from an AI-powered Urbit network monitoring system. 
           The system automatically discovers groups, monitors activity, and generates intelligent insights 
           using advanced AI analysis.</p>
           
        <p><strong>Features:</strong></p>
        <ul>
            <li>Real-time monitoring of {len(config.MONITORED_GROUPS)} Urbit channels</li>
            <li>AI-powered content analysis and insights</li>
            <li>Automatic group discovery and expansion</li>
            <li>Comprehensive reporting every hour</li>
            <li>Network health assessments</li>
        </ul>
        
        <hr>
        <p><em>Dashboard auto-updated by Urbit AI Analytics System - 
           <a href="https://github.com/{self.repo_owner}/{self.repo_name}">View on GitHub</a></em></p>
    </div>
</body>
</html>"""
        
        commit_message = f"🌐 Update web dashboard - {datetime.now().strftime('%H:%M:%S')}"
        return self.upload_file("dashboard/index.html", dashboard_html, commit_message)

def setup_github_integration():
    """Interactive setup for GitHub integration"""
    print("🔧 GITHUB INTEGRATION SETUP")
    print("=" * 50)
    
    print("\n📋 To set up GitHub integration, you'll need:")
    print("1. A GitHub account")
    print("2. A GitHub Personal Access Token")
    print("3. Repository name (will create if it doesn't exist)")
    
    print("\n🔑 GitHub Personal Access Token:")
    print("   1. Go to https://github.com/settings/tokens")
    print("   2. Click 'Generate new token (classic)'")
    print("   3. Select these scopes: 'repo', 'user'")
    print("   4. Copy the generated token")
    
    # Check if token exists in environment
    existing_token = os.environ.get("GITHUB_TOKEN")
    if existing_token:
        print(f"\n✅ Found existing GitHub token in environment")
        use_existing = input("Use existing token? (y/n): ").lower().strip() == 'y'
        if not use_existing:
            existing_token = None
    
    if not existing_token:
        token = input("\n🔑 Enter your GitHub token: ").strip()
        if not token:
            print("❌ Token required for GitHub integration")
            return None
    else:
        token = existing_token
    
    # Get repository details
    repo_name = input("\n📁 Repository name (default: urbit-analytics): ").strip() or "urbit-analytics"
    
    # Initialize uploader
    uploader = GitHubUploader(github_token=token, repo_name=repo_name)
    
    # Check setup
    setup_status = uploader.check_setup()
    
    print(f"\n📊 Setup Status:")
    for key, status in setup_status.items():
        icon = "✅" if status else "❌"
        print(f"   {icon} {key.replace('_', ' ').title()}: {status}")
    
    # Create repository if needed
    if not setup_status['repo_exists'] and setup_status['token_provided']:
        create_repo = input(f"\n🔧 Create repository '{repo_name}'? (y/n): ").lower().strip() == 'y'
        if create_repo:
            if uploader.create_repository():
                print(f"✅ Repository created successfully!")
                print(f"🌐 View at: https://github.com/{uploader.repo_owner}/{uploader.repo_name}")
            else:
                print("❌ Failed to create repository")
                return None
    
    # Save configuration to .env file
    env_updates = f"""
# GitHub Integration
GITHUB_TOKEN={token}
GITHUB_REPO_OWNER={uploader.repo_owner}
GITHUB_REPO_NAME={repo_name}
"""
    
    try:
        with open('.env', 'a') as f:
            f.write(env_updates)
        print(f"\n✅ Configuration saved to .env file")
    except Exception as e:
        print(f"⚠️ Could not save to .env: {e}")
        print("💡 Manually add these environment variables:")
        print(env_updates)
    
    return uploader

def test_github_upload():
    """Test GitHub upload functionality"""
    print("🧪 TESTING GITHUB UPLOAD")
    print("=" * 40)
    
    # Try to load from environment first
    uploader = GitHubUploader()
    
    # Check if setup is complete
    setup_status = uploader.check_setup()
    
    if not all([setup_status['token_provided'], setup_status['repo_accessible']]):
        print("⚠️ GitHub not configured. Running setup...")
        uploader = setup_github_integration()
        if not uploader:
            return False
    
    print(f"\n📤 Testing upload to: {uploader.repo_owner}/{uploader.repo_name}")
    
    # Test uploads
    test_results = []
    
    # 1. Test basic file upload
    test_content = f"""# Test Upload

This is a test upload from the Urbit AI Analytics system.

**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Test ID**: github-upload-test

✅ GitHub integration working correctly!
"""
    
    result1 = uploader.upload_file("test/upload_test.md", test_content)
    test_results.append(("Basic file upload", result1))
    
    # 2. Test analytics summary upload
    from dynamic_config_manager import DynamicConfigManager
    config_manager = DynamicConfigManager()
    stats = config_manager.get_discovery_stats()
    
    result2 = uploader.upload_analytics_summary(stats)
    test_results.append(("Analytics summary", result2))
    
    # 3. Test web dashboard
    result3 = uploader.create_web_dashboard()
    test_results.append(("Web dashboard", result3))
    
    # Show results
    print(f"\n📊 Test Results:")
    for test_name, success in test_results:
        icon = "✅" if success else "❌"
        print(f"   {icon} {test_name}")
    
    if all(result for _, result in test_results):
        print(f"\n🎉 GitHub integration fully operational!")
        print(f"🌐 View your analytics at: https://github.com/{uploader.repo_owner}/{uploader.repo_name}")
        print(f"📊 Dashboard: https://{uploader.repo_owner}.github.io/{uploader.repo_name}/dashboard/")
        return True
    else:
        print(f"\n⚠️ Some tests failed. Check configuration and try again.")
        return False

if __name__ == "__main__":
    success = test_github_upload()
    
    if success:
        print(f"\n🚀 GitHub integration ready!")
        print(f"💡 Your analytics reports will now be automatically uploaded to GitHub")
    else:
        print(f"\n🔧 Setup GitHub integration first")