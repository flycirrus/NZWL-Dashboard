"""
Dashboard – Variante 1 (W1)
Gleiche Funktionalität wie dashboard.py, überarbeitetes visuelles Design.
"""
import streamlit as st
import sys
import os
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten

# ── CSS Injizieren ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Farb-Tokens ── */
:root {
    --nzwl-blue:      #1F4E79;
    --nzwl-blue-mid:  #2E75B6;
    --nzwl-blue-light:#D6E4F0;
    --nzwl-accent:    #F59E0B;
    --nzwl-green:     #16A34A;
    --nzwl-red:       #DC2626;
    --nzwl-surface:   #F8FAFC;
    --nzwl-card:      #FFFFFF;
    --nzwl-border:    #E2E8F0;
    --nzwl-text:      #1E293B;
    --nzwl-muted:     #64748B;
}

/* ── KPI-Karten ── */
.kpi-card {
    background: var(--nzwl-card);
    border: 1px solid var(--nzwl-border);
    border-left: 4px solid var(--nzwl-blue);
    border-radius: 10px;
    padding: 1.1rem 1.3rem 0.9rem;
    box-shadow: 0 1px 4px rgba(31,78,121,0.07);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.kpi-card:hover {
    box-shadow: 0 4px 14px rgba(31,78,121,0.13);
    transform: translateY(-2px);
}
.kpi-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--nzwl-muted);
    margin-bottom: 0.35rem;
}
.kpi-value {
    font-size: 1.65rem;
    font-weight: 800;
    color: var(--nzwl-blue);
    line-height: 1.15;
    letter-spacing: -0.01em;
}
.kpi-sub {
    font-size: 0.78rem;
    color: var(--nzwl-muted);
    margin-top: 0.3rem;
    line-height: 1.45;
}
.kpi-chip-green { color: var(--nzwl-green); font-weight: 700; }
.kpi-chip-red   { color: var(--nzwl-red);   font-weight: 700; }

/* ── Wochen-Kacheln ── */
.woche-card {
    border-radius: 10px;
    padding: 0.85rem 1rem 0.75rem;
    text-align: center;
    border: 1.5px solid var(--nzwl-border);
    background: var(--nzwl-card);
    transition: all 0.18s ease;
    cursor: pointer;
    margin-bottom: 0.45rem;
}
.woche-card:hover { border-color: var(--nzwl-blue-mid); box-shadow: 0 3px 10px rgba(31,78,121,0.12); }
.woche-card.active {
    background: var(--nzwl-blue);
    border-color: var(--nzwl-blue);
    color: white;
}
.woche-card.active .woche-label { color: rgba(255,255,255,0.75) !important; }
.woche-card.active .woche-value { color: white !important; }
.woche-card.ueberfaellig { border-color: var(--nzwl-red); background: #FEF2F2; }
.woche-card.ueberfaellig .woche-value { color: var(--nzwl-red) !important; }
.woche-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--nzwl-muted);
    margin-bottom: 0.3rem;
}
.woche-value {
    font-size: 1.1rem;
    font-weight: 800;
    color: var(--nzwl-blue);
    letter-spacing: -0.01em;
}

/* ── Abschnitt-Header ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 1.5rem 0 0.8rem;
}
.section-header-line {
    flex: 1;
    height: 1px;
    background: var(--nzwl-border);
}
.section-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--nzwl-blue);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
}

/* ── Filterband (aktiver Wochen-Filter Info) ── */
.filter-badge {
    display: inline-block;
    background: var(--nzwl-blue);
    color: white;
    border-radius: 99px;
    padding: 0.22rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 0.6rem;
}

/* ── Statistik-Tabelle ── */
.stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem 0.2rem;
    border-bottom: 1px solid var(--nzwl-border);
    font-size: 0.87rem;
}
.stat-row:last-child { border-bottom: none; }
.stat-key { color: var(--nzwl-text); }
.stat-val { font-weight: 700; color: var(--nzwl-blue); }

