
-- Users Table (required for authentication)
CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'owner',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Shops table (basic) - referenced by other tables
CREATE TABLE IF NOT EXISTS shops (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_user_id INT UNSIGNED,
    address JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
 
-- Subscription Plans Table
CREATE TABLE IF NOT EXISTS subscription_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tier VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    max_file_size_mb INT NOT NULL,
    max_rows INT NOT NULL,
    max_columns INT NOT NULL,
    allowed_file_types JSON,
    allowed_analysis_types JSON,
    features JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tier (tier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default plans
INSERT INTO subscription_plans (tier, name, price, max_file_size_mb, max_rows, max_columns, 
    allowed_file_types, allowed_analysis_types, features) 
VALUES 
    ('basic', 'Basic Plan', 0.00, 10, 1000, 50, 
     '["csv", "xlsx"]', 
     '["orders"]',
     '{"multi_file_analysis": false, "power_bi_export": false, "ml_predictions": false, "api_access": false}'),
    ('premium', 'Premium Plan', 49.00, 100, 100000, 200,
     '["csv", "xlsx", "json", "parquet"]',
     '["orders", "returns", "inventory", "customers"]',
     '{"multi_file_analysis": true, "power_bi_export": true, "ml_predictions": false, "api_access": true, "anomaly_detection": true}'),
    ('ultra_premium', 'Ultra Premium Plan', 199.00, 1000, 10000000, 1000,
     '["csv", "xlsx", "json", "parquet", "xml", "sql"]',
     '["orders", "returns", "inventory", "customers", "reviews", "products", "categories", "suppliers", "shipments", "payments"]',
     '{"multi_file_analysis": true, "power_bi_export": true, "ml_predictions": true, "api_access": true, "anomaly_detection": true, "custom_ml_models": true, "real_time_processing": true}')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- User Subscriptions Table
CREATE TABLE IF NOT EXISTS user_subscriptions (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    plan_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NULL,
    trial_ends_at TIMESTAMP NULL,
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_method VARCHAR(50),
    last_payment_date TIMESTAMP NULL,
    next_billing_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_end_date (end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Feature Usage Tracking
CREATE TABLE IF NOT EXISTS feature_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    usage_count INT DEFAULT 1,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_feature (user_id, feature_name),
    INDEX idx_last_used (last_used_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- File Uploads Tracking (Enhanced)
CREATE TABLE IF NOT EXISTS file_uploads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    shop_id INT UNSIGNED,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    detected_type VARCHAR(50),
    file_size_mb DECIMAL(10, 2),
    row_count INT,
    column_count INT,
    quality_score DECIMAL(5, 2),
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_time_seconds DECIMAL(10, 2),
    error_message TEXT,
    s3_key VARCHAR(500),
    metadata JSON,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (shop_id) REFERENCES shops(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_shop_id (shop_id),
    INDEX idx_uploaded_at (uploaded_at),
    INDEX idx_status (processing_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Analysis History
CREATE TABLE IF NOT EXISTS analysis_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    file_upload_id INT,
    analysis_type VARCHAR(100) NOT NULL,
    parameters JSON,
    results JSON,
    execution_time_seconds DECIMAL(10, 2),
    tier_used VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (file_upload_id) REFERENCES file_uploads(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_analysis_type (analysis_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Multi-File Analysis Sessions
CREATE TABLE IF NOT EXISTS multi_file_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    session_name VARCHAR(255),
    file_count INT DEFAULT 0,
    join_operations JSON,
    insights JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Session Files (many-to-many)
CREATE TABLE IF NOT EXISTS session_files (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    file_upload_id INT NOT NULL,
    file_role VARCHAR(50),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES multi_file_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (file_upload_id) REFERENCES file_uploads(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_file_upload_id (file_upload_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Power BI Exports
CREATE TABLE IF NOT EXISTS powerbi_exports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    file_upload_id INT,
    export_format VARCHAR(50) DEFAULT 'csv',
    metadata JSON,
    download_url VARCHAR(500),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (file_upload_id) REFERENCES file_uploads(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Subscription Payment History
CREATE TABLE IF NOT EXISTS subscription_payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_subscription_id INT UNSIGNED NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_status VARCHAR(50) DEFAULT 'pending',
    payment_method VARCHAR(50),
    transaction_id VARCHAR(255),
    billing_period_start DATE,
    billing_period_end DATE,
    paid_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_subscription_id) REFERENCES user_subscriptions(id) ON DELETE CASCADE,
    INDEX idx_subscription_id (user_subscription_id),
    INDEX idx_status (payment_status),
    INDEX idx_paid_at (paid_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- API Keys (for programmatic access)
CREATE TABLE IF NOT EXISTS api_keys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    name VARCHAR(100),
    scopes JSON,
    rate_limit_per_hour INT DEFAULT 100,
    last_used_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_key_hash (key_hash),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Upgrade Requests (for sales tracking)
CREATE TABLE IF NOT EXISTS upgrade_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    current_tier VARCHAR(50),
    requested_tier VARCHAR(50),
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    company_name VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
