"""
Automatically deploy to Vercel using API
"""
import requests
import json
import os
import subprocess
import time

GITHUB_REPO = "algotcha-project/ai-video-website"
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

def get_vercel_token_from_gh():
    """Try to get Vercel token using GitHub CLI or check if stored"""
    # Check if vercel token is in environment
    token = os.environ.get('VERCEL_TOKEN')
    if token:
        return token
    
    # Try to get from vercel CLI config
    try:
        result = subprocess.run(
            "vercel whoami",
            shell=True,
            capture_output=True,
            text=True
        )
        # If this works, we're logged in, but we still need the token
        # Let's try to deploy directly
        return None
    except:
        pass
    
    return None

def create_vercel_project_via_api(vercel_token):
    """Create Vercel project using REST API"""
    print("🚀 Creating Vercel project via API...")
    
    url = "https://api.vercel.com/v10/projects"
    
    headers = {
        "Authorization": f"Bearer {vercel_token}",
        "Content-Type": "application/json"
    }
    
    # Extract repo name
    repo_name = GITHUB_REPO.split("/")[-1]
    
    data = {
        "name": repo_name,
        "gitRepository": {
            "type": "github",
            "repo": GITHUB_REPO
        },
        "framework": "nextjs"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            project_url = result.get('url', '')
            print("SUCCESS: Project created successfully!")
            print(f"Your site: https://{project_url}")
            return project_url
        elif response.status_code == 409:
            print("⚠ Project already exists")
            # Get project info
            get_url = f"https://api.vercel.com/v9/projects/{repo_name}"
            get_response = requests.get(get_url, headers=headers)
            if get_response.status_code == 200:
                project_data = get_response.json()
                deployments_url = f"https://api.vercel.com/v6/deployments?projectId={project_data.get('id')}"
                deployments_response = requests.get(deployments_url, headers=headers)
                if deployments_response.status_code == 200:
                    deployments = deployments_response.json()
                    if deployments.get('deployments'):
                        latest = deployments['deployments'][0]
                        url = latest.get('url', '')
                        print(f"SUCCESS: Latest deployment: https://{url}")
                        return url
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
            print(f"✗ Error: {error_msg}")
            print(f"Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def deploy_via_cli():
    """Try to deploy using Vercel CLI"""
    print("🚀 Attempting deployment via Vercel CLI...")
    
    project_path = os.path.dirname(os.path.abspath(__file__))
    
    # Check if vercel CLI is available
    try:
        result = subprocess.run(
            "vercel --version",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("Installing Vercel CLI...")
            # Try to install via npm if available
            subprocess.run("npm install -g vercel", shell=True)
    except:
        pass
    
    # Try to deploy
    try:
        # Use non-interactive mode
        result = subprocess.run(
            f'cd "{project_path}" && vercel --yes --prod',
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        output = result.stdout + result.stderr
        
        if "https://" in output:
            # Extract URL
            for line in output.split('\n'):
                if 'https://' in line and 'vercel.app' in line:
                    url = line.strip().split()[-1]
                    print("SUCCESS: Deployment successful!")
                    print(f"Your site: {url}")
                    return url
        
        print("⚠ Deployment initiated. Check output:")
        print(output[:500])
        return None
    except subprocess.TimeoutExpired:
        print("⚠ Deployment is taking longer than expected...")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

def main():
    print("=" * 60)
    print("Automatic Vercel Deployment")
    print("=" * 60)
    print()
    
    # Try to get Vercel token
    vercel_token = get_vercel_token_from_gh()
    
    if vercel_token:
        print("✓ Found Vercel token, using API...")
        url = create_vercel_project_via_api(vercel_token)
        if url:
            print(f"\n✅ Deployment complete!")
            print(f"🌐 Site URL: https://{url}")
            return
    else:
        print("WARNING: No Vercel token found")
        print("Attempting CLI deployment...")
        url = deploy_via_cli()
        if url:
            print(f"\n✅ Deployment complete!")
            print(f"🌐 Site URL: {url}")
            return
    
    print("\n" + "=" * 60)
    print("Manual Step Required:")
    print("=" * 60)
    print(f"1. Go to: https://vercel.com/new")
    print(f"2. Click 'Import Git Repository'")
    print(f"3. Select: {GITHUB_REPO}")
    print(f"4. Click 'Deploy'")
    print()
    print("Or get a Vercel token and set:")
    print("  $env:VERCEL_TOKEN='your_token'")
    print("  Then run this script again")

if __name__ == "__main__":
    main()
