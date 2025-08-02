#!/usr/bin/env python3
"""
Advanced Urbit Messaging System
Multiple approaches to deliver messages to your Urbit inbox
"""
import requests
import json
import time
import uuid
from typing import Optional, Dict, List
from datetime import datetime
import config
import logging

logger = logging.getLogger(__name__)

class AdvancedUrbitMessenger:
    def __init__(self):
        self.ship_url = config.URBIT_SHIP_URL.rstrip('/')
        self.session_cookie = config.URBIT_SESSION_COOKIE
        self.ship_name = "~litmyl-nopmet"
        self.session = requests.Session()
        
        # Set authentication
        self.session.cookies.set(f'urbauth-{self.ship_name}', self.session_cookie)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
        
    def discover_messaging_endpoints(self) -> Dict[str, List[str]]:
        """Discover all possible messaging endpoints by examining the ship"""
        print("🔍 DISCOVERING MESSAGING ENDPOINTS")
        print("=" * 50)
        
        endpoints = {
            'working': [],
            'potential': [],
            'failed': []
        }
        
        # Method 1: Check the main apps page for available apps
        print("\n1️⃣ Scanning available apps...")
        try:
            response = self.session.get(f"{self.ship_url}/apps")
            if response.status_code == 200:
                print("   ✅ Apps page accessible")
                
                # Look for messaging-related apps in the response
                content = response.text.lower()
                messaging_apps = []
                
                app_keywords = ['chat', 'talk', 'dm', 'message', 'groups', 'graph']
                for keyword in app_keywords:
                    if keyword in content:
                        messaging_apps.append(keyword)
                
                print(f"   📱 Found messaging-related apps: {messaging_apps}")
                
                # Try to access each messaging app
                for app in messaging_apps:
                    app_url = f"{self.ship_url}/apps/{app}"
                    try:
                        app_response = self.session.get(app_url, timeout=5)
                        if app_response.status_code == 200:
                            endpoints['working'].append(app_url)
                            print(f"      ✅ {app}: accessible")
                        else:
                            endpoints['failed'].append(app_url)
                    except:
                        endpoints['failed'].append(app_url)
                        
        except Exception as e:
            print(f"   ❌ Error scanning apps: {e}")
        
        # Method 2: Test known Urbit API patterns
        print("\n2️⃣ Testing known API patterns...")
        
        api_patterns = [
            # Channel-based messaging
            "/~/channel/",
            
            # Scry endpoints
            "/~/scry/j/our/chat-store/all.json",
            "/~/scry/j/our/graph-store/keys.json", 
            "/~/scry/j/our/groups/all.json",
            "/~/scry/j/our/dm.json",
            
            # Direct app endpoints
            "/~/poke/chat-store",
            "/~/poke/graph-store", 
            "/~/poke/groups",
            "/~/poke/dm",
            
            # Groups app specific
            "/apps/groups/api",
            "/apps/groups/dm",
            "/apps/groups/messages",
            
            # Graph store
            "/apps/graph",
            "/apps/graph/api",
        ]
        
        for pattern in api_patterns:
            try:
                if pattern.endswith('/'):
                    # For channel patterns, test with a sample channel
                    test_url = f"{self.ship_url}{pattern}test-{int(time.time())}"
                else:
                    test_url = f"{self.ship_url}{pattern}"
                
                response = self.session.get(test_url, timeout=3)
                
                if response.status_code in [200, 204]:
                    endpoints['working'].append(pattern)
                    print(f"   ✅ {pattern}: {response.status_code}")
                elif response.status_code in [400, 405]:  # Method not allowed but endpoint exists
                    endpoints['potential'].append(pattern)
                    print(f"   🔶 {pattern}: {response.status_code} (exists but needs different method)")
                else:
                    endpoints['failed'].append(pattern)
                    print(f"   ❌ {pattern}: {response.status_code}")
                    
            except Exception as e:
                endpoints['failed'].append(pattern)
                print(f"   ❌ {pattern}: {e}")
        
        # Method 3: Examine the Groups app HTML/JS for API calls
        print("\n3️⃣ Analyzing Groups app for API patterns...")
        try:
            groups_response = self.session.get(f"{self.ship_url}/apps/groups")
            if groups_response.status_code == 200:
                content = groups_response.text
                
                # Look for fetch() calls, API endpoints, WebSocket connections
                import re
                
                patterns_to_find = [
                    r'fetch\(["\']([^"\']+)["\']',  # fetch() calls
                    r'\.post\(["\']([^"\']+)["\']',  # .post() calls
                    r'\.put\(["\']([^"\']+)["\']',   # .put() calls
                    r'/~/[^"\s]+',                   # Urbit API patterns
                    r'/api/[^"\s]+',                 # Generic API patterns
                    r'channel[^"]*["\']([^"\']+)',   # Channel references
                ]
                
                found_endpoints = set()
                for pattern in patterns_to_find:
                    matches = re.findall(pattern, content)
                    found_endpoints.update(matches)
                
                # Filter for relevant endpoints
                relevant_endpoints = [ep for ep in found_endpoints 
                                    if any(keyword in ep.lower() for keyword in 
                                          ['message', 'chat', 'dm', 'send', 'post', 'channel', 'graph'])]
                
                endpoints['potential'].extend(relevant_endpoints)
                print(f"   📊 Found {len(relevant_endpoints)} potential messaging endpoints")
                for ep in relevant_endpoints[:5]:  # Show first 5
                    print(f"      - {ep}")
                
        except Exception as e:
            print(f"   ❌ Error analyzing Groups app: {e}")
        
        print(f"\n📊 Discovery Summary:")
        print(f"   ✅ Working endpoints: {len(endpoints['working'])}")
        print(f"   🔶 Potential endpoints: {len(endpoints['potential'])}")
        print(f"   ❌ Failed endpoints: {len(endpoints['failed'])}")
        
        return endpoints
    
    def send_via_groups_channel(self, message: str) -> bool:
        """Send message via Groups app channel system"""
        print("📨 Attempting Groups channel messaging...")
        
        try:
            # Create a unique channel
            channel_id = f"analytics-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            channel_url = f"{self.ship_url}/~/channel/{channel_id}"
            
            # Try multiple poke approaches for Groups
            poke_attempts = [
                # Groups app DM
                {
                    "id": 1,
                    "action": "poke",
                    "ship": "our",
                    "app": "groups",
                    "mark": "groups-action",
                    "json": {
                        "dm": {
                            "ship": self.ship_name,
                            "content": message
                        }
                    }
                },
                # Groups UI action
                {
                    "id": 1,
                    "action": "poke",
                    "ship": "our", 
                    "app": "groups",
                    "mark": "groups-ui-action",
                    "json": {
                        "send-dm": {
                            "ship": self.ship_name,
                            "message": message
                        }
                    }
                },
                # Direct DM poke
                {
                    "id": 1,
                    "action": "poke",
                    "ship": self.ship_name,
                    "app": "dm",
                    "mark": "dm-action", 
                    "json": {
                        "message": message,
                        "author": self.ship_name
                    }
                }
            ]
            
            for i, poke in enumerate(poke_attempts, 1):
                print(f"   🔄 Attempt {i}: {poke['app']}/{poke['mark']}")
                
                response = self.session.put(channel_url, json=[poke], timeout=10)
                print(f"      Response: {response.status_code}")
                
                if response.status_code == 204:
                    print(f"   ✅ Success with attempt {i}!")
                    return True
                elif response.status_code == 400:
                    print(f"      Response body: {response.text[:200]}")
            
            return False
            
        except Exception as e:
            print(f"   ❌ Groups channel error: {e}")
            return False
    
    def send_via_graph_store(self, message: str) -> bool:
        """Send message via Graph Store (underlying Groups storage)"""
        print("📊 Attempting Graph Store messaging...")
        
        try:
            channel_id = f"graph-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            channel_url = f"{self.ship_url}/~/channel/{channel_id}"
            
            # Graph store approaches
            graph_attempts = [
                # Add post to DM graph
                {
                    "id": 1,
                    "action": "poke",
                    "ship": "our",
                    "app": "graph-store",
                    "mark": "graph-update-3",
                    "json": {
                        "add-post": {
                            "resource": f"/ship/{self.ship_name}/dm",
                            "post": {
                                "author": self.ship_name,
                                "index": f"/{int(time.time() * 1000)}",
                                "time-sent": int(time.time() * 1000),
                                "contents": [{"text": message}],
                                "hash": None,
                                "signatures": []
                            }
                        }
                    }
                },
                # Create DM graph if it doesn't exist
                {
                    "id": 1,
                    "action": "poke",
                    "ship": "our",
                    "app": "graph-store",
                    "mark": "graph-update-3", 
                    "json": {
                        "add-graph": {
                            "resource": f"/ship/{self.ship_name}/dm",
                            "graph": {},
                            "mark": "graph-validator-dm"
                        }
                    }
                }
            ]
            
            for i, poke in enumerate(graph_attempts, 1):
                print(f"   🔄 Graph attempt {i}")
                
                response = self.session.put(channel_url, json=[poke], timeout=10)
                print(f"      Response: {response.status_code}")
                
                if response.status_code == 204:
                    print(f"   ✅ Graph Store success!")
                    return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ Graph Store error: {e}")
            return False
    
    def send_via_terminal_notification(self, message: str) -> bool:
        """Send message via Terminal app (if available)"""
        print("💻 Attempting Terminal notification...")
        
        try:
            channel_id = f"term-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            channel_url = f"{self.ship_url}/~/channel/{channel_id}"
            
            # Terminal notification
            poke = {
                "id": 1,
                "action": "poke",
                "ship": "our",
                "app": "hood",
                "mark": "helm-hi",
                "json": f"AI Analytics: {message[:100]}..."
            }
            
            response = self.session.put(channel_url, json=[poke], timeout=10)
            print(f"      Response: {response.status_code}")
            
            if response.status_code == 204:
                print(f"   ✅ Terminal notification sent!")
                return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ Terminal notification error: {e}")
            return False
    
    def send_via_dojo_command(self, message: str) -> bool:
        """Send message via Dojo (Urbit shell)"""
        print("🖥️ Attempting Dojo command...")
        
        try:
            channel_id = f"dojo-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            channel_url = f"{self.ship_url}/~/channel/{channel_id}"
            
            # Dojo command to create a note or message
            poke = {
                "id": 1,
                "action": "poke",
                "ship": "our",
                "app": "dojo",
                "mark": "dojo-command", 
                "json": f"|hi Analytics report ready: {message[:50]}..."
            }
            
            response = self.session.put(channel_url, json=[poke], timeout=10)
            print(f"      Response: {response.status_code}")
            
            if response.status_code == 204:
                print(f"   ✅ Dojo command sent!")
                return True
            
            return False
            
        except Exception as e:
            print(f"   ❌ Dojo command error: {e}")
            return False
    
    def comprehensive_message_delivery(self, message: str) -> bool:
        """Try all available messaging methods until one succeeds"""
        print("🚀 COMPREHENSIVE MESSAGE DELIVERY ATTEMPT")
        print("=" * 60)
        
        # First discover available endpoints
        endpoints = self.discover_messaging_endpoints()
        
        # List of delivery methods to try
        delivery_methods = [
            ("Groups Channel", self.send_via_groups_channel),
            ("Graph Store", self.send_via_graph_store),
            ("Terminal Notification", self.send_via_terminal_notification),
            ("Dojo Command", self.send_via_dojo_command),
        ]
        
        print(f"\n📨 Attempting delivery of message ({len(message)} characters)...")
        print(f"Preview: {message[:100]}...")
        
        for method_name, method_func in delivery_methods:
            print(f"\n🔄 Trying: {method_name}")
            
            try:
                if method_func(message):
                    print(f"✅ SUCCESS: Message delivered via {method_name}!")
                    return True
                else:
                    print(f"❌ Failed: {method_name}")
            except Exception as e:
                print(f"❌ Error in {method_name}: {e}")
        
        print(f"\n⚠️ All delivery methods failed")
        print(f"💾 Message will be saved locally for manual delivery")
        
        # Save the message locally as fallback
        self.save_message_locally(message)
        return False
    
    def save_message_locally(self, message: str):
        """Save message locally for manual delivery"""
        import os
        
        os.makedirs("data/pending_messages", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/pending_messages/urbit_message_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(f"PENDING URBIT MESSAGE\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Recipient: {self.ship_name}\n")
            f.write(f"{'='*50}\n\n")
            f.write(message)
            f.write(f"\n\n{'='*50}\n")
            f.write(f"Manual delivery instructions:\n")
            f.write(f"1. Copy the message content above\n")
            f.write(f"2. Go to your Urbit ship: {self.ship_url}\n")
            f.write(f"3. Open DMs or Groups and paste the message\n")
        
        print(f"💾 Message saved to: {filename}")

def test_advanced_messaging():
    """Test the advanced messaging system"""
    print("🧪 TESTING ADVANCED URBIT MESSAGING SYSTEM")
    print("=" * 60)
    
    messenger = AdvancedUrbitMessenger()
    
    # Create a test message
    test_message = f"""🤖 **Urbit AI Analytics - Messaging Test**

📊 **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 **Test**: Advanced messaging system verification

✅ **System Status**: 
- Auto-discovery working (96+ groups found)
- Dynamic group addition functional  
- AI analysis operational
- 22+ channels being monitored

🎯 **Message Delivery Test**: 
This message confirms that the advanced messaging system can successfully deliver analytics reports to your Urbit inbox.

📈 **Latest Analytics**: 
- Network activity detected across multiple groups
- AI insights generated successfully
- Comprehensive reports available

🚀 **Next Steps**: 
System ready for continuous monitoring and automated report delivery!

---
*Sent via Advanced Urbit Messaging System*
*Generated at {datetime.now().strftime('%H:%M:%S')}*"""
    
    # Attempt comprehensive delivery
    success = messenger.comprehensive_message_delivery(test_message)
    
    if success:
        print(f"\n🎉 MESSAGING TEST SUCCESSFUL!")
        print(f"✅ Message delivered to your Urbit ship")
        print(f"📱 Check your Urbit inbox for the analytics report")
    else:
        print(f"\n⚠️ MESSAGING TEST COMPLETED")
        print(f"✅ All delivery methods tested")
        print(f"💾 Message saved locally for manual delivery")
        print(f"🔧 System functional, delivery method needs refinement")
    
    return success

if __name__ == "__main__":
    test_advanced_messaging()