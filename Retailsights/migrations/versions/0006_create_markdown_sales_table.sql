-- 0006_create_markdown_sales_table.sql
-- Tracks discounted sales (yellow sticker markdowns)

CREATE TABLE IF NOT EXISTS markdown_sales (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  shop_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  expiry_record_id BIGINT NULL,
  sku VARCHAR(255) NOT NULL,
  quantity_sold INT NOT NULL DEFAULT 1,
  original_price DECIMAL(10,2) NOT NULL,
  discounted_price DECIMAL(10,2) NOT NULL,
  discount_percent DECIMAL(6,2) NOT NULL,
  discount_amount DECIMAL(10,2) NOT NULL,
  rule_id BIGINT NULL,
  rule_name VARCHAR(100),
  sold_by BIGINT NULL,
  sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (shop_id),
  INDEX (product_id),
  INDEX (sold_at),
  INDEX (sku)
);
