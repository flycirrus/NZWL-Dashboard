import streamlit as st
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten
from core.calculations import (
    ampel_zusammenfassung, klassifiziere_faelligkeit,
    AMPEL_ROT, AMPEL_GELB, AMPEL_GRUEN,
    FARBE_ROT, FARBE_GELB, FARBE_GRUEN,
    FARBE_ROT_BG, FARBE_GELB_BG, FARBE_GRUEN_BG,
)

st.title("Dashboard")

# ── Kernlogik ausfuehren + Daten aktualisieren ───────────────────────────────
import os
import subprocess

col_kern, col_refresh, col_ts = st.columns([1, 1, 2])
ausgabe_container = st.empty()

with col_kern:
    if os.name == "nt":
        if st.button("Kernlogik ausfuehren"):
            skript = r"C:\nzwl-cashflow-core\src\kreditor_debitor\kreditor_debitor_logik.py"

            if not os.path.exists(skript):
                st.error(f"Fehler: Das Skript wurde nicht gefunden!\nPfad: `{skript}`\nBitte den Pfad auf dem Server pruefen.")
            else:
                st.info("Starte Kernlogik...")
                log_text = ""

                with st.spinner("Kernlogik laeuft — bitte warten (Live-Ausgabe unten)..."):
                    try:
                        process = subprocess.Popen(
                            [sys.executable, skript],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )

                        for line in process.stdout:
                            log_text += line
                            ausgabe_container.code(log_text, language="shell")

                        process.wait()

                        if process.returncode == 0:
                            st.success("Kernlogik erfolgreich ausgefuehrt!")
                            st.cache_data.clear()
                        else:
                            st.error(f"Kernlogik abgebrochen mit Fehlercode {process.returncode}!")

                    except Exception as e:
                        st.error(f"Systemfehler beim Ausfuehren: {e}")
    else:
        st.caption("Kernlogik nur auf dem Windows-Server verfuegbar")

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
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} EUR"


def fmt_mio(betrag: float) -> str:
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000:
        return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. EUR"
    if abs_b >= 1_000_000:
        return f"{_fmt_num(betrag / 1_000_000, 2)} M EUR"
    if abs_b >= 1_000:
        return f"{_fmt_num(betrag / 1_000, 1)} T EUR"
    return fmt_eur(betrag)


# ── Ampel-KPI-Karten (Rot/Gelb/Gruen) ───────────────────────────────────────
ampel = ampel_zusammenfassung(detail)

if "ampel_filter" not in st.session_state:
    st.session_state["ampel_filter"] = "Alle"

st.markdown("### Ampel-Status")

ampel_col1, ampel_col2, ampel_col3, ampel_col4 = st.columns([1, 1, 1, 0.8])

ampel_daten = [
    (AMPEL_ROT, FARBE_ROT, FARBE_ROT_BG, "Ueberfaellig", ampel_col1),
    (AMPEL_GELB, FARBE_GELB, FARBE_GELB_BG, "Faellig bald", ampel_col2),
    (AMPEL_GRUEN, FARBE_GRUEN, FARBE_GRUEN_BG, "OK / Freigegeben", ampel_col3),
]

for ampel_key, farbe, farbe_bg, label, col in ampel_daten:
    werte = ampel[ampel_key]
    is_active = st.session_state["ampel_filter"] == ampel_key
    border_width = "3px" if is_active else "1px"
    border_style = f"{border_width} solid {farbe}"

    col.markdown(f"""
    <div style="
        background: {farbe_bg};
        border: {border_style};
        border-left: 5px solid {farbe};
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
    ">
        <div style="color: #555555; font-size: 13px; font-weight: 600;">{label}</div>
        <div style="color: {farbe}; font-size: 28px; font-weight: 700;">{werte['anzahl']} Belege</div>
        <div style="color: #1A1A1A; font-size: 16px;">{fmt_mio(werte['betrag'])}</div>
    </div>
    """, unsafe_allow_html=True)

    btn_label = "Aktiv" if is_active else "Filtern"
    if col.button(btn_label, key=f"ampel_btn_{ampel_key}", use_container_width=True):
        st.session_state["ampel_filter"] = "Alle" if is_active else ampel_key
        st.rerun()

