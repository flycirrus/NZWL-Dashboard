import streamlit as st
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import load_sap_files

st.title("Liquidität")

data_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'input'
data = load_sap_files(str(data_dir))
debitoren = data.get('opos_debitoren')
kreditoren_opos = data.get('opos_kreditoren')

col1, col2 = st.columns(2)

with col1:
    st.subheader("Liquiditäts-Zufluss (Debitoren)")
    if debitoren is not None and not debitoren.empty:
        st.dataframe(debitoren, use_container_width=True)
        
with col2:
    st.subheader("Liquiditäts-Abfluss (Kreditoren)")
    if kreditoren_opos is not None and not kreditoren_opos.empty:
        st.dataframe(kreditoren_opos[['Kreditor-ID', 'Betrag', 'Fälligkeit', 'Kategorie']], use_container_width=True)

st.markdown("---")

st.subheader("Liquiditäts-Trend (Schätzung)")
if debitoren is not None and not debitoren.empty and kreditoren_opos is not None and not kreditoren_opos.empty:
    # Dummy trend aggregation
    debitoren['Typ'] = 'Einzahlung'
    kreditoren_opos['Typ'] = 'Auszahlung'
    
    # Merge and sum by date for the chart
    trend_data = pd.concat([
        debitoren[['Fälligkeit', 'Betrag', 'Typ']],
        kreditoren_opos[['Fälligkeit', 'Betrag', 'Typ']]
    ])
    st.bar_chart(trend_data, x="Fälligkeit", y="Betrag", color="Typ", use_container_width=True)
else:
    st.info("Zu wenige Daten für den Trend Chart.")
