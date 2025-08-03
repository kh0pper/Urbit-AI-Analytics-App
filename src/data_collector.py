"""
Data collection and storage system for Urbit network monitoring
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path
import config

logger = logging.getLogger(__name__)

class DataCollector:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.activity_file = self.data_dir / "activity.json"
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)
        
        # Initialize data structures
        self.activity_data = self._load_activity_data()
        self.historical_averages = self._load_historical_averages()
    
    def _load_activity_data(self) -> Dict:
        """Load existing activity data"""
        if self.activity_file.exists():
            try:
                with open(self.activity_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading activity data: {e}")
                return {"groups": {}, "metadata": {"last_updated": None}}
        return {"groups": {}, "metadata": {"last_updated": None}}
    
    def _save_activity_data(self):
        """Save activity data to disk"""
        try:
            self.activity_data["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.activity_file, 'w') as f:
                json.dump(self.activity_data, f, indent=2, default=str)
            logger.debug("Activity data saved")
        except Exception as e:
            logger.error(f"Error saving activity data: {e}")
    
    def _load_historical_averages(self) -> Dict:
        """Load or calculate historical averages"""
        averages_file = self.data_dir / "historical_averages.json"
        if averages_file.exists():
            try:
                with open(averages_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading historical averages: {e}")
        return {}
    
    def store_group_activity(self, group_path: str, activities: List[Dict]):
        """Store activity data for a group"""
        timestamp = datetime.now().isoformat()
        
        if group_path not in self.activity_data["groups"]:
            self.activity_data["groups"][group_path] = {
                "activity_log": [],
                "stats_history": [],
                "first_monitored": timestamp
            }
        
        # Store the activity data
        activity_entry = {
            "timestamp": timestamp,
            "activities": activities,
            "message_count": len(activities),
            "user_count": len(set([act.get('author', 'unknown') for act in activities]))
        }
        
        self.activity_data["groups"][group_path]["activity_log"].append(activity_entry)
        
        # Keep only last 100 entries per group to manage storage
        if len(self.activity_data["groups"][group_path]["activity_log"]) > 100:
            self.activity_data["groups"][group_path]["activity_log"] = \
                self.activity_data["groups"][group_path]["activity_log"][-100:]
        
        self._save_activity_data()
        logger.info(f"Stored {len(activities)} activities for {group_path}")
    
    def store_analysis_result(self, group_path: str, analysis: Dict):
        """Store AI analysis results"""
        timestamp = datetime.now().isoformat()
        
        if group_path not in self.activity_data["groups"]:
            self.activity_data["groups"][group_path] = {
                "activity_log": [],
                "stats_history": [],
                "first_monitored": timestamp
            }
        
        # Store analysis in stats history
        analysis_entry = {
            "timestamp": timestamp,
            "analysis": analysis,
            "stats": analysis.get("stats", {}),
            "ai_summary": analysis.get("ai_analysis", "")
        }
        
        self.activity_data["groups"][group_path]["stats_history"].append(analysis_entry)
        
        # Keep only last 50 analyses per group
        if len(self.activity_data["groups"][group_path]["stats_history"]) > 50:
            self.activity_data["groups"][group_path]["stats_history"] = \
                self.activity_data["groups"][group_path]["stats_history"][-50:]
        
        self._save_activity_data()
        self._update_historical_averages(group_path, analysis.get("stats", {}))
    
    def _update_historical_averages(self, group_path: str, current_stats: Dict):
        """Update rolling averages for anomaly detection"""
        if group_path not in self.historical_averages:
            self.historical_averages[group_path] = {
                "avg_message_count": 0,
                "avg_user_count": 0,
                "avg_message_length": 0,
                "sample_count": 0
            }
        
        averages = self.historical_averages[group_path]
        n = averages["sample_count"]
        
        # Update rolling averages
        message_count = current_stats.get("message_count", 0)
        user_count = current_stats.get("user_count", 0)
        message_length = current_stats.get("avg_message_length", 0)
        
        averages["avg_message_count"] = (averages["avg_message_count"] * n + message_count) / (n + 1)
        averages["avg_user_count"] = (averages["avg_user_count"] * n + user_count) / (n + 1)
        averages["avg_message_length"] = (averages["avg_message_length"] * n + message_length) / (n + 1)
        averages["sample_count"] = min(n + 1, 30)  # Cap at 30 samples for rolling average
        
        # Save averages
        averages_file = self.data_dir / "historical_averages.json"
        try:
            with open(averages_file, 'w') as f:
                json.dump(self.historical_averages, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving historical averages: {e}")
    
    def get_recent_activity(self, group_path: str, hours_back: int = 24) -> List[Dict]:
        """Get recent activity for a group"""
        if group_path not in self.activity_data["groups"]:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        recent_activities = []
        
        for entry in self.activity_data["groups"][group_path]["activity_log"]:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff_time:
                recent_activities.extend(entry["activities"])
        
        return recent_activities
    
    def get_group_stats_history(self, group_path: str, days_back: int = 7) -> List[Dict]:
        """Get historical stats for a group"""
        if group_path not in self.activity_data["groups"]:
            return []
        
        cutoff_time = datetime.now() - timedelta(days=days_back)
        recent_stats = []
        
        for entry in self.activity_data["groups"][group_path]["stats_history"]:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if entry_time >= cutoff_time:
                recent_stats.append(entry)
        
        return recent_stats
    
    def save_report(self, report_content: str, report_type: str = "daily"):
        """Save a generated report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_report_{timestamp}.md"
        report_path = self.reports_dir / filename
        
        try:
            with open(report_path, 'w') as f:
                f.write(f"# Urbit Network Analytics Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Report Type: {report_type}\n\n")
                f.write(report_content)
            
            logger.info(f"Report saved: {report_path}")
            return str(report_path)
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None
    
    def get_network_overview(self) -> Dict:
        """Get overall network monitoring statistics"""
        total_groups = len(self.activity_data["groups"])
        total_activities = 0
        active_groups = 0
        
        recent_cutoff = datetime.now() - timedelta(hours=24)
        
        for group_path, group_data in self.activity_data["groups"].items():
            # Count total activities
            for entry in group_data["activity_log"]:
                total_activities += entry["message_count"]
            
            # Check if group was active recently
            if group_data["activity_log"]:
                last_activity = datetime.fromisoformat(group_data["activity_log"][-1]["timestamp"])
                if last_activity >= recent_cutoff:
                    active_groups += 1
        
        return {
            "total_groups_monitored": total_groups,
            "active_groups_24h": active_groups,
            "total_activities_collected": total_activities,
            "monitoring_since": self.activity_data["metadata"].get("last_updated"),
            "data_directory": str(self.data_dir)
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to manage storage"""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)
        cleaned_groups = 0
        
        for group_path in self.activity_data["groups"]:
            group_data = self.activity_data["groups"][group_path]
            
            # Clean activity log
            original_count = len(group_data["activity_log"])
            group_data["activity_log"] = [
                entry for entry in group_data["activity_log"]
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
            ]
            
            # Clean stats history
            group_data["stats_history"] = [
                entry for entry in group_data["stats_history"]
                if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
            ]
            
            cleaned_count = original_count - len(group_data["activity_log"])
            if cleaned_count > 0:
                cleaned_groups += 1
                logger.info(f"Cleaned {cleaned_count} old entries from {group_path}")
        
        if cleaned_groups > 0:
            self._save_activity_data()
            logger.info(f"Cleanup complete: {cleaned_groups} groups cleaned")
    
    def export_data(self, format: str = "json") -> str:
        """Export all collected data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            export_file = self.data_dir / f"export_{timestamp}.json"
            try:
                with open(export_file, 'w') as f:
                    json.dump({
                        "activity_data": self.activity_data,
                        "historical_averages": self.historical_averages,
                        "export_timestamp": datetime.now().isoformat()
                    }, f, indent=2, default=str)
                return str(export_file)
            except Exception as e:
                logger.error(f"Export failed: {e}")
                return None