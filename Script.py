from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def get_product_title(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    browser = webdriver.Chrome(options=options)

    browser.get(url)
    time.sleep(3)  # Let page load

    try:
        title_element = browser.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]')
        title = title_element.text.strip()
    except:
        title = "Title not found"

    browser.quit()
    return title

# Example usage
url = "https://chaldal.com/radhuni-chotpoti-masala-special-offer-20-gm"  # use your real product URL
print(get_product_title(url))
