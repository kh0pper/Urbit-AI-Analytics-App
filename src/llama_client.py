#!/usr/bin/env python3
"""
Custom Llama API client that works reliably
"""
import requests
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LlamaClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def chat_completion(self, messages: List[Dict], model: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Send a chat completion request to Llama API"""
        try:
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return data['choices'][0]['message']['content']
                else:
                    logger.error(f"Unexpected API response format: {data}")
                    return "AI analysis failed: Unexpected response format"
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                return f"AI analysis failed: API error {response.status_code}"
                
        except Exception as e:
            logger.error(f"AI API request failed: {e}")
            return f"AI analysis failed: {str(e)}"

def test_llama_client():
    """Test the Llama client"""
    import config
    
    print("🧪 Testing Llama API client...")
    
    if not config.LLAMA_API_KEY or config.LLAMA_API_KEY == "your_llama_api_key_here":
        print("❌ No valid Llama API key configured")
        return False
    
    client = LlamaClient(config.LLAMA_API_KEY, config.LLAMA_BASE_URL)
    
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello World' to test the API connection."}
    ]
    
    result = client.chat_completion(test_messages, config.LLAMA_MODEL, max_tokens=50)
    
    if "failed" not in result.lower():
        print("✅ Llama API working correctly!")
        print(f"Response: {result}")
        return True
    else:
        print(f"❌ Llama API test failed: {result}")
        return False

if __name__ == "__main__":
    test_llama_client()