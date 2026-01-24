"""
Complete Vercel deployment automation
Uses browser automation to connect GitHub repo to Vercel
"""
import subprocess
import time
import webbrowser
import urllib.parse

def open_vercel_import():
    """Open Vercel import page with GitHub repo pre-filled"""
    repo = "algotcha-project/ai-video-website"
    
    # Vercel import URL format
    # This will open the import page - user may need to authenticate
    url = f"https://vercel.com/new?import-project=https://github.com/{repo}"
    
    print(f"Opening Vercel import page for: {repo}")
    print(f"URL: {url}")
    
    webbrowser.open(url)
    
    print("\n" + "="*60)
    print("Browser opened!")
    print("="*60)
    print("\nIf you're already logged into Vercel, the import should start automatically.")
    print("If not, please:")
    print("1. Log in to Vercel")
    print("2. Click 'Import' on the repository")
    print("3. Wait for deployment to complete")
    print("\nThe site will be live in 2-3 minutes!")

if __name__ == "__main__":
    open_vercel_import()