/* ── Page-Header ── */
.page-hero {
    background: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
    border-radius: 14px;
    padding: 1.4rem 1.8rem 1.2rem;
    color: white;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 4px 18px rgba(31,78,121,0.22);
}
.page-hero h1 {
    font-size: 1.55rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.01em;
}
.page-hero p {
    font-size: 0.85rem;
    opacity: 0.75;
    margin: 0.25rem 0 0;
}
.page-hero .ts-badge {
    background: rgba(255,255,255,0.15);
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
    text-align: right;
}
.page-hero .ts-badge span {
    display: block;
    opacity: 0.65;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.15rem;
}

/* ── Schaltflächen neutralisieren ── */
div[data-testid="stButton"] button {
    transition: all 0.18s ease !important;
}
</style>
""", unsafe_allow_html=True)


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────
def _fmt_num(value: float, decimals: int = 2) -> str:
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} €"

def fmt_mio(betrag: float) -> str:
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000:
        return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. €"
    if abs_b >= 1_000_000:
        return f"{_fmt_num(betrag / 1_000_000, 2)} M€"
    if abs_b >= 1_000:
        return f"{_fmt_num(betrag / 1_000, 1)} T€"
    return fmt_eur(betrag)


# ── Kernlogik & Daten laden ───────────────────────────────────────────────────
c_kern, c_refresh, c_spacer = st.columns([1.2, 1, 4])

ausgabe_container = st.empty()

with c_kern:
    if os.name == "nt":
        if st.button("⚙️ Kernlogik ausführen", help="Startet die Kernlogik auf dem Windows-Server"):
            skript = r"C:\nzwl-cashflow-core\src\kreditor_debitor\kreditor_debitor_logik.py"
            if not os.path.exists(skript):
                st.error(f"Skript nicht gefunden:\n`{skript}`")
            else:
                log_text = ""
                with st.spinner("Kernlogik läuft …"):
                    try:
                        process = subprocess.Popen(
                            [sys.executable, skript],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, bufsize=1, universal_newlines=True,
                        )
                        for line in process.stdout:
                            log_text += line
                            ausgabe_container.code(log_text, language="shell")
                        process.wait()
                        if process.returncode == 0:
                            st.success("Kernlogik erfolgreich ausgeführt!")
                            st.cache_data.clear()
                        else:
                            st.error(f"Abgebrochen (Code {process.returncode})")
                    except Exception as e:
                        st.error(f"Systemfehler: {e}")
    else:
        st.caption("Kernlogik nur auf Windows verfügbar")

with c_refresh:
    if st.button("🔄 Neu laden", help="Cache leeren und Daten neu laden"):
        st.cache_data.clear()
        st.rerun()


# ── Daten laden ───────────────────────────────────────────────────────────────
daten      = lade_ergebnis_daten()
detail     = daten["detail"]
nv_raw     = daten.get("nicht_verknuepft", pd.DataFrame())
uebersicht = daten["uebersicht"]
statistik  = daten["statistik"]

# Zeitstempel
zeitstempel = "—"
if not detail.empty and "aktualisiert_am" in detail.columns:
    try:
        ts = pd.to_datetime(detail["aktualisiert_am"]).max()
        zeitstempel = ts.strftime("%d.%m.%Y, %H:%M Uhr")
    except Exception:
        pass

# ── Page Hero-Header ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="page-hero">
  <div>
    <h1>📊 Dashboard – Version 02</h1>
    <p>Kreditor-Debitor Liquiditätssteuerung · NZWL Leipzig &amp; ZWL Slovakia</p>
  </div>
  <div class="ts-badge">
    <span>Datenstand</span>
    {zeitstempel}
  </div>
</div>
""", unsafe_allow_html=True)

if detail.empty and uebersicht.empty:
    st.warning("⚠️ Keine Daten vorhanden — bitte JSON-Dateien in **data/input/** ablegen.")
    st.stop()


# ── Statistik-Dict ────────────────────────────────────────────────────────────
stat = {}
if not statistik.empty:
    for _, row in statistik.iterrows():
        stat[row["kennzahl"]] = row["wert"]


# ── Gesamtbetrag berechnen ────────────────────────────────────────────────────
if not detail.empty and "buchhaltungsbeleg" in detail.columns and "offener_betrag" in detail.columns:
    gesamt_betrag = detail.drop_duplicates(subset=["buchhaltungsbeleg"])["offener_betrag"].sum()
    if not nv_raw.empty and "offener_betrag" in nv_raw.columns:
        gesamt_betrag += nv_raw["offener_betrag"].sum()
