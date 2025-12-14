# RetailSight Implementation Checklist

## Pre-Launch Setup (Required)

### Database
- [ ] MySQL 8.0+ installed and running
- [ ] Database created: `CREATE DATABASE retailsight;`
- [ ] Run migration 0001: `python scripts/run_migration.py migrations/versions/0001_create_users_shops.sql --yes`
- [ ] Run migration 0002: `python scripts/run_migration.py migrations/versions/0002_create_sales_tables.sql --yes`
- [ ] Run migration 0003: `python scripts/run_migration.py migrations/versions/0003_create_product_expiry_tables.sql --yes`
- [ ] Run migration 0004: `python scripts/run_migration.py migrations/versions/0004_create_alert_tables.sql --yes`
- [ ] Verify tables: `mysql -u root -p retailsight -e "SHOW TABLES;"`

### Environment Configuration
- [ ] Create `.env` file in project root
- [ ] Set DB_HOST, DB_USER, DB_PASSWORD
- [ ] Set DB_NAME=retailsight
- [ ] Set REDIS_URL=redis://localhost:6379/0
- [ ] Optional: Set SENDGRID_API_KEY
- [ ] Optional: Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER

### User & Access
- [ ] Run: `python create_admin.py`
- [ ] Create admin user (email + password)
- [ ] Create at least one shop
- [ ] Assign admin user to shop

### Dependencies
- [ ] Python 3.13+ installed
- [ ] venv created: `python -m venv venv`
- [ ] venv activated: `source venv/bin/activate`
- [ ] Requirements installed: `pip install -r requirements.txt`
- [ ] Redis installed and running: `redis-server`

---

## Launch Sequence

### Terminal 1 - Redis Broker
```bash
redis-server
# Verify: redis-cli ping (should return PONG)
```

### Terminal 2 - Celery Worker
```bash
cd /Users/shaiksohail/retailsight
source venv/bin/activate
celery -A services.celery_app worker --loglevel=info
```

### Terminal 3 - Celery Beat (Scheduler)
```bash
cd /Users/shaiksohail/retailsight
source venv/bin/activate
celery -A services.celery_app beat --loglevel=info
```

### Terminal 4 - Streamlit Application
```bash
cd /Users/shaiksohail/retailsight
source venv/bin/activate
streamlit run app.py
# App will open at http://localhost:8501
```

---

## First-Run Validation

### Login & Navigation
- [ ] Navigate to http://localhost:8501
- [ ] Login with admin credentials
- [ ] Select shop from dropdown
- [ ] Navigate to each tab (no errors)

### Test Each Feature
- [ ] **Admin Panel** → Create new user → Assign to shop
- [ ] **Sales Upload** → Upload sample sales file → View analytics
- [ ] **Expiry & Waste → Bulk Import** → Download template → Upload CSV
- [ ] **Expiry & Waste → Discount Rules** → Create a rule
- [ ] **Expiry & Waste → Discount Reports** → View metrics (should show 0 if no sales yet)
- [ ] **Admin Panel → Alert Settings** → Configure shop alerts

### Celery Tasks
- [ ] Check worker terminal for: "Received task" messages
- [ ] Check beat terminal for: "Scheduler" startup message
- [ ] Manually trigger test: In Celery worker terminal, should see task execution

---

## Configuration Guide

### .env File Template
```env
# Database Connection
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/retailsight
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=retailsight

# Redis (Celery Broker)
REDIS_URL=redis://localhost:6379/0

# Flask/Streamlit
FLASK_ENV=production
STREAMLIT_SERVER_PORT=8501

# Email (SendGrid) - Optional
SENDGRID_API_KEY=
SENDER_EMAIL=noreply@retailsight.local

# SMS (Twilio) - Optional
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# Cloud Storage (S3) - Optional
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=retailsight-exports
AWS_REGION=us-east-1

# Logging
LOG_LEVEL=INFO
FLASK_LOG_LEVEL=INFO

# Feature Flags
FEATURE_FLAG_GPT5_MINI_ENABLED=false
GPT5_MINI_CANARY_PERCENTAGE=0
```

