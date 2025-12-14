-- Yellow Sticker System Setup SQL
-- Run this with: mysql -u root -p retailsight < setup_yellow_sticker.sql

-- Create tables
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
  days_left INT,
  status VARCHAR(32) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (product_id),
  INDEX (expiry_date),
  INDEX (status)
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

-- Insert sample products
INSERT INTO products (shop_id, sku, name, category, cost_price, selling_price, current_stock)
VALUES 
  (1, 'MILK001', 'Fresh Whole Milk 2L', 'Dairy', 1.20, 2.50, 15),
  (1, 'BREAD001', 'White Bread', 'Bakery', 0.50, 1.20, 20),
  (1, 'YOGURT001', 'Greek Yogurt 500g', 'Dairy', 1.00, 2.00, 12),
  (1, 'CHEESE001', 'Cheddar Cheese 400g', 'Dairy', 2.50, 4.50, 8),
  (1, 'CHICKEN001', 'Fresh Chicken Breast 1kg', 'Meat', 4.00, 7.99, 10),
  (1, 'FISH001', 'Salmon Fillet 400g', 'Fish', 5.00, 9.99, 6),
  (1, 'SALAD001', 'Mixed Salad Leaves 200g', 'Produce', 0.80, 1.50, 18),
  (1, 'JUICE001', 'Orange Juice 1L', 'Beverages', 1.20, 2.50, 14)
ON DUPLICATE KEY UPDATE 
  name = VALUES(name),
  selling_price = VALUES(selling_price),
  current_stock = VALUES(current_stock);

-- Insert expiry records (various dates)
INSERT INTO expiry_records (product_id, batch_number, quantity_received, quantity_remaining, expiry_date, received_date, status)
SELECT 
  p.id,
  CONCAT('BATCH', DATE_FORMAT(NOW(), '%Y%m'), LPAD(p.id, 3, '0')),
  10,
  10,
  CASE p.sku
    WHEN 'MILK001' THEN DATE_ADD(CURDATE(), INTERVAL 1 DAY)
    WHEN 'BREAD001' THEN DATE_ADD(CURDATE(), INTERVAL 2 DAY)
    WHEN 'YOGURT001' THEN DATE_ADD(CURDATE(), INTERVAL 3 DAY)
    WHEN 'CHEESE001' THEN DATE_ADD(CURDATE(), INTERVAL 5 DAY)
    WHEN 'CHICKEN001' THEN DATE_ADD(CURDATE(), INTERVAL 2 DAY)
    WHEN 'FISH001' THEN DATE_ADD(CURDATE(), INTERVAL 1 DAY)
    WHEN 'SALAD001' THEN DATE_ADD(CURDATE(), INTERVAL 3 DAY)
    WHEN 'JUICE001' THEN DATE_ADD(CURDATE(), INTERVAL 7 DAY)
  END,
  DATE_SUB(CURDATE(), INTERVAL 2 DAY),
  'active'
FROM products p
WHERE p.shop_id = 1;
-- Update days_left calculation
UPDATE expiry_records SET days_left = DATEDIFF(expiry_date, CURDATE());


-- Insert discount rules
INSERT INTO discount_rules (shop_id, name, days_left_min, days_left_max, quantity_min, discount_percent, active)
VALUES 
  (1, '10% off - 7+ days', 7, 999, 0, 10, 1),
  (1, '20% off - 5-6 days', 5, 6, 0, 20, 1),
  (1, '30% off - 3-4 days', 3, 4, 0, 30, 1),
  (1, '40% off - 2 days', 2, 2, 0, 40, 1),
  (1, '50% off - last day', 0, 1, 0, 50, 1)
ON DUPLICATE KEY UPDATE 
  days_left_min = VALUES(days_left_min),
  days_left_max = VALUES(days_left_max),
  discount_percent = VALUES(discount_percent);

-- Show results
SELECT '=== PRODUCTS ===' AS '';
SELECT sku, name, selling_price, current_stock FROM products WHERE shop_id = 1;

SELECT '=== EXPIRING PRODUCTS ===' AS '';
SELECT 
  p.sku,
  p.name,
  p.selling_price,
  e.expiry_date,
  e.days_left,
  e.batch_number
FROM expiry_records e
JOIN products p ON e.product_id = p.id
WHERE e.status = 'active'
ORDER BY e.days_left ASC;

SELECT '=== DISCOUNT RULES ===' AS '';
SELECT name, days_left_min, days_left_max, discount_percent FROM discount_rules WHERE shop_id = 1 ORDER BY discount_percent DESC;

SELECT 'Setup complete! You can now generate yellow sticker labels.' AS '';
