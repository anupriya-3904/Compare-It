from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to ChromeDriver (update accordingly)
chrome_driver_path = "chromedriver.exe"

# Set up Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# Initialize WebDriver using Service
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)

# Flipkart product review page URL (replace with the actual product URL)
url = "https://www.flipkart.com/vivo-t3-5g-crystal-flake-128-gb/product-reviews/itm69b3c5633378f?pid=MOBGYT3VN2J3GM45&lid=LSTMOBGYT3VN2J3GM45LBHTKC&marketplace=FLIPKART"

driver.get(url)
wait = WebDriverWait(driver, 10)

for page in range(1, 4):
    print(f"\n--- Page {page} Reviews ---")
    
    try:
        # Scroll to the bottom to load all reviews
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
        time.sleep(3)  # Give time for reviews to load
        
        # Extract reviews using the correct class
        review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'VLIitu')]")

        if not review_elements:
            print("No reviews found on this page. Trying another selector...")
            review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'JxFEK3 _4800EI')]")  

        if not review_elements:
            print("Still no reviews found. Check class names or XPath.")
            break

        # Print each review text
        for review in review_elements:
            print(review.text)

        # Find and click "Next" button
        next_buttons = driver.find_elements(By.XPATH, "//a[contains(@class, '_1LKTO3')]")
        if len(next_buttons) > 1:
            next_buttons[1].click()  # Click "Next"
            time.sleep(3)
        else:
            print("No more pages.")
            break

    except Exception as e:
        print(f"Error: {e}")
        break

# Close the browser
driver.quit()
