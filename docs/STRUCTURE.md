# 📁 Directory Structure

## Core Application
- `main.py` - Main application entry point
- `config.py` - Configuration settings
- `requirements.txt` - Python dependencies

## Source Code (`src/`)
- `urbit_client.py` - Urbit API client
- `ai_analyzer.py` - AI analysis engine
- `data_collector.py` - Data collection and storage
- `llama_client.py` - Llama API integration

## Tools (`tools/`)
- `smart_group_discovery.py` - Advanced group discovery
- `dashboard_update.py` - Dashboard maintenance
- `update_discovery_log.py` - Discovery log management
- `github_uploader.py` - GitHub integration

## Dashboard (`dashboard/`)
- `index.html` - Main dashboard interface
- `*.json` - Data APIs for dashboard

## Data (`data/`)
- Application data, reports, and discovery logs

## Archive (`archive/`)
- Old, duplicate, and test files (kept for reference)

## Usage

### Start Monitoring
```bash
python main.py
```

### Discover New Groups
```bash
python tools/smart_group_discovery.py
```

### Update Dashboard
```bash
python tools/dashboard_update.py
```
