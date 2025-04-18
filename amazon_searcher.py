from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import time
import random
import requests
import os
import zipfile
import sys
import pickle
import logging
from win32com.client import Dispatch
from textblob import TextBlob

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEBUG = True

def log_debug(message):
    if DEBUG:
        print(f"[DEBUG] {message}")

def get_chrome_version():
    """Get the installed Chrome version."""
    try:
        chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
        if os.path.exists(chrome_path):
            parser = Dispatch('Scripting.FileSystemObject')
            version = parser.GetFileVersion(chrome_path)
            return version.split('.')[0]  # Return major version number
    except Exception as e:
        log_debug(f"Error getting Chrome version: {e}")
    return None

def download_chromedriver():
    """Download the appropriate ChromeDriver version."""
    try:
        chrome_version = get_chrome_version()
        if not chrome_version:
            log_debug("Could not determine Chrome version. Please install Chrome first.")
            sys.exit(1)

        log_debug(f"Downloading ChromeDriver for Chrome version {chrome_version}")
        download_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{chrome_version}"
        response = requests.get(download_url)
        driver_version = response.text.strip()
        
        driver_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_win32.zip"
        response = requests.get(driver_url)
        
        with open("chromedriver.zip", "wb") as f:
            f.write(response.content)
        
        with zipfile.ZipFile("chromedriver.zip", "r") as zip_ref:
            zip_ref.extractall()
        
        os.remove("chromedriver.zip")
        log_debug("ChromeDriver downloaded and extracted successfully")
        return True
    except Exception as e:
        log_debug(f"Error downloading ChromeDriver: {e}")
        return False

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
    ]
    return random.choice(user_agents)

def setup_chrome_driver(driver_path):
    """Setup Chrome driver with anti-detection measures"""
    chrome_options = Options()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument(f'user-agent={get_random_user_agent()}')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    
    log_debug("Starting Chrome browser...")
    
    try:
        service = Service(driver_path)
        browser = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        if "This version of ChromeDriver only supports Chrome version" in str(e):
            log_debug("ChromeDriver version mismatch detected. Downloading correct version...")
            if download_chromedriver():
                # Retry with new ChromeDriver
                service = Service(driver_path)
                browser = webdriver.Chrome(service=service, options=chrome_options)
            else:
                raise Exception("Failed to download compatible ChromeDriver")
        else:
            raise e
    
    browser.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": get_random_user_agent()
    })
    browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    browser.set_window_size(1920, 1080)
    return browser