with ampel_col4:
    gesamt_belege = sum(v["anzahl"] for v in ampel.values())
    gesamt_betrag_ampel = sum(v["betrag"] for v in ampel.values())
    st.markdown(f"""
    <div style="
        background: #F5F7FA;
        border: 1px solid #E0E0E0;
        border-left: 5px solid #1F4E79;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 8px;
    ">
        <div style="color: #555555; font-size: 13px; font-weight: 600;">Gesamt</div>
        <div style="color: #1F4E79; font-size: 28px; font-weight: 700;">{gesamt_belege} Belege</div>
        <div style="color: #1A1A1A; font-size: 16px;">{fmt_mio(gesamt_betrag_ampel)}</div>
    </div>
    """, unsafe_allow_html=True)
    is_alle = st.session_state["ampel_filter"] == "Alle"
    if ampel_col4.button("Alle" if not is_alle else "Aktiv", key="ampel_btn_alle", use_container_width=True):
        st.session_state["ampel_filter"] = "Alle"
        st.rerun()

st.markdown("---")

# ── Allgemeine KPI-Karten ────────────────────────────────────────────────────
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

# ── Faelligkeiten (Wochenansicht) ────────────────────────────────────────────
df_faellig_week = pd.DataFrame()

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

    # Ampel-Filter anwenden
    aktiver_ampel = st.session_state["ampel_filter"]
    if aktiver_ampel != "Alle":
        df_faellig_week_unique = df_faellig_week_unique.copy()
        df_faellig_week_unique["_ampel"] = klassifiziere_faelligkeit(df_faellig_week_unique["nettofaelligkeit"])
        df_faellig_week_unique = df_faellig_week_unique[df_faellig_week_unique["_ampel"] == aktiver_ampel]
        df_faellig_week_unique = df_faellig_week_unique.drop(columns=["_ampel"])

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

    wk_cols = st.columns([1, 1, 1, 1, 1, 0.7])
    for i, woche in enumerate(wochen_order):
        betrag = wochen_summe.get(woche, 0)
        is_active = st.session_state["selected_woche"] == woche
        wk_cols[i].metric(woche, fmt_mio(betrag))
        btn_label = "Aktiv" if is_active else "Filtern"
        if wk_cols[i].button(btn_label, key=f"btn_{woche}", use_container_width=True):
            st.session_state["selected_woche"] = "Alle" if is_active else woche
            st.rerun()

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


# ── Expander: Ueberfaellig / Faellig bald / Naechste Woche ──────────────────
if not df_faellig_week.empty and "nettofaelligkeit" in detail.columns:
    df_exp = df_faellig_week.drop_duplicates(subset=["buchhaltungsbeleg"]).copy()

    # Ampel-Filter anwenden
    if aktiver_ampel != "Alle":
        df_exp["_ampel"] = klassifiziere_faelligkeit(df_exp["nettofaelligkeit"])
        df_exp = df_exp[df_exp["_ampel"] == aktiver_ampel]
        df_exp = df_exp.drop(columns=["_ampel"])

    heute = pd.Timestamp.now().normalize()
    df_exp["_zeitraum"] = df_exp["nettofaelligkeit"].apply(
        lambda d: "Ueberfaellig" if d < heute
        else "Faellig diese Woche" if d < heute + pd.Timedelta(days=7)
        else "Naechste Woche" if d < heute + pd.Timedelta(days=14)
        else "Spaeter"
    )

    zeitraum_config = [
        ("Ueberfaellig", FARBE_ROT, "Ueberfaellig"),
        ("Faellig diese Woche", FARBE_GELB, "Faellig diese Woche"),
        ("Naechste Woche", "#2E75B6", "Naechste Woche"),
        ("Spaeter", "#1F4E79", "Spaeter (2+ Wochen)"),
    ]

    for zeitraum_key, farbe, expander_label in zeitraum_config:
        subset = df_exp[df_exp["_zeitraum"] == zeitraum_key].sort_values("nettofaelligkeit")
        anzahl = len(subset)
        betrag = subset["offener_betrag"].sum() if not subset.empty else 0

        with st.expander(f"{expander_label} — {anzahl} Belege, {fmt_mio(betrag)}", expanded=(zeitraum_key == "Ueberfaellig" and anzahl > 0)):
            if subset.empty:
                st.info("Keine Belege in diesem Zeitraum.")
            else:
                anzeige = subset[["nettofaelligkeit", "buchhaltungsbeleg", "kreditor_name", "offener_betrag"]].copy()
                anzeige["nettofaelligkeit"] = anzeige["nettofaelligkeit"].dt.strftime("%d.%m.%Y")
                anzeige["offener_betrag"] = anzeige["offener_betrag"].apply(fmt_eur)
                anzeige.columns = ["Faellig am", "Beleg", "Kreditor", "Offener Betrag"]
                st.dataframe(anzeige, use_container_width=True, hide_index=True)

    st.markdown("---")


