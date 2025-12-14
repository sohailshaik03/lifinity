"""Helper to run a SQL migration file against the configured DB.

Usage:
  python3 scripts/run_migration.py migrations/versions/0001_add_manager_role.sql

This script reads DB credentials from environment variables (see `.env.example`).
It will prompt before executing SQL unless `--yes` is passed.
"""

import os
import sys
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv


def load_env():
    p = Path(__file__).parents[1] / ".env"
    if p.exists():
        load_dotenv(str(p))


def run_sql_file(path, yes=False):
    load_env()
    DB_HOST = os.environ.get("DB_HOST")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_USER = os.environ.get("DB_USER")
    # Support both DB_PASS and DB_PASSWORD env var names
    DB_PASS = os.environ.get("DB_PASS") or os.environ.get("DB_PASSWORD")
    DB_NAME = os.environ.get("DB_NAME")

    if not (DB_HOST and DB_USER and DB_NAME):
        print("Missing DB configuration in environment. Aborting.")
        print("Please set DB_HOST, DB_USER, DB_NAME and DB_PASS (or DB_PASSWORD) in your .env or environment.")
        return 2

    sql = Path(path).read_text()
    print("SQL to run:\n", sql)
    if not yes:
        confirm = input("Proceed to execute SQL against the configured DB? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted by user.")
            return 1

    cnx = mysql.connector.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, database=DB_NAME
    )
    try:
        cur = cnx.cursor()
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            print("Executing:", stmt[:200])
            cur.execute(stmt)
        cnx.commit()
        print("Migration finished.")
    finally:
        cnx.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_migration.py <sql-file> [--yes]")
        sys.exit(2)
    path = sys.argv[1]
    yes = "--yes" in sys.argv
    sys.exit(run_sql_file(path, yes=yes) or 0)
