"""
Vercel Deployment Script
Deploys the project to Vercel using their REST API
"""
import os
import json
import hashlib
import requests
from pathlib import Path
import zipfile

def get_file_sha1(file_path):
    """Calculate SHA1 hash of a file"""
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            sha1.update(chunk)
    return sha1.hexdigest()

def upload_file_to_vercel(file_path, token):
    """Upload a single file to Vercel"""
    url = "https://api.vercel.com/v2/files"
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    sha1_hash = get_file_sha1(file_path)
    file_size = len(file_content)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Length": str(file_size),
        "x-vercel-digest": sha1_hash
    }
    
    response = requests.post(url, headers=headers, data=file_content)
    
    if response.status_code == 200:
        return {"sha": sha1_hash, "size": file_size}
    else:
        print(f"Error uploading {file_path}: {response.status_code} - {response.text}")
        return None

def get_all_files(directory):
    """Get all files in directory (excluding node_modules, .next, etc.)"""
    ignore_dirs = {'.next', 'node_modules', '.git', '.vercel', '__pycache__'}
    ignore_files = {'.DS_Store', '*.log'}
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for filename in filenames:
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(directory)
            files.append((str(file_path), str(relative_path).replace('\\', '/')))
    
    return files

def create_deployment(files_data, token, project_name="ai-video-website"):
    """Create a deployment on Vercel"""
    url = "https://api.vercel.com/v13/deployments"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Prepare file list for deployment
    file_list = []
    for file_info in files_data:
        if file_info:
            file_list.append({
                "file": file_info['relative_path'],
                "sha": file_info['sha'],
                "size": file_info['size']
            })
    
    payload = {
        "name": project_name,
        "files": file_list,
        "projectSettings": {
            "framework": "nextjs"
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code in [200, 201]:
        data = response.json()
        return data.get('url', '')
    else:
        print(f"Error creating deployment: {response.status_code} - {response.text}")
        return None

def main():
    print("=" * 60)
    print("Vercel Deployment Script")
    print("=" * 60)
    
    # Get Vercel token
    token = os.environ.get('VERCEL_TOKEN')
    if not token:
        print("\n⚠️  VERCEL_TOKEN environment variable not found!")
        print("\nTo get your token:")
        print("1. Go to https://vercel.com/account/tokens")
        print("2. Create a new token")
        print("3. Set it as environment variable:")
        print("   set VERCEL_TOKEN=your_token_here")
        print("\nOr run this script with:")
        print("   $env:VERCEL_TOKEN='your_token'; python deploy_vercel.py")
        return
    
    project_dir = Path(__file__).parent
    print(f"\n📁 Project directory: {project_dir}")
    
    # Get all files
    print("\n📦 Collecting files...")
    all_files = get_all_files(project_dir)
    print(f"Found {len(all_files)} files")
    
    # Upload files
    print("\n⬆️  Uploading files to Vercel...")
    files_data = []
    for i, (file_path, relative_path) in enumerate(all_files, 1):
        print(f"  [{i}/{len(all_files)}] Uploading {relative_path}...", end=' ')
        file_info = upload_file_to_vercel(file_path, token)
        if file_info:
            file_info['relative_path'] = relative_path
            files_data.append(file_info)
            print("✓")
        else:
            print("✗")
            return
    
    # Create deployment
    print("\n🚀 Creating deployment...")
    deployment_url = create_deployment(files_data, token)
    
    if deployment_url:
        print(f"\n✅ Deployment successful!")
        print(f"🌐 Your site is live at: https://{deployment_url}")
    else:
        print("\n❌ Deployment failed!")

if __name__ == "__main__":
    main()
