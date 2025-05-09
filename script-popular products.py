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
EXCEL_FILE = "Tracking popular products.xlsx"
CHANGE_LOG_DIR = "change_log_popular_products"
os.makedirs(CHANGE_LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(CHANGE_LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.txt")

def launch_browser():
    """Launches a headless Chrome browser with images disabled."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")
    return webdriver.Chrome(options=options)

def scroll_to_bottom(browser, pause_time=2):
    """Scrolls to the bottom of the page until no new content loads."""
    last_height = browser.execute_script("return document.body.scrollHeight")
    while True:
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_popular_products(url="https://chaldal.com/popular"):
    """
    Scrapes product details from the Popular page.
    
    Returns:
        List of dictionaries with keys:
          "SKU Name", "Pack Size", "MRP", "Selling Price", "Discount",
          "Product URL", "LastUpdated"
    """
    browser = launch_browser()
    browser.get(url)
    
    WebDriverWait(browser, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.productPane div.product"))
    )
    scroll_to_bottom(browser, pause_time=2)
    
    product_elements = browser.find_elements(By.CSS_SELECTOR, "div.productPane div.product")
    products = []
    
    def to_float(val):
        try:
            return float(val.replace(",", ""))
        except Exception:
            return None

    for prod in product_elements:
        try:
            sku_name = prod.find_element(By.CSS_SELECTOR, ".name").text.strip()
            if "Loading more" in sku_name:
                continue
        except Exception:
            continue

        try:
            pack_size = prod.find_element(By.CSS_SELECTOR, ".subText").text.strip()
        except Exception:
            pack_size = "N/A"
            
        try:
            discount_section = prod.find_element(By.CSS_SELECTOR, ".discountedPriceSection")
            selling_price_text = discount_section.find_element(By.CSS_SELECTOR, ".discountedPrice span:last-child").text.strip()
            mrp_text = discount_section.find_element(By.CSS_SELECTOR, ".price span:last-child").text.strip()
        except Exception:
            try:
                price_elem = prod.find_element(By.CSS_SELECTOR, "div.price")
                selling_price_text = price_elem.find_element(By.CSS_SELECTOR, "span:last-child").text.strip()
            except Exception:
                selling_price_text = "0"
            mrp_text = selling_price_text
        
        try:
            product_url = prod.find_element(By.CSS_SELECTOR, "a.btnShowDetails").get_attribute("href")
        except Exception:
            product_url = "N/A"
            
        last_updated = datetime.now().strftime("%Y-%m-%d")
        
        mrp = to_float(mrp_text)
        selling_price = to_float(selling_price_text)
        if mrp is None:
            mrp = selling_price

        if mrp and mrp > 0:
            discount_value = round((mrp - selling_price) / mrp, 2)
        else:
            discount_value = 0.0

        product = {
            "SKU Name": sku_name,
            "Pack Size": pack_size,
            "MRP": mrp,
            "Selling Price": selling_price,
            "Discount": discount_value,
            "Product URL": product_url,
            "LastUpdated": last_updated
        }
        products.append(product)
    
    browser.quit()
    return products

def load_excel_data():
    """Loads the existing Excel file into a DataFrame; returns empty DataFrame if file does not exist."""
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE)
    else:
        return pd.DataFrame(columns=["SKU Name", "Pack Size", "MRP", "Selling Price", "Discount", "Product URL", "LastUpdated"])

def notify_price_change(sku_name, old_price, new_price):
    """Shows a Windows notification for a price change."""
    notification.notify(
        title=f"Price Change: {sku_name}",
        message=f"{old_price} → {new_price}",
        timeout=10
    )

def log_change_block(block_lines):
    """Writes the log block to file and prints it to the console."""
    block_text = "\n".join(block_lines) + "\n\n===========\n"
    print(block_text)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(block_text)

def show_summary_dialog(new_count, price_change_count):
    """Displays a tkinter dialog summarizing the changes."""
    total_changes = new_count + price_change_count
    summary_message = (
        f"📝 Popular Products Update Summary\n\n"
        f"🔄 Total Changes:         {total_changes}\n"
        f"🆕 New Products:          {new_count}\n"
        f"💸 Price Changes:         {price_change_count}\n\n"
        f"📁 See detailed log at:\n{os.path.abspath(CHANGE_LOG_DIR)}"
    )
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Popular Products Update Summary", summary_message)
    root.destroy()

def update_excel_and_log(scraped_products):
    """
    Compares scraped products with existing Excel data.
    For each product, if it is new or its Selling Price differs from the last recorded price,
    appends the new entry and logs the change.
    The final Excel file is sorted by SKU Name (ascending) and LastUpdated (descending).
    
    Returns:
        tuple: (new_count, price_change_count)
    """
    df_existing = load_excel_data()
    new_entries = []
    log_blocks = []
    
    new_count = 0
    price_change_count = 0

    for product in scraped_products:
        url = product["Product URL"]
        df_sku = df_existing[df_existing["Product URL"] == url]
        if df_sku.empty:
            new_entries.append(product)
            new_count += 1
            block = [
                f"📢 New Entry..."
                f"🛒 SKU Name:       {product['SKU Name']}",
                f"📦 Pack Size:      {product['Pack Size']}\n",
                f"📅 Updated on:     {product['LastUpdated']}",
                f"💰 MRP:            {product['MRP']} BDT",
                f"💵 Selling Price:  {product['Selling Price']} BDT",
                f"📉 Discount:       {product['Discount']*100} %",
                f"🔗 URL:            {product['Product URL']}",
            ]
            log_blocks.append(block)
        else:
           # Sort existing records for this product by LastUpdated in ascending order
            df_sku_sorted = df_sku.sort_values(by="LastUpdated", ascending=True)
            last_record = df_sku_sorted.iloc[-1]  # latest record from Excel
            if last_record["Selling Price"] != product["Selling Price"]:
                new_entries.append(product)
                price_change_count += 1
                notify_price_change(product["SKU Name"], last_record["Selling Price"], product["Selling Price"])
                # Calculate the difference from the latest historical record
                diff = last_record["Selling Price"] - product["Selling Price"]
                if diff > 0:
                    # diff_alert = f"Price Decreased by {diff}"
                    diff_alert = f"📢 Alert: Price Decreased by {diff} BDT since last update."
                elif diff < 0:
                    diff_alert = f"📢 Alert: Price Increased by {abs(diff)} BDT since last update."
                else:
                    diff_alert = "📢 New Entry..."
                
                block = [
                    f"🛒 SKU Name:       {product['SKU Name']}",
                    f"📦 Pack Size:      {product['Pack Size']}\n",
                    f"{diff_alert}\n",
                    f"📅 Updated on:     {product['LastUpdated']}",
                    f"💰 MRP:            {product['MRP']} BDT",
                    f"💵 Selling Price:  {product['Selling Price']} BDT",
                    f"📉 Discount:       {product['Discount']*100} %",
                    f"🔗 URL:            {product['Product URL']}",
                    "Price History:"
                ]
                for _, row in df_sku_sorted.iterrows():
                    diff_val = row["MRP"] - row["Selling Price"] if pd.notnull(row["MRP"]) and pd.notnull(row["Selling Price"]) else "N/A"
                    block.append(f"{row['LastUpdated']:>12} -> MRP: {row['MRP']:>5} BDT | Selling Price: {row['Selling Price']:>5} | Discount: {diff_val:>5} BDT")
                log_blocks.append(block)

    if new_entries:
        df_new = pd.DataFrame(new_entries)
        if df_existing.empty:
            df_updated = df_new.copy()
        else:
            df_updated = pd.concat([df_existing, df_new], ignore_index=True)
        df_updated.sort_values(by=["SKU Name", "LastUpdated"], ascending=[True, False], inplace=True)
        df_updated.to_excel(EXCEL_FILE, index=False)

        for block in log_blocks:
            log_change_block(block)
    else:
        print("No new entries or price changes.")
    
    return new_count, price_change_count

def main():
    scraped_products = scrape_popular_products()
    new_count, price_change_count = update_excel_and_log(scraped_products)
    if new_count > 0 or price_change_count > 0:
        show_summary_dialog(new_count, price_change_count)
    else:
        print("\n✅ Finished tracking. No changes detected.")

if __name__ == "__main__":
    main()
