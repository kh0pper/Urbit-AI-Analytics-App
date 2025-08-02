# 🔍 How to Find Your Urbit Groups

## Method 1: Browser URL
1. Go to your ship: http://100.90.185.114:8080
2. Click on "Groups" app
3. Click on any group you're in
4. Look at the URL - it will show the group path
5. Example: `/ship/~zod/general` or `/ship/~sampel-palnet/dev-chat`

## Method 2: Groups App Interface
1. In Groups app, right-click on a group
2. Select "Copy link" or "Copy address"
3. The copied link will contain the group path

## Method 3: Manual Discovery
Run this command to explore your ship:
```bash
python3 manual_group_discovery.py
```

## Adding Groups to Config
Edit `config.py` and update:
```python
MONITORED_GROUPS = [
    "/ship/~your-friend/awesome-group", 
    "/ship/~another-ship/tech-chat",
    "/ship/~community-host/general"
]
```

## Testing Groups
Test if a group path works:
```bash
python3 test_cookie.py 0v7.vrs4f.2c9m0.30gdd.45thf.jjjt4
```

## Common Group Patterns
- `/ship/~HOST-SHIP/GROUP-NAME`
- Groups you host: `/ship/~litmyl-nopmet/GROUP-NAME`  
- Public groups: `/ship/~bitbet-bolbel/urbit-community`
- Development groups: `/ship/~darrux-landes/the-forge`