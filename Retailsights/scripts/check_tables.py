from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv('../.env')
DB_HOST=os.getenv('DB_HOST')
DB_USER=os.getenv('DB_USER')
DB_PASS=os.getenv('DB_PASSWORD') or os.getenv('DB_PASS')
DB_NAME=os.getenv('DB_NAME')

print('Connecting to', DB_HOST, DB_NAME, 'as', DB_USER)
try:
    cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
    cur = cnx.cursor()
    cur.execute("SHOW TABLES LIKE 'users'")
    users = cur.fetchall()
    print('users table found:', users)
    cur.execute('SHOW TABLES')
    print('tables count:', len(cur.fetchall()))
    cur.close()
    cnx.close()
except Exception as e:
    print('ERROR:', e)
