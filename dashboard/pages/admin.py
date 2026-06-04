import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from dashboard.auth import check_permission, MOCK_USERS
from core.data_import import (
    lade_ampel_status_historie,
    lade_ampel_status,
    speichere_ampel_status,
    berechne_ampel_status_zu_zeitpunkt,
    MARIADB_CONFIG,
    MARIADB_USERS,
    TABELLEN,
    _get_db_conn,
)

if not check_permission(["admin"]):
    st.error("Zugriff verweigert. Nur Administratoren dürfen diese Seite sehen.")
    st.stop()

st.title("Admin-Bereich ⚙️")

tab_users, tab_history, tab_source = st.tabs([
    "👤 Nutzerverwaltung",
    "📜 Beleg-Statusverlauf (Ampel-Historie)",
    "🔌 Datenquelle & Diagnose",
])

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

        # ── System-Wiederherstellung (Ampel-Rollback) ──────────────────────────────────
        st.markdown("---")
        with st.expander("🔄 System-Wiederherstellung (Ampel-Rollback)", expanded=False):
            st.markdown("""
            Hier können Sie den Zustand aller Ampeln im System auf einen beliebigen historischen Zeitpunkt zurücksetzen.
            Dies fügt neue Historien-Einträge hinzu, um die Nachvollziehbarkeit im Audit-Trail vollständig zu wahren.
            """)
            
            # Datetime pickers
            from datetime import datetime, date, time
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                target_date = st.date_input("Historisches Datum wählen", value=date.today())
            with col_d2:
                target_time = st.time_input("Historische Uhrzeit wählen", value=time(12, 0))
                
            target_dt = datetime.combine(target_date, target_time)
            
            # Zustand berechnen
            current_status = lade_ampel_status()
            historical_status = berechne_ampel_status_zu_zeitpunkt(target_dt)
            
            # Änderungen ermitteln
            changes = []
            all_beleg_ids = set(current_status.keys()).union(historical_status.keys())
            for b_id in all_beleg_ids:
                curr = current_status.get(b_id, "keine")
                hist = historical_status.get(b_id, "keine")
                if curr != hist:
                    changes.append({
                        "Belegnummer": b_id,
                        "Aktueller Status": curr,
                        "Ziel-Status": hist
                    })
                    
            if not changes:
                st.info(f"Der Zustand der Ampeln am **{target_dt.strftime('%d.%m.%Y %H:%M:%S')}** entspricht dem aktuellen Zustand. Keine Änderungen erforderlich.")
            else:
                st.warning(f"**Achtung:** Es wurden **{len(changes)}** Belege identifiziert, deren Ampel-Status sich vom Zustand am **{target_dt.strftime('%d.%m.%Y %H:%M:%S')}** unterscheidet.")
                
                # Preview Table
                preview_df = pd.DataFrame(changes)
                preview_display = preview_df.copy()
                status_emoji_map = {
                    "rot": "🔴 Stop / Prüfen",
                    "gelb": "🟡 In Prüfung",
                    "gruen": "🟢 Freigegeben",
                    "keine": "⚪ Keine / Zurückgesetzt"
                }
                preview_display["Aktueller Status"] = preview_display["Aktueller Status"].map(lambda x: status_emoji_map.get(x, x))
                preview_display["Ziel-Status"] = preview_display["Ziel-Status"].map(lambda x: status_emoji_map.get(x, x))
                
                st.dataframe(preview_display, use_container_width=True)
                
                confirm_rollback = st.checkbox("Ja, ich möchte alle oben gelisteten Belege auf den historischen Zustand zurücksetzen.", key="confirm_rollback_chk")
                
                # Rollback executing button
                if st.button("Rollback ausführen 🔄", disabled=not confirm_rollback, type="primary"):
                    success_count = 0
                    admin_name = st.session_state.user.get("name", "Admin") if st.session_state.user else "Admin"
                    rollback_user = f"{admin_name} (Rollback auf {target_dt.strftime('%d.%m.%Y %H:%M')})"
                    
                    for c in changes:
                        beleg = c["Belegnummer"]
                        target_val = c["Ziel-Status"]
                        if speichere_ampel_status(beleg, target_val, user=rollback_user):
                            success_count += 1
                            
                    st.success(f"Erfolgreich {success_count} Belege auf den Zustand vom {target_dt.strftime('%d.%m.%Y %H:%M:%S')} zurückgesetzt!")
                    st.toast("System-Zustand erfolgreich wiederhergestellt!", icon="💾")
                    st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# TAB 3: Datenquelle & Diagnose