def get_html(url, driver_path):
    browser = setup_chrome_driver(driver_path)
    
    try:
        log_debug(f"Navigating to URL: {url}")
        browser.get(url)
        
        delay = random.uniform(3, 7)
        log_debug(f"Waiting {delay:.2f} seconds for page to load...")
        time.sleep(delay)
        
        wait = WebDriverWait(browser, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.s-result-item,div[data-component-type="s-search-result"]')))
        
        for i in range(3):
            scroll_amount = random.randint(300, 700)
            browser.execute_script(f"window.scrollTo(0, {scroll_amount})")
            time.sleep(random.uniform(0.5, 1.5))
        
        log_debug("Page loaded successfully")
        return browser.page_source
    except Exception as e:
        log_debug(f"Error during page load: {str(e)}")
        raise
    finally:
        browser.quit()

def extract_price(card):
    price_selectors = [
        'span.a-price-whole',
        'span.a-price span[aria-hidden="true"]',
        'span.a-price',
        'span.a-offscreen'
    ]
    
    for selector in price_selectors:
        price_elem = card.select_one(selector)
        if price_elem:
            price_text = price_elem.text.strip().replace('₹', '').replace(',', '').strip('.')
            # Extract numeric part only
            import re
            price_match = re.search(r'\d+(?:\.\d+)?', price_text)
            if price_match:
                return float(price_match.group())
    return float('inf')  # Return infinity for items with no price

def find_lowest_price_product(search_term, driver_path):
    search_term = search_term.replace(' ', '+')
    amazon_link = f"https://www.amazon.in/s?k={search_term}"
    amazon_home = 'https://www.amazon.in'
    max_retries = 3
    retry_count = 0
    
    lowest_price = float('inf')
    lowest_price_product = None
    
    while retry_count < max_retries:
        try:
            html = get_html(amazon_link, driver_path)
            log_debug("Parsing HTML with BeautifulSoup...")
            soup = BeautifulSoup(html, 'lxml')
            
            selectors = [
                'div[data-component-type="s-search-result"]',
                'div.s-result-item',
                'div.sg-col-inner'
            ]
            
            prod_cards = []
            for selector in selectors:
                prod_cards = soup.select(selector)
                if prod_cards:
                    log_debug(f"Found {len(prod_cards)} products using selector: {selector}")
                    break
            
            if not prod_cards:
                retry_count += 1
                log_debug(f"No products found. Retry {retry_count}/{max_retries}")
                time.sleep(random.uniform(5, 10))
                continue
            
            items = []
            for idx, card in enumerate(prod_cards[:10]):  # Look at first 10 products
                try:
                    title_elem = (card.select_one('h2 a.a-link-normal span') or 
                                card.select_one('h2 span.a-text-normal') or
                                card.select_one('h2'))
                    
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    
                    link_elem = card.select_one('h2 a') or card.select_one('a.a-link-normal')
                    if not link_elem:
                        continue
                        
                    link = link_elem.get('href', '')
                    if not link.startswith('http'):
                        link = amazon_home + link
                    
                    price = extract_price(card)
                    
                    if title and link and price != float('inf'):
                        items.append([title, price, link])
                        print(f"\nProduct {idx + 1}:")
                        print(f"Title: {title}")
                        print(f"Price: ₹{price}")
                        print(f"Link: {link}")
                        
                        if price < lowest_price:
                            lowest_price = price
                            lowest_price_product = [title, price, link]
                
                except Exception as e:
                    log_debug(f"Error processing product {idx + 1}: {str(e)}")
                    continue
            
            if items:
                print("\n" + "="*50)
                print(f"LOWEST PRICE PRODUCT:")
                print(f"Title: {lowest_price_product[0]}")
                print(f"Price: ₹{lowest_price_product[1]}")
                print(f"Link: {lowest_price_product[2]}")
                print("="*50)
                return lowest_price_product
            
        except Exception as e:
            retry_count += 1
            log_debug(f"Error during scraping (attempt {retry_count}/{max_retries}): {str(e)}")
            if retry_count < max_retries:
                time.sleep(random.uniform(5, 10))
            else:
                print(f"Error during scraping: {str(e)}")
    
    return None

class AmazonReviewScraper:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        self.driver = setup_chrome_driver(self.driver_path)
        return self.driver

    def handle_login(self):
        """Handle Amazon login process"""
        if os.path.exists('amazon_cookies.pkl'):
            self.driver.get("https://www.amazon.in")
            cookies = pickle.load(open("amazon_cookies.pkl", "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            return True

        self.driver.get("https://www.amazon.in")
        print("\nPlease log in to Amazon manually and press Enter to continue...")
        input()
        pickle.dump(self.driver.get_cookies(), open("amazon_cookies.pkl", "wb"))
        return True

    def navigate_to_reviews(self, product_url):
        """Navigate to the full review page by clicking 'See more reviews'"""
        self.driver.get(product_url)
        time.sleep(3)

        try:
            see_more_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "See more reviews"))
            )
            see_more_button.click()
            logger.info("Clicked 'See more reviews' to access the full review page.")
            time.sleep(3)
            return True
        except TimeoutException:
            logger.warning("Could not find 'See more reviews' button. Proceeding with main product page.")
            
            # Try to find alternative review links
            try:
                alt_review_links = self.driver.find_elements(By.PARTIAL_LINK_TEXT, "review")
                for link in alt_review_links:
                    if "customer-reviews" in link.get_attribute("href") or "customer-review" in link.get_attribute("href"):
                        link.click()
                        logger.info("Clicked alternative review link")
                        time.sleep(3)
                        return True
            except Exception:
                pass
                
            return False

    def extract_review_titles(self):
        """Extract only bolded review titles from the current page"""
        review_titles = []
        time.sleep(2)

        try:
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-hook="review-title"]')
            
            # If the first selector doesn't work, try alternatives
            if not review_elements:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'span[data-hook="review-title"]')
            
            if not review_elements:
                review_elements = self.driver.find_elements(By.CSS_SELECTOR, '.review-title')

            for review in review_elements:
                title = review.text.strip()
                if title:
                    review_titles.append(title)

            return review_titles

        except Exception as e:
            logger.error(f"Error extracting review titles: {e}")
            return []

    def go_to_next_page(self):
        """Attempt to go to the next page of reviews"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, 'li.a-last a')
            next_button.click()
            time.sleep(2)
            return True
        except NoSuchElementException:
            return False

    def analyze_sentiment(self, reviews):
        """Analyze sentiment and determine if the product is worth buying"""
        if not reviews:
            return "No reviews found to analyze"
            
        positive_count = 0
        negative_count = 0
        neutral_count = 0

        print("\n🔹 Sentiment Analysis of Reviews:")
        for i, review in enumerate(reviews, start=1):
            sentiment = TextBlob(review).sentiment.polarity  # Get sentiment score
            sentiment_str = ""
            
            if sentiment > 0.1:
                positive_count += 1
                sentiment_str = "Positive 👍"
            elif sentiment < -0.1:
                negative_count += 1
                sentiment_str = "Negative 👎"
            else:
                neutral_count += 1
                sentiment_str = "Neutral 😐"
                
            print(f"{i}. \"{review}\" - {sentiment_str} (score: {sentiment:.2f})")

        # Print sentiment distribution
        total = positive_count + negative_count + neutral_count
        print(f"\n📊 Sentiment Distribution:")
        print(f"Positive reviews: {positive_count} ({positive_count/total*100:.1f}%)")
        print(f"Neutral reviews: {neutral_count} ({neutral_count/total*100:.1f}%)")
        print(f"Negative reviews: {negative_count} ({negative_count/total*100:.1f}%)")

        # Determine final decision (ignoring neutral reviews for decision)
        if positive_count > negative_count:
            confidence = positive_count / max(1, (positive_count + negative_count)) * 100
            return f"Buy ✅ ({confidence:.1f}% positive reviews)"
        elif negative_count > positive_count:
            confidence = negative_count / max(1, (positive_count + negative_count)) * 100
            return f"Don't Buy ❌ ({confidence:.1f}% negative reviews)"
        else:
            return "Neutral ⚖️ (Equal positive and negative sentiment)"

    def scrape_review_titles(self, product_url, max_pages=2):
        """Scrape up to max_pages review titles from Amazon and analyze sentiment"""
        self.setup_driver()
        all_titles = []
        page_number = 1

        try:
            if not self.handle_login():
                logger.error("Login failed")
                self.driver.quit()
                return [], "Login failed, could not analyze reviews"

            has_reviews_page = self.navigate_to_reviews(product_url)
            if not has_reviews_page:
                logger.warning("Could not navigate to reviews page, attempting to extract from current page")

            while page_number <= max_pages:
                logger.info(f"Scraping page {page_number}")

                page_titles = self.extract_review_titles()
                all_titles.extend(page_titles)
                logger.info(f"Collected {len(page_titles)} titles from page {page_number}")

                if not page_titles or not self.go_to_next_page():
                    logger.info("No more pages available")
                    break

                page_number += 1
                time.sleep(2)

            # Perform sentiment analysis
            final_decision = self.analyze_sentiment(all_titles)
            return all_titles, final_decision
            
        except Exception as e:
            logger.error(f"Error during review scraping: {e}")
            return [], f"Error occurred: {str(e)}"
        finally:
            if self.driver:
                self.driver.quit()

def main():
    # Setup chrome driver path
    DRIVER_PATH = str(Path('chromedriver.exe').resolve())
    
    # Get user input for product search
    search_term = input("Enter item to search: ")
    
    # Find the lowest priced product
    print("\n🔍 Searching for the lowest priced product...")
    lowest_price_product = find_lowest_price_product(search_term, DRIVER_PATH)
    
    if not lowest_price_product:
        print("❌ Could not find any products. Please try again with a different search term.")
        return
    
    product_url = lowest_price_product[2]
    
    # Now scrape reviews for the lowest priced product
    print("\n📊 Analyzing reviews for the lowest priced product...")
    print(f"Product: {lowest_price_product[0]}")
    print(f"Price: ₹{lowest_price_product[1]}")
    print(f"URL: {product_url}")
    
    # Initialize review scraper and analyze reviews
    scraper = AmazonReviewScraper(DRIVER_PATH)
    review_titles, decision = scraper.scrape_review_titles(product_url, max_pages=3)
    
    print("\n🔹 Extracted Review Titles:")
    if review_titles:
        for i, title in enumerate(review_titles, start=1):
            print(f"{i}. {title}")
    else:
        print("No review titles were extracted.")
    
    print("\n🔍 Final Verdict:", decision)
    
    print("\n💡 Should you buy the product?")
    if "Buy ✅" in decision:
        print("Recommendation: YES - This product appears to have overall positive reviews and is the lowest priced option.")
    elif "Don't Buy ❌" in decision:
        print("Recommendation: NO - Although this is the lowest priced option, reviews suggest poor quality or satisfaction.")
    else:
        print("Recommendation: MAYBE - Reviews are mixed. Consider your specific needs carefully.")

if __name__ == "__main__":
    main()