---

## Feature-by-Feature Setup

### Bulk Product Import
1. Go to **Expiry & Waste → Bulk Import**
2. Click **📥 Download template CSV**
3. Prepare CSV with columns: sku, name, cost_price, selling_price
4. (Optional) Add columns: category, expiry_date, batch_number, qty_received
5. Upload CSV
6. Check "Include expiry records" if you have expiry columns
7. Click "🚀 Import products"
8. Review results (errors/warnings)

### Alert Notifications
1. Go to **Admin Panel → Alert Settings**
2. Select shop from dropdown
3. Enable/disable email alerts (SendGrid required for actual send)
4. Enable/disable SMS alerts (Twilio required for actual send)
5. Set alert threshold (1-30 days)
6. Enter email addresses (one per line)
7. Enter phone numbers in E.164 format (e.g., +441234567890)
8. Click **💾 Save alert settings**
9. Alerts will run automatically daily or via manual trigger

### Discount Rules
1. Go to **Expiry & Waste → Discount Rules**
2. Click **+ Add new rule**
3. Configure:
   - Rule name: e.g., "1-week clearance"
   - Days left minimum: 1
   - Days left maximum: 7
   - Minimum quantity: 1
   - Discount %: 20
4. Click **Create rule**
5. Rule now applies automatically to matching products

### Discount Reports
1. Go to **Expiry & Waste → Discount Reports**
2. Slide "Analyze last N days" (default 30)
3. View metrics:
   - Discount transactions
   - Revenue forgone (£)
   - Avg discount %
4. Scroll to see:
   - Breakdown by rule
   - Expiring vs wasted comparison
5. Charts update as you adjust timeframe

---

## Troubleshooting

### Issue: App won't start
```
ERROR: No module named 'streamlit'
```
**Solution**:
```bash
pip install -r requirements.txt
```

### Issue: Database connection error
```
ERROR: Can't connect to MySQL server on 'localhost'
```
**Solution**:
```bash
# Verify MySQL running
mysql -u root -p -e "SELECT 1;"

# Check .env variables
cat .env | grep DB_

# Verify database exists
mysql -u root -p -e "SHOW DATABASES;"
```

### Issue: Celery worker not processing tasks
```
ERROR: Connection refused (Redis)
```
**Solution**:
```bash
# Start Redis in new terminal
redis-server

# Verify Redis
redis-cli ping  # Should return PONG
```

### Issue: Import fails with "Duplicate SKU"
**Solution**:
- SKU must be unique per shop
- Check database for existing SKU: `SELECT sku FROM products WHERE shop_id=X`
- Use different SKU or delete existing product first

### Issue: Alerts not sending email
**Solution**:
1. Check if SENDGRID_API_KEY is set in .env
2. Without key, alerts will log to console (stub mode)
3. To enable actual email:
   - Get API key from https://sendgrid.com
   - Add to .env: `SENDGRID_API_KEY=SG.xxxxx`
   - Restart app
4. Check logs: `tail -f logs/*.log | grep alert`

### Issue: File upload fails
**Solution**:
```bash
# Check permissions on app directory
ls -la /Users/shaiksohail/retailsight/

# Check logs
tail -f logs/*.log

# Clear browser cache and retry
```

---

## Performance Tips

### Database Optimization
- Create indexes on frequently queried columns (auto in migrations)
- Archive old sales data (> 1 year) to separate table
- Schedule backup: `mysqldump retailsight > backup_$(date +%Y%m%d).sql`

### Celery Optimization
- Monitor worker: `celery -A services.celery_app inspect active`
- Adjust concurrency: `celery -A services.celery_app worker --concurrency=4`
- Monitor queue: `celery -A services.celery_app inspect reserved`

### Streamlit Optimization
- Enable caching on slow queries: `@st.cache_data(ttl=3600)`
- Use multiselect instead of looping queries
- Pre-compute reports off-peak

