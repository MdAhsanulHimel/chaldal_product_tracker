
# Chaldal Products Price Tracker

This project contains two Python scripts that automatically track product prices on the [Chaldal](https://chaldal.com/) website. The scripts scrape product details from designated pages, save the data in an Excel file, log any changes (new products or price changes) in a text log, and display a summary dialog box. You can use these scripts to monitor both popular products and selected products by providing a list of product URLs.

## Running the Scripts


   Open a terminal or command prompt and run:

   ```bash
   python "script-popular products.py"
   ```
   or
   ```bash
   python "script-selected products.py"
   ```
---



## Scripts Overview

### 1. script-popular products.py
- **Purpose:**  
  Scrapes product details from the Popular products page (`https://chaldal.com/popular`).
- **Output:**  
  Saves data in an Excel file named `Tracking popular products.xlsx` with columns:  
  - SKU Name  
  - Pack Size  
  - MRP  
  - Selling Price  
  - Discount (as a decimal, e.g., 0.1 for 10%)  
  - Product URL  
  - LastUpdated  
- **Logging:**  
  Any new product or price change is logged in a text file (named with the current date) inside the `change_log_popular_products` folder.

### 2. script-selected products.py
- **Purpose:**  
  Tracks selected products by reading product URLs from a CSV file (named `product_urls.csv`).
- **Output:**  
  Saves data in an Excel file named `Tracking selected products.xlsx` with the same columns as above.
- **Logging:**  
  Changes (new products or price changes) are logged in a text file (named with the current date) inside the `change_log_selected_products` folder.


## Requirements

- **Python 3.x**
- **Google Chrome** installed (with matching [ChromeDriver](https://sites.google.com/chromium.org/driver/) in your PATH)
- **Dependencies:**  
  Install required Python packages using pip:

  ```bash
  pip install selenium pandas openpyxl plyer
  ```

  (The scripts also use the built-in `tkinter` module for the dialog boxes.)

## Setup and Configuration

1. **Product URLs:**  
   Create a CSV file named `product_urls.csv` with at least one column called `URL`.  
   Example content:
   ```csv
   URL
   https://chaldal.com/your-first-product
   https://chaldal.com/your-second-product
   ```
   - For the "popular products" script, product details are scraped directly from the [Popular](https://chaldal.com/popular) page.
   - For the "selected products" script, the script reads URLs from `product_urls.csv`.

2. **Adjusting File Names and Paths:**  
   You can modify the Excel file names and log folder names in the script if needed.


