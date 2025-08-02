"""
Main application for Urbit AI Analytics & Monitoring System
"""
import asyncio
import schedule
import time
import logging
from datetime import datetime
from typing import List, Dict
import json
import traceback

from urbit_client import UrbitClient
from ai_analyzer import AIAnalyzer  
from data_collector import DataCollector
from group_discovery import GroupDiscovery
from dynamic_config_manager import DynamicConfigManager
from fixed_messaging import FixedUrbitMessenger
from github_uploader import GitHubUploader
import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UrbitAnalyticsMonitor:
    def __init__(self):
        self.urbit_client = None
        self.ai_analyzer = AIAnalyzer()
        self.data_collector = DataCollector(config.DATA_DIR)
        self.group_discovery = GroupDiscovery()
        self.config_manager = DynamicConfigManager()
        self.messenger = FixedUrbitMessenger()
        self.github_uploader = GitHubUploader()
        self.is_running = False
        self.monitored_targets = []  # Dynamic list of groups/channels
        
    def initialize(self) -> bool:
        """Initialize connections and verify configuration"""
        logger.info("Initializing Urbit AI Analytics Monitor...")
        
        # Check configuration
        if not config.LLAMA_API_KEY:
            logger.error("LLAMA_API_KEY not configured")
            return False
            
        if not config.URBIT_SHIP_URL or not config.URBIT_SESSION_COOKIE:
            logger.error("Urbit connection parameters not configured")
            return False
        
        # Initialize Urbit client
        try:
            self.urbit_client = UrbitClient(
                config.URBIT_SHIP_URL,
                config.URBIT_SESSION_COOKIE
            )
            
            if not self.urbit_client.authenticate():
                logger.error("Failed to authenticate with Urbit ship")
                return False
                
            logger.info("Successfully connected to Urbit ship")
            
        except Exception as e:
            logger.error(f"Failed to initialize Urbit client: {e}")
            return False
        
        # Test AI analyzer
        try:
            # Quick test call
            test_activities = [{
                'author': '~test-ship',
                'content': 'Test message for AI analyzer',
                'timestamp': datetime.now().isoformat(),
                'type': 'message'
            }]
            
            test_result = self.ai_analyzer.analyze_group_activity(
                "test-group", test_activities, 1
            )
            
            if 'ai_analysis' in test_result:
                logger.info("AI Analyzer working correctly")
            else:
                logger.warning("AI Analyzer test returned unexpected result")
                
        except Exception as e:
            logger.error(f"AI Analyzer test failed: {e}")
            # Continue anyway - non-critical for startup
        
        return True
    
    def refresh_monitored_targets(self):
        """Dynamically discover and update the list of monitored groups/channels"""
        logger.info("🔍 Refreshing monitored targets...")
        
        try:
            # Discover all available groups
            discovered_groups = self.group_discovery.discover_all_groups()
            logger.info(f"🌐 Discovered {len(discovered_groups)} total groups on network")
            
            # Auto-add promising new groups to config
            if discovered_groups:
                auto_added = self.config_manager.filter_and_add_promising_groups(discovered_groups)
                if auto_added:
                    logger.info(f"➕ Auto-added {len(auto_added)} promising groups to monitoring")
                    
                    # Reload config to get updated groups
                    import importlib
                    importlib.reload(config)
            
            # Get all current groups and channels (including newly added ones)
            new_targets = self.group_discovery.get_all_monitorable_targets()
            
            # Check for new targets
            added_targets = set(new_targets) - set(self.monitored_targets)
            removed_targets = set(self.monitored_targets) - set(new_targets)
            
            if added_targets:
                logger.info(f"➕ Found {len(added_targets)} new targets: {list(added_targets)[:3]}{'...' if len(added_targets) > 3 else ''}")
                
            if removed_targets:
                logger.info(f"➖ Removed {len(removed_targets)} targets: {list(removed_targets)[:3]}{'...' if len(removed_targets) > 3 else ''}")
            
            # Update the monitored list
            self.monitored_targets = new_targets
            
            # Save discovery results for reference
            self.group_discovery.save_discovery_results("data/latest_discovery.json")
            
            # Show discovery stats
            stats = self.config_manager.get_discovery_stats()
            logger.info(f"📊 Discovery stats: {stats['total_discovered']} discovered, {stats['auto_added']} auto-added, {len(self.monitored_targets)} monitoring")
            
        except Exception as e:
            logger.error(f"Error refreshing monitored targets: {e}")
            # Fallback to config file groups if discovery fails
            if not self.monitored_targets:
                self.monitored_targets = config.MONITORED_GROUPS
                logger.info(f"Using fallback groups from config: {len(self.monitored_targets)} groups")
    
    def monitor_groups(self):
        """Monitor all configured groups and collect activity data"""
        # Refresh targets periodically (every hour during monitoring)
        if not self.monitored_targets or datetime.now().minute == 0:
            self.refresh_monitored_targets()
        
        targets_to_monitor = self.monitored_targets or config.MONITORED_GROUPS
        logger.info(f"Starting group monitoring cycle for {len(targets_to_monitor)} targets")
        
        for group_path in targets_to_monitor:
            try:
                logger.info(f"Monitoring group: {group_path}")
                
                # Get recent activity
                activities = self.urbit_client.get_group_activity(
                    group_path, 
                    config.ACTIVITY_LOOKBACK_HOURS
                )
                
                logger.info(f"Found {len(activities)} activities in {group_path}")
                
                # Store raw activity data
                self.data_collector.store_group_activity(group_path, activities)
                
                # Analyze if we have enough activity
                if len(activities) >= config.MIN_MESSAGES_FOR_ANALYSIS:
                    logger.info(f"Analyzing activity for {group_path}")
                    
                    analysis = self.ai_analyzer.analyze_group_activity(
                        group_path,
                        activities,
                        config.ACTIVITY_LOOKBACK_HOURS
                    )
                    
                    # Store analysis results
                    self.data_collector.store_analysis_result(group_path, analysis)
                    
                    logger.info(f"Analysis completed for {group_path}")
                    
                else:
                    logger.info(f"Insufficient activity in {group_path} for analysis ({len(activities)} messages)")
                
                # Small delay between groups to be respectful
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error monitoring group {group_path}: {e}")
                logger.error(traceback.format_exc())
    
    def generate_and_send_report(self):
        """Generate AI analysis report and send to configured recipient"""
        logger.info("Generating comprehensive report...")
        
        try:
            # Collect analyses from all groups
            group_analyses = []
            
            targets_to_analyze = self.monitored_targets or config.MONITORED_GROUPS
            for group_path in targets_to_analyze:
                recent_activities = self.data_collector.get_recent_activity(
                    group_path,
                    config.ACTIVITY_LOOKBACK_HOURS
                )
                
                if len(recent_activities) >= config.MIN_MESSAGES_FOR_ANALYSIS:
                    analysis = self.ai_analyzer.analyze_group_activity(
                        group_path,
                        recent_activities,
                        config.ACTIVITY_LOOKBACK_HOURS
                    )
                    group_analyses.append(analysis)
            
            if not group_analyses:
                logger.info("No activity to report")
                return
            
            # Generate comprehensive summary
            summary_report = self.ai_analyzer.generate_comprehensive_summary(group_analyses)
            
            # Add network overview
            network_stats = self.data_collector.get_network_overview()
            
            full_report = f"""🤖 **Urbit Network Analytics Report**
📊 **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📈 **Monitoring**: {network_stats['total_groups_monitored']} groups ({network_stats['active_groups_24h']} active)

{summary_report}

---
*Powered by AI Analytics & Monitoring System*
*Total activities analyzed: {network_stats['total_activities_collected']}*
"""
            
            # Save report
            report_path = self.data_collector.save_report(full_report, "daily")
            logger.info(f"Report saved to: {report_path}")
            
            # Display report in terminal (since Urbit messaging has issues)
            print("\n" + "="*80)
            print("📊 URBIT AI ANALYTICS REPORT")
            print("="*80)
            print(full_report)
            print("="*80)
            print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("📁 Full report saved to:", report_path)
            print("="*80 + "\n")
            
            # Try to send to Urbit ship using the improved messaging system
            if config.URBIT_RECIPIENT_SHIP:
                try:
                    # Create a concise version for messaging
                    concise_report = f"""🤖 **Urbit AI Analytics Report**

📊 **Generated**: {datetime.now().strftime('%H:%M')}
📈 **Network**: {network_stats['active_groups_24h']} active groups
🔍 **Activities**: {network_stats['total_activities_collected']} analyzed

{summary_report[:300]}...

📁 **Full Report**: Check data/reports/ folder
🚀 **Status**: System operational

*Auto-generated by AI Analytics*"""

                    success = self.messenger.comprehensive_fixed_delivery(concise_report)
                    
                    if success:
                        logger.info(f"Report successfully delivered to {config.URBIT_RECIPIENT_SHIP}")
                        print(f"✅ Report delivered to your Urbit ship!")
                    else:
                        logger.info(f"Report saved locally for manual delivery to {config.URBIT_RECIPIENT_SHIP}")
                        print(f"📁 Report saved for manual delivery - check data/pending_messages/")
                        
                except Exception as e:
                    logger.warning(f"Messaging system error: {e} - report displayed above")
            
            # Upload to GitHub if configured
            try:
                github_setup = self.github_uploader.check_setup()
                if github_setup['repo_accessible']:
                    logger.info("📤 Uploading report to GitHub...")
                    
                    # Upload the full report
                    if self.github_uploader.upload_report(report_path, full_report):
                        logger.info("✅ Report uploaded to GitHub successfully")
                        print(f"🌐 Report available at: https://github.com/{self.github_uploader.repo_owner}/{self.github_uploader.repo_name}")
                    
                    # Upload analytics summary
                    stats = self.data_collector.get_network_overview()
                    discovery_stats = self.config_manager.get_discovery_stats()
                    combined_stats = {**stats, **discovery_stats}
                    
                    self.github_uploader.upload_analytics_summary(combined_stats)
                    
                    # Upload discovery log
                    discovery_log = self.config_manager.load_discovery_log()
                    self.github_uploader.upload_discovery_log(discovery_log)
                    
                    # Update web dashboard
                    self.github_uploader.create_web_dashboard()
                    
                    print(f"📊 Analytics dashboard updated: https://{self.github_uploader.repo_owner}.github.io/{self.github_uploader.repo_name}/dashboard/")
                    
                else:
                    logger.info("GitHub not configured - skipping upload")
                    
            except Exception as e:
                logger.warning(f"GitHub upload error: {e}")
                print("⚠️ GitHub upload failed - reports saved locally")
            
            logger.info("Report generation completed")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            logger.error(traceback.format_exc())
    
    def run_analytics_cycle(self):
        """Run a complete analytics cycle"""
        logger.info("=== Starting Analytics Cycle ===")
        
        try:
            # Monitor groups and collect data
            self.monitor_groups()
            
            # Generate and send report
            self.generate_and_send_report()
            
            # Cleanup old data (once daily)
            if datetime.now().hour == 3:  # 3 AM cleanup
                logger.info("Running daily data cleanup...")
                self.data_collector.cleanup_old_data(days_to_keep=30)
            
            logger.info("=== Analytics Cycle Complete ===")
            
        except Exception as e:
            logger.error(f"Error in analytics cycle: {e}")
            logger.error(traceback.format_exc())
    
    def start_monitoring(self):
        """Start the monitoring system with scheduled runs"""
        if not self.initialize():
            logger.error("Failed to initialize monitoring system")
            return False
        
        logger.info("Starting Urbit AI Analytics Monitoring System...")
        logger.info(f"Monitoring {len(config.MONITORED_GROUPS)} groups")
        logger.info(f"Analysis interval: {config.ANALYSIS_INTERVAL_MINUTES} minutes")
        logger.info(f"Lookback period: {config.ACTIVITY_LOOKBACK_HOURS} hours")
        
        # Schedule regular monitoring
        schedule.every(config.ANALYSIS_INTERVAL_MINUTES).minutes.do(self.run_analytics_cycle)
        
        # Schedule daily comprehensive report
        schedule.every().day.at("09:00").do(self.generate_and_send_report)
        
        # Run initial cycle
        self.run_analytics_cycle()
        
        self.is_running = True
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            self.stop_monitoring()
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        logger.info("Stopping monitoring system...")
        self.is_running = False
        
        if self.urbit_client:
            self.urbit_client.close_channel()
        
        logger.info("Monitoring system stopped")
    
    def get_status(self) -> Dict:
        """Get current status of the monitoring system"""
        network_stats = self.data_collector.get_network_overview()
        
        return {
            "is_running": self.is_running,
            "monitored_groups": config.MONITORED_GROUPS,
            "analysis_interval": config.ANALYSIS_INTERVAL_MINUTES,
            "network_stats": network_stats,
            "next_scheduled_run": str(schedule.next_run()) if schedule.jobs else None
        }

def main():
    """Main entry point"""
    print("🤖 Urbit AI Analytics & Monitoring System")
    print("=" * 50)
    
    monitor = UrbitAnalyticsMonitor()
    
    # Command line interface
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            status = monitor.get_status()
            print(json.dumps(status, indent=2))
            return
            
        elif command == "test":
            print("Running system test...")
            if monitor.initialize():
                print("✅ System test passed")
                monitor.run_analytics_cycle()
            else:
                print("❌ System test failed")
            return
            
        elif command == "export":
            print("Exporting data...")
            collector = DataCollector(config.DATA_DIR)
            export_file = collector.export_data()
            print(f"Data exported to: {export_file}")
            return
    
    # Default: start monitoring
    try:
        monitor.start_monitoring()
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    main()