---

## Monitoring Checklist

### Daily
- [ ] Redis running (`redis-cli ping`)
- [ ] Celery worker running (check terminal output)
- [ ] Celery beat running (check terminal output)
- [ ] Streamlit app accessible (http://localhost:8501)
- [ ] No ERROR logs: `grep ERROR logs/*.log`

### Weekly
- [ ] Backup database: `mysqldump retailsight > backup_$(date +%Y%m%d).sql`
- [ ] Review discount report: Any unexpected patterns?
- [ ] Check waste records: Any spikes?
- [ ] Alert delivery: Any failed sends? `grep alert logs/*.log | grep ERROR`

### Monthly
- [ ] Archive old sales data (if >100k rows)
- [ ] Review discount rule effectiveness
- [ ] Check Celery task performance: `celery -A services.celery_app inspect stats`
- [ ] Test disaster recovery (backup restore)

---

## Security Hardening (Production)

- [ ] Change default admin password
- [ ] Use strong database password (20+ chars, mixed case, numbers, symbols)
- [ ] Restrict MySQL to localhost only (not 0.0.0.0)
- [ ] Store .env file outside web root
- [ ] Use HTTPS with valid SSL certificate
- [ ] Set up firewall rules (port 8501, 3306, 6379 internal only)
- [ ] Enable database backups to S3
- [ ] Set up monitoring alerts for down services
- [ ] Review user access quarterly
- [ ] Rotate API keys (SendGrid, Twilio) annually

---

## Deployment (Optional)

### Docker Deployment
- [ ] Docker installed
- [ ] `docker-compose up -d` to start all services
- [ ] App at http://localhost:8501
- [ ] Check logs: `docker-compose logs -f app`

### Cloud Deployment (AWS/GCP/Azure)
- [ ] Database (RDS/Cloud SQL)
- [ ] Application (EC2/AppEngine/Container)
- [ ] Celery worker (EC2/Compute Engine/Container)
- [ ] Redis (ElastiCache/Cloud Memorystore/Container)
- [ ] DNS configuration
- [ ] SSL/TLS certificate

---

## Completion Verification

### All Systems Running?
```bash
# Terminal 1: Redis
redis-cli ping
# Expected: PONG

# Terminal 2: Celery Worker
# Check for: "celery@hostname ready"

# Terminal 3: Celery Beat
# Check for: "Scheduler initialized"

# Terminal 4: Streamlit
curl http://localhost:8501
# Expected: HTTP 200
```

### Database Ready?
```bash
mysql -u root -p retailsight -e "SHOW TABLES;"
# Expected: 15+ tables including products, alert_notifications, etc.
```

### Features Working?
- [ ] Login successful
- [ ] Bulk import works (CSV uploaded, products created)
- [ ] Discount rules created
- [ ] Alert settings saved
- [ ] Report displays data
- [ ] No error messages in any logs

---

## Support & Escalation

### Level 1: Check Logs
- App logs: `tail -f logs/*.log`
- MySQL logs: `/var/log/mysql/error.log` (or MySQL workbench)
- Redis logs: Check terminal where redis-server runs
- Celery logs: Check worker/beat terminal

### Level 2: Test Components
- Database: `mysql -u root -p retailsight -e "SELECT COUNT(*) FROM products;"`
- Redis: `redis-cli info`
- Celery: `celery -A services.celery_app inspect active`

### Level 3: Review Code
- Check imports: `python -c "from services.bulk_import_service import BulkImportService"`
- Verify migrations: `python scripts/run_migration.py --list`
- Test Celery task: Manual trigger in worker

### Level 4: Seek Help
- GitHub repo (if applicable)
- Documentation files (SETUP_GUIDE.md, FEATURE_SUMMARY.md)
- Code comments and docstrings

---

**Setup Status**: Ready for Production  
**Last Updated**: 2024  
**Estimated Setup Time**: 30-45 minutes  
**Estimated First Feature Test**: 5 minutes after launch