else:
    gesamt_betrag = (
        uebersicht["offener_betrag_summe"].sum()
        if not uebersicht.empty and "offener_betrag_summe" in uebersicht.columns
        else 0.0
    )

# Verknüpft / nicht verknüpft / Gutschriften
_betrag_verknuepft = (
    detail.drop_duplicates(subset=["buchhaltungsbeleg"])["offener_betrag"].sum()
    if not detail.empty and "buchhaltungsbeleg" in detail.columns and "offener_betrag" in detail.columns
    else 0.0
)
if not nv_raw.empty:
    _gut_by_grund  = (nv_raw["grund"].astype(str).str.strip().str.lower() == "gutschrift"
                      if "grund" in nv_raw.columns
                      else pd.Series(False, index=nv_raw.index))
    _gut_by_betrag = (nv_raw["offener_betrag"] < 0
                      if "offener_betrag" in nv_raw.columns
                      else pd.Series(False, index=nv_raw.index))
    _ist_gutschrift = _gut_by_grund | _gut_by_betrag
    _gs         = nv_raw[_ist_gutschrift]
    _nv_ohne_gs = nv_raw[~_ist_gutschrift]
else:
    _gs         = pd.DataFrame()
    _nv_ohne_gs = nv_raw

_betrag_nicht_verknuepft = (
    _nv_ohne_gs["offener_betrag"].sum()
    if not _nv_ohne_gs.empty and "offener_betrag" in _nv_ohne_gs.columns
    else 0.0
)
_betrag_gutschriften = (
    _gs["offener_betrag"].sum()
    if not _gs.empty and "offener_betrag" in _gs.columns
    else 0.0
)
_anzahl_gutschriften = len(_gs)


# ── Abschnitt: KPI-Karten ─────────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-title">📌 Kennzahlen</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    gs_sub = f'<span class="kpi-chip-green">✔ {fmt_mio(_betrag_verknuepft)}</span> verknüpft'
    if _anzahl_gutschriften > 0:
        gs_sub += f'<br>↩️ {_anzahl_gutschriften} Gutschrift(en): {fmt_mio(abs(_betrag_gutschriften))}'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Gesamtverbindlichkeiten</div>
        <div class="kpi-value">{fmt_mio(gesamt_betrag)}</div>
        <div class="kpi-sub">{gs_sub}</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    kred_verknuepft = stat.get("Kreditoren bis Debitor (Schritt 4)", "?")
    kred_gesamt     = stat.get("Kreditoren gesamt (OPOS)", "?")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Kreditoren verknüpft / gesamt</div>
        <div class="kpi-value">{kred_verknuepft} <span style="font-size:1rem;color:#64748B">/ {kred_gesamt}</span></div>
        <div class="kpi-sub">Aktive Lieferanten im OPOS-Master</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    belege_gesamt = stat.get("Buchhaltungsbelege gesamt (OPOS)", "?")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Buchungsbelege (OPOS)</div>
        <div class="kpi-value">{belege_gesamt}</div>
        <div class="kpi-sub">Offene Positionen gesamt</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    match_quote = stat.get("Gesamte Match-Quote", "?")
    nv_sub = f'<span class="kpi-chip-red">✖ {fmt_mio(_betrag_nicht_verknuepft)}</span> nicht verknüpft'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Match-Quote</div>
        <div class="kpi-value">{match_quote}</div>
        <div class="kpi-sub">{nv_sub}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Abschnitt: Fälligkeiten nach Woche ───────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.8rem">
  <span class="section-title">📅 Fälligkeiten nach Woche</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

df_faellig_week        = pd.DataFrame()
df_faellig_week_unique = pd.DataFrame()
selected_woche         = "Alle"

