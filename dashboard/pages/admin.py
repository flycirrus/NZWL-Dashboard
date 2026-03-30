import streamlit as st
import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from dashboard.auth import check_permission, MOCK_USERS

if not check_permission(["admin"]):
    st.error("Zugriff verweigert. Nur Administratoren dürfen diese Seite sehen.")
    st.stop()

st.title("Nutzerverwaltung (Admin)")

st.markdown("""
Hier können neue Nutzer angelegt und bestehende Rollen verwaltet werden.
In dieser Phase 2 dient es als Demo für das Rollenmodell (Vorbereiter, Geschäftsleitung, FiBu, Viewer, Admin).
""")

users_df = pd.DataFrame.from_dict(MOCK_USERS, orient="index")
st.dataframe(users_df, use_container_width=True)

st.markdown("---")

with st.expander("Neuen Nutzer anlegen"):
    with st.form("new_user"):
        new_user = st.text_input("Benutzername")
        new_name = st.text_input("Voller Name")
        new_role = st.selectbox("Rolle", ["vorbereiter", "geschaeftsleitung", "fibu", "viewer", "admin"])
        new_ges = st.selectbox("Gesellschaft", ["beide", "nzwl", "zwl_sk"])
        new_pwd = st.text_input("Passwort", type="password")
        if st.form_submit_button("Speichern"):
            st.success(f"Nutzer '{new_user}' erfolgreich angelegt (nur in dieser Demo-Session).")
