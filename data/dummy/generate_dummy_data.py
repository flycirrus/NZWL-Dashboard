import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_dummy_data():
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
    os.makedirs(input_dir, exist_ok=True)
    
    np.random.seed(42)
    today = datetime.now()
    
    # 1. Kreditor Stammdaten
    kreditoren = pd.DataFrame({
        'Kreditor-ID': [f'K{str(1000+i)}' for i in range(15)],
        'Name': ['Lieferant ' + chr(65+i) for i in range(15)],
        'Zahlungsziel': [np.random.choice(['14T 2% 30T netto', '30 Tage netto', '60 Tage netto']) for _ in range(15)],
        'Gesellschaft': [np.random.choice(['NZWL', 'ZWL_SK']) for _ in range(15)]
    })
    kreditoren.to_excel(os.path.join(input_dir, 'SAP_Stammdaten_Kreditoren.xlsx'), index=False)
    
    # 2. Offene Posten Kreditoren
    num_opos = 50
    kred_ids = np.random.choice(kreditoren['Kreditor-ID'], num_opos)
    faelligkeiten = [today + timedelta(days=np.random.randint(-10, 45)) for _ in range(num_opos)]
    betraege = np.random.uniform(500, 25000, num_opos).round(2)
    
    opos = pd.DataFrame({
        'Kreditor-ID': kred_ids,
        'Dokumentennummer': [f'INV-{str(20000+i)}' for i in range(num_opos)],
        'Betrag': betraege,
        'Fälligkeit': faelligkeiten,
        'Skontoziel': [f - timedelta(days=14) for f in faelligkeiten],
        'Kategorie': [np.random.choice(['Ersatzteile', 'Hilfsmaterial', 'Speditionen', 'Energie', 'Reparatur']) for _ in range(num_opos)],
        'Status': [np.random.choice(['ausstehend', 'freigegeben'], p=[0.8, 0.2]) for _ in range(num_opos)]
    })
    opos.to_excel(os.path.join(input_dir, 'SAP_OPOS_Vertrieb.xlsx'), index=False)
    
    # 3. Offene Posten Debitoren (Expected incoming)
    num_deb = 30
    deb_opos = pd.DataFrame({
        'Debitor-ID': [f'D{str(5000+i)}' for i in range(num_deb)],
        'Betrag': np.random.uniform(1000, 50000, num_deb).round(2),
        'Fälligkeit': [today + timedelta(days=np.random.randint(0, 30)) for _ in range(num_deb)],
        'Gesellschaft': [np.random.choice(['NZWL', 'ZWL_SK']) for _ in range(num_deb)]
    })
    deb_opos.to_excel(os.path.join(input_dir, 'SAP_offen_Posten_Debitoren.xlsx'), index=False)
    
    print("Dummy Excel files successfully generated in /data/input/")

if __name__ == "__main__":
    generate_dummy_data()
