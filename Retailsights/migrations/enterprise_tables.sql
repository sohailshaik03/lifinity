-- Enterprise Features Database Tables
-- Run this to create missing tables for advanced features

-- Alert Notifications Table
CREATE TABLE IF NOT EXISTS alert_notifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    shop_id INT UNSIGNED NOT NULL,
    product_id INT UNSIGNED,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    recipient_email VARCHAR(255),
    recipient_phone VARCHAR(20),
    sent BOOLEAN DEFAULT FALSE,
    delivery_status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_shop_sent (shop_id, sent),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Alert Settings Table
CREATE TABLE IF NOT EXISTS alert_settings (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    shop_id INT UNSIGNED NOT NULL UNIQUE,
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    alert_days_threshold INT DEFAULT 7,
    alert_emails TEXT,
    alert_phones TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Blockchain Ledger Table
CREATE TABLE IF NOT EXISTS blockchain_ledger (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    block_index INT UNSIGNED NOT NULL UNIQUE,
    block_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp DATETIME NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    product_id INT UNSIGNED,
    sku VARCHAR(100),
    data JSON,
    verified BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    INDEX idx_product (product_id),
    INDEX idx_event (event_type),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- IoT Sensors Table
CREATE TABLE IF NOT EXISTS iot_sensors (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    shop_id INT UNSIGNED NOT NULL,
    sensor_id VARCHAR(100) NOT NULL UNIQUE,
    sensor_type VARCHAR(50) NOT NULL,
    location VARCHAR(255) NOT NULL,
    zone_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    last_reading_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
    INDEX idx_shop_status (shop_id, status),
    INDEX idx_sensor_type (sensor_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sensor Readings Table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT UNSIGNED NOT NULL,
    temperature DECIMAL(5,2),
    humidity DECIMAL(5,2),
    reading_timestamp DATETIME NOT NULL,
    status VARCHAR(20) DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sensor_id) REFERENCES iot_sensors(id) ON DELETE CASCADE,
    INDEX idx_sensor_time (sensor_id, reading_timestamp),
    INDEX idx_timestamp (reading_timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sensor Alerts Table
CREATE TABLE IF NOT EXISTS sensor_alerts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sensor_id INT UNSIGNED NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    value DECIMAL(10,2),
    threshold DECIMAL(10,2),
    resolved BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    FOREIGN KEY (sensor_id) REFERENCES iot_sensors(id) ON DELETE CASCADE,
    INDEX idx_sensor_resolved (sensor_id, resolved),
    INDEX idx_severity (severity),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Quality Inspections Table (Computer Vision)
CREATE TABLE IF NOT EXISTS quality_inspections (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    product_id INT UNSIGNED,
    shop_id INT UNSIGNED NOT NULL,
    inspection_type VARCHAR(50) NOT NULL,
    quality_score DECIMAL(5,2),
    freshness_score DECIMAL(5,2),
    damage_detected BOOLEAN DEFAULT FALSE,
    compliance_status VARCHAR(20),
    image_path VARCHAR(500),
    findings JSON,
    inspected_by INT UNSIGNED,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
    FOREIGN KEY (inspected_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_product (product_id),
    INDEX idx_shop_type (shop_id, inspection_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
