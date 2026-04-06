import sqlite3

db_path = 'anton.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("ESTADO PLAN filters in DB:")
for r in c.execute("SELECT valor FROM filtros_maestros WHERE entidad = 'ESTADO PLAN'"):
    val = r[0]
    print(f"  '{val}' | bytes: {val.encode('utf-8')}")

print("\nSUBPROYECTO filters with 'Diseño' in name:")
for r in c.execute("SELECT valor FROM filtros_maestros WHERE valor LIKE '%Dise%'"):
    val = r[0]
    print(f"  '{val}' | bytes: {val.encode('utf-8')}")

conn.close()
