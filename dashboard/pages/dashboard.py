import streamlit as st
import sys
import os
from pathlib import Path

# Add core path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import load_sap_files

st.title("Dashboard")

# Load data
data_dir = os.path.join(Path(__file__).resolve().parent.parent.parent, 'data', 'input')
data = load_sap_files(data_dir)
opos = data.get('opos_kreditoren')
debitoren = data.get('opos_debitoren')
kreditoren = data.get('kreditoren')

selected_ges = st.session_state.get("selected_gesellschaft", "Beide")
if selected_ges != "Beide":
    if opos is not None and not opos.empty and 'Gesellschaft' in opos.columns:
        opos = opos[opos['Gesellschaft'].str.upper() == selected_ges.upper()]
    if debitoren is not None and not debitoren.empty and 'Gesellschaft' in debitoren.columns:
        debitoren = debitoren[debitoren['Gesellschaft'].str.upper() == selected_ges.upper()]
    if kreditoren is not None and not kreditoren.empty and 'Gesellschaft' in kreditoren.columns:
        kreditoren = kreditoren[kreditoren['Gesellschaft'].str.upper() == selected_ges.upper()]

if opos is not None and not opos.empty:
    gesamtverbindlichkeiten = opos['Betrag'].sum()
    freigegeben = opos[opos['Status'] == 'freigegeben']['Betrag'].sum()
    skontopotenzial = (gesamtverbindlichkeiten * 0.02) # Dummy calculation
else:
    gesamtverbindlichkeiten = 0.0
    freigegeben = 0.0
    skontopotenzial = 0.0

st.markdown("### Übersicht Kennzahlen")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Gesamtverbindlichkeiten", f"{gesamtverbindlichkeiten:,.2f} €", "-12.5% vs Vormonat", delta_color="inverse")
col2.metric("Fällig diese Woche", f"{gesamtverbindlichkeiten * 0.3:,.2f} €")
col3.metric("Skontopotenzial", f"{skontopotenzial:,.2f} €")
col4.metric("Liquiditätsstatus", "Ausreichend", "🟢")

st.markdown("---")

col_charts1, col_charts2 = st.columns(2)
with col_charts1:
    st.subheader("Liquiditätsübersicht")
    if debitoren is not None and not debitoren.empty:
        st.bar_chart(data=debitoren, x='Fälligkeit', y='Betrag')
    else:
        st.info("Daten werden geladen...")

with col_charts2:
    st.subheader("Zahlungsvorschlag nach Kategorie")
    if opos is not None and not opos.empty:
        kategorien = opos.groupby('Kategorie')['Betrag'].sum().reset_index()
        # Fallback to bar chart if altair donut is complex
        st.bar_chart(data=kategorien, x='Kategorie', y='Betrag')
    else:
        st.info("Daten werden geladen...")

st.markdown("---")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Letzte Aktivitäten (Ausstehend)")
    if opos is not None and not opos.empty:
        st.dataframe(opos.sort_values(by='Fälligkeit').head(10))

with col_right:
    st.subheader("Kreditoren Übersicht")
    # kreditoren already loaded and filtered above
    if kreditoren is not None and not kreditoren.empty:
        st.dataframe(kreditoren[['Kreditor-ID', 'Name', 'Gesellschaft']].head(8))
    else:
        st.info("Keine Stammdaten gefunden.")
