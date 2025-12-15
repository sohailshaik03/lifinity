# RetailSight Enterprise Setup Guide

## Overview

RetailSight is a professional-grade retail inventory management system built with Streamlit, MySQL, and Celery. It provides sales analytics, expiry tracking, dynamic pricing, AI model rollout control, and automated alert notifications.

## Prerequisites

- Python 3.13+
- MySQL 8.0+
- Redis (for Celery task broker)
- Git

## Installation

### 1. Clone and set up environment

```bash
cd /Users/shaiksohail/retailsight
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/retailsight
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=retailsight

# Flask/Streamlit
FLASK_ENV=production
STREAMLIT_SERVER_PORT=8501

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Email (SendGrid)
SENDGRID_API_KEY=your_sendgrid_key
SENDER_EMAIL=noreply@retailsight.local

# SMS (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Cloud Storage (S3 - optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_S3_BUCKET=retailsight-exports
AWS_REGION=us-east-1

# AI Rollout Control
FEATURE_FLAG_GPT5_MINI_ENABLED=false
GPT5_MINI_CANARY_PERCENTAGE=0

# Logging
LOG_LEVEL=INFO
```

### 3. Initialize database

```bash
# Create database schema
python scripts/run_migration.py migrations/versions/0001_create_users_shops.sql --yes
python scripts/run_migration.py migrations/versions/0002_create_sales_tables.sql --yes
python scripts/run_migration.py migrations/versions/0003_create_product_expiry_tables.sql --yes
python scripts/run_migration.py migrations/versions/0004_create_alert_tables.sql --yes

# Create initial admin user
python create_admin.py
```

### 4. Start services

**Terminal 1 - Streamlit app:**
```bash
streamlit run app.py
```

**Terminal 2 - Celery worker (for background tasks):**
```bash
celery -A services.celery_app worker --loglevel=info
```

**Terminal 3 - Celery beat (for scheduled tasks):**
```bash
celery -A services.celery_app beat --loglevel=info
```

**Terminal 4 - Redis (if not running as service):**
```bash
redis-server
```

The app will be available at `http://localhost:8501`

## Key Features

### 1. Sales & Analytics
- File upload (CSV/Excel)
- Sales forecasting (Holt-Winters, ARIMA, Prophet, scikit-learn)
- Export analytics (PDF, CSV, Excel)
- Cloud storage export (S3 optional)
- Historical reports with charts

### 2. Expiry & Waste Management
- Product inventory tracking
- Expiry records with batch management
- M&S-style dynamic discount rules
- Waste logging and analytics
- Bulk product import with CSV validation
- Automatic discount calculation based on days-to-expiry

### 3. Alerts & Notifications
- Email alerts (SendGrid integration)
- SMS alerts (Twilio integration)
- Per-shop alert configuration
- Customizable expiry threshold (1-30 days)
- Automatic daily expiry checks
- Alert history and delivery status tracking

### 4. AI Model Rollout
- Feature flags for controlled rollout
- Canary deployment strategy (0-100% user distribution)
- Cost estimator dashboard
- Cost breakdown: fixed + per-user + per-request + token costs
- Comprehensive safety checklist

### 5. User Management
- Role-based access control (admin, manager, user)
- Multi-shop user assignment
- Admin panel for user/shop management
- Audit logging

## Bulk Product Import

### Format
Upload a CSV with required columns:

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| sku | string | Yes | Product SKU (unique per shop) |
| name | string | Yes | Product name |
| cost_price | float | Yes | Cost price |
| selling_price | float | Yes | Selling price |
| category | string | No | Product category |
| expiry_date | date | No | If include_expiry=true (YYYY-MM-DD) |
| batch_number | string | No | If include_expiry=true |
| qty_received | int | No | If include_expiry=true |

### Usage in UI

1. Go to **Expiry & Waste** → **Bulk Import** tab
2. Click **📥 Download template CSV** for sample format
3. Populate your products (validate: no duplicates, required fields present)
4. Upload CSV file
5. Check **Include expiry records** if you have expiry columns
6. Click **🚀 Import products**
7. Review results (errors/warnings displayed)

### Validation Rules
- SKU must be unique per shop (duplicates rejected)
- cost_price and selling_price must be numeric and ≥ 0
- expiry_date (if present) must be valid date format (YYYY-MM-DD)
- Required columns must not be empty
- Max 10,000 products per import

## Alert Configuration

### Step 1: Enable alerts in Admin Panel
1. Login as admin
2. Go to **⚙️ Admin Panel** → **Alert Settings**
3. Select shop from dropdown
4. Enable/disable **Email alerts** and **SMS alerts**
5. Set **Alert threshold** (1-30 days before expiry)

### Step 2: Configure Recipients
- **Email addresses**: Enter one per line (e.g., `shop1@example.com`)
- **Phone numbers**: E.164 format, one per line (e.g., `+441234567890`)

### Step 3: Save and test
1. Click **💾 Save alert settings**
2. Alerts will run automatically daily via Celery Beat
3. Or manually trigger: Admin Panel → **Alert Settings** → Test button (if available)

### Environment Setup
- **SendGrid**: Set `SENDGRID_API_KEY` in `.env` (free tier: 100 emails/day)
- **Twilio**: Set `TWILIO_*` credentials in `.env` (SMS charges apply)
- Without credentials, alerts are logged to console (stub mode)

