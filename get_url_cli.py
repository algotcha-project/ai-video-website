"""
Get deployment URL using CLI/API methods
"""
import subprocess
import json
import requests
import os

REPO_NAME = "ai-video-website"
GITHUB_REPO = "algotcha-project/ai-video-website"

def get_from_gh_api():
    """Get deployment info from GitHub API"""
    print("Checking GitHub API for deployment info...")
    
    try:
        # Get repo info
        result = subprocess.run(
            f'gh api repos/{GITHUB_REPO}',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            repo_data = json.loads(result.stdout)
            homepage = repo_data.get('homepage')
            if homepage and 'vercel.app' in homepage:
                return homepage
        
        # Check deployments
        result = subprocess.run(
            f'gh api repos/{GITHUB_REPO}/deployments',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            deployments = json.loads(result.stdout)
            if deployments:
                # Get latest deployment
                latest = deployments[0]
                deployment_id = latest.get('id')
                
                # Get deployment status
                result = subprocess.run(
                    f'gh api repos/{GITHUB_REPO}/deployments/{deployment_id}/statuses',
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    statuses = json.loads(result.stdout)
                    if statuses:
                        target_url = statuses[0].get('target_url')
                        if target_url and 'vercel.app' in target_url:
                            return target_url
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def get_from_vercel_api():
    """Try to get from Vercel API using GitHub token"""
    print("Checking Vercel API...")
    
    # Try to get Vercel token from environment or config
    token = os.environ.get('VERCEL_TOKEN')
    if not token:
        # Try to get from vercel config
        try:
            vercel_dir = os.path.join(os.path.dirname(__file__), '.vercel')
            if os.path.exists(vercel_dir):
                # Check for token in config
                pass
        except:
            pass
    
    if token:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Get project
        try:
            response = requests.get(
                f"https://api.vercel.com/v9/projects/{REPO_NAME}",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                project = response.json()
                # Get latest deployment
                deployments_url = f"https://api.vercel.com/v6/deployments?projectId={project.get('id')}"
                deployments_response = requests.get(deployments_url, headers=headers, timeout=10)
                if deployments_response.status_code == 200:
                    deployments = deployments_response.json()
                    if deployments.get('deployments'):
                        latest = deployments['deployments'][0]
                        url = latest.get('url', '')
                        if url:
                            return f"https://{url}"
        except Exception as e:
            print(f"API error: {e}")
    
    return None

def check_common_urls():
    """Check common Vercel URL patterns"""
    print("Checking common URL patterns...")
    
    urls = [
        f"https://{REPO_NAME}.vercel.app",
        f"https://{REPO_NAME}-algotcha-project.vercel.app",
    ]
    
    for url in urls:
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                content = response.text.lower()
                if any(kw in content for kw in ['відео', 'фотографій', 'ai-відео', 'замовлення']):
                    return url
        except:
            continue
    
    return None

def main():
    print("=" * 70)
    print("GETTING DEPLOYMENT URL VIA CLI/API")
    print("=" * 70)
    print()
    
    # Method 1: GitHub API
    url = get_from_gh_api()
    if url:
        print(f"\nFOUND via GitHub API: {url}")
        return url
    
    # Method 2: Vercel API
    url = get_from_vercel_api()
    if url:
        print(f"\nFOUND via Vercel API: {url}")
        return url
    
    # Method 3: Direct URL check
    url = check_common_urls()
    if url:
        print(f"\nFOUND via direct check: {url}")
        return url
    
    print("\nCould not find URL via CLI/API methods.")
    print("\nTrying to construct standard Vercel URL...")
    standard_url = f"https://{REPO_NAME}.vercel.app"
    print(f"\nMost likely URL: {standard_url}")
    print("\nPlease verify at: https://vercel.com/dashboard")
    
    return standard_url

if __name__ == "__main__":
    url = main()
    print(f"\n{'='*70}")
    print(f"DEPLOYMENT URL: {url}")
    print(f"{'='*70}")
