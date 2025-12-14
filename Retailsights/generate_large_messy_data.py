"""
Generate a large, comprehensive messy CSV file with 400 columns for testing
the intelligent data analyst system.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

print("🚀 Starting large messy data generation...")

# Generate 1000 rows of data
num_rows = 1000

# Helper functions for messy data
def random_date_format(date_obj):
    """Return date in random format"""
    if random.random() < 0.1:
        return ''
    formats = [
        date_obj.strftime('%d/%m/%Y'),
        date_obj.strftime('%Y-%m-%d'),
        date_obj.strftime('%m/%d/%y'),
        date_obj.strftime('%d-%b-%y'),
        date_obj.strftime('%B %d %Y'),
        date_obj.strftime('%d.%m.%Y'),
        date_obj.strftime('%Y/%m/%d'),
        date_obj.strftime('%b %d, %Y'),
        date_obj.strftime('%d-%m-%Y'),
    ]
    return random.choice(formats)

def add_whitespace(value):
    """Add random whitespace"""
    value = str(value)
    if random.random() > 0.7:
        spaces = random.choice(['  ', '   ', ' ', '\t'])
        return f"{spaces}{value}{spaces}"
    return value

def make_negative(value):
    """Randomly make numeric values negative"""
    if random.random() > 0.85 and value > 0:
        return -value
    return value

def add_currency_symbol(value):
    """Add random currency symbol"""
    symbols = ['$', '£', '€', 'USD ', 'GBP ', '']
    return f"{random.choice(symbols)}{value}"

# Generate base data
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=random.randint(0, 365)) for _ in range(num_rows)]

# Product categories and names
categories = ['Electronics', 'Clothing', 'Food & Beverage', 'Home & Garden', 'Sports', 
              'Books', 'Toys', 'Beauty', 'Automotive', 'Health', 'Pet Supplies', 
              'Office Supplies', 'Jewelry', 'Baby Products']

products = ['Product_A', 'Product_B', 'Product_C', 'Product_D', 'Product_E', 
            'Product_F', 'Product_G', 'Product_H', 'Product_I', 'Product_J',
            'Laptop', 'Phone', 'Tablet', 'Headphones', 'Mouse', 'Keyboard',
            'Milk 2L', 'Bread Loaf', 'Eggs Dozen', 'Coffee 500g', 'Tea Bags',
            'Shirt', 'Pants', 'Shoes', 'Socks', 'Hat', 'Jacket']

stores = ['Store_North', 'Store_South', 'Store_East', 'Store_West', 'Store_Central',
          'Store_Downtown', 'Store_Mall', 'Store_Online', 'Store_Outlet']

regions = ['North America', 'Europe', 'Asia', 'South America', 'Africa', 'Oceania']

payment_methods = ['Credit Card', 'Debit Card', 'Cash', 'PayPal', 'Apple Pay', 'Google Pay']

customer_segments = ['Premium', 'Regular', 'New', 'VIP', 'Occasional']

print("📝 Generating 400 columns of data...")

# Create DataFrame with 400 columns - using all string type to avoid dtype issues
data = {}

# Column group 1: Transaction Details (50 columns)
print("  - Transaction columns (1-50)")
for i in range(1, 51):
    if i <= 10:
        data[f'Transaction_ID_{i}'] = [add_whitespace(f'TXN{random.randint(10000, 99999)}') 
                                        if random.random() > 0.05 else '' 
                                        for _ in range(num_rows)]
    elif i <= 20:
        data[f'Invoice_Number_{i}'] = [f'INV-{random.randint(1000, 9999)}' 
                                        if random.random() > 0.08 else '' 
                                        for _ in range(num_rows)]
    elif i <= 30:
        data[f'Order_Date_{i}'] = [random_date_format(dates[j]) for j in range(num_rows)]
    elif i <= 40:
        data[f'Delivery_Date_{i}'] = [random_date_format(dates[j] + timedelta(days=random.randint(1, 14))) 
                                       for j in range(num_rows)]
    else:
        data[f'Return_Date_{i}'] = [random_date_format(dates[j] + timedelta(days=random.randint(15, 30))) 
                                     if random.random() > 0.9 else '' 
                                     for j in range(num_rows)]

# Column group 2: Product Information (50 columns)
print("  - Product columns (51-100)")
for i in range(51, 101):
    if i <= 60:
        data[f'  Product_Name_{i}  '] = [add_whitespace(random.choice(products)) 
                                          for _ in range(num_rows)]
    elif i <= 70:
        data[f'PRODUCT_SKU_{i}'] = [f'SKU{random.randint(100, 999)}' 
                                     if random.random() > 0.06 else 'MISSING' 
                                     for _ in range(num_rows)]
    elif i <= 80:
        data[f'product_category_{i}'] = [add_whitespace(random.choice(categories)) 
                                          for _ in range(num_rows)]
    elif i <= 90:
        data[f'Product Brand {i}'] = [f'Brand_{chr(65 + random.randint(0, 25))}' 
                                       for _ in range(num_rows)]
    else:
        data[f'Product_Description_{i}'] = [f'Description for product {random.randint(1, 100)}' 
                                             if random.random() > 0.15 else '' 
                                             for _ in range(num_rows)]

# Column group 3: Quantity & Measurements (50 columns)
print("  - Quantity columns (101-150)")
for i in range(101, 151):
    if i <= 120:
        data[f'Quantity_Sold_{i}'] = [str(make_negative(random.randint(1, 100))) 
                                       for _ in range(num_rows)]
    elif i <= 135:
        data[f'Units_In_Stock_{i}'] = [str(make_negative(random.randint(0, 500))) 
                                        for _ in range(num_rows)]
    else:
        data[f'Weight_KG_{i}'] = [str(round(random.uniform(0.1, 50.0), 2)) 
                                   if random.random() > 0.1 else '' 
                                   for _ in range(num_rows)]

# Column group 4: Financial Data (50 columns)
print("  - Financial columns (151-200)")
for i in range(151, 201):
    if i <= 165:
        data[f'Unit_Price_{i}'] = [add_currency_symbol(round(random.uniform(5, 500), 2)) 
                                    for _ in range(num_rows)]
    elif i <= 180:
        data[f'Total_Revenue_{i}'] = [add_currency_symbol(round(random.uniform(50, 5000), 2)) 
                                       for _ in range(num_rows)]
    elif i <= 190:
        data[f'Cost_Price_{i}'] = [add_currency_symbol(round(random.uniform(3, 300), 2)) 
                                    for _ in range(num_rows)]
    else:
        data[f'Discount_Amount_{i}'] = [add_currency_symbol(round(random.uniform(0, 100), 2)) 
                                         if random.random() > 0.3 else '$0.00' 
                                         for _ in range(num_rows)]

# Column group 5: Customer Information (50 columns)
print("  - Customer columns (201-250)")
for i in range(201, 251):
    if i <= 215:
        data[f'Customer_ID_{i}'] = [add_whitespace(f'CUST{random.randint(1000, 9999)}') 
                                     if random.random() > 0.12 else '' 
                                     for _ in range(num_rows)]
    elif i <= 230:
        data[f'Customer_Name_{i}'] = [f'{random.choice(["John", "Jane", "Mike", "Sarah", "David"])} {random.choice(["Smith", "Johnson", "Williams", "Brown"])}' 
                                       for _ in range(num_rows)]
    elif i <= 240:
        data[f'Customer_Email_{i}'] = [f'customer{random.randint(1, 1000)}@{"email.com" if random.random() > 0.1 else ""}' 
                                        for _ in range(num_rows)]
    else:
        data[f'Customer_Segment_{i}'] = [add_whitespace(random.choice(customer_segments)) 
                                          for _ in range(num_rows)]

# Column group 6: Location Data (50 columns)
print("  - Location columns (251-300)")
for i in range(251, 301):
    if i <= 265:
        data[f'Store_Location_{i}'] = [add_whitespace(random.choice(stores)) 
                                        for _ in range(num_rows)]
    elif i <= 280:
        data[f'Region_{i}'] = [random.choice(regions) 
                               for _ in range(num_rows)]
    elif i <= 290:
        data[f'City_{i}'] = [f'City_{random.randint(1, 50)}' 
                             for _ in range(num_rows)]
    else:
        data[f'Postal_Code_{i}'] = [f'{random.randint(10000, 99999)}' 
                                     if random.random() > 0.08 else '' 
                                     for _ in range(num_rows)]

# Column group 7: Payment & Shipping (30 columns)
print("  - Payment columns (301-330)")
for i in range(301, 331):
    if i <= 315:
        data[f'Payment_Method_{i}'] = [random.choice(payment_methods) 
                                        for _ in range(num_rows)]
    else:
        data[f'Shipping_Cost_{i}'] = [add_currency_symbol(round(random.uniform(0, 50), 2)) 
                                       for _ in range(num_rows)]

# Column group 8: Performance Metrics (30 columns)
print("  - Performance columns (331-360)")
for i in range(331, 361):
    if i <= 345:
        data[f'Rating_{i}'] = [str(round(random.uniform(1, 5), 1)) 
                               if random.random() > 0.2 else '' 
                               for _ in range(num_rows)]
    else:
        data[f'Review_Count_{i}'] = [str(random.randint(0, 500)) 
                                      for _ in range(num_rows)]

# Column group 9: Operational Data (20 columns)
print("  - Operational columns (361-380)")
for i in range(361, 381):
    if i <= 370:
        data[f'Supplier_ID_{i}'] = [f'SUP{random.randint(100, 999)}' 
                                     for _ in range(num_rows)]
    else:
        data[f'Lead_Time_Days_{i}'] = [str(random.randint(1, 30)) 
                                        for _ in range(num_rows)]

# Column group 10: Custom Business Metrics (20 columns)
print("  - Business metrics columns (381-400)")
for i in range(381, 401):
    if i <= 390:
        data[f'Conversion_Rate_{i}'] = [f'{round(random.uniform(0, 100), 2)}%' 
                                         for _ in range(num_rows)]
    else:
        data[f'Customer_Lifetime_Value_{i}'] = [add_currency_symbol(round(random.uniform(100, 10000), 2)) 
                                                  for _ in range(num_rows)]

print("🔧 Creating DataFrame...")
# Create DataFrame
df = pd.DataFrame(data)

print("💥 Adding messy data patterns...")
# Add some completely empty rows (10 random rows)
empty_indices = random.sample(range(num_rows), 10)
for idx in empty_indices:
    for col in df.columns:
        df.at[idx, col] = ''

# Add some duplicate rows (20 duplicates)
duplicate_indices = random.sample(range(num_rows - 50), 20)
for idx in duplicate_indices:
    for col in df.columns:
        df.at[idx + 50, col] = df.at[idx, col]

print("💾 Saving to CSV...")
# Save to CSV
output_file = 'large_messy_test_data_400cols.csv'
df.to_csv(output_file, index=False)

import os
file_size_mb = round(os.path.getsize(output_file) / (1024*1024), 2)

print("\n" + "="*60)
print("✅ SUCCESS! File created successfully")
print("="*60)
print(f"📁 Filename: {output_file}")
print(f"📊 Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
print(f"💾 File size: {file_size_mb} MB")
print(f"\n🔍 Data Quality Issues Included:")
print(f"  ✓ Mixed date formats (9 different formats)")
print(f"  ✓ Currency symbols mixed ($, £, €, USD, GBP)")
print(f"  ✓ Extra whitespace throughout")
print(f"  ✓ ~{int(num_rows * 0.12)} rows with missing values")
print(f"  ✓ {len(empty_indices)} completely empty rows")
print(f"  ✓ {len(duplicate_indices)} duplicate rows")
print(f"  ✓ ~{int(num_rows * 0.15)} negative values in quantity/stock fields")
print(f"  ✓ Mixed column name formats (spaces, underscores, CAPS)")
print(f"  ✓ Inconsistent data types (numbers as strings)")
print(f"  ✓ Missing critical IDs in various columns")
print("="*60)
print("\n🚀 Ready to test! Upload this file in the app.")
print(f"📍 Location: /Users/shaiksohail/retailsight/{output_file}")
