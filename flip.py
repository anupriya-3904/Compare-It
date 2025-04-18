from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import sys

def extract_flipkart_reviews(product_url, pages_to_scrape=3):
    """
    Extract and print reviews from a Flipkart product page
    
    Args:
        product_url: URL of the Flipkart product or product review page
        pages_to_scrape: Number of review pages to scrape
    """
    # Path to ChromeDriver
    chrome_driver_path = "chromedriver.exe"
    
    # Set up Chrome options with comprehensive configurations
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        # Initialize WebDriver
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set wait time for elements
        wait = WebDriverWait(driver, 10)
        
        # Navigate to the product URL
        print(f"Navigating to: {product_url}")
        driver.get(product_url)
        time.sleep(3)
        
        # If the URL is a product page (not review page), find and click the reviews button
        if "product-reviews" not in product_url:
            print("Looking for the reviews section...")
            
            # Get total page height for scrolling
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            # Review button XPath variations to try
            review_button_xpaths = [
                "//div[contains(text(), 'All') and contains(text(), 'reviews')]",
                "//a[contains(text(), 'All') and contains(text(), 'reviews')]",
                "//span[contains(text(), 'All') and contains(text(), 'reviews')]",
                "//*[contains(text(), 'View all reviews')]",
                "//*[contains(text(), 'All reviews')]",
                "//div[contains(@class, 'reviews-count')]",
                "//div[contains(text(), 'reviews')]",
                "//div[contains(@class, '_3UAT2v') and contains(text(), 'Ratings & Reviews')]",
                "//div[contains(@class, '_3UAT2v')]//span[contains(text(), 'reviews')]"
            ]
            
            # Scroll through page looking for review button
            review_button_found = False
            for scroll_percent in [0, 0.25, 0.5, 0.75, 1]:
                # Scroll to position
                scroll_height = int(total_height * scroll_percent)
                driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                time.sleep(1)
                
                # Try each XPath at current scroll position
                for xpath in review_button_xpaths:
                    try:
                        potential_buttons = driver.find_elements(By.XPATH, xpath)
                        for button in potential_buttons:
                            if button.is_displayed() and button.is_enabled():
                                print(f"Found review button: {button.text}")
                                try:
                                    # Try different click methods
                                    try:
                                        button.click()
                                    except:
                                        try:
                                            driver.execute_script("arguments[0].click();", button)
                                        except:
                                            driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                            time.sleep(1)
                                            button.click()
                                    
                                    print("Successfully clicked review button")
                                    time.sleep(3)
                                    review_button_found = True
                                    break
                                except Exception as click_error:
                                    print(f"Failed to click button: {click_error}")
                    except Exception:
                        continue
                
                if review_button_found:
                    break
            
            if not review_button_found:
                print("Could not find reviews button. Attempting to extract reviews from current page...")
        
        # Extract reviews from each page
        all_reviews = []
        
        for page in range(1, pages_to_scrape + 1):
            print(f"\n--- Page {page} Reviews ---")
            
            # Scroll to the bottom to load all reviews
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
            time.sleep(3)  # Give time for reviews to load
            
            # Try different review element selectors
            review_xpath_patterns = [
                "//div[contains(@class, 'VLIitu')]",
                "//div[contains(@class, 'JxFEK3 _4800EI')]",
                "//div[contains(@class, '_27M-vq')]",
                "//div[contains(@class, 't-ZTKy')]//div[contains(@class, '_6K-7Co')]",
                "//div[contains(@class, '_27M-vq')]//div[contains(@class, 't-ZTKy')]",
                "//div[contains(@class, 'review-text')]"
            ]
            
            review_elements = []
            for xpath in review_xpath_patterns:
                review_elements = driver.find_elements(By.XPATH, xpath)
                if review_elements:
                    print(f"Found {len(review_elements)} reviews using pattern: {xpath}")
                    break
            
            if not review_elements:
                print("No reviews found on this page. Checking for any text content...")
                try:
                    # Try to extract reviews as text elements
                    potential_text_elements = driver.find_elements(By.XPATH, 
                                            "//div[contains(@class, 'col') and string-length(text()) > 20]")
                    if potential_text_elements:
                        review_elements = potential_text_elements
                        print(f"Found {len(review_elements)} potential text elements")
                    else:
                        print("No text elements found. Moving to next page.")
                except:
                    print("Failed to find any reviews on this page.")
            
            # Extract and print reviews
            for i, review in enumerate(review_elements):
                try:
                    review_text = review.text.strip()
                    if review_text and review_text not in all_reviews:
                        all_reviews.append(review_text)
                        print(f"Review {i+1}:")
                        print("-" * 50)
                        print(review_text)
                        print("-" * 50)
                except Exception as e:
                    print(f"Error extracting review: {e}")
            
            # If there are more pages to scrape, click the "Next" button
            if page < pages_to_scrape:
                next_button_found = False
                next_button_patterns = [
                    "//a[contains(@class, '_1LKTO3')]",
                    "//span[contains(text(), 'Next')]",
                    "//a[contains(text(), 'Next')]",
                    "//button[contains(text(), 'Next')]"
                ]
                
                for pattern in next_button_patterns:
                    try:
                        next_buttons = driver.find_elements(By.XPATH, pattern)
                        if next_buttons:
                            if len(next_buttons) > 1:
                                # Usually the second one is "Next" (first is "Previous")
                                next_buttons[1].click()
                            else:
                                next_buttons[0].click()
                                
                            next_button_found = True
                            print("Clicked Next button")
                            time.sleep(3)
                            break
                    except Exception as e:
                        continue
                
                if not next_button_found:
                    print("No more pages or couldn't find Next button.")
                    break
        
        # Print summary
        print("\n--- Review Summary ---")
        print(f"Total reviews extracted: {len(all_reviews)}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        # Clean up resources
        driver.quit()
        print("Browser closed successfully")

if __name__ == "__main__":
    # Get product URL from command line argument or user input
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Enter the Flipkart product URL: ")
    
    # Specify number of pages to scrape
    pages = 3
    
    # Run the scraper
    extract_flipkart_reviews(url, pages)