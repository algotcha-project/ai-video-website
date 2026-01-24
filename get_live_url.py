"""
Get the live Vercel URL by checking the dashboard
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests

REPO_NAME = "ai-video-website"

def check_urls_directly():
    """Try common Vercel URL patterns"""
    print("Checking common Vercel URL patterns...")
    
    possible_urls = [
        f"https://{REPO_NAME}.vercel.app",
        f"https://{REPO_NAME}-algotcha-project.vercel.app",
        f"https://{REPO_NAME}-git-master-algotcha-project.vercel.app",
        f"https://{REPO_NAME}-algotcha-project-*.vercel.app",
    ]
    
    for url in possible_urls:
        if '*' in url:
            continue
        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                print(f"FOUND: {url}")
                return url
        except:
            continue
    
    return None

def get_url_from_dashboard():
    """Use Selenium to check Vercel dashboard"""
    print("Opening Vercel dashboard to get deployment URL...")
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Try to go to the project page directly
        project_url = f"https://vercel.com/algotcha-project/{REPO_NAME}"
        print(f"Trying: {project_url}")
        driver.get(project_url)
        time.sleep(3)
        
        # Look for deployment URL
        try:
            # Common selectors for deployment URL
            url_selectors = [
                "a[href*='vercel.app']",
                "[data-testid='deployment-url']",
                ".deployment-url",
                "//a[contains(@href, 'vercel.app')]",
            ]
            
            for selector in url_selectors:
                try:
                    if selector.startswith("//"):
                        elements = driver.find_elements(By.XPATH, selector)
                    else:
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        url = element.get_attribute('href') or element.text
                        if url and 'vercel.app' in url:
                            if not url.startswith('http'):
                                url = 'https://' + url
                            print(f"FOUND URL: {url}")
                            driver.quit()
                            return url
                except:
                    continue
            
            # Try to get from page source
            page_source = driver.page_source
            import re
            urls = re.findall(r'https://[a-zA-Z0-9-]+\.vercel\.app', page_source)
            if urls:
                url = urls[0]
                print(f"FOUND URL in page: {url}")
                driver.quit()
                return url
                
        except Exception as e:
            print(f"Error finding URL: {e}")
        
        # If not found, try dashboard
        print("Trying dashboard...")
        driver.get("https://vercel.com/dashboard")
        time.sleep(5)
        
        # Look for project
        try:
            project_links = driver.find_elements(By.PARTIAL_LINK_TEXT, REPO_NAME)
            if project_links:
                project_links[0].click()
                time.sleep(3)
                
                # Now look for deployment URL
                url_selectors = [
                    "a[href*='vercel.app']",
                    "//a[contains(@href, 'vercel.app')]",
                ]
                
                for selector in url_selectors:
                    try:
                        if selector.startswith("//"):
                            elements = driver.find_elements(By.XPATH, selector)
                        else:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        for element in elements:
                            url = element.get_attribute('href') or element.text
                            if url and 'vercel.app' in url:
                                if not url.startswith('http'):
                                    url = 'https://' + url
                                print(f"FOUND URL: {url}")
                                driver.quit()
                                return url
                    except:
                        continue
        except:
            pass
        
        print("Could not find URL automatically. Keeping browser open for manual check...")
        time.sleep(10)
        driver.quit()
        
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def main():
    print("=" * 70)
    print("GETTING LIVE DEPLOYMENT URL")
    print("=" * 70)
    print()
    
    # First try direct URL checks
    url = check_urls_directly()
    if url:
        print("\n" + "=" * 70)
        print("SUCCESS! FOUND LIVE SITE")
        print("=" * 70)
        print(f"\nYour live website:")
        print(f"  {url}")
        print()
        return url
    
    # Try Selenium to get from dashboard
    print("\nTrying to get URL from Vercel dashboard...")
    url = get_url_from_dashboard()
    
    if url:
        print("\n" + "=" * 70)
        print("SUCCESS! FOUND LIVE SITE")
        print("=" * 70)
        print(f"\nYour live website:")
        print(f"  {url}")
        print()
        return url
    else:
        print("\n" + "=" * 70)
        print("Could not automatically detect URL")
        print("=" * 70)
        print("\nPlease check Vercel dashboard manually:")
        print("  https://vercel.com/dashboard")
        print(f"\nOr try these URLs:")
        print(f"  https://{REPO_NAME}.vercel.app")
        print(f"  https://{REPO_NAME}-algotcha-project.vercel.app")
        return None

if __name__ == "__main__":
    main()
