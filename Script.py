from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def init_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)

def get_title_and_size(browser):
    try:
        wrapper = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.nameAndSubtext'))
        )
        title = wrapper.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]').text.strip()
        size = wrapper.find_element(By.CSS_SELECTOR, 'span').text.strip()
        return title, size
    except:
        return "Title not found", "Size not found"

def get_product_price(url, browser):
    try:
        price_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[itemprop="price"]'))
        )
        return price_element.get_attribute("content").strip()
    except:
        return "Price not found"

def get_full_price(browser):
    try:
        full_price_element = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.fullPrice span:last-child'))
        )
        return full_price_element.text.strip()
    except:
        return "Full price not found"

def get_discount_info(browser):
    try:
        discount_element = browser.find_element(By.CSS_SELECTOR, 'div.discount span')
        return discount_element.text.strip()
    except:
        return "No discount"

def get_all_product_info(url):
    browser = init_browser()
    browser.get(url)

    title, pack_size = get_title_and_size(browser)
    price = get_product_price(url, browser)
    full_price = get_full_price(browser)
    discount = get_discount_info(browser)

    browser.quit()

    return {
        "Title": title,
        "Current Price": price,
        "Pack Size": pack_size,
        "Original Price": full_price,
        "Discount": discount
    }

# Example usage
url = "https://chaldal.com/radhuni-chotpoti-masala-special-offer-50-gm"
product_info = get_all_product_info(url)

for key, value in product_info.items():
    print(f"{key}: {value}")
