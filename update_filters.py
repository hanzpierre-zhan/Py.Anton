import sqlite3

db_path = 'anton.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

to_add = [
    ('SUBPROYECTO', 'FTTH TRANSPORTE -STC'),
    ('SUBPROYECTO', 'PEXT SITIOS NUEVOS 2026 PROV 2Q'),
    ('SUBPROYECTO', 'PEXT SITIOS NUEVOS 2026 LIMA 2Q'),
    ('SUBPROYECTO', 'PROYECTOS TRUNCOS PEX -STC 2026'),
    ('SUBPROYECTO', 'MIGRACION RADIO - FO MIMO - 25 -STC'),
    ('SUBPROYECTO', 'DAÑO CONOCIDO FON O&M'),
    ('SUBPROYECTO', 'DAÑO CONOCIDO INTERCONEXIONES O&M'),
    ('SUBPROYECTO', 'APAGADO DE LOCAL - CT MAGDALENA'),
    ('JEFATURA', 'CAJAMARCA')
]

for entidad, valor in to_add:
    # Check if already exists
    cursor.execute("SELECT count(*) FROM filtros_maestros WHERE entidad = ? AND valor = ?", (entidad, valor))
    if cursor.fetchone()[0] == 0:
        print(f"Añadiendo {entidad}: '{valor}'")
        cursor.execute("INSERT INTO filtros_maestros (entidad, valor) VALUES (?, ?)", (entidad, valor))
    else:
        print(f"Skipping {entidad}: '{valor}' (Already exists)")

conn.commit()
conn.close()
print("\nFiltros actualizados exitosamente.")
