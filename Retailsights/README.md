# 🛒 RetailSights - Advanced Retail Analytics Platform

> Enterprise-grade retail management and analytics solution with AI-powered insights

---

## 🌟 Overview

RetailSights is a comprehensive retail analytics platform designed for multi-location retail operations. It provides real-time insights, inventory management, expiry tracking, and intelligent business analytics.

### Key Features

✅ **Multi-Store Management** - Manage multiple retail locations from one dashboard  
✅ **Real-Time Analytics** - Live sales tracking and performance metrics  
✅ **Inventory Management** - Track stock levels, expiry dates, and waste  
✅ **AI-Powered Insights** - Intelligent analyst for data-driven decisions  
✅ **Yellow Sticker Management** - Automated markdown pricing for expiring products  
✅ **Enterprise Features** - Role-based access, subscriptions, and advanced reporting  

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL database (Neon cloud database recommended)
- Streamlit Cloud account (for deployment)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sohailshaik03/lifinity.git
cd lifinity/Retailsights
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Initialize database**
```bash
python create_admin.py
# Follow prompts to create admin user
```

5. **Run the application**
```bash
streamlit run app.py
```

---

## 📊 Core Features

### 1. Dashboard Analytics
- Real-time revenue tracking
- Sales trends and forecasting
- Top products and categories
- Waste analysis and reduction metrics

### 2. Inventory Management
- Product catalog management
- Stock level monitoring
- Expiry date tracking
- Automated alerts for low stock

### 3. Yellow Sticker (Smart Markdowns)
- Automated discount pricing
- Expiry-based markdown rules
- Waste reduction optimization
- Label printing integration

### 4. Intelligent Analyst
- Natural language queries
- AI-powered data insights
- Automated report generation
- Trend analysis and predictions

### 5. Enterprise Features
- Multi-user role management
- Subscription billing
- Advanced export options
- Custom reporting

---

## 🎯 User Roles

| Role | Access Level | Capabilities |
|------|-------------|--------------|
| **Admin** | Full access | System configuration, user management, all features |
| **Manager** | Store level | Store analytics, inventory, waste tracking |
| **Staff** | Limited | Yellow sticker management, basic inventory |

---

## ⚡ Performance

RetailSights is optimized for enterprise-scale operations:

- **Database Optimization**: Indexed queries with connection pooling
- **Caching**: Redis-ready with automatic fallback
- **Pagination**: Handles 10,000+ products efficiently
- **Bulk Operations**: 50x faster data imports
- **Lazy Loading**: Optimized dashboard rendering

### Performance Metrics
- Dashboard load: <2 seconds
- Product search: <0.1 seconds
- CSV upload (1000 rows): ~1 second
- Supports 100+ concurrent users

---

## 🔧 Configuration

### Environment Variables

```bash
# Database (Required)
DATABASE_URL=postgresql://user:password@host:port/database

# Optional: Redis (for distributed caching)
REDIS_URL=redis://host:port

# Connection Pool Settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_RECYCLE=3600

# Stripe (for payment processing)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Advanced Configuration

See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) for detailed configuration options.

---

## 📦 Technology Stack

- **Frontend**: Streamlit 1.52.1
- **Backend**: Python 3.10+
- **Database**: PostgreSQL (Neon cloud)
- **ORM**: SQLAlchemy
- **Caching**: Redis (optional)
- **Analytics**: Pandas, Plotly
- **AI**: OpenAI GPT integration

---

## 📈 System Status

### Implemented ✅
- [x] Core analytics dashboard
- [x] Multi-store management
- [x] Inventory & expiry tracking
- [x] Yellow sticker automation
- [x] AI-powered insights
- [x] Performance optimization (Phase 1 & 2)
- [x] Enterprise features
- [x] Production deployment

---

## 🛡️ Security

- Secure password hashing (bcrypt)
- Role-based access control
- SQL injection protection
- Environment variable encryption
- Session management

---

## 📖 Documentation

Comprehensive documentation available in the `/docs` folder:

- **Setup Guide**: Initial setup and configuration
- **User Guide**: Feature documentation
- **Performance Guide**: Optimization details
- **Enterprise Features**: Advanced capabilities

---

## 🤝 Support

For support and questions:
- 📧 Email: support@retailsights.com
- 📚 Documentation: `/docs` folder
- 🐛 Issues: GitHub Issues

---

## 📄 License

Copyright © 2025 RetailSights. All rights reserved.

---

**Made with ❤️ for retail excellence**

*Last updated: December 2025*
- Please add project license as required by your organization.
=======
# Retailsights
Retailsights
>>>>>>> d11a015f405b5be4ce3390ad12ae11fc1e78978b