## Discount Rules & Reports

### Creating Discount Rules

1. Go to **Expiry & Waste** → **Discount Rules** tab
2. Click **+ Add new rule**
3. Configure:
   - **Rule name**: e.g., "1-week before expiry"
   - **Days left (min/max)**: e.g., 1-7 days
   - **Min quantity**: e.g., 1 unit minimum
   - **Discount %**: e.g., 20% off
4. Click **Create rule**

### Viewing Discount Impact Reports

1. Go to **Expiry & Waste** → **Discount Reports**
2. Select analysis period (1-365 days)
3. View metrics:
   - Discount transactions count
   - Revenue forgone (£)
   - Average discount %
4. Breakdown by rule with chart
5. Expiring vs Wasted comparison (pie/bar chart)

**What gets tracked:**
- Each sale with a discount (from discount rules) creates a `discount_applied` record
- Revenue forgone = units_sold × (original_price - discounted_price)
- Report correlates discounts with product expiry/waste records

## Troubleshooting

### Celery tasks not running
1. Ensure Redis is running: `redis-cli ping` (should return PONG)
2. Check Celery worker logs for errors
3. Verify `REDIS_URL` in `.env` is correct

### Alerts not sending
1. Check if SendGrid/Twilio credentials are set in `.env`
2. Review app logs: `tail -f logs/*.log`
3. Verify email/phone format in Alert Settings
4. Test manually: run `celery -A services.celery_app call services.alert_tasks.send_pending_alerts`

### Database connection error
1. Verify MySQL is running: `mysql -u root -p -e "SELECT 1"`
2. Check `DATABASE_URL` in `.env`
3. Ensure database exists: `CREATE DATABASE retailsight;`

### Import fails with "Duplicate SKU"
- SKU must be unique per shop
- If re-importing same products, delete old records first or use different SKUs

## Docker Deployment (Optional)

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app
```

See `docker-compose.yml` for service configuration.

## Testing

Run unit tests:
```bash
pytest -v tests/
```

With coverage:
```bash
pytest --cov=services --cov=repositories tests/
```

## Project Structure

```
retailsight/
├── app.py                          # Main Streamlit app
├── config.py                       # Configuration
├── db.py                           # Database connection
├── logger.py                       # Logging setup
├── requirements.txt                # Dependencies
│
├── migrations/
│   └── versions/
│       ├── 0001_*.sql              # Users/shops schema
│       ├── 0002_*.sql              # Sales schema
│       ├── 0003_*.sql              # Expiry/waste schema
│       └── 0004_*.sql              # Alert schema
│
├── repositories/                   # Data access layer (CRUD)
│   ├── users_repo.py
│   ├── shops_repo.py
│   ├── products_repo.py            # Products + expiry/waste/discount_rules
│   ├── sales_repo.py
│   ├── alerts_repo.py              # Alert notifications + settings
│   └── expiry_repo.py
│
├── services/                       # Business logic layer
│   ├── bulk_import_service.py      # CSV import with validation
│   ├── notification_service.py     # Email/SMS sending (SendGrid/Twilio)
│   ├── alert_tasks.py              # Celery tasks for alerts
│   ├── discount_report_service.py  # Report generation
│   ├── analytics_service.py        # Sales forecasting + export
│   ├── expiry_service.py           # Expiry tracking logic
│   ├── user_service.py
│   ├── discount_service.py
│   └── celery_app.py               # Celery config + optional stub
│
├── ui/                             # Streamlit UI layer
│   ├── layout.py                   # Page layout
│   ├── components.py               # Reusable components
│   ├── theme.py                    # Color theme
│   └── tabs/
│       ├── login_tab.py
│       ├── admin_tab.py            # Admin + alert settings
│       ├── manager_tab.py
│       ├── upload_tab.py           # Sales upload + analytics
│       ├── expiry_tab.py           # Expiry/waste + bulk import + reports
│       ├── history_tab.py
│       └── ai_management_tab.py    # AI rollout control
│
├── utils/                          # Utilities
│   ├── helpers.py
│   ├── security.py                 # Password hashing
│   └── validation.py               # Input validation
│
├── scripts/
│   └── run_migration.py            # Database migration runner
│
├── tests/                          # Unit tests
│   ├── test_*.py
│   └── conftest.py
│
└── README.md / SETUP_GUIDE.md      # Documentation
```

## Production Checklist

- [ ] Set strong database password
- [ ] Configure SendGrid API key for production
- [ ] Configure Twilio credentials (or disable SMS)
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS (reverse proxy or Streamlit config)
- [ ] Set up automated backups (database)
- [ ] Monitor Celery worker health
- [ ] Review and adjust Celery task timeouts
- [ ] Configure log rotation (logs/ directory)
- [ ] Test alert delivery end-to-end
- [ ] Load test with sample data
- [ ] Set up monitoring/alerting for service health
- [ ] Document runbooks for incident response

## Support

For issues or questions, check:
1. Logs in `logs/` directory
2. Database logs (MySQL error log)
3. Celery worker output
4. Streamlit console output

---

**Version**: 1.0  
**Last updated**: 2024  
**Maintained by**: RetailSight Dev Team
