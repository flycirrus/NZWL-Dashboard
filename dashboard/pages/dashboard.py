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

with col_kern:
    if os.name == "nt":
        if st.button("Kernlogik ausfuehren"):
            skript = r"C:\nzwl-cashflow-core\src\kreditor_debitor\kreditor_debitor_logik.py"
            with st.spinner("Kernlogik laeuft — SAP-Daten werden verarbeitet..."):
                result = subprocess.run(
                    [sys.executable, skript],
                    capture_output=True, text=True, timeout=300,
                )
            if result.returncode == 0:
                st.success("Kernlogik erfolgreich ausgefuehrt!")
                with st.expander("Ausgabe anzeigen"):
                    st.code(result.stdout)
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Fehler bei der Kernlogik!")
                with st.expander("Fehlerdetails"):
                    st.code(result.stderr)
    else:
        st.caption("Kernlogik nur auf dem Server verfuegbar")

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
def fmt_eur(betrag):
    return f"{betrag:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_mio(betrag):
    if abs(betrag) >= 1_000_000:
        return f"{betrag / 1_000_000:,.1f} Mio. EUR".replace(",", "X").replace(".", ",").replace("X", ".")
    elif abs(betrag) >= 1_000:
        return f"{betrag / 1_000:,.1f} Tsd. EUR".replace(",", "X").replace(".", ",").replace("X", ".")
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

# ── Faelligkeiten (Wochenansicht) ─────────────────────────────────────────────
if not detail.empty and "nettofaelligkeit" in detail.columns:
    st.subheader("Faelligkeiten nach Woche")
    st.caption("Was muss in den naechsten Wochen bezahlt werden?")

    df_faellig = detail[["buchhaltungsbeleg", "kreditor_name", "offener_betrag", "nettofaelligkeit"]].copy()
    df_faellig["nettofaelligkeit"] = pd.to_datetime(df_faellig["nettofaelligkeit"], errors="coerce")
    df_faellig = df_faellig.dropna(subset=["nettofaelligkeit"])
    df_faellig = df_faellig.drop_duplicates(subset=["buchhaltungsbeleg"])

    heute = pd.Timestamp.now().normalize()
    df_faellig["woche"] = df_faellig["nettofaelligkeit"].apply(
        lambda d: "Ueberfaellig" if d < heute
        else "Diese Woche" if d < heute + pd.Timedelta(days=7)
        else "Naechste Woche" if d < heute + pd.Timedelta(days=14)
        else "In 2 Wochen" if d < heute + pd.Timedelta(days=21)
        else "Spaeter"
    )

    wochen_order = ["Ueberfaellig", "Diese Woche", "Naechste Woche", "In 2 Wochen", "Spaeter"]
    wochen_summe = df_faellig.groupby("woche")["offener_betrag"].sum().reindex(wochen_order, fill_value=0)

    cols = st.columns(len(wochen_order))
    for i, woche in enumerate(wochen_order):
        betrag = wochen_summe.get(woche, 0)
        cols[i].metric(woche, fmt_mio(betrag))

    st.markdown("---")
else:
    st.info("Faelligkeitsdaten werden nach dem naechsten Kernlogik-Lauf verfuegbar sein.")
    st.markdown("---")

# ── Charts ────────────────────────────────────────────────────────────────────
if not uebersicht.empty and "offener_betrag_summe" in uebersicht.columns:
    try:
        import altair as alt

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Top 10 Kreditoren nach offenem Betrag")
            top10 = (
                uebersicht
                .nlargest(10, "offener_betrag_summe")
                [["kreditor_name", "offener_betrag_summe"]]
                .copy()
            )
            chart = alt.Chart(top10).mark_bar(color="#1F4E79").encode(
                x=alt.X("offener_betrag_summe:Q", title="Offener Betrag (EUR)", axis=alt.Axis(format=",.0f")),
                y=alt.Y("kreditor_name:N", title="", sort="-x"),
                tooltip=[
                    alt.Tooltip("kreditor_name:N", title="Kreditor"),
                    alt.Tooltip("offener_betrag_summe:Q", title="Betrag (EUR)", format=",.2f"),
                ],
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)

        with col_right:
            st.subheader("Kreditoren nach Anzahl Endkunden")
            if "anzahl_debitoren" in uebersicht.columns:
                deb_data = (
                    uebersicht[["kreditor_name", "anzahl_debitoren"]]
                    .copy()
                    .sort_values("anzahl_debitoren", ascending=False)
                    .head(10)
                )
                chart2 = alt.Chart(deb_data).mark_bar(color="#2E75B6").encode(
                    x=alt.X("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                    y=alt.Y("kreditor_name:N", title="", sort="-x"),
                    tooltip=[
                        alt.Tooltip("kreditor_name:N", title="Kreditor"),
                        alt.Tooltip("anzahl_debitoren:Q", title="Endkunden"),
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
        anz["offener_betrag_summe"] = anz["offener_betrag_summe"].apply(fmt_eur)

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
