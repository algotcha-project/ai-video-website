"""
Script to help get GitHub token from browser or create repo
"""
import os
import json
import subprocess
from pathlib import Path

def check_browser_storage():
    """Try to find GitHub token in common locations"""
    # Check common browser storage locations
    possible_paths = [
        Path.home() / ".gitconfig",
        Path.home() / ".github" / "token",
        Path.home() / ".config" / "gh" / "hosts.yml",
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"Found: {path}")
            try:
                content = path.read_text()
                if "token" in content.lower() or "github" in content.lower():
                    print(f"  Content preview: {content[:100]}...")
            except:
                pass

def get_git_credentials():
    """Try to get git credentials"""
    try:
        result = subprocess.run(
            "git config --global credential.helper",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(f"Git credential helper: {result.stdout.strip()}")
    except:
        pass

if __name__ == "__main__":
    print("Checking for GitHub credentials...")
    check_browser_storage()
    get_git_credentials()
    print("\nTo create a token:")
    print("1. Go to: https://github.com/settings/tokens")
    print("2. Generate new token (classic)")
    print("3. Select 'repo' scope")
    print("4. Copy token and set: $env:GITHUB_TOKEN='your_token'")
