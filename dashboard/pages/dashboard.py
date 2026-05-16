import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten

st.title("Dashboard")

# ── Kernlogik ausfuehren + Daten aktualisieren ───────────────────────────────
import os
import subprocess

col_kern, col_refresh, col_ts = st.columns([1, 1, 2])
ausgabe_container = st.empty() # Container in voller Breite für Terminal-Output

with col_kern:
    if os.name == "nt":
        if st.button("Kernlogik ausfuehren"):
            skript = r"C:\nzwl-cashflow-core\src\kreditor_debitor\kreditor_debitor_logik.py"
            
            if not os.path.exists(skript):
                st.error(f"Fehler: Das Skript wurde nicht gefunden!\nPfad: `{skript}`\nBitte den Pfad auf dem Server prüfen.")
            else:
                st.info("Starte Kernlogik...")
                log_text = ""
                
                with st.spinner("Kernlogik läuft — bitte warten (Live-Ausgabe unten)..."):
                    try:
                        # Popen statt run(), um Output live zu lesen
                        process = subprocess.Popen(
                            [sys.executable, skript],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, # stderr in stdout umleiten
                            text=True,
                            bufsize=1, # Zeilenweise puffern
                            universal_newlines=True
                        )
                        
                        # Output live mitlesen und anzeigen
                        for line in process.stdout:
                            log_text += line
                            ausgabe_container.code(log_text, language="shell")
                            
                        process.wait()
                        
                        if process.returncode == 0:
                            st.success("Kernlogik erfolgreich ausgeführt!")
                            st.cache_data.clear()
                            # Optionaler kurzer Rerun nach Erfolg, oder Benutzer Button klicken lassen
                            # st.rerun() 
                        else:
                            st.error(f"Kernlogik abgebrochen mit Fehlercode {process.returncode}!")
                            
                    except Exception as e:
                        st.error(f"Systemfehler beim Ausführen: {e}")
    else:
        st.caption("Kernlogik nur auf dem Windows-Server verfügbar")

with col_refresh:
    if st.button("Daten neu laden"):
        st.cache_data.clear()
        st.rerun()

daten = lade_ergebnis_daten()
detail = daten["detail"]
uebersicht = daten["uebersicht"]
statistik = daten["statistik"]

# Zeitstempel aus den Daten
zeitstempel = "unbekannt"
if not detail.empty and "aktualisiert_am" in detail.columns:
    try:
        ts = pd.to_datetime(detail["aktualisiert_am"]).max()
        zeitstempel = ts.strftime("%d.%m.%Y %H:%M")
    except Exception:
        pass

with col_ts:
    st.caption(f"Datenstand: {zeitstempel}")

if detail.empty and uebersicht.empty:
    st.warning("Keine Daten geladen. Bitte JSON-Dateien in data/input/ ablegen.")
    st.stop()

# ── Statistik-Dict ────────────────────────────────────────────────────────────
stat = {}
if not statistik.empty:
    for _, row in statistik.iterrows():
        stat[row["kennzahl"]] = row["wert"]


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────
def _fmt_num(value: float, decimals: int = 2) -> str:
    """Zahl auf Deutsch formatieren (Punkt = Tausender, Komma = Dezimal)."""
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} €"


def fmt_mio(betrag: float) -> str:
    """Kompakte EUR-Darstellung: Mrd.€ / M€ / T€."""
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000:
        return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. €"
    if abs_b >= 1_000_000:
        return f"{_fmt_num(betrag / 1_000_000, 2)} M€"
    if abs_b >= 1_000:
        return f"{_fmt_num(betrag / 1_000, 1)} T€"
    return fmt_eur(betrag)


# ── KPI-Karten ────────────────────────────────────────────────────────────────
gesamt_betrag = (
    uebersicht["offener_betrag_summe"].sum()
    if not uebersicht.empty and "offener_betrag_summe" in uebersicht.columns
    else 0.0
)

st.markdown("### Kennzahlen")
col1, col2, col3, col4 = st.columns(4)

col1.metric(
    label="Gesamtverbindlichkeiten",
    value=fmt_mio(gesamt_betrag),
)
col2.metric(
    label="Kreditoren (verknuepft / gesamt)",
    value=f"{stat.get('Kreditoren bis Debitor (Schritt 4)', '?')} / {stat.get('Kreditoren gesamt (OPOS)', '?')}",
)
col3.metric(
    label="Buchungsbelege (OPOS)",
    value=stat.get("Buchhaltungsbelege gesamt (OPOS)", "?"),
)
col4.metric(
    label="Match-Quote",
    value=stat.get("Gesamte Match-Quote", "?"),
)

