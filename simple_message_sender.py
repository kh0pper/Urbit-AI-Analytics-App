#!/usr/bin/env python3
"""
Simple message sender for Urbit AI Analytics reports
"""
import json
from datetime import datetime

def display_report(report_content):
    """Display the report in a formatted way"""
    print("\n" + "="*60)
    print("📊 URBIT AI ANALYTICS REPORT")
    print("="*60)
    print(report_content)
    print("="*60)
    print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("💡 To receive reports on your ship, check the setup guide")
    print("="*60 + "\n")

def save_report_to_file(report_content, filename=None):
    """Save report to a file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"urbit_report_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("URBIT AI ANALYTICS REPORT\n")
        f.write("="*60 + "\n")
        f.write(report_content)
        f.write("\n" + "="*60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return filename

# Example usage:
if __name__ == "__main__":
    sample_report = """
🤖 **Daily Urbit Network Report**
📊 3 groups monitored, 45 messages analyzed
🎯 Key insights: High developer activity, new app launches trending
🚀 System status: Fully operational
    """
    
    display_report(sample_report)
    filename = save_report_to_file(sample_report)
    print(f"📁 Report saved to: {filename}")
