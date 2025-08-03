#!/usr/bin/env python3
"""
Simplified Urbit AI Analytics & Monitoring System
Clean, focused implementation for monitoring Urbit groups
"""
import time
import logging
import sys
import json
from datetime import datetime
from typing import List, Dict

from src.urbit_client import UrbitClient
from src.ai_analyzer import AIAnalyzer  
from src.data_collector import DataCollector
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/urbit_analytics.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UrbitAnalyticsApp:
    """Simplified Urbit Analytics Application"""
    
    def __init__(self):
        self.urbit_client = None
        self.ai_analyzer = AIAnalyzer()
        self.data_collector = DataCollector(config.DATA_DIR)
        self.is_running = False
        
    def initialize(self) -> bool:
        """Initialize the application"""
        logger.info("🚀 Initializing Urbit AI Analytics...")
        
        # Check configuration
        if not config.LLAMA_API_KEY:
            logger.error("❌ LLAMA_API_KEY not configured")
            return False
            
        if not config.URBIT_SHIP_URL or not config.URBIT_SESSION_COOKIE:
            logger.error("❌ Urbit connection parameters not configured")
            return False
        
        # Initialize Urbit client
        try:
            self.urbit_client = UrbitClient(
                config.URBIT_SHIP_URL,
                config.URBIT_SESSION_COOKIE
            )
            
            if self.urbit_client.authenticate():
                logger.info("✅ Connected to Urbit ship")
                return True
            else:
                logger.error("❌ Failed to authenticate with Urbit ship")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Urbit client: {e}")
            return False
    
    def monitor_groups(self) -> Dict:
        """Monitor all configured groups and collect activity"""
        logger.info(f"📊 Monitoring {len(config.MONITORED_GROUPS)} groups...")
        
        total_activities = 0
        active_groups = 0
        group_analyses = []
        
        for group_path in config.MONITORED_GROUPS:
            try:
                logger.info(f"🔍 Checking: {group_path}")
                
                # Get recent activity
                activities = self.urbit_client.get_group_activity(
                    group_path, 
                    config.ACTIVITY_LOOKBACK_HOURS
                )
                
                total_activities += len(activities)
                
                if activities:
                    active_groups += 1
                    logger.info(f"  📈 {len(activities)} activities found")
                    
                    # Store activity data
                    self.data_collector.store_group_activity(group_path, activities)
                    
                    # Analyze if enough activity
                    if len(activities) >= config.MIN_MESSAGES_FOR_ANALYSIS:
                        analysis = self.ai_analyzer.analyze_group_activity(
                            group_path, activities, config.ACTIVITY_LOOKBACK_HOURS
                        )
                        group_analyses.append(analysis)
                        self.data_collector.store_analysis_result(group_path, analysis)
                        logger.info(f"  🧠 Analysis completed")
                else:
                    logger.info(f"  💤 No recent activity")
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                logger.error(f"❌ Error monitoring {group_path}: {e}")
        
        return {
            'total_activities': total_activities,
            'active_groups': active_groups,
            'total_groups': len(config.MONITORED_GROUPS),
            'analyses': group_analyses
        }
    
    def generate_report(self, monitoring_results: Dict) -> str:
        """Generate a comprehensive analytics report"""
        logger.info("📝 Generating report...")
        
        # Generate AI summary if we have analyses
        ai_summary = ""
        if monitoring_results['analyses']:
            try:
                ai_summary = self.ai_analyzer.generate_comprehensive_summary(
                    monitoring_results['analyses']
                )
            except Exception as e:
                logger.warning(f"AI summary generation failed: {e}")
                ai_summary = "AI analysis unavailable"
        
        # Create report
        report = f"""🤖 **Urbit AI Analytics Report**

📊 **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📈 **Network Status**: {monitoring_results['active_groups']}/{monitoring_results['total_groups']} groups active
🔍 **Activities Collected**: {monitoring_results['total_activities']} messages

## 🧠 AI Analysis Summary

{ai_summary if ai_summary else 'No significant activity to analyze'}

## 📊 Monitoring Statistics

- **Total Groups Monitored**: {monitoring_results['total_groups']}
- **Active Groups (24h)**: {monitoring_results['active_groups']}
- **Total Activities**: {monitoring_results['total_activities']}
- **Analyses Generated**: {len(monitoring_results['analyses'])}

## 📋 Monitored Groups

"""
        
        for i, group in enumerate(config.MONITORED_GROUPS, 1):
            report += f"{i:2d}. `{group}`\n"
        
        report += f"""
---
*Generated by Urbit AI Analytics System*
*{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return report
    
    def run_analysis_cycle(self):
        """Run a complete monitoring and analysis cycle"""
        logger.info("🔄 Starting analysis cycle...")
        
        # Monitor all groups
        results = self.monitor_groups()
        
        # Generate report
        report = self.generate_report(results)
        
        # Save report
        report_file = self.data_collector.save_report(report, "cycle")
        logger.info(f"📁 Report saved: {report_file}")
        
        # Display report
        print("\n" + "="*60)
        print("📊 URBIT AI ANALYTICS REPORT")
        print("="*60)
        print(report)
        print("="*60 + "\n")
        
        logger.info("✅ Analysis cycle complete")
        return results
    
    def test_system(self):
        """Test system functionality"""
        print("🧪 Testing Urbit AI Analytics System...")
        
        if not self.initialize():
            print("❌ Initialization failed")
            return False
        
        print("✅ Initialization successful")
        
        # Test monitoring
        try:
            results = self.run_analysis_cycle()
            print(f"✅ Monitoring test complete: {results['active_groups']} active groups")
            return True
        except Exception as e:
            print(f"❌ Monitoring test failed: {e}")
            return False
    
    def start_continuous_monitoring(self):
        """Start continuous monitoring with periodic reports"""
        if not self.initialize():
            return False
        
        logger.info("🚀 Starting continuous monitoring...")
        logger.info(f"📊 Monitoring {len(config.MONITORED_GROUPS)} groups")
        logger.info(f"⏰ Analysis interval: {config.ANALYSIS_INTERVAL_MINUTES} minutes")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Run analysis cycle
                self.run_analysis_cycle()
                
                # Wait for next cycle
                logger.info(f"⏳ Waiting {config.ANALYSIS_INTERVAL_MINUTES} minutes for next cycle...")
                
                for _ in range(config.ANALYSIS_INTERVAL_MINUTES * 60):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Received shutdown signal")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the monitoring system"""
        logger.info("🛑 Stopping monitoring system...")
        self.is_running = False
        
        if self.urbit_client:
            # Clean shutdown
            pass
        
        logger.info("✅ System stopped")
    
    def get_status(self):
        """Get current system status"""
        status = {
            "system": "Urbit AI Analytics",
            "running": self.is_running,
            "monitored_groups": len(config.MONITORED_GROUPS),
            "groups": config.MONITORED_GROUPS,
            "config": {
                "analysis_interval": config.ANALYSIS_INTERVAL_MINUTES,
                "lookback_hours": config.ACTIVITY_LOOKBACK_HOURS,
                "min_messages": config.MIN_MESSAGES_FOR_ANALYSIS
            },
            "timestamp": datetime.now().isoformat()
        }
        return status

def main():
    """Main entry point"""
    print("🤖 Urbit AI Analytics System")
    print("=" * 40)
    
    app = UrbitAnalyticsApp()
    
    # Command line interface
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            print("🧪 Running system test...")
            success = app.test_system()
            sys.exit(0 if success else 1)
            
        elif command == "status":
            print("📊 System Status:")
            status = app.get_status()
            print(json.dumps(status, indent=2))
            return
            
        elif command == "once":
            print("🔄 Running single analysis cycle...")
            if app.initialize():
                app.run_analysis_cycle()
            return
            
        elif command == "discover":
            print("🔍 Running group discovery...")
            try:
                import subprocess
                subprocess.run([sys.executable, "tools/smart_group_discovery.py"])
            except Exception as e:
                print(f"❌ Discovery failed: {e}")
            return
    
    # Default: start continuous monitoring
    print("🚀 Starting continuous monitoring...")
    print("💡 Use Ctrl+C to stop")
    print("📖 Commands: test, status, once, discover")
    print("-" * 40)
    
    try:
        app.start_continuous_monitoring()
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    main()