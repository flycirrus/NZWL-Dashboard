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
nv_raw = daten.get("nicht_verknuepft", pd.DataFrame())
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
# Gesamtverbindlichkeiten: eindeutig pro Buchhaltungsbeleg (sonst Mehrfachzählung durch BOM-Join)
if not detail.empty and "buchhaltungsbeleg" in detail.columns and "offener_betrag" in detail.columns:
    gesamt_betrag = (
        detail.drop_duplicates(subset=["buchhaltungsbeleg"])["offener_betrag"].sum()
    )
else:
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
col1.caption("💡 Summe aller offenen Belege (OPOS), je Beleg einmalig gezählt")
col2.metric(
    label="Kreditoren (verknüpft / gesamt)",
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
# Gleiche Datenbasis wie Fälligkeiten-Seite: detail (dedupliziert) + nv_raw
df_faellig_week = pd.DataFrame()  # used later for chart filtering

if not detail.empty and "nettofaelligkeit" in detail.columns:
    st.subheader("Faelligkeiten nach Woche")
    st.caption("Klicken zum Filtern der Diagramme unten.")

    # ── Datenbasis: identisch zur Fälligkeiten-Seite ──────────────────────────
    _df = detail.copy()
    _df["nettofaelligkeit"] = pd.to_datetime(_df["nettofaelligkeit"], errors="coerce")
    _df = _df.dropna(subset=["nettofaelligkeit"])

    # Pro Buchhaltungsbeleg eine Zeile (wie in faelligkeiten.py)
    _agg_cols = {"kreditor_name": "first", "kreditor": "first",
                 "offener_betrag": "first", "nettofaelligkeit": "first"}
    _agg_cols = {k: v for k, v in _agg_cols.items() if k in _df.columns}
    belege_dash = _df.groupby("buchhaltungsbeleg", as_index=False).agg(_agg_cols)

    # Nicht-verknüpfte Positionen hinzufügen (nv_raw)
    if not nv_raw.empty and "nettofaelligkeit" in nv_raw.columns:
        _nv = nv_raw.copy()
        _nv["nettofaelligkeit"] = pd.to_datetime(_nv["nettofaelligkeit"], errors="coerce")
        _nv = _nv.dropna(subset=["nettofaelligkeit"])
        if not _nv.empty:
            for c in belege_dash.columns:
                if c not in _nv.columns:
                    _nv[c] = "" if belege_dash[c].dtype == object else 0
            belege_dash = pd.concat([belege_dash, _nv[belege_dash.columns]], ignore_index=True)

    df_faellig_week = belege_dash.copy()
    df_faellig_week_unique = belege_dash.copy()

    heute = pd.Timestamp.now().normalize()
    # ISO-Kalenderwochen-Grenzen: Montag dieser KW als Ankerpunkt
    heute_montag   = heute - pd.Timedelta(days=heute.weekday())  # Montag der aktuellen KW
    naechste_kw    = heute_montag + pd.Timedelta(weeks=1)
    in_2_wochen    = heute_montag + pd.Timedelta(weeks=2)
    in_3_wochen    = heute_montag + pd.Timedelta(weeks=3)

    df_faellig_week_unique["woche"] = df_faellig_week_unique["nettofaelligkeit"].apply(
        lambda d: "Ueberfaellig"   if d < heute_montag
        else "Diese Woche"         if d < naechste_kw
        else "Naechste Woche"      if d < in_2_wochen
        else "In 2 Wochen"         if d < in_3_wochen
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

            def _namen_set(series):
                namen = set()
                for v in series.dropna():
                    for teil in str(v).split(","):
                        teil = teil.strip()
                        if teil and teil not in ("nan", "NaT", ""):
                            namen.add(teil)
                return namen

            # Betrag: pro Beleg nur einmal zaehlen (BOM-Join vervielfacht Zeilen)
            chart_belege = chart_base.drop_duplicates(subset=["buchhaltungsbeleg"])
            kred_agg = chart_belege.groupby(grp_cols, as_index=False).agg(
                offener_betrag_summe=("offener_betrag", "sum")
            )

            # Debitoren: aus allen Detail-Zeilen (verschiedene Debitoren pro Zeile)
            if hat_debitor_name:
                deb_agg = chart_base.groupby(grp_cols, as_index=False).agg(
                    anzahl_debitoren=("debitor_name", lambda x: len(_namen_set(x))),
                    endkunden_namen=("debitor_name", lambda x: ", ".join(sorted(_namen_set(x))) or "—"),
                )
                kred_agg = kred_agg.merge(deb_agg, on=grp_cols, how="left")
            elif hat_debitor:
                deb_agg = chart_base.groupby(grp_cols, as_index=False).agg(
                    anzahl_debitoren=("debitor", "nunique")
                )
                kred_agg = kred_agg.merge(deb_agg, on=grp_cols, how="left")

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
