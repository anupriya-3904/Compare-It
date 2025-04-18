import time
import pickle
import os
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from textblob import TextBlob  # Import TextBlob for sentiment analysis

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AmazonReviewScraper:
    def __init__(self, driver_path):
        self.driver_path = driver_path
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        chrome_options = Options()
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        service = Service(executable_path=self.driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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
            logger.error("Could not find 'See more reviews' button. Proceeding with main product page.")
            return False

    def extract_review_titles(self):
        """Extract only bolded review titles from the current page"""
        review_titles = []
        time.sleep(2)

        try:
            review_elements = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-hook="review-title"]')

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
        positive_count = 0
        negative_count = 0

        for review in reviews:
            sentiment = TextBlob(review).sentiment.polarity  # Get sentiment score
            if sentiment > 0:
                positive_count += 1
            elif sentiment < 0:
                negative_count += 1

        # Determine final decision
        if positive_count > negative_count:
            return "Buy ✅ (Majority of reviews are positive)"
        else:
            return "Don't Buy ❌ (Majority of reviews are negative)"

    def scrape_review_titles(self, product_url, max_pages=2):
        """Scrape up to max_pages review titles from Amazon and analyze sentiment"""
        all_titles = []
        page_number = 1

        if not self.handle_login():
            logger.error("Login failed")
            return []

        self.navigate_to_reviews(product_url)

        while page_number <= max_pages:
            logger.info(f"Scraping page {page_number}")

            page_titles = self.extract_review_titles()
            all_titles.extend(page_titles)
            logger.info(f"Collected {len(page_titles)} titles from page {page_number}")

            if not self.go_to_next_page():
                logger.info("No more pages available")
                break

            page_number += 1
            time.sleep(2)

        self.driver.quit()

        # Perform sentiment analysis
        final_decision = self.analyze_sentiment(all_titles)
        return all_titles, final_decision

def main():
    driver_path = "chromedriver.exe"  # Update this path if needed
    product_url = "https://www.amazon.in/iPhone-16-128-Plus-Ultrmarine/dp/B0DGJ65N7V/?_encoding=UTF8&pd_rd_w=yEakG&content-id=amzn1.sym.509965a2-791b-4055-b876-943397d37ed3%3Aamzn1.symc.fc11ad14-99c1-406b-aa77-051d0ba1aade&pf_rd_p=509965a2-791b-4055-b876-943397d37ed3&pf_rd_r=SCX972VD4SUQEN5IGP37&pd_rd_wg=sWC41&pd_rd_r=9b386d7d-1d0f-4706-b51f-bc998968b776&ref_=pd_hp_d_atf_ci_mcx_mr_ca_hp_atf_d&th=1"

    scraper = AmazonReviewScraper(driver_path)
    review_titles, decision = scraper.scrape_review_titles(product_url, max_pages=3)

    print("\n🔹 Extracted Bolded Review Titles:")
    for i, title in enumerate(review_titles, start=1):
        print(f"{i}. {title}")

    print("\n🔍 **Final Verdict:**", decision)

if __name__ == "__main__":
    main()
