import pandas as pd
import sqlite3

ruta_plan = r"C:\Cobra\OneDrive - COBRA PERU S.A\Extractor\HubLean\planobraCSV.xlsx"
db_path = 'anton.db'

def get_db_filters():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    filters = {}
    for row in c.execute("SELECT entidad, valor FROM filtros_maestros"):
        ent, val = row[0].upper(), row[1].upper()
        if ent not in filters: filters[ent] = set()
        filters[ent].add(val)
    conn.close()
    return filters

try:
    df = pd.read_excel(ruta_plan)
    db_filters = get_db_filters()
    
    entities = ['JEFATURA', 'SUBPROYECTO', 'ESTADO PLAN']
    
    for ent in entities:
        if ent in df.columns:
            excel_values = set(df[ent].dropna().astype(str).str.strip().unique())
            excel_values_upper = {v.upper() for v in excel_values}
            db_vals = db_filters.get(ent.upper(), set())
            
            missing = sorted([v for v in excel_values if v.upper() not in db_vals])
            
            print(f"\nMISSING for {ent}:")
            if missing:
                for m in missing:
                    print(f"  - {m}")
            else:
                print("  (None)")
        else:
            print(f"\nCOLUMN {ent} NOT FOUND in Excel")
            
except Exception as e:
    print(f"Error: {e}")
