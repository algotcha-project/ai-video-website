"""
Get the live Vercel deployment URL
"""
import requests
import time
import subprocess
import json

GITHUB_REPO = "algotcha-project/ai-video-website"
REPO_NAME = "ai-video-website"

def check_vercel_deployment():
    """Check Vercel deployment status and get URL"""
    print("Checking Vercel deployment status...")
    print("=" * 70)
    
    # Try to get deployment info from Vercel API
    # First, let's try to find the project URL through GitHub Pages or Vercel
    
    # Check if there's a way to get it from Vercel dashboard
    # Since we don't have Vercel token, let's try checking the repo for deployment info
    
    print(f"Repository: https://github.com/{GITHUB_REPO}")
    print()
    print("Checking deployment status...")
    
    # Try to get from Vercel API (might need auth)
    # For now, let's construct the likely URL
    # Vercel URLs are typically: project-name-username.vercel.app
    
    possible_urls = [
        f"https://{REPO_NAME}.vercel.app",
        f"https://{REPO_NAME}-algotcha-project.vercel.app",
        f"https://{REPO_NAME}-git-master-algotcha-project.vercel.app",
    ]
    
    print("\nTrying to verify deployment URLs...")
    for url in possible_urls:
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                print(f"\n✅ FOUND LIVE SITE!")
                print(f"🌐 URL: {url}")
                return url
            elif response.status_code in [301, 302, 307, 308]:
                final_url = response.url
                print(f"✅ Found redirect to: {final_url}")
                return final_url
        except:
            continue
    
    # If direct check doesn't work, try to get from Vercel API using GitHub token
    print("\nAttempting to get deployment info from Vercel...")
    
    # Try checking Vercel's public API
    try:
        # Vercel might expose project info
        api_url = f"https://api.vercel.com/v9/projects/{REPO_NAME}"
        # This won't work without auth, but let's try
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'url' in data:
                url = data['url']
                print(f"\n✅ FOUND DEPLOYMENT!")
                print(f"🌐 URL: https://{url}")
                return f"https://{url}"
    except:
        pass
    
    return None

def wait_for_deployment(max_wait=180):
    """Wait for deployment to complete and check periodically"""
    print("Waiting for deployment to complete...")
    print("This may take 2-3 minutes...")
    print()
    
    start_time = time.time()
    check_interval = 10  # Check every 10 seconds
    
    while time.time() - start_time < max_wait:
        url = check_vercel_deployment()
        if url:
            return url
        
        elapsed = int(time.time() - start_time)
        print(f"Still deploying... ({elapsed}s / {max_wait}s)")
        time.sleep(check_interval)
    
    return None

def main():
    print("=" * 70)
    print("GETTING DEPLOYMENT URL")
    print("=" * 70)
    print()
    
    # First, try immediate check
    url = check_vercel_deployment()
    
    if not url:
        print("\nDeployment might still be in progress...")
        print("Waiting and checking...")
        url = wait_for_deployment()
    
    if url:
        print("\n" + "=" * 70)
        print("✅ DEPLOYMENT COMPLETE!")
        print("=" * 70)
        print(f"\n🌐 YOUR LIVE SITE:")
        print(f"   {url}")
        print()
        print("=" * 70)
        return url
    else:
        print("\n" + "=" * 70)
        print("⚠ Could not automatically detect deployment URL")
        print("=" * 70)
        print("\nPlease check your Vercel dashboard:")
        print("  https://vercel.com/dashboard")
        print(f"\nOr try these possible URLs:")
        for possible in [
            f"https://{REPO_NAME}.vercel.app",
            f"https://{REPO_NAME}-algotcha-project.vercel.app",
        ]:
            print(f"  {possible}")
        return None

if __name__ == "__main__":
    main()
