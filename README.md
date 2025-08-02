# 🤖 Urbit AI Analytics App

A comprehensive AI-powered analytics system for monitoring Urbit groups, discovering new channels, and generating intelligent insights with automated reporting and web dashboard.

![System Status](https://img.shields.io/badge/Status-Operational-green)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![AI Powered](https://img.shields.io/badge/AI-Llama%20API-orange)
![Real-time](https://img.shields.io/badge/Monitoring-Real--time-brightgreen)

## 🌟 Features

### 📊 **Network Analytics**
- Monitor multiple Urbit groups simultaneously
- Track message volume, user activity, and engagement patterns
- Detect anomalies and trending topics
- Historical data analysis and trend identification

### 🧠 **AI-Powered Analysis**
- **Content Analysis**: Llama AI analyzes conversations for key topics and insights
- **Sentiment Analysis**: Understand the mood and tone of discussions
- **Trend Detection**: Identify emerging topics and patterns
- **Smart Summaries**: Concise, actionable reports delivered to your ship

### 🔄 **Automated Monitoring**
- Continuous background monitoring
- Scheduled report generation
- Real-time activity tracking
- Configurable monitoring intervals

### 📈 **Advanced Analytics**
- User engagement metrics
- Language detection
- Activity timeline analysis
- Cross-group comparison
- Network health monitoring

## 🚀 Quick Start

### 1. **Installation**
```bash
cd urbit-ai-analytics
pip install -r requirements.txt
```

### 2. **Configuration**
Copy the example environment file and configure:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Llama API Configuration
LLAMA_API_KEY=your_llama_api_key_here

# Urbit Ship Configuration  
URBIT_SHIP_URL=http://your-ship-ip:8080
URBIT_SESSION_COOKIE=your_session_cookie_here
URBIT_RECIPIENT_SHIP=your-ship-name
```

### 3. **Configure Groups to Monitor**
Edit `config.py` and add the groups you want to monitor:
```python
MONITORED_GROUPS = [
    "/ship/~zod/example-group",
    "/ship/~sampel-palnet/another-group",
    # Add more groups here
]
```

### 4. **Run the System**
```bash
python main.py
```

## 🛠️ Usage Examples

### **Start Monitoring**
```bash
python main.py
```

### **Run System Test**
```bash
python main.py test
```

### **Check Status**
```bash
python main.py status
```

### **Export Data**
```bash
python main.py export
```

## 📋 Configuration Options

### **Analysis Settings**
- `ANALYSIS_INTERVAL_MINUTES`: How often to run analysis (default: 60)
- `ACTIVITY_LOOKBACK_HOURS`: How far back to analyze (default: 24)  
- `MIN_MESSAGES_FOR_ANALYSIS`: Minimum messages to trigger analysis (default: 5)

### **AI Analysis Prompts**
Customize the AI analysis prompts in `config.py`:
- `ANALYSIS_PROMPT_TEMPLATE`: Group analysis prompt
- `SUMMARY_PROMPT_TEMPLATE`: Overall summary prompt

## 🔧 Advanced Features

### **Custom Analytics**
The system provides several analysis capabilities:

1. **Activity Monitoring**: Track messages, users, and engagement
2. **Trend Analysis**: Identify growing or declining activity patterns  
3. **Anomaly Detection**: Spot unusual activity spikes or drops
4. **Cross-Group Analysis**: Compare activity across multiple groups
5. **Language Detection**: Identify primary languages used
6. **Sentiment Tracking**: Monitor positive/negative sentiment trends

### **Report Types**
- **Hourly**: Quick activity summaries
- **Daily**: Comprehensive analysis reports
- **Weekly**: Trend analysis and insights
- **Custom**: On-demand analysis

### **Data Export**
Export collected data in multiple formats:
- JSON for further analysis
- CSV for spreadsheet import
- Markdown reports for documentation

## 📊 Sample Report Output

```markdown
🤖 **Urbit Network Analytics Report**
📊 **Generated**: 2024-08-01 15:30:00
📈 **Monitoring**: 5 groups (3 active)

## Executive Summary
High activity detected across monitored groups with 147 messages from 23 users. 
Notable increase in technical discussions and new user onboarding.

## Top 3 Most Active Groups
1. **~zod/developer-chat**: 89 messages, 12 users
2. **~sampel-palnet/general**: 34 messages, 8 users  
3. **~marzod/announcements**: 24 messages, 6 users

## Key Insights
- 40% increase in developer-related discussions
- New user engagement up 25%
- Strong positive sentiment (78% positive)
- Emerging topic: "Mars colonization protocols"

## Recommendations
Consider creating dedicated channels for Mars protocol discussions
```

## 🔒 Security & Privacy

- All data stored locally in your UserLAnd environment
- Session cookies encrypted and stored securely
- No data transmitted to third parties (except AI API calls)
- Optional data export for backup purposes

## 🛡️ Troubleshooting

### **Connection Issues**
- Verify Urbit ship URL and port
- Check session cookie validity
- Ensure ship allows external connections

### **AI Analysis Issues**  
- Verify Llama API key
- Check API quota and rate limits
- Monitor log files for detailed errors

### **Group Monitoring Issues**
- Confirm group paths are correct
- Verify permissions to access groups
- Check if groups are active

## 📚 API Reference

### **UrbitClient Methods**
- `authenticate()`: Verify connection to ship
- `create_channel()`: Establish communication channel
- `subscribe_to_group()`: Monitor group activity
- `get_group_activity()`: Retrieve recent messages
- `send_message()`: Send reports to ship

### **AIAnalyzer Methods**
- `analyze_group_activity()`: AI analysis of group content
- `generate_comprehensive_summary()`: Overall network summary
- `analyze_trends()`: Historical trend analysis
- `detect_anomalies()`: Unusual activity detection

### **DataCollector Methods**
- `store_group_activity()`: Save activity data
- `store_analysis_result()`: Save AI analysis
- `get_recent_activity()`: Retrieve stored data
- `export_data()`: Export collected data

## 🤝 Contributing

This system is designed to be extensible. Areas for enhancement:

1. **Additional AI Models**: Support for OpenAI, Claude, etc.
2. **Visualization**: Web dashboard for analytics
3. **Alerts**: Real-time notifications for important events
4. **Integration**: Webhook support, Slack/Discord integration
5. **Mobile App**: Companion mobile application

## 📄 License

MIT License - Feel free to modify and extend for your needs!

---

**Built for the Urbit network with ❤️ and AI**