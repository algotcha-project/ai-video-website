"""
Complete deployment and get the live URL
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import re

REPO_NAME = "ai-video-website"
IMPORT_URL = "https://vercel.com/new/import?repositoryUrl=https://github.com/algotcha-project/ai-video-website"

def complete_deployment_and_get_url():
    """Complete the deployment and wait for URL"""
    print("=" * 70)
    print("COMPLETING DEPLOYMENT AND GETTING URL")
    print("=" * 70)
    print()
    
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("Step 1: Opening Vercel import page...")
        driver.get(IMPORT_URL)
        time.sleep(5)
        
        # Check if we need to deploy
        print("Step 2: Checking if deployment is needed...")
        
        # Look for Deploy button
        deploy_button = None
        deploy_selectors = [
            "//button[contains(text(), 'Deploy')]",
            "button[type='submit']",
            "//button[@type='submit']",
        ]
        
        for selector in deploy_selectors:
            try:
                if selector.startswith("//"):
                    deploy_button = driver.find_element(By.XPATH, selector)
                else:
                    deploy_button = driver.find_element(By.CSS_SELECTOR, selector)
                if deploy_button and deploy_button.is_displayed():
                    print("Found Deploy button, clicking...")
                    driver.execute_script("arguments[0].scrollIntoView(true);", deploy_button)
                    time.sleep(1)
                    deploy_button.click()
                    print("Deploy button clicked!")
                    break
            except:
                continue
        
        if not deploy_button:
            print("Deploy button not found - checking if already deployed...")
        
        # Wait for deployment to start
        print("\nStep 3: Waiting for deployment to start...")
        time.sleep(10)
        
        # Look for deployment URL or status
        print("Step 4: Looking for deployment URL...")
        
        max_wait = 180  # 3 minutes
        start_time = time.time()
        check_interval = 5
        
        while time.time() - start_time < max_wait:
            # Check page source for vercel.app URLs
            page_source = driver.page_source
            urls = re.findall(r'https://[a-zA-Z0-9-]+\.vercel\.app[^"\s]*', page_source)
            
            if urls:
                # Filter to get the main deployment URL
                for url in urls:
                    if REPO_NAME in url or 'vercel.app' in url:
                        # Clean URL
                        url = url.split('"')[0].split("'")[0].split(' ')[0]
                        # Verify it's accessible
                        try:
                            response = requests.get(url, timeout=5)
                            if response.status_code == 200:
                                print(f"\n" + "=" * 70)
                                print("SUCCESS! FOUND LIVE SITE")
                                print("=" * 70)
                                print(f"\nYour live website:")
                                print(f"  {url}")
                                print()
                                driver.quit()
                                return url
                        except:
                            continue
            
            # Check if there's a link to the deployment
            try:
                links = driver.find_elements(By.XPATH, "//a[contains(@href, 'vercel.app')]")
                for link in links:
                    href = link.get_attribute('href')
                    if href and REPO_NAME in href:
                        url = href.split('?')[0]  # Remove query params
                        try:
                            response = requests.get(url, timeout=5)
                            if response.status_code == 200:
                                print(f"\n" + "=" * 70)
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
            if elapsed % 15 == 0:  # Print every 15 seconds
                print(f"Still deploying... ({elapsed}s)")
            
            time.sleep(check_interval)
            
            # Refresh page occasionally
            if elapsed % 30 == 0:
                driver.refresh()
                time.sleep(3)
        
        print("\nDeployment is taking longer than expected...")
        print("Checking final status...")
        
        # Final check
        page_source = driver.page_source
        urls = re.findall(r'https://[a-zA-Z0-9-]+\.vercel\.app[^"\s]*', page_source)
        if urls:
            url = urls[0].split('"')[0].split("'")[0]
            print(f"\nFound URL: {url}")
            driver.quit()
            return url
        
        print("\nCould not find URL automatically.")
        print("Please check the Vercel dashboard manually.")
        print("Browser will stay open for 30 seconds...")
        time.sleep(30)
        driver.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        return None
    
    return None

if __name__ == "__main__":
    url = complete_deployment_and_get_url()
    if url:
        print(f"\n✅ DEPLOYMENT COMPLETE!")
        print(f"🌐 Live URL: {url}")
    else:
        print("\n⚠ Could not get URL automatically.")
        print("Please check: https://vercel.com/dashboard")
