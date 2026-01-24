"""
Verify and get the working URL
"""
import requests
import time

REPO_NAME = "ai-video-website"

def verify_url(url):
    """Verify if URL is live and working"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            content = response.text.lower()
            # Check for Ukrainian keywords
            ukrainian_keywords = ['відео', 'фотографій', 'ai-відео', 'замовлення', 'весілля', 'дні народження']
            # Check for English keywords
            english_keywords = ['ai video', 'photographs', 'custom', 'order', 'wedding', 'birthday']
            
            if any(kw in content for kw in ukrainian_keywords + english_keywords):
                return True, url
            # Also check for Next.js indicators
            if 'next.js' in content or 'react' in content:
                return True, url
    except requests.exceptions.RequestException:
        pass
    return False, None

def main():
    print("=" * 70)
    print("VERIFYING DEPLOYMENT URL")
    print("=" * 70)
    print()
    
    # Standard Vercel URL format
    standard_url = f"https://{REPO_NAME}.vercel.app"
    
    print(f"Checking: {standard_url}")
    is_live, url = verify_url(standard_url)
    
    if is_live:
        print("\n" + "=" * 70)
        print("SUCCESS! SITE IS LIVE")
        print("=" * 70)
        print(f"\nYour live website:")
        print(f"  {url}")
        print()
        return url
    
    print("Not ready yet. Waiting 30 seconds and checking again...")
    time.sleep(30)
    
    print(f"\nRe-checking: {standard_url}")
    is_live, url = verify_url(standard_url)
    
    if is_live:
        print("\n" + "=" * 70)
        print("SUCCESS! SITE IS LIVE")
        print("=" * 70)
        print(f"\nYour live website:")
        print(f"  {url}")
        print()
        return url
    
    print("\n" + "=" * 70)
    print("DEPLOYMENT STATUS")
    print("=" * 70)
    print(f"\nMost likely URL (may still be deploying):")
    print(f"  {standard_url}")
    print("\nPlease check Vercel dashboard:")
    print("  https://vercel.com/dashboard")
    print("\nOr wait a few more minutes and try the URL above.")
    
    return standard_url

if __name__ == "__main__":
    url = main()
    print(f"\n{'='*70}")
    print(f"URL: {url}")
    print(f"{'='*70}")
