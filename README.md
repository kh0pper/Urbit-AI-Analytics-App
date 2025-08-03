# 🤖 Urbit AI Analytics System

A clean, simplified AI-powered analytics system for monitoring Urbit groups and generating intelligent insights.

![System Status](https://img.shields.io/badge/Status-Operational-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![AI Powered](https://img.shields.io/badge/AI-Llama%20API-orange)

## ✨ Features

- **📊 Group Monitoring**: Track activity across multiple Urbit groups
- **🧠 AI Analysis**: Intelligent insights powered by Llama API
- **🔍 Group Discovery**: Automatically find new groups to monitor
- **📈 Dashboard**: Live web dashboard with statistics
- **📝 Reports**: Automated analytics reports

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Settings
Edit `config.py` with your credentials:
```python
# Llama API
LLAMA_API_KEY = "your_api_key_here"

# Urbit Ship
URBIT_SHIP_URL = "http://your-ship-ip:8080"
URBIT_SESSION_COOKIE = "your_session_cookie"

# Groups to monitor
MONITORED_GROUPS = [
    "/ship/~zod/general",
    "/ship/~bitbet-bolbel/urbit-community",
    # Add more groups...
]
```

### 3. Run the System
```bash
# Test the system
python main.py test

# Run single analysis
python main.py once

# Start continuous monitoring
python main.py
```

## 📋 Commands

- `python main.py` - Start continuous monitoring
- `python main.py test` - Test system functionality
- `python main.py once` - Run single analysis cycle
- `python main.py status` - Show system status
- `python main.py discover` - Find new groups

## 🔧 Tools

### Group Discovery
Find new Urbit groups to monitor:
```bash
python tools/smart_group_discovery.py
```

### Dashboard Update
Update the web dashboard:
```bash
python tools/dashboard_update.py
```

## 📁 Directory Structure

```
📂 src/              - Core application code
📂 tools/            - Utility scripts
📂 dashboard/        - Web dashboard files
📂 data/             - Reports and activity data
📂 logs/             - Application logs
📂 docs/             - Documentation
```

## 📊 Dashboard

View live analytics at: https://kh0pper.github.io/urbit-analytics/dashboard/

## ⚙️ Configuration

Key settings in `config.py`:

- `ANALYSIS_INTERVAL_MINUTES` - How often to analyze (default: 60)
- `ACTIVITY_LOOKBACK_HOURS` - How far back to look (default: 24)
- `MIN_MESSAGES_FOR_ANALYSIS` - Minimum messages for AI analysis (default: 5)

## 🛠️ Development

### Core Components

- **`src/urbit_client.py`** - Urbit API client
- **`src/ai_analyzer.py`** - AI analysis engine  
- **`src/data_collector.py`** - Data storage and management

### Adding New Groups

1. Run group discovery: `python tools/smart_group_discovery.py`
2. Review discovered groups in the output
3. Add promising groups to `MONITORED_GROUPS` in `config.py`

## 📈 Sample Output

```
🤖 Urbit AI Analytics Report
📊 Generated: 2025-08-03 12:00:00
📈 Network Status: 5/8 groups active
🔍 Activities Collected: 47 messages

🧠 AI Analysis Summary
Active developer discussions in ~darrux-landes/the-forge
with focus on app development and network improvements.
Growing engagement in community groups.

📊 Monitoring Statistics
- Total Groups Monitored: 8
- Active Groups (24h): 5  
- Total Activities: 47
- Analyses Generated: 3
```

## 🔒 Security

- All data stored locally
- Session cookies handled securely
- No data shared with third parties (except AI API)

## 📄 License

MIT License - Free to use and modify!

---
**Built for the Urbit network with ❤️ and AI**