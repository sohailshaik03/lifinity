-- 0002_create_report_exports.sql
-- Create table to track generated export reports

CREATE TABLE IF NOT EXISTS report_exports (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  shop_id BIGINT NULL,
  user_id BIGINT NULL,
  filename VARCHAR(255) NOT NULL,
  provider VARCHAR(50) NULL,
  url TEXT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  task_id VARCHAR(255) NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP NULL,
  INDEX (shop_id),
  INDEX (task_id)
);
