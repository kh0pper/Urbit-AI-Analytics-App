#!/usr/bin/env python3
"""
Helper to test different cookie values and find the working one
"""
import requests
import time

def test_cookie_value(cookie_value: str) -> bool:
    """Test if a cookie value works"""
    print(f"🧪 Testing cookie: {cookie_value[:20]}...")
    
    session = requests.Session()
    session.cookies.set('urbauth-~litmyl-nopmet', cookie_value)
    
    try:
        response = session.get("http://100.90.185.114:8080/~/login", timeout=10)
        if response.status_code == 200:
            print("✅ Cookie works!")
            return True
        else:
            print(f"❌ Cookie failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def interactive_cookie_finder():
    """Interactive helper to find the right cookie"""
    print("🔍 Cookie Finder Helper")
    print("=" * 30)
    print()
    print("If you can see your ship's interface, but can't find the cookie,")
    print("try these common cookie patterns for Urbit ships:")
    print()
    
    # Common patterns people might see
    suggestions = [
        "Try looking for any cookie that contains 'auth'",
        "Look for cookies with long random strings (20+ characters)", 
        "Check if there are multiple auth cookies",
        "Look for Base64-encoded strings (ending with = or ==)"
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")
    
    print()
    print("Enter potential cookie values to test (type 'quit' to exit):")
    
    while True:
        cookie_input = input("\n🔑 Enter cookie value: ").strip()
        
        if cookie_input.lower() == 'quit':
            break
            
        if len(cookie_input) < 10:
            print("⚠️  Cookie seems too short, try a longer value")
            continue
            
        if test_cookie_value(cookie_input):
            print(f"\n🎉 Found working cookie!")
            print(f"📝 Updating configuration...")
            
            # Update .env file
            try:
                with open('.env', 'r') as f:
                    content = f.read()
                
                content = content.replace(
                    'URBIT_SESSION_COOKIE=your_session_cookie_here',
                    f'URBIT_SESSION_COOKIE={cookie_input}'
                )
                
                with open('.env', 'w') as f:
                    f.write(content)
                
                print("✅ Configuration updated!")
                print("\n🚀 Next step: python3 main.py test")
                break
                
            except Exception as e:
                print(f"❌ Error updating config: {e}")
                print(f"Manual update needed: {cookie_input}")
        else:
            print("❌ Cookie doesn't work, try another one")

def show_mobile_help():
    """Show mobile-specific cookie extraction help"""
    print("📱 Mobile Cookie Extraction Guide")
    print("=" * 35)
    print()
    print("For Brave Mobile:")
    print("1. Go to http://100.90.185.114:8080")
    print("2. Make sure you're logged in")
    print("3. Tap ⋮ (three dots) → Settings → Advanced → Site settings")
    print("4. Tap 'Cookies' → '100.90.185.114'")
    print("5. Look for 'urbauth-~litmyl-nopmet'")
    print("6. Tap it and copy the value")
    print()
    print("Alternative for Brave Mobile:")
    print("1. While on your ship page, tap ⋮ → More tools")
    print("2. If available, tap 'Developer tools'")
    print("3. Look for Console or Application tab")
    print("4. Try pasting this JavaScript:")
    print("   document.cookie")
    print("5. Look for 'urbauth-~litmyl-nopmet=' in the output")
    print()
    print("If all else fails:")
    print("- Try accessing from a desktop browser")
    print("- Or use the interactive cookie finder below")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_mobile_help()
    elif len(sys.argv) > 1 and sys.argv[1] == '--test':
        cookie = sys.argv[2] if len(sys.argv) > 2 else input("Enter cookie to test: ")
        test_cookie_value(cookie)
    else:
        show_mobile_help()
        print()
        interactive_cookie_finder()