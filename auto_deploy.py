"""
Automatic deployment script for GitHub + Vercel
This script will:
1. Create a GitHub repository
2. Push code to GitHub
3. Deploy to Vercel
"""
import os
import subprocess
import requests
import json
from pathlib import Path
import time

def run_command(cmd, cwd=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        return None, e.stderr

def check_git():
    """Check if git is available"""
    stdout, stderr = run_command("git --version")
    return stdout is not None

def init_git_repo(project_path):
    """Initialize git repository"""
    print("📦 Initializing git repository...")
    
    # Check if already initialized
    if (Path(project_path) / ".git").exists():
        print("✓ Git repository already exists")
        return True
    
    # Initialize git
    stdout, stderr = run_command("git init", cwd=project_path)
    if stderr:
        print(f"✗ Error initializing git: {stderr}")
        return False
    
    print("✓ Git repository initialized")
    return True

def commit_files(project_path):
    """Add and commit all files"""
    print("📝 Committing files...")
    
    # Add all files
    stdout, stderr = run_command("git add .", cwd=project_path)
    if stderr:
        print(f"⚠ Warning: {stderr}")
    
    # Check if there are changes
    stdout, stderr = run_command("git status --porcelain", cwd=project_path)
    if not stdout:
        print("✓ No changes to commit")
        return True
    
    # Commit
    stdout, stderr = run_command(
        'git commit -m "Initial commit: AI Video website"',
        cwd=project_path
    )
    if stderr and "nothing to commit" not in stderr.lower():
        print(f"⚠ Warning: {stderr}")
    
    print("✓ Files committed")
    return True

def create_github_repo(repo_name, token, description="AI Video website"):
    """Create a GitHub repository using API"""
    print(f"🔨 Creating GitHub repository '{repo_name}'...")
    
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": False,
        "auto_init": False
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            repo_data = response.json()
            print(f"✓ Repository created: {repo_data['html_url']}")
            return repo_data['clone_url'], None
        elif response.status_code == 422:
            # Repository might already exist
            print("⚠ Repository might already exist, trying to use existing...")
            return f"https://github.com/{get_github_username(token)}/{repo_name}.git", "exists"
        else:
            error_msg = response.json().get('message', 'Unknown error')
            print(f"✗ Error creating repository: {error_msg}")
            return None, error_msg
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None, str(e)

def get_github_username(token):
    """Get GitHub username from token"""
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['login']
    except:
        pass
    return None

def push_to_github(project_path, repo_url):
    """Push code to GitHub"""
    print("⬆️ Pushing to GitHub...")
    
    # Check if remote already exists
    stdout, stderr = run_command("git remote -v", cwd=project_path)
    if "origin" in (stdout or ""):
        # Update remote URL
        run_command(f'git remote set-url origin {repo_url}', cwd=project_path)
    else:
        # Add remote
        stdout, stderr = run_command(f"git remote add origin {repo_url}", cwd=project_path)
        if stderr and "already exists" not in stderr.lower():
            print(f"⚠ Warning: {stderr}")
    
    # Set branch to main
    run_command("git branch -M main", cwd=project_path)
    
    # Push
    stdout, stderr = run_command("git push -u origin main", cwd=project_path)
    if stderr and "error" in stderr.lower() and "already up to date" not in stderr.lower():
        print(f"✗ Error pushing: {stderr}")
        return False
    
    print("✓ Code pushed to GitHub")
    return True

def deploy_to_vercel(project_path, vercel_token):
    """Deploy to Vercel using CLI"""
    print("🚀 Deploying to Vercel...")
    
    # Check if vercel CLI is installed
    stdout, stderr = run_command("vercel --version")
    if not stdout:
        print("⚠ Vercel CLI not found, installing...")
        run_command("npm install -g vercel")
    
    # Deploy
    env = os.environ.copy()
    env['VERCEL_TOKEN'] = vercel_token
    
    stdout, stderr = run_command(
        "vercel --yes --prod",
        cwd=project_path
    )
    
    if stdout and "https://" in stdout:
        # Extract URL from output
        for line in stdout.split('\n'):
            if 'https://' in line:
                url = line.strip().split()[-1]
                print(f"✓ Deployment successful!")
                print(f"🌐 Your site is live at: {url}")
                return url
    
    print("⚠ Deployment initiated. Check Vercel dashboard for status.")
    return None

def main():
    print("=" * 60)
    print("🚀 Automatic Deployment Script")
    print("=" * 60)
    print()
    
    project_path = Path(__file__).parent
    repo_name = "ai-video-website"
    
    # Get tokens from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    vercel_token = os.environ.get('VERCEL_TOKEN')
    
    if not github_token:
        print("⚠ GITHUB_TOKEN not found in environment")
        print("Please set it: $env:GITHUB_TOKEN='your_token'")
        print("Get token from: https://github.com/settings/tokens")
        return
    
    # Check git
    if not check_git():
        print("✗ Git is not available. Please install Git.")
        return
    
    # Initialize and commit
    if not init_git_repo(project_path):
        return
    
    if not commit_files(project_path):
        return
    
    # Create GitHub repo
    repo_url, error = create_github_repo(repo_name, github_token)
    if not repo_url:
        print(f"✗ Failed to create repository: {error}")
        return
    
    # Push to GitHub
    if not push_to_github(project_path, repo_url):
        print("⚠ Failed to push, but continuing...")
    
    # Deploy to Vercel
    if vercel_token:
        deploy_to_vercel(project_path, vercel_token)
    else:
        print()
        print("⚠ VERCEL_TOKEN not found")
        print("To deploy to Vercel:")
        print("1. Get token from: https://vercel.com/account/tokens")
        print("2. Set: $env:VERCEL_TOKEN='your_token'")
        print("3. Run this script again")
        print()
        print("Or connect the GitHub repo manually:")
        print(f"   https://vercel.com/new (import {repo_name})")
    
    print()
    print("=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
