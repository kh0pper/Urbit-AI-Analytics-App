// Urbit Cookie Extractor JavaScript
// Copy and paste this into your browser console

console.log("🔑 Urbit Cookie Extractor");
console.log("========================");

// Function to extract the Urbit auth cookie
function extractUrbitCookie() {
    const cookies = document.cookie.split(';');
    let urbitCookie = '';
    
    console.log("🔍 Looking for Urbit auth cookie...");
    console.log("All cookies:", document.cookie);
    
    for (let cookie of cookies) {
        cookie = cookie.trim();
        console.log("Checking cookie:", cookie);
        
        if (cookie.startsWith('urbauth-~litmyl-nopmet=')) {
            urbitCookie = cookie.split('=')[1];
            console.log("✅ Found Urbit cookie!");
            console.log("Cookie value:", urbitCookie);
            
            // Try to copy to clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(urbitCookie).then(() => {
                    console.log("✅ Cookie copied to clipboard!");
                    alert("✅ Cookie copied! Value: " + urbitCookie);
                }).catch((err) => {
                    console.log("❌ Could not copy to clipboard:", err);
                    alert("Cookie value: " + urbitCookie);
                });
            } else {
                alert("Cookie value: " + urbitCookie);
            }
            
            return urbitCookie;
        }
    }
    
    console.log("❌ Urbit auth cookie not found");
    console.log("Expected cookie name: urbauth-~litmyl-nopmet");
    alert("❌ Urbit cookie not found. Make sure you're logged in!");
    return null;
}

// Run the extraction
extractUrbitCookie();