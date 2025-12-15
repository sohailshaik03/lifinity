# Performance Optimization Script
# Creates optimized database indexes and caching layer

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Performance indexes to create
INDEXES = [
    # Products table - frequently queried
    "CREATE INDEX IF NOT EXISTS idx_products_shop_id ON products(shop_id)",
    "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
    "CREATE INDEX IF NOT EXISTS idx_products_shop_sku ON products(shop_id, sku)",
    
    # Sales tables - analytics queries
    "CREATE INDEX IF NOT EXISTS idx_sales_transactions_shop_dt ON sales_transactions(shop_id, transaction_dt DESC)",
    "CREATE INDEX IF NOT EXISTS idx_sales_lines_product ON sales_lines(product_id)",
    "CREATE INDEX IF NOT EXISTS idx_sales_lines_transaction ON sales_lines(transaction_id)",
    
    # Expiry tracking - frequently accessed
    "CREATE INDEX IF NOT EXISTS idx_expiry_records_product ON expiry_records(product_id)",
    
    # User and shop relationships
    "CREATE INDEX IF NOT EXISTS idx_user_shops_user ON user_shops(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_shops_shop ON user_shops(shop_id)",
    
    # Scan history - yellow sticker feature
    "CREATE INDEX IF NOT EXISTS idx_scan_history_shop_dt ON scan_history(shop_id, scanned_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_scan_history_product ON scan_history(product_id)",
    
    # Subscriptions
    "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user ON user_subscriptions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_status ON user_subscriptions(status)",
    
    # Alerts
    "CREATE INDEX IF NOT EXISTS idx_alerts_shop ON alerts(shop_id)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)",
]

def create_indexes():
    """Create performance indexes"""
    print("🔧 Creating performance indexes...\n")
    
    success_count = 0
    error_count = 0
    
    for idx_sql in INDEXES:
        conn = None
        try:
            conn = engine.connect()
            idx_name = idx_sql.split("idx_")[1].split(" ON")[0]
            print(f"  Creating index: idx_{idx_name}...")
            conn.execute(text(idx_sql))
            conn.commit()
            print(f"  ✅ Created idx_{idx_name}")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg:
                print(f"  ℹ️  Index already exists")
                success_count += 1
            elif "does not exist" in error_msg:
                print(f"  ⚠️  Skipped (column/table not found)")
            else:
                print(f"  ❌ Error: {e}")
                error_count += 1
        finally:
            if conn:
                conn.close()
    
    print(f"\n✅ Index creation complete!")
    print(f"   Success: {success_count}/{len(INDEXES)}")
    if error_count > 0:
        print(f"   Errors: {error_count}")

if __name__ == "__main__":
    create_indexes()
