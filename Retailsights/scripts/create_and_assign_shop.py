from dotenv import load_dotenv
import os
import mysql.connector

# Load project .env
load_dotenv('Retailsights/.env')
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD') or os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME')

# Configuration for new shop
SHOP_NAME = os.getenv('NEW_SHOP_NAME') or 'Demo Store'
ADDRESS_LINE1 = os.getenv('NEW_SHOP_ADDR') or '1 Demo Street'
CITY = os.getenv('NEW_SHOP_CITY') or 'Demo City'
POSTCODE = os.getenv('NEW_SHOP_POSTCODE') or '00000'
COUNTRY = os.getenv('NEW_SHOP_COUNTRY') or 'UK'
USER_ID = int(os.getenv('TARGET_USER_ID') or 1)

print('Connecting to DB', DB_HOST, DB_NAME, 'as', DB_USER)
cnx = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
cur = cnx.cursor()

# Ensure user_shops table exists
cur.execute('''
CREATE TABLE IF NOT EXISTS user_shops (
    user_id INT UNSIGNED NOT NULL,
    shop_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (user_id, shop_id),
    INDEX idx_user_id (user_id),
    INDEX idx_shop_id (shop_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
''')
cnx.commit()

import json

# Create shop (match current `shops` schema: name, owner_user_id, address JSON)
print('Creating shop:', SHOP_NAME)
address_obj = {"line1": ADDRESS_LINE1, "city": CITY, "postcode": POSTCODE, "country": COUNTRY}
cur.execute(
    "INSERT INTO shops (name, owner_user_id, address, is_active) VALUES (%s,%s,%s,%s)",
    (SHOP_NAME, USER_ID, json.dumps(address_obj), 1),
)
cnx.commit()
shop_id = cur.lastrowid
print('Created shop id:', shop_id)

# Assign user to shop
print(f'Assigning user {USER_ID} to shop {shop_id}')
cur.execute(
    "INSERT INTO user_shops (user_id, shop_id) VALUES (%s,%s) ON DUPLICATE KEY UPDATE user_id = user_id",
    (USER_ID, shop_id),
)
cnx.commit()

# Verify
cur.execute(
    "SELECT s.id, s.name FROM shops s JOIN user_shops us ON us.shop_id = s.id WHERE us.user_id = %s",
    (USER_ID,),
)
rows = cur.fetchall()
print('Shops for user', USER_ID, ':', rows)

cur.close()
cnx.close()
print('Done')
