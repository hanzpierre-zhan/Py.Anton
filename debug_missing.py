import pandas as pd

ruta_plan = r"C:\Cobra\OneDrive - COBRA PERU S.A\Extractor\HubLean\planobraCSV.xlsx"
itemplans = ['26-8442134732', '24-1424875100', '26-9728115765']

try:
    df = pd.read_excel(ruta_plan)
    # Check JEFATURA column
    jefatura_col = 'JEFATURA' if 'JEFATURA' in df.columns else None
    
    for itp in itemplans:
        row = df[df['ITEMPLAN'].astype(str).str.strip() == itp]
        if not row.empty:
            print(f"DEBUG for {itp}:")
            print(f"  PROYECTO: {row.iloc[0].get('PROYECTO')}")
            print(f"  SUBPROYECTO: '{row.iloc[0].get('SUBPROYECTO')}'")
            print(f"  ESTADO PLAN: '{row.iloc[0].get('ESTADO PLAN')}'")
            if jefatura_col:
                print(f"  JEFATURA: '{row.iloc[0].get(jefatura_col)}'")
            else:
                print("  JEFATURA: NO COLUMN FOUND")
        else:
            print(f"ITEMPLAN {itp} NOT FOUND in planobraCSV.xlsx")
            
except Exception as e:
    print(f"Error: {e}")
