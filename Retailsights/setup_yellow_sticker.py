"""
Setup script for Yellow Sticker Label System
Creates tables and populates with sample data for testing
"""
import mysql.connector
from datetime import datetime, timedelta
from config import get_env
from logger import log

def get_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host=get_env("DB_HOST", "localhost"),
        port=int(get_env("DB_PORT", "3306")),
        user=get_env("DB_USER", "root"),
        password=get_env("DB_PASSWORD", ""),
        database=get_env("DB_NAME", "retailsight")
    )

def create_tables(cursor):
    """Create required tables"""
    print("Creating tables...")
    
    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          shop_id BIGINT NOT NULL,
          sku VARCHAR(255) NOT NULL,
          name VARCHAR(255) NOT NULL,
          category VARCHAR(100),
          cost_price DECIMAL(10, 2),
          selling_price DECIMAL(10, 2),
          current_stock INT DEFAULT 0,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          UNIQUE KEY unique_shop_sku (shop_id, sku),
          INDEX (shop_id)
        )
    """)
    print("✅ Products table ready")
    
    # Expiry records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expiry_records (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          product_id BIGINT NOT NULL,
          batch_number VARCHAR(100),
          quantity_received INT,
          quantity_remaining INT,
          expiry_date DATE NOT NULL,
          received_date DATE,
          days_left INT GENERATED ALWAYS AS (DATEDIFF(expiry_date, CURDATE())) STORED,
          status VARCHAR(32) DEFAULT 'active',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX (product_id),
          INDEX (expiry_date),
          INDEX (status)
        )
    """)
    print("✅ Expiry records table ready")
    
    # Discount rules table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discount_rules (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          shop_id BIGINT NOT NULL,
          name VARCHAR(100),
          days_left_min INT,
          days_left_max INT,
          quantity_min INT,
          discount_percent DECIMAL(5, 2),
          active BOOLEAN DEFAULT 1,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX (shop_id),
          INDEX (active)
        )
    """)
    print("✅ Discount rules table ready")
    
    # Waste records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS waste_records (
          id BIGINT PRIMARY KEY AUTO_INCREMENT,
          product_id BIGINT NOT NULL,
          expiry_record_id BIGINT,
          quantity_wasted INT,
          reason VARCHAR(100),
          recorded_by BIGINT,
          recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          INDEX (product_id),
          INDEX (expiry_record_id)
        )
    """)
    print("✅ Waste records table ready")

