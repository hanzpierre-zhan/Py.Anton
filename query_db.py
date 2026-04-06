import sqlite3
import os

db_path = 'anton.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} no existe.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Count by entity
    cursor.execute("SELECT entidad, count(*) FROM filtros_maestros GROUP BY entidad")
    print("RESUMEN DE FILTROS:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} filtros")
        
    # 2. Check for PROYECTO values specifically
    cursor.execute("SELECT valor FROM filtros_maestros WHERE entidad = 'PROYECTO'")
    proyectos = cursor.fetchall()
    if proyectos:
        print("\nVALORES DE PROYECTO:")
        for p in proyectos:
            print(f"  - {p[0]}")
    else:
        print("\nNo hay filtros de tipo 'PROYECTO'.")
        
    conn.close()
