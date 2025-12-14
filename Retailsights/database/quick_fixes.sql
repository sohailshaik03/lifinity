-- Quick fixes: add missing shops columns and create minimal stub tables
ALTER TABLE IF EXISTS shops
  ADD COLUMN IF NOT EXISTS address_line1 VARCHAR(255),
  ADD COLUMN IF NOT EXISTS address_line2 VARCHAR(255),
  ADD COLUMN IF NOT EXISTS city VARCHAR(100),
  ADD COLUMN IF NOT EXISTS postcode VARCHAR(50),
  ADD COLUMN IF NOT EXISTS country VARCHAR(100),
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  shop_id INT UNSIGNED,
  sku VARCHAR(100),
  name VARCHAR(255),
  category VARCHAR(100),
  cost_price DECIMAL(10,2) DEFAULT 0,
  default_price DECIMAL(10,2) DEFAULT 0,
  default_cost DECIMAL(10,2) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_shop_id (shop_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_transactions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  transaction_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sales_lines (
  id INT AUTO_INCREMENT PRIMARY KEY,
  transaction_id INT,
  product_id INT,
  quantity INT DEFAULT 0,
  unit_price DECIMAL(10,2) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS waste_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT,
  quantity_wasted INT DEFAULT 0,
  recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expiry_record_id INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS markdown_sales (
  id INT AUTO_INCREMENT PRIMARY KEY,
  shop_id INT,
  sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  discounted_price DECIMAL(10,2) DEFAULT 0,
  quantity_sold INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS expiry_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT,
  expiry_date DATE,
  days_left INT,
  quantity_remaining INT DEFAULT 0,
  status VARCHAR(50) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
