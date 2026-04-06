import pandas as pd
import sqlite3

# Simulación de la lógica de app.py sobre los nuevos ITEMPLANs
def check_new_image_items():
    db_path = 'anton.db'
    ruta_plan = r"C:\Cobra\OneDrive - COBRA PERU S.A\Extractor\HubLean\planobraCSV.xlsx"
    
    conn = sqlite3.connect(db_path)
    filtros_dict = {}
    for row in conn.execute("SELECT entidad, valor FROM filtros_maestros"):
        e, v = row[0].strip().upper(), row[1].strip().upper()
        if e not in filtros_dict: filtros_dict[e] = []
        filtros_dict[e].append(v)
    conn.close()

    # Algunos items de la 2da imagen
    sample_itps = [
        '24-4140067600', # CAJAMARCA, FTTH TRANSPORTE -STC
        '26-1035446765', # CHICLAYO, PEXT SITIOS NUEVOS 2026 PROV 2Q
        '26-2922214362', # CHICLAYO, DAÑO CONOCIDO FON O&M
        '25-5118818514', # LIMA, APAGADO DE LOCAL - CT MAGDALENA
        '26-9123512144', # PIURA, PROYECTOS TRUNCOS PEX -STC 2026
        '26-7391145919'  # TUMBES, DAÑO CONOCIDO INTERCONEXIONES O&M
    ]
    
    try:
        df = pd.read_excel(ruta_plan)
        
        for itp_target in sample_itps:
            row_data = df[df['ITEMPLAN'].astype(str).str.strip() == itp_target]
            if row_data.empty:
                print(f"\nITEMPLAN {itp_target} NOT FOUND in Excel source.")
                continue
                
            row = row_data.iloc[0]
            row_upper = {str(k).upper().strip(): str(v).strip().upper() for k, v in row.items() if v is not None}
            
            print(f"\nANALISIS PARA {itp_target}:")
            for entidad, valores_permitidos in filtros_dict.items():
                val_fila = str(row_upper.get(entidad, "")).strip().upper()
                if val_fila:
                    if val_fila not in valores_permitidos:
                        # Aplicar la excepción de la lógica nueva para SUBESTADO TRUNCO
                        if entidad == 'SUBESTADO TRUNCO':
                            estado_plan_val = str(row_upper.get('ESTADO PLAN', '')).strip().upper()
                            if estado_plan_val != 'TRUNCO':
                                continue
                        
                        print(f"  FAILED {entidad}: '{val_fila}' NO está en Filtros Maestros.")
                    else:
                        pass # print(f"  Passed {entidad}: '{val_fila}'")
                
    except Exception as e:
        print(f"Error: {e}")

check_new_image_items()
