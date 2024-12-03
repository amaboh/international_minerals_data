import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings()

def test_connection():
    url = "https://www.usgs.gov/centers/national-minerals-information-center/international-minerals-statistics-and-information"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    
    try:
        # Try with verify=False first
        response = requests.get(url, headers=headers, verify=False)
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = test_connection()
    print(f"Connection successful: {result}")