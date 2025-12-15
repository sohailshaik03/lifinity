from dotenv import load_dotenv
import os
import mysql.connector
import sys
import os
# Ensure project package path is on sys.path for local imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Retailsights.utils.security import hash_password

# Load .env
load_dotenv('Retailsights/.env')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD') or os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL') or 'admin@retailsight.local'
ADMIN_FULL_NAME = os.getenv('ADMIN_FULL_NAME') or 'RetailSight Admin'
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') or 'AdminPass123!'

if not (DB_HOST and DB_USER and DB_NAME):
    print('Missing DB config in environment. Set DB_HOST, DB_USER, DB_NAME, DB_PASSWORD')
    raise SystemExit(1)

print('Connecting to DB', DB_HOST, DB_NAME, 'as', DB_USER)
cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
cur = cnx.cursor()

# Check if user exists
cur.execute('SELECT id FROM users WHERE email = %s', (ADMIN_EMAIL,))
row = cur.fetchone()
if row:
    print('Admin already exists with id', row[0])
else:
    pw_hash = hash_password(ADMIN_PASSWORD)
    cur.execute(
        "INSERT INTO users (email, password_hash, full_name, role, is_active) VALUES (%s,%s,%s,'admin',1)",
        (ADMIN_EMAIL, pw_hash, ADMIN_FULL_NAME),
    )
    cnx.commit()
    print('Created admin', ADMIN_EMAIL, 'id', cur.lastrowid)

cur.close()
cnx.close()