# ── Charts (gefiltert nach Wochenauswahl + Ampel) ───────────────────────────
if not detail.empty:
    try:
        import altair as alt

        chart_base = detail.copy()

        # Ampel-Filter anwenden
        if aktiver_ampel != "Alle" and "nettofaelligkeit" in chart_base.columns:
            chart_base["_ampel"] = klassifiziere_faelligkeit(chart_base["nettofaelligkeit"])
            chart_base = chart_base[chart_base["_ampel"] == aktiver_ampel]
            chart_base = chart_base.drop(columns=["_ampel"])

        # Wochen-Filter anwenden
        if not df_faellig_week.empty and selected_woche != "Alle":
            df_week_tmp = df_faellig_week.drop_duplicates(subset=["buchhaltungsbeleg"]).copy()
            df_week_tmp["woche"] = df_week_tmp["nettofaelligkeit"].apply(
                lambda d: "Ueberfaellig" if d < heute
                else "Diese Woche" if d < heute + pd.Timedelta(days=7)
                else "Naechste Woche" if d < heute + pd.Timedelta(days=14)
                else "In 2 Wochen" if d < heute + pd.Timedelta(days=21)
                else "Spaeter"
            )
            belege_im_zeitraum = set(
                df_week_tmp[df_week_tmp["woche"] == selected_woche]["buchhaltungsbeleg"]
            )
            chart_base = chart_base[chart_base["buchhaltungsbeleg"].isin(belege_im_zeitraum)]

        grp_cols = [c for c in ["kreditor", "kreditor_name"] if c in chart_base.columns]
        if grp_cols and not chart_base.empty:
            hat_debitor = "debitor" in chart_base.columns
            hat_debitor_name = "debitor_name" in chart_base.columns

            agg_dict = {"offener_betrag_summe": ("offener_betrag", "sum")}
            if hat_debitor:
                agg_dict["anzahl_debitoren"] = ("debitor", "nunique")
            if hat_debitor_name:
                agg_dict["endkunden_namen"] = (
                    "debitor_name",
                    lambda x: "\n".join(sorted(set(
                        str(v) for v in x.dropna() if str(v) not in ("nan", "", "NaT")
                    ))) or "—"
                )

            kred_agg = chart_base.groupby(grp_cols, as_index=False).agg(**agg_dict)
            kred_agg["betrag_fmt"] = kred_agg["offener_betrag_summe"].apply(fmt_mio)
        else:
            kred_agg = pd.DataFrame()

        filter_suffix_parts = []
        if aktiver_ampel != "Alle":
            filter_suffix_parts.append(aktiver_ampel)
        if selected_woche != "Alle":
            filter_suffix_parts.append(selected_woche)
        chart_titel_suffix = f" — {', '.join(filter_suffix_parts)}" if filter_suffix_parts else ""

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
                st.info("Keine Daten fuer diesen Zeitraum.")

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
