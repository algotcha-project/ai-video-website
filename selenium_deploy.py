"""
Selenium automation to complete Vercel deployment
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def deploy_with_selenium():
    """Automate Vercel deployment using Selenium"""
    print("Starting Selenium automation...")
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    # Don't run headless so user can see what's happening
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        url = "https://vercel.com/new/import?repositoryUrl=https://github.com/algotcha-project/ai-video-website"
        print(f"Opening: {url}")
        driver.get(url)
        
        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Try to find and click Deploy button
        try:
            # Look for deploy button - it might have different selectors
            deploy_selectors = [
                "button[type='submit']",
                "button:contains('Deploy')",
                "[data-testid='deploy-button']",
                "//button[contains(text(), 'Deploy')]",
            ]
            
            deploy_button = None
            for selector in deploy_selectors:
                try:
                    if selector.startswith("//"):
                        deploy_button = driver.find_element(By.XPATH, selector)
                    else:
                        deploy_button = driver.find_element(By.CSS_SELECTOR, selector)
                    if deploy_button:
                        break
                except:
                    continue
            
            if deploy_button:
                print("Found Deploy button, clicking...")
                driver.execute_script("arguments[0].scrollIntoView(true);", deploy_button)
                time.sleep(1)
                deploy_button.click()
                print("Deploy button clicked!")
                print("Waiting for deployment to start...")
                time.sleep(10)
                print("Deployment initiated! Check the Vercel dashboard.")
            else:
                print("Could not find Deploy button automatically.")
                print("Please click 'Deploy' manually on the page.")
                print("The page will stay open for 60 seconds...")
                time.sleep(60)
                
        except Exception as e:
            print(f"Error clicking button: {e}")
            print("Please click 'Deploy' manually.")
            time.sleep(30)
        
        # Keep browser open for a bit to see results
        print("\nBrowser will stay open for 30 more seconds...")
        time.sleep(30)
        
        driver.quit()
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nPlease complete deployment manually:")
        print("1. Go to: https://vercel.com/new/import?repositoryUrl=https://github.com/algotcha-project/ai-video-website")
        print("2. Click 'Deploy'")
        print("3. Wait for deployment")

if __name__ == "__main__":
    deploy_with_selenium()