# ──────────────────────────────────────────────────────────────────────────────
with tab_source:
    st.subheader("🔌 Datenquelle & Diagnose")

    # ── 1) Aktive Datenquelle ────────────────────────────────────────────────
    is_windows = os.name == "nt"
    if is_windows:
        st.success("**Datenquelle: MariaDB** — Dieser Server läuft auf Windows (os.name = 'nt').\n\nAlle Analysedaten werden ausschließlich aus der MariaDB-Datenbank geladen.")
        source_label = "MariaDB"
        source_color = "#16a34a"
    else:
        st.warning("**Datenquelle: Lokale JSON-Dateien** — Dieses System läuft auf macOS/Linux.\n\nAuf dem Windows-Server würde dieselbe Seite direkt aus MariaDB laden.")
        source_label = "Lokale JSON-Dateien"
        source_color = "#d97706"

    col_info1, col_info2 = st.columns(2)
    col_info1.metric("Betriebssystem", "Windows Server" if is_windows else "macOS / Linux")
    col_info2.metric("Aktive Datenquelle", source_label)

    st.markdown("---")

    # ── 2) MariaDB Verbindungstest ────────────────────────────────────────────
    st.markdown("### MariaDB Verbindungstest")
    st.caption(f"Host: `{MARIADB_CONFIG['host']}:{MARIADB_CONFIG['port']}` · Datenbank: `{MARIADB_CONFIG['database']}`")

    if st.button("Verbindung testen", key="test_mariadb_conn"):
        conn = _get_db_conn()
        if conn:
            st.success(f"✅ Verbindung zu MariaDB erfolgreich!")
            # Tabellen abfragen
            rows_info = []
            for tabelle in TABELLEN:
                try:
                    df_t = pd.read_sql(f"SELECT COUNT(*) AS anzahl FROM {tabelle}", conn)
                    rows_info.append({"Tabelle": tabelle, "Anzahl Zeilen": int(df_t["anzahl"].iloc[0]), "Status": "✅ vorhanden"})
                except Exception as e:
                    rows_info.append({"Tabelle": tabelle, "Anzahl Zeilen": 0, "Status": f"❌ Fehler: {e}"})
            conn.close()
            st.dataframe(pd.DataFrame(rows_info), use_container_width=True, hide_index=True)
        else:
            st.error("❌ Verbindung zur MariaDB konnte nicht hergestellt werden.")
            st.info("Auf dem Windows-Server muss MariaDB erreichbar sein. Lokal (macOS) ist das erwartet.")

    st.markdown("---")

    # ── 3) JSON-Dateien Inventar ─────────────────────────────────────────────
    st.markdown("### Lokale JSON-Dateien auf diesem Server")
    _data_dir = Path(__file__).resolve().parent.parent.parent / "data" / "input"
    json_files = {t: _data_dir / f"{t}.json" for t in TABELLEN}

    aktive_json, versteckte_json = [], []
    for tabelle, pfad in json_files.items():
        bak = pfad.with_suffix(".json.bak")
        if pfad.exists():
            size_mb = pfad.stat().st_size / 1_000_000
            aktive_json.append({"Tabelle": tabelle, "Datei": pfad.name, "Grösse": f"{size_mb:.1f} MB", "Status": "✅ aktiv"})
        elif bak.exists():
            versteckte_json.append({"Tabelle": tabelle, "Datei": bak.name, "Grösse": "—", "Status": "📦 gesichert (.bak)"})
        else:
            aktive_json.append({"Tabelle": tabelle, "Datei": "—", "Grösse": "—", "Status": "⚪ nicht vorhanden"})

    has_active_json = any(pfad.exists() for pfad in json_files.values())
    has_backup_json = any(pfad.with_suffix(".json.bak").exists() for pfad in json_files.values())

    if aktive_json:
        st.dataframe(pd.DataFrame(aktive_json), use_container_width=True, hide_index=True)
    if versteckte_json:
        st.dataframe(pd.DataFrame(versteckte_json), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── 4) Beweis-Bereich ─────────────────────────────────────────────────────
    st.markdown("### 🧪 Beweis: Woher kommen die Daten?")

    if is_windows and not has_active_json and not has_backup_json:
        # ── BEWEIS ERBRACHT: Server hat gar keine JSON-Dateien ─────────────────
        st.success("""
**✅ Beweis erbracht — Alle Daten kommen aus MariaDB.**

Auf diesem Windows-Server existieren **keine JSON-Dateien** im Ordner `data/input/`.
Das Dashboard zeigt dennoch Daten — diese können daher **ausschließlich aus der MariaDB-Datenbank** stammen.

**Logik:**
- Windows-Server → Code führt immer `_lade_aus_mariadb()` aus (unabhängig von JSON)
- Keine JSON-Dateien vorhanden → kein Fallback möglich
- Dashboard zeigt Daten → **Quelle = MariaDB** ✓
        """)

        st.markdown("#### Live-Bestätigung: Aktuelle Zeilenzahlen aus MariaDB")
        st.caption("Klicken Sie auf 'Bestätigen' um die Zeilenzahlen direkt aus der Datenbank zu lesen:")
        if st.button("🔍 Zeilenzahlen aus MariaDB bestätigen", type="primary", key="confirm_mariadb"):
            conn = _get_db_conn()
            if conn:
                rows_info = []
                total_rows = 0
                for tabelle in TABELLEN:
                    try:
                        df_t = pd.read_sql(f"SELECT COUNT(*) AS anzahl FROM {tabelle}", conn)
                        n = int(df_t["anzahl"].iloc[0])
                        total_rows += n
                        rows_info.append({
                            "Tabelle": tabelle,
                            "Zeilen in MariaDB": n,
                            "Quelle bestätigt": "✅ MariaDB"
                        })
                    except Exception as e:
                        rows_info.append({
                            "Tabelle": tabelle,
                            "Zeilen in MariaDB": 0,
                            "Quelle bestätigt": f"❌ {e}"
                        })
                conn.close()
                st.dataframe(pd.DataFrame(rows_info), use_container_width=True, hide_index=True)
                st.success(f"**{total_rows:,} Datensätze gesamt direkt aus MariaDB gelesen.** Keine JSON-Quelle beteiligt.")
            else:
                st.error("Verbindung zur MariaDB fehlgeschlagen.")

    elif is_windows and has_active_json:
        # Windows mit JSON-Dateien (ungewöhnlich, aber möglich)
        st.warning("""
⚠️ Auf diesem Windows-Server wurden JSON-Dateien gefunden.
Der Code ignoriert diese und lädt trotzdem aus MariaDB — aber zur Sicherheit können Sie die Dateien hier sichern.
        """)
        col_hide, col_restore = st.columns(2)
        with col_hide:
            if st.button("📦 JSON-Dateien sichern (.bak)", type="primary", key="hide_json"):
                moved = []
                for tabelle, pfad in json_files.items():
                    if pfad.exists():
                        bak = pfad.with_suffix(".json.bak")
                        pfad.rename(bak)
                        moved.append(pfad.name)
                if moved:
                    st.success(f"✅ {len(moved)} Dateien gesichert.")
                    st.cache_data.clear()
                    st.rerun()
        with col_restore:
            if st.button("♻️ JSON-Dateien wiederherstellen", disabled=not has_backup_json, key="restore_json"):
                restored = []
                for tabelle, pfad in json_files.items():
                    bak = pfad.with_suffix(".json.bak")
                    if bak.exists():
                        bak.rename(pfad)
                        restored.append(pfad.name)
                if restored:
                    st.success(f"✅ {len(restored)} Dateien wiederhergestellt.")
                    st.cache_data.clear()
                    st.rerun()

    else:
        # macOS / Linux — JSON-Test für lokale Entwicklung
        st.info("""
Dieses System läuft auf **macOS/Linux** und nutzt lokale JSON-Dateien als Datenquelle.

Zum Testen ob MariaDB erreichbar wäre: JSON-Dateien umbenennen und Dashboard neu laden.
        """)
        col_hide, col_restore = st.columns(2)
        with col_hide:
            if st.button(
                "📦 JSON-Dateien sichern (.bak)",
                disabled=not has_active_json,
                type="primary",
                key="hide_json",
                help="Benennt alle JSON-Dateien in .bak um",
            ):
                moved = []
                for tabelle, pfad in json_files.items():
                    if pfad.exists():
                        bak = pfad.with_suffix(".json.bak")
                        pfad.rename(bak)
                        moved.append(pfad.name)
                if moved:
                    st.success(f"✅ {len(moved)} Dateien gesichert.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Keine aktiven JSON-Dateien gefunden.")
        with col_restore:
            if st.button(
                "♻️ JSON-Dateien wiederherstellen",
                disabled=not has_backup_json,
                key="restore_json",
            ):
                restored = []
                for tabelle, pfad in json_files.items():
                    bak = pfad.with_suffix(".json.bak")
                    if bak.exists():
                        bak.rename(pfad)
                        restored.append(pfad.name)
                if restored:
                    st.success(f"✅ {len(restored)} Dateien wiederhergestellt.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Keine .bak-Dateien gefunden.")

    st.caption("ℹ️ Windows-Server: immer MariaDB · macOS/Linux: JSON-Fallback")
