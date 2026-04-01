import streamlit as st
import sys
from pathlib import Path

# Add core path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import load_sap_files

st.title("Offene Posten (Kreditoren)")

data_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'input'
data = load_sap_files(str(data_dir))
opos = data.get('opos_kreditoren')

selected_ges = st.session_state.get("selected_gesellschaft", "Beide")
if selected_ges != "Beide" and opos is not None and not opos.empty and 'Gesellschaft' in opos.columns:
    opos = opos[opos['Gesellschaft'].str.upper() == selected_ges.upper()]
if opos is not None and not opos.empty:
    # Let users filter by status if they want
    st.subheader("Filter")
    
    col1, col2 = st.columns(2)
    with col1:
        kat_filter = st.multiselect("Kategorie filtern:", list(opos['Kategorie'].unique()))
    with col2:
        status_filter = st.multiselect("Status filtern:", list(opos['Status'].unique()))
    
    filtered_opos = opos.copy()
    if kat_filter:
        filtered_opos = filtered_opos[filtered_opos['Kategorie'].isin(kat_filter)]
    if status_filter:
        filtered_opos = filtered_opos[filtered_opos['Status'].isin(status_filter)]
        
    st.dataframe(filtered_opos)
else:
    st.warning("Keine Daten geladen.")
