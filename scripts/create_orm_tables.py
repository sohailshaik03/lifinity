"""Create DB tables from SQLAlchemy models. Uses DATABASE_URL or falls back to sqlite file."""
import os
from Retailsights.db_orm import create_all_tables
from Retailsights.models import Base


def main():
    print("Creating ORM tables using DATABASE_URL or sqlite fallback...")
    create_all_tables(Base)
    print("Done.")


if __name__ == '__main__':
    main()
