# PostgreSQL Migration TODO

## Completed
- [x] Updated Retailsights/db.py to use PostgreSQL with SQLAlchemy instead of MySQL
- [x] Updated Retailsights/create_admin.py to use SQLAlchemy ORM instead of raw SQL

## Remaining Tasks
- [ ] Update remaining service files to use SQLAlchemy sessions instead of get_connection (many files in services/ and repositories/)
- [ ] Test the app with PostgreSQL database
- [ ] Run migrations if needed (alembic is configured for DATABASE_URL)
- [ ] Create tables if not exist (use scripts/create_orm_tables.py)

## Notes
- The app.py health_check now uses PostgreSQL
- Repositories already use SQLAlchemy from db_orm.py
- DATABASE_URL should be set in .env for Neon PostgreSQL