if not detail.empty and "nettofaelligkeit" in detail.columns:
    _df = detail.copy()
    _df["nettofaelligkeit"] = pd.to_datetime(_df["nettofaelligkeit"], errors="coerce")
    _df = _df.dropna(subset=["nettofaelligkeit"])

    _agg_cols = {k: v for k, v in {
        "kreditor_name": "first", "kreditor": "first",
        "offener_betrag": "first", "nettofaelligkeit": "first",
    }.items() if k in _df.columns}
    belege_dash = _df.groupby("buchhaltungsbeleg", as_index=False).agg(_agg_cols)

    if not nv_raw.empty and "nettofaelligkeit" in nv_raw.columns:
        _nv = nv_raw.copy()
        _nv["nettofaelligkeit"] = pd.to_datetime(_nv["nettofaelligkeit"], errors="coerce")
        _nv = _nv.dropna(subset=["nettofaelligkeit"])
        if not _nv.empty:
            for c in belege_dash.columns:
                if c not in _nv.columns:
                    _nv[c] = "" if belege_dash[c].dtype == object else 0
            belege_dash = pd.concat([belege_dash, _nv[belege_dash.columns]], ignore_index=True)

    df_faellig_week        = belege_dash.copy()
    df_faellig_week_unique = belege_dash.copy()

    heute        = pd.Timestamp.now().normalize()
    heute_montag = heute - pd.Timedelta(days=heute.weekday())
    naechste_kw  = heute_montag + pd.Timedelta(weeks=1)
    in_2_wochen  = heute_montag + pd.Timedelta(weeks=2)
    in_3_wochen  = heute_montag + pd.Timedelta(weeks=3)

    df_faellig_week_unique["woche"] = df_faellig_week_unique["nettofaelligkeit"].apply(
        lambda d: "Überfällig"    if d < heute_montag
        else "Diese Woche"        if d < naechste_kw
        else "Nächste Woche"      if d < in_2_wochen
        else "In 2 Wochen"        if d < in_3_wochen
        else "Später"
    )

    wochen_order = ["Überfällig", "Diese Woche", "Nächste Woche", "In 2 Wochen", "Später"]
    wochen_summe = (
        df_faellig_week_unique.groupby("woche")["offener_betrag"]
        .sum()
        .reindex(wochen_order, fill_value=0)
    )

    if "selected_woche_w1" not in st.session_state:
        st.session_state["selected_woche_w1"] = "Alle"

    # ── Wochenkacheln als Buttons ─────────────────────────────────────────────
    wk_cols = st.columns([1, 1, 1, 1, 1, 0.65])
    for i, woche in enumerate(wochen_order):
        betrag    = wochen_summe.get(woche, 0)
        is_active = st.session_state["selected_woche_w1"] == woche
        is_overd  = woche == "Überfällig"

        card_cls  = "woche-card"
        if is_active: card_cls += " active"
        elif is_overd: card_cls += " ueberfaellig"

        wk_cols[i].markdown(f"""
        <div class="{card_cls}">
            <div class="woche-label">{woche}</div>
            <div class="woche-value">{fmt_mio(betrag)}</div>
        </div>
        """, unsafe_allow_html=True)

        btn_label = "✓ Aktiv" if is_active else "Filtern"
        btn_type  = "primary" if is_active else "secondary"
        if wk_cols[i].button(btn_label, key=f"w1_btn_{woche}", use_container_width=True, type=btn_type):
            st.session_state["selected_woche_w1"] = "Alle" if is_active else woche
            st.rerun()

    wk_cols[5].markdown("""
    <div class="woche-card" style="border-style:dashed;">
        <div class="woche-label">Gesamt</div>
        <div class="woche-value">Alle</div>
    </div>
    """, unsafe_allow_html=True)
    if wk_cols[5].button("Alle", key="w1_btn_alle", use_container_width=True):
        st.session_state["selected_woche_w1"] = "Alle"
        st.rerun()

    selected_woche = st.session_state["selected_woche_w1"]

    if selected_woche != "Alle":
        import datetime as _dt
        _heute = _dt.date.today()
        _kw_heute = _heute.isocalendar()[1]
        _kw_hint = ""
        if selected_woche == "Überfällig":
            _kw_hint = ""
        else:
            # Wochennummer aus dem Label ableiten (z.B. "KW23", "KW24" ...)
            # Label kommt aus wochen_order: "Überfällig", "KW23", "KW24" ...
            import re as _re
            _m = _re.search(r"KW\s*(\d+)", selected_woche)
            if _m:
                _kw_hint = f" &nbsp;·&nbsp; <span style='font-size:0.72rem;opacity:0.7'>KW&nbsp;{_m.group(1)}</span>"
            elif selected_woche == "Diese Woche":
                _kw_hint = f" &nbsp;·&nbsp; <span style='font-size:0.72rem;opacity:0.7'>KW&nbsp;{_kw_heute}</span>"
        st.markdown(
            f'<div class="filter-badge">\U0001f50d Filter aktiv: {selected_woche}{_kw_hint}</div>',
            unsafe_allow_html=True,
        )
