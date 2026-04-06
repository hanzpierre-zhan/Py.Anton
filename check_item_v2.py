import sqlite3

db_path = 'anton.db'
itemplan = '24-1424875100'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT count(*) FROM gestion_obras WHERE data_json LIKE ?", (f'%{itemplan}%',))
count = cursor.fetchone()[0]
print(f"ITEMPLAN {itemplan} count in DB: {count}")
conn.close()
