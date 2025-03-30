import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CSV_FILE = "chaldal_products.csv"

def load_urls_from_csv(file_path="product_urls.csv"):
    if not os.path.exists(file_path):
        print("URL list file not found!")
        return []
    
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row["URL"].strip() for row in reader if row["URL"].strip()]


def init_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")

    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
    }
    options.add_experimental_option("prefs", prefs)

    return webdriver.Chrome(options=options)

def get_title_and_size(browser):
    try:
        wrapper = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.nameAndSubtext'))
        )
        title = wrapper.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]').text.strip()
        size = wrapper.find_element(By.CSS_SELECTOR, 'span').text.strip()
        return title, size
    except:
        return "Title not found", "Size not found"

def get_product_price(browser):
    try:
        price_element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[itemprop="price"]'))
        )
        return price_element.get_attribute("content").strip()
    except:
        return "Price not found"

def get_full_price(browser):
    try:
        full_price_element = WebDriverWait(browser, 5).until(
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

def get_all_product_info(browser, url):
    browser.get(url)
    title, size = get_title_and_size(browser)
    selling_price = get_product_price(browser)
    mrp = get_full_price(browser)

    if mrp == "Full price not found" or not mrp.isdigit():
        mrp = selling_price  # Fallback to selling price

    discount = get_discount_info(browser)
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    return {
        "URL": url,
        "Title": title,
        "Pack Size": size,
        "Selling Price": selling_price,
        "MRP": mrp,
        "Discount": discount,
        "LastUpdated": timestamp
    }

def load_existing_data():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def append_row(row):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["URL", "Title", "Pack Size", "Selling Price", "MRP", "Discount", "LastUpdated"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def main():
    browser = init_browser()
    existing_data = load_existing_data()

    urls = load_urls_from_csv()
    for url in urls:
        print(f"Fetching: {url}")
        new_entry = get_all_product_info(browser, url)

        # Check if URL already exists
        previous_prices = [row for row in existing_data if row["URL"] == url]
        latest_entry = previous_prices[-1] if previous_prices else None

        if not latest_entry or latest_entry["Current Price"] != new_entry["Current Price"]:
            print(f"New price or product detected. Appending to CSV.")
            append_row(new_entry)
        else:
            print(f"No price change for: {new_entry['Title']}")

    browser.quit()
    print("Done ✅")

if __name__ == "__main__":
    main()
