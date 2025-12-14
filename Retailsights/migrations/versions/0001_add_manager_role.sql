-- 0001_add_manager_role.sql
-- Safe migration to add 'manager' value to users.role enum
-- IMPORTANT: Run backups before applying.

-- Backup the current table definition (run this separately and save output):
-- SHOW CREATE TABLE users;

-- The safe, in-place ALTER (simple approach):
ALTER TABLE users
  MODIFY COLUMN role ENUM('owner','staff','admin','manager') NOT NULL DEFAULT 'owner';

-- Note: For production systems prefer creating a new column, backfilling and swapping to avoid enum issues.
