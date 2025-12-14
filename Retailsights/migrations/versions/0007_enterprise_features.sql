-- Migration 0007: Enterprise Features
-- Blockchain, IoT Sensors, Computer Vision

-- Blockchain ledger table
CREATE TABLE IF NOT EXISTS blockchain_ledger (
    id INT PRIMARY KEY AUTO_INCREMENT,
    block_index INT NOT NULL,
    block_hash VARCHAR(64) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    timestamp DATETIME NOT NULL,
    event_type ENUM('RECEIVED', 'STORED', 'DISCOUNTED', 'SOLD', 'WASTED', 'RECALL') NOT NULL,
    product_id INT,
    sku VARCHAR(50),
    data JSON,
    verified BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_block (block_index),
    INDEX idx_product (product_id),
    INDEX idx_sku (sku),
    INDEX idx_event_type (event_type),
    INDEX idx_timestamp (timestamp),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- IoT sensors table
CREATE TABLE IF NOT EXISTS iot_sensors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    shop_id INT NOT NULL,
    sensor_id VARCHAR(100) NOT NULL,
    sensor_type ENUM('temperature', 'humidity', 'temperature_humidity', 'door', 'motion', 'power') NOT NULL,
    location VARCHAR(200) NOT NULL,
    zone_type ENUM('frozen', 'chilled', 'ambient') NOT NULL,
    status ENUM('active', 'inactive', 'maintenance') DEFAULT 'active',
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reading_at TIMESTAMP NULL,
    UNIQUE KEY unique_sensor (sensor_id),
    INDEX idx_shop (shop_id),
    INDEX idx_status (status),
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sensor readings table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id VARCHAR(100) NOT NULL,
    temperature DECIMAL(5,2) NULL,
    humidity DECIMAL(5,2) NULL,
    door_open BOOLEAN NULL,
    power_status BOOLEAN NULL,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sensor (sensor_id),
    INDEX idx_recorded_at (recorded_at),
    FOREIGN KEY (sensor_id) REFERENCES iot_sensors(sensor_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sensor alerts table
CREATE TABLE IF NOT EXISTS sensor_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sensor_id VARCHAR(100) NOT NULL,
    shop_id INT NOT NULL,
    severity ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    alert_type ENUM('TEMP_TOO_HIGH', 'TEMP_TOO_LOW', 'DOOR_OPEN', 'POWER_FAILURE', 'SENSOR_OFFLINE') NOT NULL,
    message TEXT,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    resolved_by INT NULL,
    INDEX idx_sensor (sensor_id),
    INDEX idx_shop (shop_id),
    INDEX idx_resolved (resolved),
    INDEX idx_triggered_at (triggered_at),
    FOREIGN KEY (sensor_id) REFERENCES iot_sensors(sensor_id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Quality inspections table (computer vision)
CREATE TABLE IF NOT EXISTS quality_inspections (
    id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    overall_score DECIMAL(5,2) NOT NULL,
    freshness_score DECIMAL(5,2) NULL,
    packaging_score DECIMAL(5,2) NULL,
    action_required ENUM('SELL_FULL_PRICE', 'MINOR_DISCOUNT', 'HEAVY_DISCOUNT', 'REMOVE') NOT NULL,
    recommendation TEXT,
    image_path VARCHAR(500) NULL,
    inspected_by INT NULL,
    inspected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_product (product_id),
    INDEX idx_inspected_at (inspected_at),
    INDEX idx_action (action_required),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (inspected_by) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Customer API related tables
CREATE TABLE IF NOT EXISTS customer_price_alerts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_sku VARCHAR(50) NOT NULL,
    shop_id INT NOT NULL,
    target_discount_percent INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered BOOLEAN DEFAULT FALSE,
    triggered_at TIMESTAMP NULL,
    INDEX idx_customer (customer_id),
    INDEX idx_sku (product_sku),
    INDEX idx_triggered (triggered),
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS customer_reservations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    product_id INT NOT NULL,
    shop_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    reserved_until TIMESTAMP NOT NULL,
    status ENUM('active', 'collected', 'expired', 'cancelled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    collected_at TIMESTAMP NULL,
    INDEX idx_customer (customer_id),
    INDEX idx_product (product_id),
    INDEX idx_status (status),
    INDEX idx_reserved_until (reserved_until),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add batch_id column to products table for recall tracking
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS batch_id VARCHAR(100) NULL AFTER sku,
ADD INDEX idx_batch_id (batch_id);

-- Add status column to products for recall status
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS status ENUM('active', 'RECALLED', 'discontinued') DEFAULT 'active' AFTER batch_id;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_blockchain_hash ON blockchain_ledger(block_hash);
CREATE INDEX IF NOT EXISTS idx_sensor_shop_location ON iot_sensors(shop_id, location);
CREATE INDEX IF NOT EXISTS idx_quality_score ON quality_inspections(overall_score);

-- Insert sample IoT data for demo
-- This will be removed in production and sensors will register via API
