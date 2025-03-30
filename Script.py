import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from plyer import notification

# Paths
CSV_FILE = "chaldal_products.csv"
LOG_DIR = "change_log"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.txt")

# Load product URLs from file
def load_product_urls(file_path="product_urls.csv"):
    if not os.path.exists(file_path):
        print("URL list file not found!")
        return []
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row["URL"].strip() for row in reader if row["URL"].strip()]

# Setup headless browser
def launch_browser():
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

# Extract product title and pack size
def extract_title_and_pack_size(browser):
    try:
        wrapper = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.nameAndSubtext'))
        )
        title = wrapper.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]').text.strip()
        pack_size = wrapper.find_element(By.CSS_SELECTOR, 'span').text.strip()
        return title, pack_size
    except:
        return "Title not found", "Size not found"

# Extract selling price
def extract_selling_price(browser):
    try:
        price_element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[itemprop="price"]'))
        )
        return price_element.get_attribute("content").strip()
    except:
        return "Price not found"

# Extract MRP
def extract_mrp(browser):
    try:
        mrp_element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.fullPrice span:last-child'))
        )
        return mrp_element.text.strip()
    except:
        return "Full price not found"

# Extract discount info
def extract_discount_info(browser):
    try:
        discount_element = browser.find_element(By.CSS_SELECTOR, 'div.discount span')
        return discount_element.text.strip()
    except:
        return "No discount"

# Collect all product info
def collect_product_info(browser, url):
    browser.get(url)
    title, pack_size = extract_title_and_pack_size(browser)
    selling_price = extract_selling_price(browser)
    mrp = extract_mrp(browser)

    if mrp == "Full price not found" or not mrp.replace('.', '', 1).isdigit():
        mrp = selling_price  # fallback if MRP missing

    discount = extract_discount_info(browser)
    last_updated = datetime.now().strftime("%Y-%m-%d")
    return {
        "URL": url,
        "Title": title,
        "Pack Size": pack_size,
        "Selling Price": selling_price,
        "MRP": mrp,
        "Discount": discount,
        "LastUpdated": last_updated
    }

# Load previously saved product data
def load_existing_data():
    if not os.path.exists(CSV_FILE):
        return []
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

# Append new entry to CSV
def append_product_row(row):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["URL", "Title", "Pack Size", "MRP", "Selling Price", "Discount", "LastUpdated"])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# Sort CSV by Title and LastUpdated
def sort_csv_file():
    if not os.path.exists(CSV_FILE):
        return
    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        data = list(csv.DictReader(f))
    sorted_data = sorted(data, key=lambda x: (
        x["Title"],
        datetime.strptime(x["LastUpdated"], "%Y-%m-%d")
    ))
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["URL", "Title", "Pack Size", "MRP", "Selling Price", "Discount", "LastUpdated"])
        writer.writeheader()
        writer.writerows(sorted_data)

# Show Windows notification
def notify_price_change(title, old_price, new_price):
    notification.notify(
        title=f"Price Change: {title}",
        message=f"{old_price} → {new_price}",
        timeout=10
    )

# Log to both file and console
def log_change_block(lines):
    block = "\n".join(lines) + "\n\n===========\n"
    print(block)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(block)

# Main workflow
def main():
    browser = launch_browser()
    existing_data = load_existing_data()
    product_urls = load_product_urls()

    for url in product_urls:
        print(f"\n🔍 Fetching: {url}")
        new_entry = collect_product_info(browser, url)

        # Find existing records
        history = [row for row in existing_data if row["URL"] == url]
        latest = history[-1] if history else None

        is_new_product = not latest
        price_changed = latest and latest["Selling Price"] != new_entry["Selling Price"]

        if is_new_product or price_changed:
            if price_changed:
                notify_price_change(new_entry["Title"], latest["Selling Price"], new_entry["Selling Price"])

            log_lines = [
                f"Title: {new_entry['Title']}",
                f"Pack Size: {new_entry['Pack Size']}",
                f"MRP: {new_entry['MRP']}",
                f"Selling Price: {new_entry['Selling Price']}",
                f"Discount: {new_entry['Discount']}",
                "Previous prices:"
            ]
            for row in history:
                log_lines.append(f"{row['LastUpdated']}: {row['Selling Price']}")
            log_change_block(log_lines)
            append_product_row(new_entry)
        else:
            print(f"✅ No price change for: {new_entry['Title']}")

    browser.quit()
    sort_csv_file()
    print("\n✅ Finished tracking.")

if __name__ == "__main__":
    main()