st.markdown("---")

# ── Faelligkeiten (Wochenansicht) ─────────────────────────────────────────────────────
df_faellig_week = pd.DataFrame()  # used later for chart filtering

if not detail.empty and "nettofaelligkeit" in detail.columns:
    st.subheader("Faelligkeiten nach Woche")
    st.caption("Klicken zum Filtern der Diagramme unten.")

    _cols_needed = [c for c in ["buchhaltungsbeleg", "kreditor_name", "kreditor",
                                 "offener_betrag", "nettofaelligkeit", "debitor_name", "debitor"]
                    if c in detail.columns]
    df_faellig_week = detail[_cols_needed].copy()
    df_faellig_week["nettofaelligkeit"] = pd.to_datetime(df_faellig_week["nettofaelligkeit"], errors="coerce")
    df_faellig_week = df_faellig_week.dropna(subset=["nettofaelligkeit"])
    df_faellig_week_unique = df_faellig_week.drop_duplicates(subset=["buchhaltungsbeleg"])

    heute = pd.Timestamp.now().normalize()
    df_faellig_week_unique = df_faellig_week_unique.copy()
    df_faellig_week_unique["woche"] = df_faellig_week_unique["nettofaelligkeit"].apply(
        lambda d: "Ueberfaellig" if d < heute
        else "Diese Woche" if d < heute + pd.Timedelta(days=7)
        else "Naechste Woche" if d < heute + pd.Timedelta(days=14)
        else "In 2 Wochen" if d < heute + pd.Timedelta(days=21)
        else "Spaeter"
    )

    wochen_order = ["Ueberfaellig", "Diese Woche", "Naechste Woche", "In 2 Wochen", "Spaeter"]
    wochen_summe = df_faellig_week_unique.groupby("woche")["offener_betrag"].sum().reindex(wochen_order, fill_value=0)

    if "selected_woche" not in st.session_state:
        st.session_state["selected_woche"] = "Alle"

    # 5 Wochen-Spalten + 1 schmalere Spalte rechts für "Alle"
    wk_cols = st.columns([1, 1, 1, 1, 1, 0.7])
    for i, woche in enumerate(wochen_order):
        betrag = wochen_summe.get(woche, 0)
        is_active = st.session_state["selected_woche"] == woche
        wk_cols[i].metric(woche, fmt_mio(betrag))
        btn_label = "Aktiv" if is_active else "Filtern"
        if wk_cols[i].button(btn_label, key=f"btn_{woche}", use_container_width=True):
            st.session_state["selected_woche"] = "Alle" if is_active else woche
            st.rerun()

    # "Alle" Knopf rechts — Dummy-Metric zum perfekten vertikalen Ausrichten
    wk_cols[5].metric(" ", " ")
    if wk_cols[5].button("Alle", key="btn_alle", use_container_width=True):
        st.session_state["selected_woche"] = "Alle"
        st.rerun()

    selected_woche = st.session_state["selected_woche"]

    st.markdown("---")
else:
    st.info("Faelligkeitsdaten werden nach dem naechsten Kernlogik-Lauf verfuegbar sein.")
    selected_woche = "Alle"
    st.markdown("---")



