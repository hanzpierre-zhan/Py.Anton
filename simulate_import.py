import pandas as pd
import sqlite3
import os

db_path = 'anton.db'
ruta_plan = r"C:\Cobra\OneDrive - COBRA PERU S.A\Extractor\HubLean\planobraCSV.xlsx"

# 1. Load filters as app.py does
conn = sqlite3.connect(db_path)
filtros_dict = {}
# app.py rows 541-544
for row in conn.execute("SELECT entidad, valor FROM filtros_maestros"):
    e, v = row[0].strip().upper(), row[1].strip().upper()
    if e not in filtros_dict: filtros_dict[e] = []
    filtros_dict[e].append(v)
conn.close()

# 2. Sample items from the user's image
# 24-4481573193 (CHICLAYO, MTC, Diseño Ejecutado)
# 24-1488234004 (LIMA, EMAPE, Diseño Ejecutado)
# 24-1424875100 (TRUJILLO, CONSORCIOS PRIVADOS, Diseño Ejecutado)
sample_itps = ['24-4481573193', '24-1488234004', '24-1424875100']

try:
    df = pd.read_excel(ruta_plan)
    
    for itp_target in sample_itps:
        row_data = df[df['ITEMPLAN'].astype(str).str.strip() == itp_target]
        if row_data.empty:
            print(f"\nITEMPLAN {itp_target} NOT FOUND in Excel source.")
            continue
            
        row = row_data.iloc[0]
        # Normalize row as app.py does (UPPER headers, UPPER values)
        row_upper = {str(k).upper().strip(): str(v).strip().upper() for k, v in row.items() if v is not None}
        
        print(f"\nDEBUGGING FILTERS FOR {itp_target}:")
        passed_all = True
        for entidad, valores_permitidos in filtros_dict.items():
            # app.py row 625
            val_fila = str(row_upper.get(entidad, "")).strip().upper()
            
            if val_fila:
                if val_fila in valores_permitidos:
                    print(f"  [PASS] {entidad}: '{val_fila}' is in filters.")
                else:
                    print(f"  [FAIL] {entidad}: '{val_fila}' is NOT in filters!")
                    # Check for hidden characters or slight mismatches
                    print(f"      - Hex val_fila: {val_fila.encode('utf-8').hex()}")
                    if valores_permitidos:
                        # Find closest match
                        import difflib
                        closest = difflib.get_close_matches(val_fila, valores_permitidos, n=1)
                        if closest:
                            print(f"      - Closest filter: '{closest[0]}' (Hex: {closest[0].encode('utf-8').hex()})")
                    passed_all = False
            else:
                print(f"  [SKIP] {entidad}: Column empty or missing in row.")
        
        if passed_all:
            print(f"CONCLUSION: {itp_target} SHOULD PASS the filters.")
        else:
            print(f"CONCLUSION: {itp_target} WILL BE DISCARDED.")

except Exception as e:
    print(f"Error: {e}")
