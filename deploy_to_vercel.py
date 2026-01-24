"""
Deploy to Vercel using REST API
"""
import requests
import json
import os

def deploy_to_vercel(github_repo, vercel_token):
    """Deploy GitHub repo to Vercel"""
    print(f"🚀 Deploying {github_repo} to Vercel...")
    
    # Vercel API endpoint to create a project from GitHub
    url = "https://api.vercel.com/v10/projects"
    
    headers = {
        "Authorization": f"Bearer {vercel_token}",
        "Content-Type": "application/json"
    }
    
    # Extract owner and repo name
    parts = github_repo.replace("https://github.com/", "").split("/")
    owner = parts[0]
    repo = parts[1].replace(".git", "")
    
    data = {
        "name": repo,
        "gitRepository": {
            "type": "github",
            "repo": f"{owner}/{repo}"
        },
        "framework": "nextjs"
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            result = response.json()
            project_url = result.get('url', '')
            print(f"✅ Project created successfully!")
            print(f"🌐 Your site will be available at: https://{project_url}")
            return project_url
        elif response.status_code == 409:
            print("⚠ Project already exists. Checking deployments...")
            # Try to get project info
            get_url = f"https://api.vercel.com/v9/projects/{repo}"
            get_response = requests.get(get_url, headers=headers)
            if get_response.status_code == 200:
                project_data = get_response.json()
                print(f"✅ Project exists: {project_data.get('name')}")
                return project_data.get('name')
        else:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get('error', {}).get('message', response.text)
            print(f"✗ Error: {error_msg}")
            print(f"Response: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None

if __name__ == "__main__":
    github_repo = "https://github.com/algotcha-project/ai-video-website"
    
    vercel_token = os.environ.get('VERCEL_TOKEN')
    if not vercel_token:
        print("WARNING: VERCEL_TOKEN not found in environment")
        print("\nTo get your token:")
        print("1. Go to: https://vercel.com/account/tokens")
        print("2. Create a new token")
        print("3. Set it: $env:VERCEL_TOKEN='your_token'")
        print("\nOr connect manually:")
        print(f"   https://vercel.com/new (import {github_repo})")
    else:
        deploy_to_vercel(github_repo, vercel_token)