# ── Charts (gefiltert nach Wochenauswahl) ─────────────────────────────────────
if not detail.empty:
    try:
        import altair as alt

        # Basis-Datensatz je nach Wochen-Filter aufbauen
        if not df_faellig_week.empty and selected_woche != "Alle":
            belege_im_zeitraum = set(
                df_faellig_week_unique[df_faellig_week_unique["woche"] == selected_woche]["buchhaltungsbeleg"]
            )
            chart_base = detail[detail["buchhaltungsbeleg"].isin(belege_im_zeitraum)].copy()
        else:
            chart_base = detail.copy()

        # Aggregation pro Kreditor mit Endkunden-Namen für Tooltip
        grp_cols = [c for c in ["kreditor", "kreditor_name"] if c in chart_base.columns]
        if grp_cols and not chart_base.empty:
            hat_debitor = "debitor" in chart_base.columns
            hat_debitor_name = "debitor_name" in chart_base.columns

            agg_dict = {"offener_betrag_summe": ("offener_betrag", "sum")}
            if hat_debitor_name:
                # Endkunden-Namen: nur Einträge mit echtem Namen (kein nan/leer)
                _valide_namen = lambda x: sorted(set(
                    str(v) for v in x.dropna() if str(v) not in ("nan", "", "NaT")
                ))
                # Anzahl aus denselben Namen → stimmt immer mit der Liste überein
                agg_dict["anzahl_debitoren"] = (
                    "debitor_name",
                    lambda x: len(set(
                        str(v) for v in x.dropna() if str(v) not in ("nan", "", "NaT")
                    ))
                )
                agg_dict["endkunden_namen"] = (
                    "debitor_name",
                    lambda x: "\n".join(sorted(set(
                        str(v) for v in x.dropna() if str(v) not in ("nan", "", "NaT")
                    ))) or "—"
                )
            elif hat_debitor:
                # Fallback falls kein debitor_name: IDs zählen
                agg_dict["anzahl_debitoren"] = ("debitor", "nunique")

            kred_agg = chart_base.groupby(grp_cols, as_index=False).agg(**agg_dict)
            kred_agg["betrag_fmt"] = kred_agg["offener_betrag_summe"].apply(fmt_mio)
        else:
            kred_agg = pd.DataFrame()

        chart_titel_suffix = f" — {selected_woche}" if selected_woche != "Alle" else ""
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader(f"Top 10 Kreditoren nach Betrag{chart_titel_suffix}")
            if not kred_agg.empty:
                top10 = kred_agg.nlargest(10, "offener_betrag_summe").copy()
                chart = alt.Chart(top10).mark_bar(color="#1F4E79").encode(
                    x=alt.X("offener_betrag_summe:Q", title="Offener Betrag",
                             axis=alt.Axis(format=",.0f")),
                    y=alt.Y("kreditor_name:N", title="", sort="-x"),
                    tooltip=[
                        alt.Tooltip("kreditor_name:N", title="Kreditor"),
                        alt.Tooltip("betrag_fmt:N", title="Offener Betrag"),
                        alt.Tooltip("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                        alt.Tooltip("endkunden_namen:N", title="Endkunden"),
                    ],
                ).properties(height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Keine Daten für diesen Zeitraum.")

        with col_right:
            st.subheader(f"Top 10 Kreditoren nach Endkunden{chart_titel_suffix}")
            if not kred_agg.empty and "anzahl_debitoren" in kred_agg.columns:
                deb_data = kred_agg.sort_values("anzahl_debitoren", ascending=False).head(10).copy()
                chart2 = alt.Chart(deb_data).mark_bar(color="#2E75B6").encode(
                    x=alt.X("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                    y=alt.Y("kreditor_name:N", title="", sort="-x"),
                    tooltip=[
                        alt.Tooltip("kreditor_name:N", title="Kreditor"),
                        alt.Tooltip("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                        alt.Tooltip("endkunden_namen:N", title="Endkunden"),
                        alt.Tooltip("betrag_fmt:N", title="Offener Betrag"),
                    ],
                ).properties(height=400)
                st.altair_chart(chart2, use_container_width=True)

    except ImportError:
        st.info("Altair nicht verfuegbar — Charts uebersprungen.")

st.markdown("---")


# ── Verknuepfungsstatistik ────────────────────────────────────────────────────
st.subheader("Verknuepfungsstatistik (4-Schritt-Kette)")
if not statistik.empty:
    anzeige = statistik[["kennzahl", "wert"]].copy()
    anzeige.columns = ["Kennzahl", "Wert"]
    st.dataframe(anzeige, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Kreditor-Uebersicht mit Download ─────────────────────────────────────────
st.subheader("Kreditor-Uebersicht")

if not uebersicht.empty:
    anzeige_spalten = [c for c in [
        "kreditor", "kreditor_name", "offener_betrag_summe",
        "anzahl_rohteile", "anzahl_fertigteile", "anzahl_debitoren",
        "aktualisiert_am"
    ] if c in uebersicht.columns]

    anz = uebersicht[anzeige_spalten].copy().sort_values(
        "offener_betrag_summe", ascending=False
    )

    if "aktualisiert_am" in anz.columns:
        anz["aktualisiert_am"] = pd.to_datetime(anz["aktualisiert_am"], errors="coerce").dt.strftime("%d.%m.%Y %H:%M")

    if "offener_betrag_summe" in anz.columns:
        anz["offener_betrag_summe"] = anz["offener_betrag_summe"].apply(fmt_mio)

    anz = anz.rename(columns={
        "kreditor": "Kreditor-Nr.",
        "kreditor_name": "Kreditor",
        "offener_betrag_summe": "Offener Betrag",
        "anzahl_rohteile": "Rohteile",
        "anzahl_fertigteile": "Fertigteile",
        "anzahl_debitoren": "Endkunden",
        "aktualisiert_am": "Stand",
    })
    st.dataframe(anz, use_container_width=True, hide_index=True)

    st.download_button(
        "Kreditor-Uebersicht als CSV",
        data=uebersicht.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
        file_name="kreditor_uebersicht.csv",
        mime="text/csv",
    )
