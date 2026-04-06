import pandas as pd
import sqlite3

# Simulación de la NUEVA lógica de app.py
def simulate_new_logic():
    db_path = 'anton.db'
    ruta_plan = r"C:\Cobra\OneDrive - COBRA PERU S.A\Extractor\HubLean\planobraCSV.xlsx"
    
    conn = sqlite3.connect(db_path)
    filtros_dict = {}
    for row in conn.execute("SELECT entidad, valor FROM filtros_maestros"):
        e, v = row[0].strip().upper(), row[1].strip().upper()
        if e not in filtros_dict: filtros_dict[e] = []
        filtros_dict[e].append(v)
    conn.close()

    itp_chiclayo = '24-4481573193'
    
    try:
        df = pd.read_excel(ruta_plan)
        row_data = df[df['ITEMPLAN'].astype(str).str.strip() == itp_chiclayo]
        if row_data.empty: return "Item non found"
        
        row = row_data.iloc[0]
        row_upper = {str(k).upper().strip(): str(v).strip().upper() for k, v in row.items() if v is not None}
        
        skip = False
        print(f"VERIFICANDO {itp_chiclayo} (NUEVA LOGICA):")
        for entidad, valores_permitidos in filtros_dict.items():
            val_fila = str(row_upper.get(entidad, "")).strip().upper()
            if val_fila and val_fila not in valores_permitidos:
                # LA NUEVA LOGICA
                if entidad == 'SUBESTADO TRUNCO':
                    estado_plan_val = str(row_upper.get('ESTADO PLAN', '')).strip().upper()
                    if estado_plan_val != 'TRUNCO':
                        print(f"  [FIXED] Ignorando filtro SUBESTADO TRUNCO porque ESTADO PLAN es '{estado_plan_val}'")
                        continue
                
                print(f"  [FAIL] {entidad}: '{val_fila}' no permitido.")
                skip = True
                break
        
        if not skip:
            print("RESULTADO: EL ITEM SERA IMPORTADO CORRECTAMENTE.")
        else:
            print("RESULTADO: EL ITEM SIGUE SIENDO DESCARTADO.")
            
    except Exception as e:
        print(f"Error: {e}")

simulate_new_logic()
