import os
import time
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from plyer import notification
import tkinter as tk
from tkinter import messagebox

# File and folder paths
EXCEL_FILE = "Tracking selected products.xlsx"
LOG_DIR = "change_log_selected_products"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.txt")

def load_product_urls(file_path="product_urls.csv"):
    """Loads product URLs from a CSV file."""
    if not os.path.exists(file_path):
        print("URL list file not found!")
        return []
    df_urls = pd.read_csv(file_path)
    return df_urls["URL"].dropna().astype(str).tolist()

def launch_browser():
    """Launches a headless Chrome browser with images disabled."""
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

def to_float(val):
    """Converts a string to float; returns None on failure."""
    try:
        return float(val.replace(",", "").strip())
    except Exception:
        return None

# --- Extraction Functions ---

def extract_title_and_pack_size(browser):
    """Extracts the product title and pack size from the page."""
    try:
        wrapper = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.nameAndSubtext'))
        )
        title = wrapper.find_element(By.CSS_SELECTOR, 'h1[itemprop="name"]').text.strip()
        pack_size = wrapper.find_element(By.CSS_SELECTOR, 'span').text.strip()
        return title, pack_size
    except:
        return "Title not found", "Size not found"

def extract_selling_price(browser):
    """Extracts the selling price from the page."""
    try:
        price_element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span[itemprop="price"]'))
        )
        return price_element.get_attribute("content").strip()
    except:
        return "Price not found"

def extract_mrp(browser):
    """Extracts the MRP from the page."""
    try:
        mrp_element = WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.fullPrice span:last-child'))
        )
        return mrp_element.text.strip()
    except:
        return "Full price not found"

def extract_discount_info(browser):
    """Extracts discount information from the page."""
    try:
        discount_element = browser.find_element(By.CSS_SELECTOR, 'div.discount span')
        return discount_element.text.strip()
    except:
        return "No discount"

def collect_product_info(browser, url):
    """
    Navigates to the given URL and extracts product information.
    Returns a dictionary with numeric prices and a computed discount.
    """
    browser.get(url)
    title, pack_size = extract_title_and_pack_size(browser)
    selling_price_text = extract_selling_price(browser)
    mrp_text = extract_mrp(browser)
    
    # Fallback for MRP if missing or non-numeric
    if mrp_text == "Full price not found" or not mrp_text.replace('.', '', 1).isdigit():
        mrp_text = selling_price_text
    
    selling_price = to_float(selling_price_text)
    mrp = to_float(mrp_text)
    if mrp is None:
        mrp = selling_price
    
    # Compute discount: (MRP - Selling Price) / MRP, rounded to 2 decimals.
    if mrp and mrp > 0 and selling_price is not None:
        discount_value = round((mrp - selling_price) / mrp, 2)
    else:
        discount_value = 0.0
    
    last_updated = datetime.now().strftime("%Y-%m-%d")
    
    return {
        "URL": url,
        "Title": title,
        "Pack Size": pack_size,
        "MRP": mrp,
        "Selling Price": selling_price,
        "Discount": discount_value,
        "LastUpdated": last_updated
    }

# --- Data Storage Functions using Excel ---

def load_existing_data():
    """Loads existing Excel data into a DataFrame; returns an empty DataFrame if file does not exist."""
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    else:
        return pd.DataFrame(columns=["URL", "Title", "Pack Size", "MRP", "Selling Price", "Discount", "LastUpdated"])

def update_excel_and_log(scraped_products):
    """
    Compares scraped products with existing Excel data.
    For each product, if it is new or its Selling Price differs from the latest record,
    appends the new entry and logs the change.
    The Excel file is sorted by Title (ascending) and LastUpdated (descending).
    
    Returns:
        tuple: (new_count, price_change_count)
    """
    df_existing = load_existing_data()
    new_entries = []
    log_blocks = []
    new_count = 0
    price_change_count = 0

    for product in scraped_products:
        sku = product["Title"]
        df_sku = df_existing[df_existing["Title"] == sku]
        if df_sku.empty:
            new_entries.append(product)
            new_count += 1
            block = [
                f"SKU Name: {product['Title']}",
                f"Pack Size: {product['Pack Size']}",
                f"MRP: {product['MRP']}",
                f"Selling Price: {product['Selling Price']}",
                f"Discount: {product['Discount']}",
                f"Product URL: {product['URL']}",
                f"LastUpdated: {product['LastUpdated']}",
                "Previous prices: None"
            ]
            log_blocks.append(block)
        else:
            # Sort existing records for this product by LastUpdated (descending: latest first)
            df_sku_sorted = df_sku.sort_values(by="LastUpdated", ascending=False)
            last_record = df_sku_sorted.iloc[0]
            if last_record["Selling Price"] != product["Selling Price"]:
                new_entries.append(product)
                price_change_count += 1
                notify_price_change(product["Title"], last_record["Selling Price"], product["Selling Price"])
                block = [
                    f"SKU Name: {product['Title']}",
                    f"Pack Size: {product['Pack Size']}",
                    f"MRP: {product['MRP']}",
                    f"Selling Price: {product['Selling Price']}",
                    f"Discount: {product['Discount']}",
                    f"Product URL: {product['URL']}",
                    f"LastUpdated: {product['LastUpdated']}",
                    "Previous prices:"
                ]
                for _, row in df_sku_sorted.iterrows():
                    block.append(f"{row['LastUpdated']}: {row['Selling Price']}")
                log_blocks.append(block)

    if new_entries:
        df_new = pd.DataFrame(new_entries)
        if df_existing.empty:
            df_updated = df_new.copy()
        else:
            df_updated = pd.concat([df_existing, df_new], ignore_index=True)
        df_updated.sort_values(by=["Title", "LastUpdated"], ascending=[True, False], inplace=True)
        df_updated.to_excel(EXCEL_FILE, index=False)

        for block in log_blocks:
            log_change_block(block)
    else:
        print("No new entries or price changes.")
    
    return new_count, price_change_count

# --- Notification and Summary Dialog Functions ---

def notify_price_change(title, old_price, new_price):
    """Shows a Windows notification for a price change."""
    notification.notify(
        title=f"Price Change: {title}",
        message=f"{old_price} → {new_price}",
        timeout=10
    )

def log_change_block(lines):
    """Writes a log block to file and prints it to the console."""
    block_text = "\n".join(lines) + "\n\n===========\n"
    print(block_text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(block_text)

def show_summary_dialog(new_count, price_change_count):
    """Displays a tkinter dialog summarizing the changes."""
    total_changes = new_count + price_change_count
    summary_message = (
        f"Total changes: {total_changes}\n"
        f"New products added: {new_count}\n"
        f"Products with price change: {price_change_count}\n\n"
        f"Please check the log file in:\n{os.path.abspath(LOG_DIR)}"
    )
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Selected Products Update Summary", summary_message)
    root.destroy()

# --- Main Workflow ---

def main():
    browser = launch_browser()
    product_urls = load_product_urls()
    scraped_products = []
    for url in product_urls:
        print(f"\n🔍 Fetching: {url}")
        product_info = collect_product_info(browser, url)
        scraped_products.append(product_info)
    browser.quit()
    new_count, price_change_count = update_excel_and_log(scraped_products)
    if new_count > 0 or price_change_count > 0:
        show_summary_dialog(new_count, price_change_count)
    else:
        print("\n✅ Finished tracking. No changes detected.")

if __name__ == "__main__":
    main()
