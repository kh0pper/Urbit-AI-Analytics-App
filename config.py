"""
Configuration settings for Urbit AI Analytics Tool
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
LLAMA_API_KEY = os.environ.get("LLAMA_API_KEY")
LLAMA_BASE_URL = "https://api.llama.com/compat/v1/"
LLAMA_MODEL = "Llama-4-Maverick-17B-128E-Instruct-FP8"

# Urbit Configuration
URBIT_SHIP_URL = os.environ.get("URBIT_SHIP_URL", "http://100.90.185.114:8080")  # Your ship's URL
URBIT_SESSION_COOKIE = os.environ.get("URBIT_SESSION_COOKIE")  # Authentication cookie
URBIT_RECIPIENT_SHIP = os.environ.get("URBIT_RECIPIENT_SHIP")  # Ship to send reports to (~sampel-palnet)
URBIT_CHANNEL_ID = None  # Will be generated dynamically

# Monitoring Configuration
MONITORED_GROUPS = [
    # Auto-discovered: 2025-08-02
    "/ship/~bitbet-bolbel/urbit-community",
    # Auto-discovered: 2025-08-02
    "/ship/~darrux-landes/the-forge",
    "/ship/~halbex-palheb/uf-public/announcements",
    "/ship/~halbex-palheb/uf-public/chat",
    "/ship/~halbex-palheb/uf-public/default",
    "/ship/~halbex-palheb/uf-public/dev",
    "/ship/~halbex-palheb/uf-public/discussion",
    "/ship/~halbex-palheb/uf-public/general",
    "/ship/~halbex-palheb/uf-public/help",
    "/ship/~halbex-palheb/uf-public/intro",
    "/ship/~halbex-palheb/uf-public/links",
    "/ship/~halbex-palheb/uf-public/lobby",
    "/ship/~halbex-palheb/uf-public/main",
    "/ship/~halbex-palheb/uf-public/public",
    "/ship/~halbex-palheb/uf-public/random",
    "/ship/~halbex-palheb/uf-public/testing",
    "/ship/~halbex-palheb/uf-public/welcome",
    "/ship/~litmyl-nopmet/chat",
    "/ship/~litmyl-nopmet/general",
    "/ship/~litmyl-nopmet/testing",
    # Auto-discovered: 2025-08-02
    "/ship/~zod/general",
    # Popular public groups to try:
    "/ship/~libset-rirbep/landscape",
    "/ship/~dister-dozzod-basbys/urbitfoundation",
    "/ship/~sogryp-dister-dozzod-dozzod/network-states",
    "/ship/~pindet-timmut/hackroom"
]

# Analytics Configuration
ANALYSIS_INTERVAL_MINUTES = 60  # How often to analyze and send reports
ACTIVITY_LOOKBACK_HOURS = 24    # How far back to look for activity
MIN_MESSAGES_FOR_ANALYSIS = 5   # Minimum messages needed to trigger analysis

# AI Analysis Prompts
ANALYSIS_PROMPT_TEMPLATE = """
You are an AI assistant monitoring Urbit network activity. Analyze the following group activity data and provide a concise, insightful summary.

Group: {group_name}
Time Period: Last {hours} hours
Total Messages: {message_count}
Active Users: {user_count}

Messages and Activity:
{activity_data}

Please provide:
1. A brief summary of the main topics discussed
2. Notable trends or patterns in activity
3. Key insights or interesting developments
4. Sentiment analysis (positive/negative/neutral)
5. Any actionable insights or recommendations

Keep the response concise but informative (max 300 words).
"""

SUMMARY_PROMPT_TEMPLATE = """
Create a comprehensive daily summary report for Urbit network monitoring:

Groups Monitored: {group_count}
Total Activity: {total_messages} messages
Active Period: {time_period}

Individual Group Summaries:
{group_summaries}

Please provide:
1. Executive Summary (2-3 sentences)
2. Top 3 Most Active Groups
3. Interesting Trends Across Groups
4. Notable Discussions or Events
5. Network Health Assessment

Format this as a clear, professional report suitable for a chat message.
"""

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "urbit_analytics.log"

# Data Storage
DATA_DIR = "data"
ACTIVITY_DB = "activity.json"
REPORTS_DIR = "reports"