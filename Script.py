import requests
from bs4 import BeautifulSoup
import csv
import schedule
import time
import smtplib
from email.message import EmailMessage

# Configuration
PRODUCT_URLS = [
    "https://chaldal.com/your-product-url-1",
    "https://chaldal.com/your-product-url-2"
]
CSV_FILE = "product_data.csv"
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_RECEIVER = "receiver_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"  # Use app password, not main password

def fetch_product_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    title = soup.find("h1").text.strip()
    
    size_tag = soup.find("div", string="Size")
    size = size_tag.find_next_sibling("div").text.strip() if size_tag else "N/A"

    price_tag = soup.find("span", class_="price")
    price = price_tag.text.strip() if price_tag else "N/A"

    discount = "Yes" if soup.find("del") else "No"

    return {
        "URL": url,
        "Title": title,
        "Size": size,
        "Price": price,
        "Discount": discount
    }

def load_existing_data():
    try:
        with open(CSV_FILE, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        return []

def save_data(data):
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["URL", "Title", "Size", "Price", "Discount"])
        writer.writeheader()
        writer.writerows(data)

def send_email_alert(changes):
    msg = EmailMessage()
    msg['Subject'] = 'Chaldal Product Price Alert'
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    content = "\n\n".join([f"{change['Title']}:\nOld Price: {change['Old Price']}\nNew Price: {change['Price']}\nURL: {change['URL']}" for change in changes])
    msg.set_content("Product price/discount has changed:\n\n" + content)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(msg)

def check_for_changes():
    print("Checking for product updates...")
    current_data = [fetch_product_data(url) for url in PRODUCT_URLS]
    previous_data = load_existing_data()
    save_data(current_data)

    changes = []
    for curr in current_data:
        for prev in previous_data:
            if curr["URL"] == prev["URL"]:
                if curr["Price"] != prev["Price"] or curr["Discount"] != prev["Discount"]:
                    changes.append({
                        **curr,
                        "Old Price": prev["Price"]
                    })

    if changes:
        send_email_alert(changes)
    else:
        print("No changes found.")


# Schedule the script to run every 24 hours
schedule.every(24).hours.do(check_for_changes)

# First run
check_for_changes()

# Keep it running
while True:
    schedule.run_pending()
    time.sleep(1)