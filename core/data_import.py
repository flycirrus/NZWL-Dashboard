"""
SAP Data Import and Consolidation Module.

This module handles the manual loading of SAP export Excel files from the `/data/input/` directory.
It does not connect directly to SAP or any external API.
"""
import os
import pandas as pd
import streamlit as st

@st.cache(allow_output_mutation=True)
def load_sap_files(path: str) -> dict:
    """
    Imports all SAP export files from the specified path and returns a dictionary of DataFrames.
    Uses st.cache to prevent reloading the Excel files on every UI interaction.
    """
    data = {}
    files = {
        'kreditoren': 'SAP_Stammdaten_Kreditoren.xlsx',
        'opos_kreditoren': 'SAP_OPOS_Vertrieb.xlsx',
        'opos_debitoren': 'SAP_offen_Posten_Debitoren.xlsx'
    }
    
    for key, filename in files.items():
        filepath = os.path.join(path, filename)
        if os.path.exists(filepath):
            try:
                data[key] = pd.read_excel(filepath)
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                data[key] = pd.DataFrame()
        else:
            data[key] = pd.DataFrame()
            
    return data
