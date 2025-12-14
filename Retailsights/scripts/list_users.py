from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv('Retailsights/.env')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD') or os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

print('Connecting to', DB_HOST, DB_NAME, 'as', DB_USER)
cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
cur = cnx.cursor(dictionary=True)
cur.execute("SELECT id, email, full_name, role, is_active, created_at FROM users ORDER BY id DESC LIMIT 50")
rows = cur.fetchall()
if not rows:
    print('No users found')
else:
    for r in rows:
        print(r)
cur.close()
cnx.close()
