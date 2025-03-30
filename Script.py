from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def init_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)

def get_product_title(url):
    browser = init_browser()
    browser.get(url)
    time.sleep(3)

    try:
        title_element = browser.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]')
        title = title_element.text.strip()
    except:
        title = "Title not found"

    browser.quit()
    return title

def get_product_price(url):
    browser = init_browser()
    browser.get(url)
    time.sleep(3)

    try:
        price_element = browser.find_element(By.CSS_SELECTOR, 'span[itemprop="price"]')
        price = price_element.get_attribute("content").strip()
    except:
        price = "Price not found"

    browser.quit()
    return price

# Example usage
url = "https://chaldal.com/radhuni-chotpoti-masala-special-offer-50-gm"
print("Title:", get_product_title(url))
print("Price:", get_product_price(url))
