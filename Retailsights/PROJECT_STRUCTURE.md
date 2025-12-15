# 📁 RetailSights - Project Structure

```
Retailsights/
│
├── 📄 app.py                      # Main Streamlit application entry point
├── 📄 config.py                   # Application configuration
├── 📄 models.py                   # SQLAlchemy database models
├── 📄 db.py                       # Database connection & pooling
├── 📄 db_orm.py                   # ORM session management
├── 📄 logger.py                   # Centralized logging
├── 📄 create_admin.py             # Admin user creation script
├── 📄 check_redis.py              # Redis connection tester
├── 📄 optimize_database.py        # Database index optimization
│
├── 📁 ui/                         # User Interface Components
│   ├── components.py              # Reusable UI components
│   └── tabs/                      # Application tabs
│       ├── dashboard_tab.py       # Main dashboard
│       ├── upload_tab.py          # Data upload interface
│       ├── history_tab.py         # Sales history
│       ├── expiry_tab.py          # Expiry management
│       ├── manager_tab.py         # Manager analytics
│       ├── yellow_sticker_tab.py  # Markdown pricing
│       ├── ai_management_tab.py   # AI insights
│       └── enterprise_tab.py      # Enterprise features
│
├── 📁 services/                   # Business Logic Layer
│   ├── analytics_service.py       # Core analytics
│   ├── managers_services.py       # Manager dashboards
│   ├── upload_service.py          # File upload processing
│   ├── export_service.py          # Data export utilities
│   ├── label_print_service.py     # Label generation
│   ├── intelligent_analyst.py     # AI-powered insights
│   ├── advanced_analytics_service.py
│   └── ...                        # Additional services
│
├── 📁 repositories/               # Data Access Layer
│   ├── products_repo.py           # Product data access
│   ├── sales_repo.py              # Sales data access
│   ├── expiry_repo.py             # Expiry tracking
│   ├── shops_repo.py              # Shop management
│   ├── users_repo.py              # User management
│   ├── subscription_repo.py       # Subscription handling
│   └── ...                        # Additional repositories
│
├── 📁 reports/                    # Report Generation
│   ├── pdf_reports.py             # PDF report generation
│   └── label_reports.py           # Label printing
│
├── 📁 utils/                      # Utility Functions
│   ├── cache_manager.py           # Caching utilities (Redis + Streamlit)
│   ├── performance_monitor.py     # Performance tracking
│   ├── pagination.py              # Pagination helpers
│   └── lazy_loading.py            # Lazy loading components
│
├── 📁 assets/                     # Static Assets
│   ├── theme.css                  # Custom styling
│   └── branding/                  # Logos and branding
│
├── 📁 database/                   # Database Scripts
│   └── subscription_schema.sql    # Database schema
│
├── 📁 migrations/                 # Database Migrations
│   ├── enterprise_tables.sql      # Enterprise features
│   └── README.md                  # Migration guide
│
├── 📁 scripts/                    # Utility Scripts
│   ├── check_tables.py            # Database verification
│   ├── create_admin_noninteractive.py
│   └── ...
│
├── 📁 docs/                       # Documentation
│   ├── SETUP_GUIDE.md             # Setup instructions
│   ├── DEPLOYMENT_GUIDE.md        # Deployment guide
│   ├── ENTERPRISE_FEATURES.md     # Enterprise documentation
│   ├── OPTIMIZATION_PHASE2.md     # Performance guide
│   └── ...                        # Additional documentation
│
├── 📁 alembic/                    # Database Migration Tool
│   ├── env.py                     # Alembic configuration
│   └── versions/                  # Migration versions
│
├── 📁 .streamlit/                 # Streamlit Configuration
│   └── config.toml                # Streamlit settings
│
├── 📄 requirements.txt            # Python dependencies
├── 📄 requirements-dev.txt        # Development dependencies
├── 📄 Dockerfile                  # Docker container config
├── 📄 docker-compose.yml          # Docker Compose config
├── 📄 .env.example                # Environment template
├── 📄 .gitignore                  # Git ignore rules
└── 📄 README.md                   # Project documentation
```

---

## 🎯 Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────┐
│         UI Layer (Streamlit)            │
│  - tabs/: Page components               │
│  - components.py: Reusable UI widgets   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│       Service Layer (Business Logic)    │
│  - Analytics & computations             │
│  - Data transformation                  │
│  - Business rules                       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│    Repository Layer (Data Access)       │
│  - Database queries                     │
│  - ORM operations                       │
│  - Data persistence                     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Database (PostgreSQL/Neon)         │
│  - SQLAlchemy models                    │
│  - Optimized indexes                    │
│  - Connection pooling                   │
└─────────────────────────────────────────┘
```

---

## 📝 Key Files Explained

### Core Application
- **app.py**: Main entry point, navigation, authentication
- **config.py**: Environment variables and app configuration
- **models.py**: Database table definitions (SQLAlchemy)

### Database
- **db.py**: Database engine and connection pool setup
- **db_orm.py**: Session management and ORM helpers

### Performance
- **utils/cache_manager.py**: Redis + Streamlit caching
- **utils/performance_monitor.py**: Query performance tracking
- **utils/pagination.py**: Large dataset handling
- **optimize_database.py**: Create performance indexes

### Features
- **services/intelligent_analyst.py**: AI-powered insights
- **ui/tabs/yellow_sticker_tab.py**: Markdown pricing
- **repositories/\*.py**: Database operations for each entity

---

## 🔄 Data Flow Example

**User uploads CSV file:**

```
1. UI (upload_tab.py)
   ↓
2. Service (upload_service.py)
   - Parse CSV
   - Validate data
   - Transform format
   ↓
3. Repository (sales_repo.py)
   - Bulk insert transactions
   - Bulk insert sales lines
   ↓
4. Database
   - Store in PostgreSQL
   - Update indexes
   ↓
5. UI (dashboard_tab.py)
   - Refresh analytics
   - Display updated charts
```

---

## 🛠️ Development Guidelines

### Adding New Features

1. **Create repository** in `repositories/` for data access
2. **Create service** in `services/` for business logic
3. **Create UI tab** in `ui/tabs/` for user interface
4. **Update models.py** if new database tables needed
5. **Add tests** in appropriate test files

### Code Organization

- **Repositories**: Pure database operations, no business logic
- **Services**: Business logic, calculations, transformations
- **UI**: Display only, minimal logic, call services

### Performance Best Practices

- Use `@st.cache_data` for expensive computations
- Implement pagination for lists >100 items
- Use bulk operations for database inserts
- Monitor slow queries with performance_monitor

---

## 📦 Deployment Structure

```
Production Deployment:
├── Streamlit Cloud (Frontend)
├── Neon Database (PostgreSQL)
├── Upstash Redis (Caching) - Optional
└── GitHub (Version Control)
```

---

## 🔐 Security

- **Secrets**: Store in `.env` (local) or Streamlit secrets (production)
- **Database**: Use environment variables, never hardcode
- **Passwords**: Hashed with bcrypt
- **API Keys**: Stored securely, never committed

---

*For detailed documentation, see the `/docs` folder*
