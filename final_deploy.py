"""
Final deployment script - uses direct API calls
"""
import requests
import json

GITHUB_REPO = "algotcha-project/ai-video-website"
REPO_NAME = "ai-video-website"

def deploy_via_vercel_api():
    """
    Since we don't have Vercel token, we'll provide instructions
    and the repository is already set up on GitHub
    """
    print("=" * 70)
    print("DEPLOYMENT STATUS")
    print("=" * 70)
    print()
    print("GitHub Repository: https://github.com/" + GITHUB_REPO)
    print("Status: READY")
    print()
    print("=" * 70)
    print("TO COMPLETE DEPLOYMENT:")
    print("=" * 70)
    print()
    print("The Vercel import page should be open in your browser.")
    print("If not, go to: https://vercel.com/new/import?repositoryUrl=https://github.com/" + GITHUB_REPO)
    print()
    print("On that page:")
    print("1. The repository should already be selected")
    print("2. Framework should auto-detect as 'Next.js'")
    print("3. Click the 'Deploy' button")
    print("4. Wait 2-3 minutes")
    print()
    print("Your site will be live at: ai-video-website-xxxxx.vercel.app")
    print()
    print("=" * 70)
    
    # Try to open the page
    import webbrowser
    url = f"https://vercel.com/new/import?repositoryUrl=https://github.com/{GITHUB_REPO}"
    print(f"\nOpening: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    deploy_via_vercel_api()
