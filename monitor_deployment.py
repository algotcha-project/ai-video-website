"""
Monitor deployment and notify when ready
"""
import requests
import time

REPO_NAME = "ai-video-website"
USERNAME = "algotcha-project"

URLS_TO_CHECK = [
    f"https://{REPO_NAME}.vercel.app",
    f"https://{REPO_NAME}-{USERNAME}.vercel.app",
]

def check_if_live(url):
    """Check if URL is live with our content"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            keywords = ['відео', 'фотографій', 'ai-відео', 'замовлення', 'весілля', 'ai video', 'custom']
            if any(kw in content for kw in keywords):
                return True
    except:
        pass
    return False

print("Monitoring deployment...")
print("This will check every 15 seconds for up to 5 minutes...")
print()

start_time = time.time()
max_wait = 300  # 5 minutes

while time.time() - start_time < max_wait:
    for url in URLS_TO_CHECK:
        if check_if_live(url):
            print("\n" + "="*70)
            print("SUCCESS! YOUR SITE IS LIVE!")
            print("="*70)
            print(f"\nYour live website:")
            print(f"  {url}")
            print()
            exit(0)
    
    elapsed = int(time.time() - start_time)
    if elapsed % 15 == 0:
        print(f"Still deploying... ({elapsed}s)")
    
    time.sleep(15)

print("\nTimeout reached. Please check manually:")
print("  https://vercel.com/dashboard")
for url in URLS_TO_CHECK:
    print(f"  {url}")
