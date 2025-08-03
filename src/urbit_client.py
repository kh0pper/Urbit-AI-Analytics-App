"""
Urbit HTTP API Client for monitoring groups and sending messages
"""
import json
import requests
import time
import uuid
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class UrbitClient:
    def __init__(self, ship_url: str, session_cookie: str, ship_name: str = None):
        self.ship_url = ship_url.rstrip('/')
        self.session_cookie = session_cookie
        self.ship_name = ship_name or self._extract_ship_name_from_url()
        self.channel_id = None
        self.event_id = 0
        self.session = requests.Session()
        # Set cookie with proper ship name
        cookie_name = f'urbauth-{self.ship_name}'
        self.session.cookies.set(cookie_name, session_cookie)
        
    def _extract_ship_name_from_url(self) -> str:
        """Extract ship name from URL or use default"""
        # For now, return a reasonable default - this should be configurable
        return "~litmyl-nopmet"
        
    def authenticate(self) -> bool:
        """Authenticate with the Urbit ship"""
        try:
            response = self.session.get(f"{self.ship_url}/~/login")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def create_channel(self) -> str:
        """Create a new channel for communication"""
        if self.channel_id:
            return self.channel_id
            
        timestamp = int(time.time())
        random_id = str(uuid.uuid4())[:8]
        self.channel_id = f"{timestamp}-{random_id}"
        
        # Initialize channel
        channel_url = f"{self.ship_url}/~/channel/{self.channel_id}"
        
        try:
            response = self.session.put(
                channel_url,
                json=[{
                    "id": self.event_id,
                    "action": "poke",
                    "ship": "our",
                    "app": "hood",
                    "mark": "helm-hi",
                    "json": "opening airlock"
                }]
            )
            
            if response.status_code == 204:
                self.event_id += 1
                logger.info(f"Channel created: {self.channel_id}")
                return self.channel_id
            else:
                logger.error(f"Failed to create channel: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            return None
    
    def subscribe_to_group(self, group_path: str) -> bool:
        """Subscribe to a group for monitoring"""
        if not self.channel_id:
            self.create_channel()
            
        channel_url = f"{self.ship_url}/~/channel/{self.channel_id}"
        
        subscribe_action = {
            "id": self.event_id,
            "action": "subscribe",
            "ship": group_path.split('/')[2],  # Extract ship name from path
            "app": "graph-store",
            "path": f"/updates{group_path}",
        }
        
        try:
            response = self.session.put(channel_url, json=[subscribe_action])
            if response.status_code == 204:
                self.event_id += 1
                logger.info(f"Subscribed to group: {group_path}")
                return True
            else:
                logger.error(f"Failed to subscribe to {group_path}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error subscribing to group {group_path}: {e}")
            return False
    
    def get_group_activity(self, group_path: str, hours_back: int = 24) -> List[Dict]:
        """Get recent activity from a group"""
        # This is a simplified version - in reality you'd need to implement
        # proper graph-store queries based on Urbit's specific API
        
        try:
            # Scry for group data
            scry_path = f"/gx/graph-store/graph{group_path}/newest/100/noun"
            scry_url = f"{self.ship_url}{scry_path}"
            
            response = self.session.get(scry_url)
            if response.status_code == 200:
                # Parse the response (this would need proper Urbit data parsing)
                data = response.json() if response.content else []
                return self._parse_group_activity(data, hours_back)
            else:
                logger.warning(f"No activity data for {group_path}: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting activity for {group_path}: {e}")
            return []
    
    def _parse_group_activity(self, raw_data: Any, hours_back: int) -> List[Dict]:
        """Parse raw Urbit activity data into structured format"""
        # This would need to be implemented based on actual Urbit data structures
        # For now, return mock data structure
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        activities = []
        # Mock parsing - replace with actual Urbit data parsing
        if isinstance(raw_data, list):
            for item in raw_data:
                activity = {
                    'timestamp': datetime.now().isoformat(),
                    'author': self.ship_name,
                    'content': 'Sample message content',
                    'type': 'message',
                    'node_id': str(uuid.uuid4())
                }
                activities.append(activity)
        
        return activities
    
    def send_message(self, recipient_ship: str, message: str) -> bool:
        """Send a direct message to a ship"""
        if not self.channel_id:
            self.create_channel()
            
        channel_url = f"{self.ship_url}/~/channel/{self.channel_id}"
        
        # Poke the chat-view app to send a message
        poke_action = {
            "id": self.event_id,
            "action": "poke",
            "ship": recipient_ship,
            "app": "chat-view",
            "mark": "chat-view-action",
            "json": {
                "create": {
                    "path": f"/dm/{recipient_ship}",
                    "ship": recipient_ship,
                    "message": message
                }
            }
        }
        
        try:
            response = self.session.put(channel_url, json=[poke_action])
            if response.status_code == 204:
                self.event_id += 1
                logger.info(f"Message sent to {recipient_ship}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def get_ship_status(self, ship_name: str) -> Dict:
        """Get status information about a ship"""
        try:
            # Scry for ship information
            scry_url = f"{self.ship_url}/~/scry/j/our/life.json"
            response = self.session.get(scry_url)
            
            if response.status_code == 200:
                return response.json()
            return {}
            
        except Exception as e:
            logger.error(f"Error getting ship status: {e}")
            return {}
    
    def close_channel(self):
        """Close the communication channel"""
        if self.channel_id:
            try:
                channel_url = f"{self.ship_url}/~/channel/{self.channel_id}"
                self.session.delete(channel_url)
                logger.info(f"Channel closed: {self.channel_id}")
            except Exception as e:
                logger.error(f"Error closing channel: {e}")