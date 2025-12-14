-- 0003_create_product_expiry_tables.sql

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
);

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
);

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
);

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
);
