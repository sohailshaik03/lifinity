-- 0005_create_scan_history_table.sql
-- Tracks barcode / QR scans for audit & analytics

CREATE TABLE IF NOT EXISTS scan_history (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  shop_id BIGINT NOT NULL,
  product_id BIGINT NULL,
  code VARCHAR(255) NOT NULL,
  code_type VARCHAR(32) NOT NULL, -- barcode | qr
  source VARCHAR(32) NOT NULL,    -- manual | image | webcam
  discount_applied BOOLEAN DEFAULT 0,
  discount_percent DECIMAL(6,2) DEFAULT 0,
  original_price DECIMAL(10,2) NULL,
  discounted_price DECIMAL(10,2) NULL,
  message VARCHAR(255),
  scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (shop_id),
  INDEX (product_id),
  INDEX (code),
  INDEX (scanned_at)
);
