-- 0004_create_alert_tables.sql

CREATE TABLE IF NOT EXISTS alert_notifications (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  shop_id BIGINT NOT NULL,
  product_id BIGINT,
  alert_type VARCHAR(50),
  message LONGTEXT,
  recipient_email VARCHAR(255),
  recipient_phone VARCHAR(20),
  sent BOOLEAN DEFAULT 0,
  delivery_status VARCHAR(50),
  sent_at TIMESTAMP NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (shop_id),
  INDEX (sent)
);

CREATE TABLE IF NOT EXISTS alert_settings (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  shop_id BIGINT UNIQUE,
  email_enabled BOOLEAN DEFAULT 1,
  sms_enabled BOOLEAN DEFAULT 0,
  alert_days_threshold INT DEFAULT 7,
  alert_emails TEXT,
  alert_phones TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX (shop_id)
);
