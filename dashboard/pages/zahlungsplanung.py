import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Fix module imports
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import load_sap_files
from dashboard.auth import check_permission

st.title("Zahlungsplanung & Freigabe")

st.markdown("""
Übersicht der vorgeschlagenen Zahlungen basierend auf Prioritäten und dem zweistufigen Freigabeprozess.
""")

if "payment_status_db" not in st.session_state:
    st.session_state.payment_status_db = {}
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

def update_status(doc_id, new_status, amount):
    st.session_state.payment_status_db[doc_id] = new_status
    user = st.session_state.user['name']
    st.session_state.audit_log.append({
        "Benutzer": user,
        "Rolle": st.session_state.role,
        "Aktion": new_status,
        "Dokument": doc_id,
        "Betrag": amount,
        "Zeitpunkt": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    })

data_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'input'
data = load_sap_files(str(data_dir))
opos = data.get('opos_kreditoren')

selected_ges = st.session_state.get("selected_gesellschaft", "Beide")
if selected_ges != "Beide" and opos is not None and not opos.empty and 'Gesellschaft' in opos.columns:
    opos = opos[opos['Gesellschaft'].str.upper() == selected_ges.upper()]
if opos is None or opos.empty:
    st.warning("Keine Daten gefunden. Bitte stellen Sie sicher, dass die Dummy-Dateien geladen wurden.")
    st.stop()

# Get live status from session state fake-DB
def get_current_status(row):
    return st.session_state.payment_status_db.get(row['Dokumentennummer'], "ausstehend")

opos['Aktueller_Status'] = opos.apply(get_current_status, axis=1)

role = st.session_state.role
st.warning(f"Aktuelle Freigabe-Ansicht für deine Rolle: **{role.upper()}**")

# ==========================================
# 1. VORBEREITER VIEW
# ==========================================
if role in ["vorbereiter", "admin"]:
    st.subheader("1. Aufgabe: Zahlungen vorbereiten (Vorbereiter)")
    ausstehend = opos[opos['Aktueller_Status'] == 'ausstehend'].sort_values('Fälligkeit').head(10)
    
    if ausstehend.empty:
        st.info("Keine anstehenden Posten zur Vorbereitung.")
    else:
        st.write("Bitte wähle die Posten aus, die der Geschäftsleitung vorgeschlagen werden sollen:")
        for idx, row in ausstehend.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            col1.write(f"**{row['Kreditor-ID']}** | {row['Dokumentennummer']}")
            
            # Format datetime safely
            faell_str = row['Fälligkeit'].strftime('%d.%m.%y') if pd.notnull(row['Fälligkeit']) else '?'
            col2.write(f"**{row['Betrag']:,.2f} €** (Fällig: {faell_str})")
            
            col3.write(row['Kategorie'])
            if col4.button("Vorbereiten", key=f"vor_{idx}"):
                update_status(row['Dokumentennummer'], "vorbereitet", row['Betrag'])
                st.rerun()

st.markdown("---")

# ==========================================
# 2. GESCHÄFTSLEITUNG VIEW
# ==========================================
if role in ["geschaeftsleitung", "admin"]:
    st.subheader("2. Aufgabe: Zahlungen freigeben (Geschäftsleitung)")
    vorbereitet = opos[opos['Aktueller_Status'] == 'vorbereitet'].sort_values('Fälligkeit')
    
    if vorbereitet.empty:
        st.info("Actuell keine Zahlungen durch den Vorbereiter eingereicht.")
    else:
        st.write("Diese Posten wurden vorbereitet und warten auf Ihre **finale Freigabe**:")
        for idx, row in vorbereitet.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
            col1.write(f"**{row['Kreditor-ID']}** | {row['Dokumentennummer']}")
            col2.write(f"**{row['Betrag']:,.2f} €**")
            col3.write(row['Kategorie'])
            if col4.button("Freigeben", key=f"frei_{idx}"):
                update_status(row['Dokumentennummer'], "freigegeben", row['Betrag'])
                st.rerun()
            if col5.button("Ablehnen", key=f"abl_{idx}"):
                update_status(row['Dokumentennummer'], "ausstehend", row['Betrag'])
                st.rerun()

st.markdown("---")

# ==========================================
# 3. FiBu VIEW
# ==========================================
if role in ["fibu", "admin"]:
    st.subheader("3. Aufgabe: Zahlungen ausführen (FiBu)")
    freigegeben = opos[opos['Aktueller_Status'] == 'freigegeben']
    
    if freigegeben.empty:
        st.info("Keine neu freigegebenen Zahlungen.")
    else:
        st.write("Diese Posten wurden von der Geschäftsleitung freigegeben. Bitte nach Bank-Überweisung als bezahlt markieren:")
        for idx, row in freigegeben.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            col1.write(f"**{row['Kreditor-ID']}** | {row['Dokumentennummer']}")
            col2.write(f"**{row['Betrag']:,.2f} €**")
            col3.write(row['Kategorie'])
            if col4.button("Auszahlen", key=f"ausg_{idx}"):
                update_status(row['Dokumentennummer'], "ausgezahlt", row['Betrag'])
                st.rerun()

st.markdown("---")

# Log summary for current users
with st.expander("Aktueller Status der Datenbank"):
    st.write(st.session_state.payment_status_db)
