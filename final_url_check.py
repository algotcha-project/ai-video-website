"""
Final check for deployment URL
"""
import requests
import time

REPO_NAME = "ai-video-website"
USERNAME = "algotcha-project"

# Common Vercel URL patterns
possible_urls = [
    f"https://{REPO_NAME}.vercel.app",
    f"https://{REPO_NAME}-{USERNAME}.vercel.app",
    f"https://{REPO_NAME}-{USERNAME}.vercel.app",
    f"https://{REPO_NAME}-git-master-{USERNAME}.vercel.app",
]

def check_url(url):
    """Check if URL is live and contains our content"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            content = response.text.lower()
            # Check for Ukrainian content or AI video keywords
            if any(keyword in content for keyword in ['відео', 'фотографій', 'ai-відео', 'замовлення', 'весілля']):
                return True, url
            # Also check for English keywords from our site
            if any(keyword in content for keyword in ['ai video', 'photographs', 'custom', 'order']):
                return True, url
    except:
        pass
    return False, None

def main():
    print("=" * 70)
    print("CHECKING FOR LIVE DEPLOYMENT URL")
    print("=" * 70)
    print()
    
    print("Checking possible URLs...")
    for url in possible_urls:
        print(f"Checking: {url}")
        is_live, final_url = check_url(url)
        if is_live:
            print("\n" + "=" * 70)
            print("SUCCESS! FOUND LIVE SITE")
            print("=" * 70)
            print(f"\nYour live website:")
            print(f"  {final_url}")
            print()
            return final_url
    
    print("\nURLs not found yet. Deployment might still be in progress.")
    print("Waiting 60 seconds and checking again...")
    time.sleep(60)
    
    print("\nRe-checking...")
    for url in possible_urls:
        print(f"Checking: {url}")
        is_live, final_url = check_url(url)
        if is_live:
            print("\n" + "=" * 70)
            print("SUCCESS! FOUND LIVE SITE")
            print("=" * 70)
            print(f"\nYour live website:")
            print(f"  {final_url}")
            print()
            return final_url
    
    print("\n" + "=" * 70)
    print("DEPLOYMENT MAY STILL BE IN PROGRESS")
    print("=" * 70)
    print("\nPlease check your Vercel dashboard:")
    print("  https://vercel.com/dashboard")
    print(f"\nOr try these URLs manually:")
    for url in possible_urls:
        print(f"  {url}")
    
    return None

if __name__ == "__main__":
    url = main()
    if url:
        print(f"\nDEPLOYMENT COMPLETE!")
        print(f"Live URL: {url}")