else:
    st.info("ℹ️ Fälligkeitsdaten werden nach dem nächsten Kernlogik-Lauf verfügbar.")


# ── Abschnitt: Charts ─────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.5rem">
  <span class="section-title">📈 Analysen</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

if not detail.empty:
    try:
        import altair as alt

        # Basis-Datensatz je nach Filter
        if not df_faellig_week.empty and selected_woche != "Alle":
            belege_im_zeitraum = set(
                df_faellig_week_unique[df_faellig_week_unique["woche"] == selected_woche]["buchhaltungsbeleg"]
            )
            chart_base = detail[detail["buchhaltungsbeleg"].isin(belege_im_zeitraum)].copy()
        else:
            chart_base = detail.copy()

        grp_cols = [c for c in ["kreditor", "kreditor_name"] if c in chart_base.columns]

        if grp_cols and not chart_base.empty:
            hat_debitor_name = "debitor_name" in chart_base.columns
            hat_debitor      = "debitor" in chart_base.columns

            def _namen_set(series):
                namen = set()
                for v in series.dropna():
                    for teil in str(v).split(","):
                        teil = teil.strip()
                        if teil and teil not in ("nan", "NaT", ""):
                            namen.add(teil)
                return namen

            chart_belege = chart_base.drop_duplicates(subset=["buchhaltungsbeleg"])
            kred_agg = chart_belege.groupby(grp_cols, as_index=False).agg(
                offener_betrag_summe=("offener_betrag", "sum")
            )

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

        suffix = f" · {selected_woche}" if selected_woche != "Alle" else ""
        col_left, col_right = st.columns(2, gap="medium")

        # ── Chart 1: Top 10 Kreditoren nach Betrag ────────────────────────────
        with col_left:
            st.markdown(f"**Top 10 Kreditoren nach Betrag{suffix}**")
            if not kred_agg.empty:
                top10 = kred_agg.nlargest(10, "offener_betrag_summe").copy()

                tooltip_fields = [
                    alt.Tooltip("kreditor_name:N", title="Kreditor"),
                    alt.Tooltip("betrag_fmt:N",    title="Offener Betrag"),
                ]
                if "anzahl_debitoren" in top10.columns:
                    tooltip_fields.append(alt.Tooltip("anzahl_debitoren:Q", title="Anzahl Endkunden"))
                if "endkunden_namen" in top10.columns:
                    tooltip_fields.append(alt.Tooltip("endkunden_namen:N", title="Endkunden"))

                bars = alt.Chart(top10).mark_bar(
                    cornerRadiusTopRight=4,
                    cornerRadiusBottomRight=4,
                ).encode(
                    x=alt.X(
                        "offener_betrag_summe:Q",
                        title="Offener Betrag (€)",
                        axis=alt.Axis(format=",.0f", labelFontSize=11),
                    ),
                    y=alt.Y(
                        "kreditor_name:N",
                        title="",
                        sort="-x",
                        axis=alt.Axis(labelFontSize=11, labelLimit=160),
                    ),
                    color=alt.condition(
                        alt.datum.offener_betrag_summe == top10["offener_betrag_summe"].max(),
                        alt.value("#1F4E79"),
                        alt.value("#2E75B6"),
                    ),
                    tooltip=tooltip_fields,
                ).properties(height=360)

                text = bars.mark_text(
                    align="left", dx=4, fontSize=10, color="#475569"
                ).encode(text="betrag_fmt:N")

                st.altair_chart((bars + text).configure_view(strokeWidth=0), use_container_width=True)
            else:
                st.info("Keine Daten für diesen Zeitraum.")

        # ── Chart 2: Top 10 Kreditoren nach Endkunden ─────────────────────────
        with col_right:
            st.markdown(f"**Top 10 Kreditoren nach Endkunden{suffix}**")
            if not kred_agg.empty and "anzahl_debitoren" in kred_agg.columns:
                deb_data = kred_agg.sort_values("anzahl_debitoren", ascending=False).head(10).copy()

                tooltip_fields2 = [
                    alt.Tooltip("kreditor_name:N",    title="Kreditor"),
                    alt.Tooltip("anzahl_debitoren:Q", title="Anzahl Endkunden"),
                    alt.Tooltip("betrag_fmt:N",        title="Offener Betrag"),
                ]
                if "endkunden_namen" in deb_data.columns:
                    tooltip_fields2.append(alt.Tooltip("endkunden_namen:N", title="Endkunden"))

                bars2 = alt.Chart(deb_data).mark_bar(
                    cornerRadiusTopRight=4,
                    cornerRadiusBottomRight=4,
                ).encode(
                    x=alt.X(
                        "anzahl_debitoren:Q",
                        title="Anzahl Endkunden",
                        axis=alt.Axis(labelFontSize=11),
                    ),
                    y=alt.Y(
                        "kreditor_name:N",
                        title="",
                        sort="-x",
                        axis=alt.Axis(labelFontSize=11, labelLimit=160),
                    ),
                    color=alt.condition(
                        alt.datum.anzahl_debitoren == int(deb_data["anzahl_debitoren"].max()),
                        alt.value("#16A34A"),
                        alt.value("#4ADE80"),
                    ),
                    tooltip=tooltip_fields2,
                ).properties(height=360)

                text2 = bars2.mark_text(
                    align="left", dx=4, fontSize=10, color="#475569"
                ).encode(text="anzahl_debitoren:Q")

                st.altair_chart((bars2 + text2).configure_view(strokeWidth=0), use_container_width=True)
            else:
                st.info("Keine Endkundendaten verfügbar.")

    except ImportError:
        st.info("Altair nicht installiert — Charts werden übersprungen.")


