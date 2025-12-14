Migrations
=========

This folder contains guidance and SQL stubs for applying schema changes.

Recommended approach for production:

1. Use Alembic (or your chosen migration tool) to manage schema changes.
2. Never modify the live enum types in MySQL without a backup.
3. When changing enum values, prefer creating a new column, backfilling data, then swapping columns in a transactional safe way where possible.

Quick local migration (example SQL):

```sql
-- migrations/versions/0001_add_manager_role.sql
-- Back up the table first:
-- SHOW CREATE TABLE users; > users_table_backup.sql

ALTER TABLE users MODIFY COLUMN role ENUM('owner','staff','admin','manager') NOT NULL DEFAULT 'owner';
```

For a robust workflow, initialize alembic in this repo and generate SQL-based migrations.
