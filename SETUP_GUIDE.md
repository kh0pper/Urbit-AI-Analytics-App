# 🔧 Setup Guide for Urbit AI Analytics

## Step 1: Get Your Llama API Key

1. Go to [Llama API website](https://api.llama.com/)
2. Sign up or log in
3. Get your API key from the dashboard
4. Copy the key for the next step

## Step 2: Configure Your Urbit Ship Connection

### Get Your Session Cookie:

1. **Open your Urbit ship in a web browser** (e.g., http://localhost:8080)
2. **Log in to your ship**
3. **Open browser developer tools** (F12 or Right-click → Inspect)
4. **Go to Application/Storage tab**
5. **Find Cookies section**
6. **Look for a cookie like `urbauth-~your-ship`**
7. **Copy the cookie value** (long string of characters)

### Get Your Ship URL:
- If running locally: `http://localhost:8080`
- If running on another machine: `http://SHIP_IP_ADDRESS:8080`
- If using HTTPS: `https://your-ship-domain.com`

## Step 3: Update Configuration

Edit the `.env` file with your actual values:

```bash
# Replace with your actual Llama API key
LLAMA_API_KEY=your_actual_llama_api_key_here

# Replace with your ship's URL
URBIT_SHIP_URL=http://localhost:8080

# Replace with your session cookie
URBIT_SESSION_COOKIE=your_actual_session_cookie_here

# Replace with your ship name (without the ~)
URBIT_RECIPIENT_SHIP=your-ship-name
```

## Step 4: Configure Groups to Monitor

Edit `config.py` and update the MONITORED_GROUPS list:

```python
MONITORED_GROUPS = [
    "/ship/~zod/general-chat",
    "/ship/~sampel-palnet/developer-discussion",
    "/ship/~marzod/announcements",
    # Add more groups here
]
```

## Step 5: Test the Setup

```bash
python3 main.py test
```

## Step 6: Run the System

```bash
python3 main.py
```

## 🔍 Finding Group Paths

To find group paths in your Urbit ship:

1. **Go to Groups app** in your ship
2. **Click on a group** you want to monitor
3. **Look at the URL** - it will show the group path
4. **Format**: `/ship/~HOST-SHIP/GROUP-NAME`

Example: If you see a group hosted by `~zod` called `general`, the path would be:
`/ship/~zod/general`

## 🛠️ Troubleshooting

### Authentication Issues:
- Make sure your session cookie is current (they expire)
- Check that your ship URL is correct and accessible
- Verify your ship allows external connections

### API Issues:
- Verify your Llama API key is correct
- Check your API quota/credits
- Monitor the logs in `urbit_analytics.log`

### Group Access Issues:
- Make sure you're a member of the groups you're trying to monitor
- Check that group paths are formatted correctly
- Verify groups are active and have recent messages

## 📊 Understanding Reports

The system will send reports like this to your ship:

```
🤖 **Urbit Network Analytics Report**
📊 Generated: 2024-08-01 15:30:00
📈 Monitoring: 3 groups (2 active)

## Executive Summary  
Moderate activity detected with 45 messages from 12 users.
Technical discussions trending upward.

## Key Insights
- Developer chat most active (67% of messages)
- Positive sentiment (72% positive)
- New topic emerging: "Decentralized social protocols"

## Recommendations
Consider creating dedicated channel for protocol discussions
```

## 🔄 Running Continuously

The system runs continuously and:
- **Monitors groups** every hour (configurable)
- **Sends daily reports** at 9 AM (configurable)
- **Stores data** locally for trend analysis
- **Logs activity** to `urbit_analytics.log`

## 📈 Advanced Configuration

You can customize monitoring in `config.py`:

- `ANALYSIS_INTERVAL_MINUTES`: How often to analyze (default: 60)
- `ACTIVITY_LOOKBACK_HOURS`: How far back to look (default: 24)
- `MIN_MESSAGES_FOR_ANALYSIS`: Minimum messages to analyze (default: 5)

## 🚀 Ready to Start!

Once configured, your system will:
1. ✅ Monitor your chosen Urbit groups
2. ✅ Analyze conversations with AI
3. ✅ Send intelligent summaries to your ship
4. ✅ Track trends and patterns over time
5. ✅ Detect anomalies and interesting developments