# ── Abschnitt: Verknüpfungsstatistik ─────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.5rem">
  <span class="section-title">🔗 Verknüpfungsstatistik (4-Schritt-Kette)</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

if not statistik.empty:
    anzeige_stat = statistik[["kennzahl", "wert"]].copy()
    anzeige_stat.columns = ["Kennzahl", "Wert"]
    anzeige_stat["Wert"] = anzeige_stat["Wert"].astype(str)
    st.dataframe(
        anzeige_stat,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Kennzahl": st.column_config.TextColumn("Kennzahl", width="large"),
            "Wert":     st.column_config.TextColumn("Wert",     width="small"),
        },
    )
else:
    st.info("Keine Statistik-Daten vorhanden.")


# ── Abschnitt: Kreditor-Übersicht ─────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.5rem">
  <span class="section-title">🏢 Kreditor-Übersicht</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

if not uebersicht.empty:
    anzeige_spalten = [c for c in [
        "kreditor", "kreditor_name", "offener_betrag_summe",
        "anzahl_rohteile", "anzahl_fertigteile", "anzahl_debitoren",
        "aktualisiert_am"
    ] if c in uebersicht.columns]

    anz = uebersicht[anzeige_spalten].copy().sort_values("offener_betrag_summe", ascending=False)

    if "aktualisiert_am" in anz.columns:
        anz["aktualisiert_am"] = pd.to_datetime(anz["aktualisiert_am"], errors="coerce").dt.strftime("%d.%m.%Y %H:%M")
    if "offener_betrag_summe" in anz.columns:
        anz["offener_betrag_summe"] = anz["offener_betrag_summe"].apply(fmt_mio)

    anz = anz.rename(columns={
        "kreditor":             "Kreditor-Nr.",
        "kreditor_name":        "Kreditor",
        "offener_betrag_summe": "Offener Betrag",
        "anzahl_rohteile":      "Rohteile",
        "anzahl_fertigteile":   "Fertigteile",
        "anzahl_debitoren":     "Endkunden",
        "aktualisiert_am":      "Stand",
    })

    st.dataframe(anz, use_container_width=True, hide_index=True)

    col_dl, _ = st.columns([1, 4])
    with col_dl:
        st.download_button(
            label="⬇️ Als CSV exportieren",
            data=uebersicht.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
            file_name="kreditor_uebersicht.csv",
            mime="text/csv",
        )
else:
    st.info("Keine Übersichtsdaten vorhanden.")
