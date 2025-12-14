import os
import sys
from sqlalchemy import create_engine, text

url = os.environ.get("DATABASE_URL") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not url:
    print("No DATABASE_URL provided. Pass it via env or as first arg.")
    sys.exit(2)

print("Using DATABASE_URL:", url[:80] + ("..." if len(url) > 80 else ""))

try:
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        one = conn.execute(text("SELECT 1")).scalar()
        version = conn.execute(text("SELECT version()")).scalar()
        print("SELECT 1 ->", one)
        print("Postgres version:", version)
    engine.dispose()
    print("Connection test: SUCCESS")
    sys.exit(0)
except Exception as e:
    print("Connection test: FAILED")
    print(str(e))
    sys.exit(1)
