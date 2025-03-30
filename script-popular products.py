import os
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from plyer import notification

# Constants and file paths
EXCEL_FILE = "Popular products tracking in Chaldal.xlsx"
CHANGE_LOG_DIR = "change_log_popular"
os.makedirs(CHANGE_LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(CHANGE_LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.txt")


def launch_browser():
    """Launches a headless Chrome browser with images disabled."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    return webdriver.Chrome(options=options)


def scrape_popular_products(url="https://chaldal.com/popular"):
    """
    Scrapes product details from the Popular page.

    Returns:
        list of dict: Each dictionary contains:
          - SKU Name
          - Pack Size
          - MRP
          - Selling Price
          - Details URL
          - LastUpdated (YYYY-MM-DD)
    """
    browser = launch_browser()
    browser.get(url)

    # Wait for product containers to load
    WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.productPane div.product"))
    )
    product_elements = browser.find_elements(By.CSS_SELECTOR, "div.productPane div.product")
    products = []

    for prod in product_elements:
        # Extract SKU Name
        try:
            sku_name = prod.find_element(By.CSS_SELECTOR, ".name").text.strip()
        except Exception:
            sku_name = "N/A"

        # Extract Pack Size (e.g. "1 kg" or "250 gm")
        try:
            pack_size = prod.find_element(By.CSS_SELECTOR, ".subText").text.strip()
        except Exception:
            pack_size = "N/A"

        # Try to extract discounted price details if available
        try:
            discount_section = prod.find_element(By.CSS_SELECTOR, ".discountedPriceSection")
            # In a discounted product, assume:
            # - The element with class 'discountedPrice' gives the current (selling) price.
            # - The element with class 'price' gives the regular price (MRP).
            selling_price = discount_section.find_element(By.CSS_SELECTOR, ".discountedPrice span:last-child").text.strip()
            mrp = discount_section.find_element(By.CSS_SELECTOR, ".price span:last-child").text.strip()
        except Exception:
            # Fallback for non-discounted product
            try:
                price_elem = prod.find_element(By.CSS_SELECTOR, "div.price")
                selling_price = price_elem.find_element(By.CSS_SELECTOR, "span:last-child").text.strip()
            except Exception:
                selling_price = "N/A"
            mrp = selling_price

        # Extract Details URL from the Details link
        try:
            details_url = prod.find_element(By.CSS_SELECTOR, "a.btnShowDetails").get_attribute("href")
        except Exception:
            details_url = "N/A"

        # Current date as LastUpdated
        last_updated = datetime.now().strftime("%Y-%m-%d")

        product = {
            "SKU Name": sku_name,
            "Pack Size": pack_size,
            "MRP": mrp,
            "Selling Price": selling_price,
            "Details URL": details_url,
            "LastUpdated": last_updated
        }
        products.append(product)

    browser.quit()
    return products


def load_excel_data():
    """Loads existing Excel data into a DataFrame; returns empty DataFrame if file not found."""
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    else:
        return pd.DataFrame(columns=["SKU Name", "Pack Size", "MRP", "Selling Price", "Details URL", "LastUpdated"])


def notify_price_change(sku_name, old_price, new_price):
    """Shows a Windows notification for a price change."""
    notification.notify(
        title=f"Price Change: {sku_name}",
        message=f"{old_price} → {new_price}",
        timeout=10
    )


def log_change_block(block_lines):
    """
    Writes a block of text (list of lines) to the log file and prints it to the console.
    """
    block_text = "\n".join(block_lines) + "\n\n===========\n"
    print(block_text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(block_text)


def update_excel_and_log(scraped_products):
    """
    Compares scraped products with existing Excel data.
    For each product, if it is new or its Selling Price differs from the last recorded price,
    appends the new entry to the Excel file and logs the details in the change log.
    The final Excel data is sorted by SKU Name.
    """
    df_existing = load_excel_data()
    new_entries = []
    log_blocks = []

    for product in scraped_products:
        sku = product["SKU Name"]
        # Filter existing records for this SKU
        df_sku = df_existing[df_existing["SKU Name"] == sku]
        if df_sku.empty:
            # New product
            new_entries.append(product)
            block = [
                f"SKU Name: {product['SKU Name']}",
                f"Pack Size: {product['Pack Size']}",
                f"MRP: {product['MRP']}",
                f"Selling Price: {product['Selling Price']}",
                f"Details URL: {product['Details URL']}",
                f"LastUpdated: {product['LastUpdated']}",
                "Previous prices: None"
            ]
            log_blocks.append(block)
        else:
            # Get the last record (by LastUpdated) for this SKU
            df_sku_sorted = df_sku.sort_values(by="LastUpdated", ascending=True)
            last_record = df_sku_sorted.iloc[-1]
            if str(last_record["Selling Price"]) != product["Selling Price"]:
                # Price changed
                new_entries.append(product)
                notify_price_change(product["SKU Name"], last_record["Selling Price"], product["Selling Price"])
                block = [
                    f"SKU Name: {product['SKU Name']}",
                    f"Pack Size: {product['Pack Size']}",
                    f"MRP: {product['MRP']}",
                    f"Selling Price: {product['Selling Price']}",
                    f"Details URL: {product['Details URL']}",
                    f"LastUpdated: {product['LastUpdated']}",
                    "Previous prices:"
                ]
                for _, row in df_sku_sorted.iterrows():
                    block.append(f"{row['LastUpdated']}: {row['Selling Price']}")
                log_blocks.append(block)

    if new_entries:
        # Append new entries to existing data
        df_new = pd.DataFrame(new_entries)
        df_updated = pd.concat([df_existing, df_new], ignore_index=True)
        # Sort by SKU Name
        df_updated.sort_values(by="SKU Name", inplace=True)
        df_updated.to_excel(EXCEL_FILE, index=False)

        # Write log file and print log blocks
        for block in log_blocks:
            log_change_block(block)
    else:
        print("No new entries or price changes.")


def main():
    scraped_products = scrape_popular_products()
    update_excel_and_log(scraped_products)


if __name__ == "__main__":
    main()