def insert_sample_data(cursor, shop_id=1):
    """Insert sample products with expiry dates"""
    print(f"\nInserting sample data for shop_id={shop_id}...")
    
    # Sample products
    products = [
        ("MILK001", "Fresh Whole Milk 2L", "Dairy", 1.20, 2.50, 15),
        ("BREAD001", "White Bread", "Bakery", 0.50, 1.20, 20),
        ("YOGURT001", "Greek Yogurt 500g", "Dairy", 1.00, 2.00, 12),
        ("CHEESE001", "Cheddar Cheese 400g", "Dairy", 2.50, 4.50, 8),
        ("CHICKEN001", "Fresh Chicken Breast 1kg", "Meat", 4.00, 7.99, 10),
        ("FISH001", "Salmon Fillet 400g", "Fish", 5.00, 9.99, 6),
        ("SALAD001", "Mixed Salad Leaves 200g", "Produce", 0.80, 1.50, 18),
        ("JUICE001", "Orange Juice 1L", "Beverages", 1.20, 2.50, 14),
    ]
    
    inserted_products = []
    for sku, name, category, cost, price, stock in products:
        try:
            cursor.execute("""
                INSERT INTO products (shop_id, sku, name, category, cost_price, selling_price, current_stock)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    name = VALUES(name),
                    category = VALUES(category),
                    cost_price = VALUES(cost_price),
                    selling_price = VALUES(selling_price),
                    current_stock = VALUES(current_stock)
            """, (shop_id, sku, name, category, cost, price, stock))
            
            # Get product ID
            cursor.execute("SELECT id FROM products WHERE shop_id = %s AND sku = %s", (shop_id, sku))
            product_id = cursor.fetchone()[0]
            inserted_products.append((product_id, sku, name, price))
            print(f"  ✅ {name} ({sku})")
        except Exception as e:
            print(f"  ⚠️  {name} ({sku}): {e}")
    
    # Create expiry records with various dates
    print("\nAdding expiry records...")
    today = datetime.now().date()
    
    expiry_scenarios = [
        (0, 1, "Expires today"),
        (1, 2, "Expires tomorrow"),
        (2, 3, "Expires in 2 days"),
        (3, 2, "Expires in 3 days"),
        (5, 2, "Expires in 5 days"),
        (7, 1, "Expires in 7 days"),
        (10, 1, "Expires in 10 days"),
        (14, 1, "Expires in 14 days"),
    ]
    
    for idx, (product_id, sku, name, price) in enumerate(inserted_products):
        if idx < len(expiry_scenarios):
            days_offset, qty, desc = expiry_scenarios[idx]
            expiry_date = today + timedelta(days=days_offset)
            received_date = today - timedelta(days=2)
            batch = f"BATCH{datetime.now().strftime('%Y%m')}{idx:03d}"
            
            try:
                cursor.execute("""
                    INSERT INTO expiry_records 
                    (product_id, batch_number, quantity_received, quantity_remaining, expiry_date, received_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'active')
                """, (product_id, batch, qty * 5, qty * 5, expiry_date, received_date))
                print(f"  ✅ {name}: {desc} ({expiry_date})")
            except Exception as e:
                print(f"  ⚠️  {name}: {e}")
    
    # Insert discount rules
    print("\nAdding discount rules...")
    discount_rules = [
        ("10% off - 7+ days", 7, 999, 0, 10),
        ("20% off - 5-6 days", 5, 6, 0, 20),
        ("30% off - 3-4 days", 3, 4, 0, 30),
        ("40% off - 2 days", 2, 2, 0, 40),
        ("50% off - last day", 0, 1, 0, 50),
    ]
    
    for name, days_min, days_max, qty_min, discount in discount_rules:
        try:
            cursor.execute("""
                INSERT INTO discount_rules 
                (shop_id, name, days_left_min, days_left_max, quantity_min, discount_percent, active)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE 
                    days_left_min = VALUES(days_left_min),
                    days_left_max = VALUES(days_left_max),
                    quantity_min = VALUES(quantity_min),
                    discount_percent = VALUES(discount_percent)
            """, (shop_id, name, days_min, days_max, qty_min, discount))
            print(f"  ✅ {name}: {discount}% off")
        except Exception as e:
            print(f"  ⚠️  {name}: {e}")

def main():
    print("=" * 60)
    print("YELLOW STICKER SYSTEM - DATABASE SETUP")
    print("=" * 60)
    print()
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_connection()
        cursor = conn.cursor()
        print("✅ Connected\n")
        
        # Create tables
        create_tables(cursor)
        conn.commit()
        
        # Insert sample data
        insert_sample_data(cursor, shop_id=1)
        conn.commit()
        
        # Summary
        print("\n" + "=" * 60)
        print("SETUP COMPLETE!")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE shop_id = 1")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM expiry_records WHERE status = 'active'")
        expiry_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM discount_rules WHERE shop_id = 1 AND active = 1")
        rule_count = cursor.fetchone()[0]
        
        print(f"\n📦 Products: {product_count}")
        print(f"⏰ Expiry records: {expiry_count}")
        print(f"💰 Discount rules: {rule_count}")
        
        # Show expiring products
        print("\n" + "=" * 60)
        print("PRODUCTS EXPIRING SOON")
        print("=" * 60)
        
        cursor.execute("""
            SELECT 
                p.sku,
                p.name,
                p.selling_price,
                e.expiry_date,
                e.days_left,
                e.batch_number
            FROM expiry_records e
            JOIN products p ON e.product_id = p.id
            WHERE e.status = 'active' AND e.days_left <= 14
            ORDER BY e.days_left ASC
        """)
        
        rows = cursor.fetchall()
        for sku, name, price, expiry_date, days_left, batch in rows:
            print(f"{name} ({sku})")
            print(f"  Price: £{price:.2f} | Expires: {expiry_date} ({days_left} days)")
            print(f"  Batch: {batch}")
            print()
        
        print("=" * 60)
        print("✅ Ready to generate yellow sticker labels!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: streamlit run app.py")
        print("2. Navigate to 'Yellow Stickers 🏷️' tab")
        print("3. Set threshold to 14 days to see all products")
        print("4. Click 'Preview Products & Discounts'")
        print("5. Generate and print labels!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        log.exception("Setup error")
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("- Check your .env file has correct database credentials")
        print("- Ensure MySQL server is running")
        print("- Database 'retailsight' should exist")

if __name__ == "__main__":
    main()
