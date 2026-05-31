import streamlit as st
import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from dashboard.auth import check_permission, MOCK_USERS
from core.data_import import lade_ampel_status_historie

if not check_permission(["admin"]):
    st.error("Zugriff verweigert. Nur Administratoren dürfen diese Seite sehen.")
    st.stop()

st.title("Admin-Bereich ⚙️")

tab_users, tab_history = st.tabs(["👤 Nutzerverwaltung", "📜 Beleg-Statusverlauf (Ampel-Historie)"])

with tab_users:
    st.subheader("Nutzerverwaltung")
    st.markdown("""
    Hier können neue Nutzer angelegt und bestehende Rollen verwaltet werden.
    In dieser Entwicklungsphase dient es als Demonstration des Rollenmodells (Vorbereiter, Geschäftsleitung, FiBu, Viewer, Admin).
    """)

    users_df = pd.DataFrame.from_dict(MOCK_USERS, orient="index")
    # Spalten lesbar umbenennen
    users_df_display = users_df.rename(columns={
        "name": "Name",
        "email": "E-Mail-Adresse",
        "role": "Rolle (System)",
        "gesellschaft": "Zugeordnete Gesellschaft"
    })
    st.dataframe(users_df_display, use_container_width=True)

    with st.expander("Neuen Nutzer anlegen", expanded=False):
        with st.form("new_user"):
            new_user = st.text_input("Benutzername")
            new_name = st.text_input("Voller Name")
            new_role = st.selectbox("Rolle", ["vorbereiter", "geschaeftsleitung", "fibu", "viewer", "admin"])
            new_ges = st.selectbox("Gesellschaft", ["beide", "nzwl", "zwl_sk"])
            new_pwd = st.text_input("Passwort", type="password")
            if st.form_submit_button("Nutzer anlegen"):
                if new_user.strip() == "":
                    st.error("Bitte einen Benutzernamen angeben.")
                else:
                    st.success(f"Nutzer '{new_user}' erfolgreich angelegt (lokale Demo-Session).")

with tab_history:
    st.subheader("Änderungshistorie der Beleg-Ampeln")
    st.markdown("""
    Diese Historie dokumentiert revisionssicher alle manuellen Ampel-Status-Änderungen von Belegen. 
    Einträge werden chronologisch aufgelistet und nicht überschrieben.
    """)

    # Historie laden
    hist_df = lade_ampel_status_historie()

    if hist_df.empty:
        st.info("Bisher wurden keine Statusänderungen in der Historie erfasst.")
    else:
        # Filter-Bereich in 3 Spalten
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            search_beleg = st.text_input("Nach Beleg-Nr. suchen", "")
        with col_f2:
            unique_users = ["Alle"] + sorted(list(hist_df["geaendert_von"].dropna().unique()))
            selected_user = st.selectbox("Geändert von", unique_users)
        with col_f3:
            status_opts = {
                "Alle": "Alle",
                "rot": "🔴 Stop / Prüfen",
                "gelb": "🟡 In Prüfung",
                "gruen": "🟢 Freigegeben",
                "keine": "⚪ Zurückgesetzt / Keine"
            }
            selected_status_key = st.selectbox("Ampel-Status", list(status_opts.keys()), format_func=lambda x: status_opts[x])

        # Filter anwenden
        filtered_df = hist_df.copy()
        if search_beleg.strip():
            filtered_df = filtered_df[filtered_df["buchhaltungsbeleg"].astype(str).str.contains(search_beleg.strip(), case=False)]
        if selected_user != "Alle":
            filtered_df = filtered_df[filtered_df["geaendert_von"] == selected_user]
        if selected_status_key != "Alle":
            filtered_df = filtered_df[filtered_df["ampel_status"] == selected_status_key]

        # Schöne Formatierung
        display_df = filtered_df.copy()
        
        # Status-Text & Emojis
        status_map = {
            "rot": "🔴 Stop / Prüfen",
            "gelb": "🟡 In Prüfung",
            "gruen": "🟢 Freigegeben",
            "keine": "⚪ Zurückgesetzt / Keine"
        }
        display_df["ampel_status"] = display_df["ampel_status"].map(lambda x: status_map.get(x, x))
        
        # Zeitstempel formatieren
        if not display_df.empty and "geaendert_am" in display_df.columns:
            display_df["geaendert_am"] = pd.to_datetime(display_df["geaendert_am"]).dt.strftime("%d.%m.%Y %H:%M:%S")

        # Spalten umbenennen
        display_df = display_df.rename(columns={
            "buchhaltungsbeleg": "Belegnummer",
            "ampel_status": "Gesetzter Ampel-Status",
            "geaendert_am": "Geändert am",
            "geaendert_von": "Geändert von"
        })

        # Zeigen
        st.write(f"**Gefundene Einträge:** {len(display_df)}")
        st.dataframe(display_df, use_container_width=True)

        # Export zu CSV
        csv_data = display_df.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            label="📥 Historie als CSV exportieren",
            data=csv_data,
            file_name="ampel_status_historie.csv",
            mime="text/csv",
        )
