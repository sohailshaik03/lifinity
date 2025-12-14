# config.py
import os
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.getenv("ENV", "development")

    # Support DATABASE_URL or individual DB vars
    DATABASE_URL = os.getenv("DATABASE_URL")
    if DATABASE_URL:
        parsed = urlparse(DATABASE_URL)
        DB_HOST = parsed.hostname or "localhost"
        DB_USER = parsed.username or "root"
        DB_PASSWORD = parsed.password or ""
        DB_NAME = parsed.path.lstrip("/") or "retailsight"
    else:
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_USER = os.getenv("DB_USER", "root")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "Shybash630shaik@")
        DB_NAME = os.getenv("DB_NAME", "lifinity")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


config = Config()
# Debug: Print loaded DB credentials at startup
print("[DEBUG] DB_HOST:", config.DB_HOST)
print("[DEBUG] DB_USER:", config.DB_USER)
print("[DEBUG] DB_PASSWORD:", repr(config.DB_PASSWORD))
print("[DEBUG] DB_NAME:", config.DB_NAME)
