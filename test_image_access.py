#!/usr/bin/env python3
"""
Test if images are accessible
"""

import urllib.request
import urllib.error

def test_image_access():
    """Test if sample images are accessible"""
    test_images = [
        "https://ekos.gr/images/detailed/355/29290450_9975645960.jpg",
        "https://ekos.gr/images/detailed/213/75083976_1361490113.jpg"
    ]
    
    for image_url in test_images:
        try:
            print(f"Testing: {image_url}")
            req = urllib.request.Request(image_url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                print(f"  ✅ Success! Status: {response.status}")
                print(f"  Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        except urllib.error.HTTPError as e:
            print(f"  ❌ HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"  ❌ URL Error: {e.reason}")
        except Exception as e:
            print(f"  ❌ Other Error: {e}")
        print()

if __name__ == "__main__":
    test_image_access() 