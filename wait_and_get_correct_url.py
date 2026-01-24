"""
Wait for deployment and get the correct URL
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import requests
import re

REPO_NAME = "ai-video-website"

def get_correct_url():
    """Wait for deployment and get the correct URL"""
    print("=" * 70)
    print("WAITING FOR DEPLOYMENT AND GETTING URL")
    print("=" * 70)
    print()
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Go to dashboard
        print("Opening Vercel dashboard...")
        driver.get("https://vercel.com/dashboard")
        time.sleep(5)
        
        # Look for the project
        print("Looking for project...")
        try:
            # Try to find project link
            project_links = driver.find_elements(By.PARTIAL_LINK_TEXT, REPO_NAME)
            if project_links:
                print(f"Found project link, clicking...")
                project_links[0].click()
                time.sleep(5)
            else:
                # Try direct project URL
                driver.get(f"https://vercel.com/algotcha-project/{REPO_NAME}")
                time.sleep(5)
        except:
            driver.get(f"https://vercel.com/algotcha-project/{REPO_NAME}")
            time.sleep(5)
        
        # Wait and look for deployment URL
        print("Waiting for deployment URL to appear...")
        max_wait = 240  # 4 minutes
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            # Get page source
            page_source = driver.page_source
            
            # Look for vercel.app URLs
            urls = re.findall(r'https://[a-zA-Z0-9-]+\.vercel\.app[^"\s<>]*', page_source)
            
            # Filter for our project
            for url in urls:
                url = url.split('"')[0].split("'")[0].split('>')[0].split('<')[0].strip()
                # Should contain repo name or be the main deployment
                if REPO_NAME in url.lower() or 'ai-video' in url.lower():
                    # Verify it works
                    try:
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            # Check if it's our site (has Ukrainian text)
                            if 'AI' in response.text or 'відео' in response.text.lower() or 'фотографій' in response.text.lower():
                                print("\n" + "=" * 70)
                                print("SUCCESS! FOUND LIVE SITE")
                                print("=" * 70)
                                print(f"\nYour live website:")
                                print(f"  {url}")
                                print()
                                driver.quit()
                                return url
                    except:
                        continue
            
            # Also check for links
            try:
                links = driver.find_elements(By.XPATH, "//a[contains(@href, 'vercel.app')]")
                for link in links:
                    href = link.get_attribute('href')
                    if href and (REPO_NAME in href.lower() or 'ai-video' in href.lower()):
                        url = href.split('?')[0]
                        try:
                            response = requests.get(url, timeout=5)
                            if response.status_code == 200:
                                if 'AI' in response.text or 'відео' in response.text:
                                    print("\n" + "=" * 70)
                                    print("SUCCESS! FOUND LIVE SITE")
                                    print("=" * 70)
                                    print(f"\nYour live website:")
                                    print(f"  {url}")
                                    print()
                                    driver.quit()
                                    return url
                        except:
                            continue
            except:
                pass
            
            elapsed = int(time.time() - start_time)
            if elapsed % 20 == 0:
                print(f"Still waiting... ({elapsed}s / {max_wait}s)")
                driver.refresh()
                time.sleep(3)
            
            time.sleep(5)
        
        print("\nTimeout reached. Checking one more time...")
        # Final check
        page_source = driver.page_source
        urls = re.findall(r'https://[a-zA-Z0-9-]+\.vercel\.app[^"\s<>]*', page_source)
        for url in urls:
            url = url.split('"')[0].split("'")[0].strip()
            if REPO_NAME in url.lower():
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"\nFound URL: {url}")
                        driver.quit()
                        return url
                except:
                    continue
        
        print("\nCould not find URL. Browser will stay open for manual check...")
        time.sleep(30)
        driver.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    return None

if __name__ == "__main__":
    url = get_correct_url()
    if url:
        print(f"\nDEPLOYMENT COMPLETE!")
        print(f"Live URL: {url}")
    else:
        print("\nCould not get URL automatically.")
        print("Please check: https://vercel.com/dashboard")
