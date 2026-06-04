"""
Fälligkeiten – Version 02
Gleiche Funktionalität wie faelligkeiten.py, Design passend zu Dashboard W1.
"""
import streamlit as st
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten, lade_ampel_status, speichere_ampel_status

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --nzwl-blue:      #1F4E79;
    --nzwl-blue-mid:  #2E75B6;
    --nzwl-blue-light:#D6E4F0;
    --nzwl-green:     #16A34A;
    --nzwl-red:       #DC2626;
    --nzwl-amber:     #D97706;
    --nzwl-surface:   #F8FAFC;
    --nzwl-card:      #FFFFFF;
    --nzwl-border:    #E2E8F0;
    --nzwl-text:      #1E293B;
    --nzwl-muted:     #64748B;
}

/* ── Page Hero ── */
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
.page-hero h1 { font-size: 1.55rem; font-weight: 800; margin: 0; letter-spacing:-0.01em; }
.page-hero p  { font-size: 0.85rem; opacity: 0.75; margin: 0.25rem 0 0; }
.hero-badge {
    background: rgba(255,255,255,0.15);
    border-radius: 8px;
    padding: 0.4rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 600;
    white-space: nowrap;
    text-align: center;
}
.hero-badge small {
    display: block;
    opacity: 0.65;
    font-size: 0.67rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.15rem;
}

/* ── Section Header ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 1.5rem 0 0.8rem;
}
.section-header-line { flex: 1; height: 1px; background: var(--nzwl-border); }
.section-title {
    font-size: 0.95rem; font-weight: 700;
    color: var(--nzwl-blue);
    text-transform: uppercase; letter-spacing: 0.08em;
    white-space: nowrap;
}

/* ── Ampel-Karten ── */
.ampel-card {
    border-radius: 10px;
    padding: 0.9rem 1rem 0.8rem;
    border: 1.5px solid var(--nzwl-border);
    background: var(--nzwl-card);
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    transition: transform 0.15s ease;
}
.ampel-card:hover { transform: translateY(-2px); }
.ampel-card.rot   { border-color: #FCA5A5; background: #FEF2F2; }
.ampel-card.gelb  { border-color: #FCD34D; background: #FFFBEB; }
.ampel-card.gruen { border-color: #86EFAC; background: #F0FDF4; }
.ampel-card.keine { border-color: var(--nzwl-border); background: var(--nzwl-surface); }
.ampel-icon { font-size: 1.5rem; line-height: 1; }
.ampel-label {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--nzwl-muted); margin: 0.25rem 0 0.1rem;
}
.ampel-count { font-size: 1.3rem; font-weight: 800; color: var(--nzwl-blue); }
.ampel-amount { font-size: 0.78rem; color: var(--nzwl-muted); margin-top: 0.1rem; }

/* ── Zeitraum-Kacheln ── */
.zeit-card {
    border-radius: 10px;
    padding: 0.75rem 0.8rem 0.65rem;
    text-align: center;
    border: 1.5px solid var(--nzwl-border);
    background: var(--nzwl-card);
    transition: all 0.18s ease;
}
.zeit-card:hover { border-color: var(--nzwl-blue-mid); box-shadow: 0 3px 10px rgba(31,78,121,0.1); }
.zeit-card.active  { background: var(--nzwl-blue); border-color: var(--nzwl-blue); }
.zeit-card.active  .zeit-label { color: rgba(255,255,255,0.7) !important; }
.zeit-card.active  .zeit-value { color: #fff !important; }
.zeit-card.active  .zeit-count { color: rgba(255,255,255,0.65) !important; }
.zeit-card.ueberfaellig { border-color: #FCA5A5; background: #FEF2F2; }
.zeit-card.ueberfaellig .zeit-value { color: var(--nzwl-red) !important; }
.zeit-label {
    font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.07em; color: var(--nzwl-muted); margin-bottom: 0.2rem;
}
.zeit-value {
    font-size: 1rem; font-weight: 800; color: var(--nzwl-blue);
    letter-spacing: -0.01em; line-height: 1.2;
}
.zeit-count { font-size: 0.72rem; color: var(--nzwl-muted); margin-top: 0.1rem; }

/* ── Filter-Badge ── */
.filter-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--nzwl-blue);
    color: white;
    border-radius: 99px;
    padding: 0.2rem 0.85rem;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    margin-bottom: 0.5rem;
}

/* ── Bulk-Action-Panel ── */
.bulk-panel {
    background: var(--nzwl-surface);
    border: 1px solid var(--nzwl-border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    margin-bottom: 0.8rem;
}

/* ── Tabellen-Header ── */
.tbl-header-w1 {
    font-size: 0.73rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--nzwl-muted);
    padding: 0.3rem 0.4rem 0.3rem;
}
.tbl-sep-w1 { border-top: 2px solid var(--nzwl-blue-light); margin: 0.2rem 0 0.3rem; }

/* ── Tabellenzellen ── */
.tbl-cell-w1 {
    font-size: 0.87rem;
    padding: 0.22rem 0.4rem;
    line-height: 1.4;
    display: flex;
    align-items: center;
    min-height: 2.9rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 100%;
}

/* ── Datum-Badge ── */
.datum-badge {
    display: inline-block;
    background: var(--nzwl-blue-light);
    color: var(--nzwl-blue);
    border-radius: 6px;
    padding: 0.1rem 0.55rem;
    font-size: 0.82rem;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
}
.datum-badge.overdue {
    background: #FEE2E2;
    color: var(--nzwl-red);
}
.datum-badge.soon {
    background: #FEF3C7;
    color: var(--nzwl-amber);
}

/* ── Zebra + Hover ── */
div[data-testid="element-container"]:nth-child(even)
  div[data-testid="stHorizontalBlock"]:has(.tbl-cell-w1) {
    background: rgba(31,78,121,0.04) !important;
    border-radius: 6px;
}
div[data-testid="stHorizontalBlock"]:has(.tbl-cell-w1):hover {
    background: rgba(31,78,121,0.08) !important;
    transition: background 0.15s ease !important;
}

/* ── Paginierungs-Leiste ── */
.page-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    padding: 0.5rem 0;
    font-size: 0.85rem;
    color: var(--nzwl-muted);
}

/* ── Ampel-Buttons: inaktiv grau, aktiv leuchtend ── */
div[data-testid="stHorizontalBlock"]:has(.tbl-cell-w1)
  > div[data-testid="stColumn"]:first-child
  div[data-testid="stButton"] button {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0.1rem 0.2rem !important;
    min-height: unset !important;
    font-size: 1.3rem !important;
    line-height: 1 !important;
    transition: filter 0.18s ease, opacity 0.18s ease, box-shadow 0.18s ease !important;
}
/* Inaktiv → ausgegraut */
div[data-testid="stHorizontalBlock"]:has(.tbl-cell-w1)
  > div[data-testid="stColumn"]:first-child
  div[data-testid="stButton"] button[kind="secondary"] {
    filter: grayscale(100%) opacity(0.30) !important;
}
div[data-testid="stHorizontalBlock"]:has(.tbl-cell-w1)
  > div[data-testid="stColumn"]:first-child
  div[data-testid="stButton"] button[kind="secondary"]:hover {
    filter: grayscale(60%) opacity(0.60) !important;
}
/* Aktiv → volle Farbe + Leuchten */
div[data-testid="stHorizontalBlock"]:has(.tbl-cell-w1)
  > div[data-testid="stColumn"]:first-child
  div[data-testid="stButton"] button[kind="primary"] {
    filter: none !important;
    opacity: 1 !important;
    background: transparent !important;
    box-shadow: 0 0 8px 2px rgba(255,255,255,0.5),
                0 0 14px 4px rgba(100,200,100,0.35) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)


# ── Formatierung ──────────────────────────────────────────────────────────────
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


AMPEL = {
    "rot":   ("🔴", "Stop / Prüfen"),
    "gelb":  ("🟡", "In Prüfung"),
    "gruen": ("🟢", "Freigegeben"),
}
PAGE_SIZE = 20


# ── Daten laden ───────────────────────────────────────────────────────────────
daten        = lade_ergebnis_daten()
detail       = daten["detail"]
nv_raw       = daten.get("nicht_verknuepft", pd.DataFrame())
ampel_status = lade_ampel_status()

if detail.empty:
    st.warning("⚠️ Keine Detail-Daten geladen.")
    st.stop()
if "nettofaelligkeit" not in detail.columns:
    st.warning("ℹ️ Fälligkeitsdaten noch nicht vorhanden — bitte Kernlogik auf dem Server ausführen.")
    st.stop()

df = detail.copy()
df["nettofaelligkeit"] = pd.to_datetime(df["nettofaelligkeit"], errors="coerce")
df = df.dropna(subset=["nettofaelligkeit"])

# Pro Buchhaltungsbeleg eine Zeile
belege = df.groupby("buchhaltungsbeleg", as_index=False).agg({
    "kreditor_name":    "first",
    "kreditor":         "first",
    "offener_betrag":   "first",
    "nettofaelligkeit": "first",
    "debitor_name": lambda x: ", ".join(sorted({
        teil.strip()
        for v in x.dropna()
        for teil in str(v).split(",")
        if teil.strip() and teil.strip() not in ("nan", "NaT", "")
    })),
})
belege["verknuepft"] = True
belege["grund"]      = ""
belege["branche"]    = ""

if not nv_raw.empty and "nettofaelligkeit" in nv_raw.columns:
    nv = nv_raw.copy()
    nv["nettofaelligkeit"] = pd.to_datetime(nv["nettofaelligkeit"], errors="coerce")
    nv = nv.dropna(subset=["nettofaelligkeit"])
    if not nv.empty:
        nv["debitor_name"] = ""
        nv["verknuepft"]   = False
        for c in belege.columns:
            if c not in nv.columns:
                nv[c] = "" if belege[c].dtype == object else 0
        belege = pd.concat([belege, nv[belege.columns]], ignore_index=True)

if belege.empty:
    st.info("Keine Belege mit Fälligkeitsdatum vorhanden.")
    st.stop()

# ── KW + Zeitraum ─────────────────────────────────────────────────────────────
heute        = pd.Timestamp.now().normalize()
aktuelle_kw  = heute.isocalendar().week
aktuelles_j  = heute.year
heute_montag = heute - pd.Timedelta(days=heute.weekday())
naechste_kw  = heute_montag + pd.Timedelta(weeks=1)
in_2_wochen  = heute_montag + pd.Timedelta(weeks=2)
in_3_wochen  = heute_montag + pd.Timedelta(weeks=3)
in_4_wochen  = heute_montag + pd.Timedelta(weeks=4)

def woche_label(d):
    if d < heute_montag:  return "Überfällig"
    if d < naechste_kw:   return "Diese Woche"
    if d < in_2_wochen:   return "Nächste Woche"
    if d < in_3_wochen:   return "In 2 Wochen"
    if d < in_4_wochen:   return "In 3 Wochen"
    return "Später (4+ Wochen)"

WOCHEN_ORDER = ["Überfällig", "Diese Woche", "Nächste Woche",
                "In 2 Wochen", "In 3 Wochen", "Später (4+ Wochen)"]

belege["kw"]       = belege["nettofaelligkeit"].dt.isocalendar().week.astype(int)
belege["jahr"]     = belege["nettofaelligkeit"].dt.year.astype(int)
belege["kw_label"] = belege.apply(lambda r: f"KW {r['kw']:02d} / {r['jahr']}", axis=1)
belege["zeitraum"] = belege["nettofaelligkeit"].apply(woche_label)
belege["ampel"]    = belege["buchhaltungsbeleg"].astype(str).map(
    lambda b: ampel_status.get(b, "keine")
)

# ── Zeitstempel ───────────────────────────────────────────────────────────────
zeitstempel = "—"
if not detail.empty and "aktualisiert_am" in detail.columns:
    try:
        ts = pd.to_datetime(detail["aktualisiert_am"]).max()
        zeitstempel = ts.strftime("%d.%m.%Y, %H:%M Uhr")
    except Exception:
        pass

# ── Page Hero ─────────────────────────────────────────────────────────────────
total_betrag = belege["offener_betrag"].sum()
st.markdown(f"""
<div class="page-hero">
  <div>
    <h1>📅 Fälligkeiten – Version 02</h1>
    <p>Was muss wann bezahlt werden? · NZWL Leipzig &amp; ZWL Slovakia</p>
  </div>
  <div style="display:flex;gap:0.8rem;align-items:center;">
    <div class="hero-badge">
      <small>Belege gesamt</small>
      {len(belege):,}
    </div>
    <div class="hero-badge">
      <small>Offenes Volumen</small>
      {fmt_mio(total_betrag)}
    </div>
    <div class="hero-badge">
      <small>Datenstand</small>
      {zeitstempel}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Ampel-Übersicht ───────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-title">🚦 Ampel-Status Übersicht</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

ampel_def = [
    ("rot",   "🔴", "Stop / Prüfen",  "rot"),
    ("gelb",  "🟡", "In Prüfung",     "gelb"),
    ("gruen", "🟢", "Freigegeben",    "gruen"),
    ("keine", "⚪", "Kein Status",    "keine"),
]
amp_cols = st.columns(4)
for col_i, (status_key, emoji, label, css_cls) in enumerate(ampel_def):
    sub = belege[belege["ampel"] == status_key]
    betrag_str = fmt_mio(sub["offener_betrag"].sum()) if len(sub) > 0 else "—"
    amp_cols[col_i].markdown(f"""
    <div class="ampel-card {css_cls}">
        <div class="ampel-icon">{emoji}</div>
        <div class="ampel-label">{label}</div>
        <div class="ampel-count">{len(sub)} Belege</div>
        <div class="ampel-amount">{betrag_str}</div>
    </div>
    """, unsafe_allow_html=True)


# ── Zeitraum-Kacheln ──────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.6rem">
  <span class="section-title">📆 Zahlungen nach Zeitraum</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)
st.caption("Kachel anklicken zum Filtern — nochmals klicken zum Zurücksetzen")

if "zeitraum_filter_w1" not in st.session_state:
    st.session_state["zeitraum_filter_w1"] = "Alle"

wochen_summe = (
    belege.groupby("zeitraum")["offener_betrag"]
    .agg(["sum", "count"])
    .reindex(WOCHEN_ORDER, fill_value=0)
)

kpi_cols = st.columns(len(WOCHEN_ORDER) + 1)
for i, woche in enumerate(WOCHEN_ORDER):
    is_active = st.session_state["zeitraum_filter_w1"] == woche
    is_overd  = woche == "Überfällig"

    card_cls = "zeit-card"
    if is_active: card_cls += " active"
    elif is_overd: card_cls += " ueberfaellig"

    count  = int(wochen_summe.loc[woche, "count"])
    summe  = wochen_summe.loc[woche, "sum"]

    kpi_cols[i].markdown(f"""
    <div class="{card_cls}">
        <div class="zeit-label">{woche}</div>
        <div class="zeit-value">{fmt_mio(summe)}</div>
        <div class="zeit-count">{count} Belege</div>
    </div>
    """, unsafe_allow_html=True)

    btn_label = "✓ Aktiv" if is_active else "Filtern"
    btn_type  = "primary" if is_active else "secondary"
    if kpi_cols[i].button(btn_label, key=f"w1_zeit_{woche}",
                          use_container_width=True, type=btn_type):
        if is_active:
            st.session_state["zeitraum_filter_w1"] = "Alle"
        else:
            st.session_state["zeitraum_filter_w1"] = woche
            st.session_state["w1_kw_override"] = "Alle"
        st.session_state["faellig_w1_page"] = 0
        st.rerun()

# Alle-Kachel
kpi_cols[-1].markdown("""
<div class="zeit-card" style="border-style:dashed;">
    <div class="zeit-label">Gesamt</div>
    <div class="zeit-value">Alle</div>
    <div class="zeit-count">&nbsp;</div>
</div>
""", unsafe_allow_html=True)
if kpi_cols[-1].button(
    "✓ Alle" if st.session_state["zeitraum_filter_w1"] == "Alle" else "Alle",
    key="w1_zeit_alle", use_container_width=True,
):
    st.session_state["zeitraum_filter_w1"] = "Alle"
    st.session_state["faellig_w1_page"] = 0
    st.rerun()

zeitraum_filter = st.session_state["zeitraum_filter_w1"]
if zeitraum_filter != "Alle":
    st.markdown(f'<div class="filter-badge">🔍 Filter aktiv: {zeitraum_filter}</div>',
                unsafe_allow_html=True)


# ── Filter-Zeile ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.2rem">
  <span class="section-title">🔎 Filter &amp; Suche</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

f1, f2, f3, f4 = st.columns(4)

kw_optionen  = sorted(belege["kw_label"].unique(),
                       key=lambda x: (int(x.split("/")[1]), int(x.split()[1])))
_kw_override = st.session_state.pop("w1_kw_override", None)
if _kw_override is not None:
    kw_default_idx = 0
else:
    aktuelle_kw_label = f"KW {aktuelle_kw:02d} / {aktuelles_j}"
    if zeitraum_filter == "Alle" and aktuelle_kw_label in kw_optionen:
        kw_default_idx = (["Alle"] + kw_optionen).index(aktuelle_kw_label)
    else:
        kw_default_idx = 0

kw_filter           = f1.selectbox("📅 Kalenderwoche", ["Alle"] + kw_optionen, index=kw_default_idx)
_kred_liste         = ["Alle"] + sorted(belege["kreditor_name"].dropna().unique().tolist())
kreditor_filter     = f2.selectbox("🏢 Kreditor", _kred_liste)
verknuepfung_filter = f3.selectbox("🔗 Verknüpfung",
                                    ["Alle", "Verknüpft (mit Debitor)", "Nicht verknüpft"])

all_customers = set()
for val in belege[belege["verknuepft"] == True]["debitor_name"].dropna():
    for name in str(val).split(","):
        name = name.strip()
        if name and name not in ("nan", "NaT", ""):
            all_customers.add(name)
sorted_customers = sorted(all_customers)
all_reasons      = sorted(belege[belege["verknuepft"] == False]["grund"].dropna().unique())

if verknuepfung_filter == "Verknüpft (mit Debitor)":
    eg_options = ["Alle"] + sorted_customers
elif verknuepfung_filter == "Nicht verknüpft":
    eg_options = ["Alle"] + all_reasons
else:
    eg_options = ["Alle"] + sorted_customers + all_reasons

endkunde_grund_filter = f4.selectbox("👤 Endkunde / Grund", eg_options)

# Filter anwenden
belege_filtered = belege.copy()
if zeitraum_filter != "Alle":
    belege_filtered = belege_filtered[belege_filtered["zeitraum"] == zeitraum_filter]
if kw_filter != "Alle":
    belege_filtered = belege_filtered[belege_filtered["kw_label"] == kw_filter]
if kreditor_filter != "Alle":
    belege_filtered = belege_filtered[belege_filtered["kreditor_name"] == kreditor_filter]
if verknuepfung_filter == "Verknüpft (mit Debitor)":
    belege_filtered = belege_filtered[belege_filtered["verknuepft"] == True]
elif verknuepfung_filter == "Nicht verknüpft":
    belege_filtered = belege_filtered[belege_filtered["verknuepft"] == False]
if endkunde_grund_filter != "Alle":
    def _matches(row):
        if row["verknuepft"]:
            return endkunde_grund_filter in str(row["debitor_name"])
        else:
            return endkunde_grund_filter in str(row["grund"])
    belege_filtered = belege_filtered[belege_filtered.apply(_matches, axis=1)]


# ── Sortierung ────────────────────────────────────────────────────────────────
SORT_SPALTEN = {
    "nettofaelligkeit": "Fällig am",
    "kreditor_name":    "Kreditor",
    "offener_betrag":   "Betrag",
    "debitor_name":     "Endkunden",
}
if "faellig_w1_sort_col" not in st.session_state:
    st.session_state["faellig_w1_sort_col"] = "nettofaelligkeit"
    st.session_state["faellig_w1_sort_asc"] = True

belege_filtered = belege_filtered.sort_values(
    st.session_state["faellig_w1_sort_col"],
    ascending=st.session_state["faellig_w1_sort_asc"],
).reset_index(drop=True)

total       = len(belege_filtered)
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

# Seite zurücksetzen
filter_key = f"{zeitraum_filter}|{kw_filter}|{verknuepfung_filter}|{endkunde_grund_filter}"
if st.session_state.get("faellig_w1_last_filter") != filter_key:
    st.session_state["faellig_w1_page"]        = 0
    st.session_state["faellig_w1_last_filter"] = filter_key
    st.session_state["faellig_w1_sort_col"]    = "nettofaelligkeit"
    st.session_state["faellig_w1_sort_asc"]    = True

cur_page = min(st.session_state.get("faellig_w1_page", 0), total_pages - 1)


# ── Tabellen-Header ───────────────────────────────────────────────────────────
def _zeitraum_kw_label(zeitraum: str) -> str:
    if zeitraum == "Alle": return ""
    subset = belege[belege["zeitraum"] == zeitraum]
    if subset.empty: return ""
    kws = sorted(set(subset["nettofaelligkeit"].dt.isocalendar().week.astype(int).unique()))
    if len(kws) == 1: return f" · KW {kws[0]:02d}"
    return f" · KW {kws[0]:02d}–{kws[-1]:02d}"

_kw_suffix = _zeitraum_kw_label(zeitraum_filter) if kw_filter == "Alle" else f" | {kw_filter}"

st.markdown(f"""
<div class="section-header" style="margin-top:1.4rem">
  <span class="section-title">📋 Rechnungen — {zeitraum_filter}{_kw_suffix}</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

# Info-Zeile: Treffer + Summe
info_col, pgbar_col = st.columns([3, 2])
info_col.caption(
    f"**{total} Belege** gefunden  ·  "
    f"Gesamt: **{fmt_eur(belege_filtered['offener_betrag'].sum())}**"
)

# ── Sammel-Aktionen ───────────────────────────────────────────────────────────
with st.expander("⚡ Sammel-Aktionen (Status für alle gefilterten Belege)", expanded=False):
    st.markdown('<div class="bulk-panel">', unsafe_allow_html=True)
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    if b_col1.button("🔴 Alle: Stop", key="w1_bulk_rot", use_container_width=True):
        for _, r in belege_filtered.iterrows():
            speichere_ampel_status(str(r["buchhaltungsbeleg"]), "rot")
        st.toast(f"{len(belege_filtered)} Belege → ROT", icon="💾")
        st.rerun()
    if b_col2.button("🟡 Alle: In Prüfung", key="w1_bulk_gelb", use_container_width=True):
        for _, r in belege_filtered.iterrows():
            speichere_ampel_status(str(r["buchhaltungsbeleg"]), "gelb")
        st.toast(f"{len(belege_filtered)} Belege → GELB", icon="💾")
        st.rerun()
    if b_col3.button("🟢 Alle: Freigeben", key="w1_bulk_gruen", use_container_width=True):
        for _, r in belege_filtered.iterrows():
            speichere_ampel_status(str(r["buchhaltungsbeleg"]), "gruen")
        st.toast(f"{len(belege_filtered)} Belege → GRÜN", icon="💾")
        st.rerun()
    if b_col4.button("⚪ Alle: Zurücksetzen", key="w1_bulk_reset", use_container_width=True):
        for _, r in belege_filtered.iterrows():
            speichere_ampel_status(str(r["buchhaltungsbeleg"]), "keine")
        st.toast(f"{len(belege_filtered)} Belege zurückgesetzt", icon="💾")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Pagination oben ───────────────────────────────────────────────────────────
if total_pages > 1:
    pc1, pc2, pc3 = st.columns([1, 4, 1])
    if pc1.button("◀ Zurück", disabled=(cur_page == 0), key="w1_pg_back"):
        st.session_state["faellig_w1_page"] = cur_page - 1
        st.rerun()
    pc2.markdown(
        f"<div class='page-bar'>{cur_page*PAGE_SIZE+1}–"
        f"{min((cur_page+1)*PAGE_SIZE, total)} von {total} Belegen "
        f"(Seite {cur_page+1}/{total_pages})</div>",
        unsafe_allow_html=True,
    )
    if pc3.button("Weiter ▶", disabled=(cur_page >= total_pages - 1), key="w1_pg_next"):
        st.session_state["faellig_w1_page"] = cur_page + 1
        st.rerun()

st.markdown('<div class="tbl-sep-w1"></div>', unsafe_allow_html=True)

# ── Tabellenkopf mit Sort-Buttons ─────────────────────────────────────────────
COL_W = [3, 2, 2, 4, 2, 5]
table_container = st.container()
hdr = table_container.columns(COL_W)

hdr[0].markdown('<div class="tbl-header-w1">Ampel</div>',  unsafe_allow_html=True)
hdr[2].markdown('<div class="tbl-header-w1">Beleg-Nr.</div>', unsafe_allow_html=True)

def _sort_label(df_col, anzeige):
    if st.session_state["faellig_w1_sort_col"] == df_col:
        pfeil = "↑" if st.session_state["faellig_w1_sort_asc"] else "↓"
        return f"{anzeige} {pfeil}"
    return f"{anzeige} ↕"

def _sort_click(df_col, default_asc=True):
    if st.session_state["faellig_w1_sort_col"] == df_col:
        st.session_state["faellig_w1_sort_asc"] = not st.session_state["faellig_w1_sort_asc"]
    else:
        st.session_state["faellig_w1_sort_col"] = df_col
        st.session_state["faellig_w1_sort_asc"] = default_asc
    st.session_state["faellig_w1_page"] = 0
    st.rerun()

if hdr[1].button(_sort_label("nettofaelligkeit", "Fällig am"),
                 key="w1_srt_datum", use_container_width=True):
    _sort_click("nettofaelligkeit", True)
if hdr[3].button(_sort_label("kreditor_name", "Kreditor"),
                 key="w1_srt_kred", use_container_width=True):
    _sort_click("kreditor_name", True)
if hdr[4].button(_sort_label("offener_betrag", "Betrag"),
                 key="w1_srt_betrag", use_container_width=True):
    _sort_click("offener_betrag", False)
if hdr[5].button(_sort_label("debitor_name", "Endkunden / Grund"),
                 key="w1_srt_endkunden", use_container_width=True):
    _sort_click("debitor_name", True)

st.markdown('<div class="tbl-sep-w1"></div>', unsafe_allow_html=True)


# ── Tabellenzeilen ────────────────────────────────────────────────────────────
def _cell(col, text, extra_cls=""):
    import re
    plain = re.sub(r'<[^>]*>', '', str(text)).replace('"', '&quot;')
    col.markdown(
        f'<div class="tbl-cell-w1 {extra_cls}" title="{plain}">{text}</div>',
        unsafe_allow_html=True,
    )

def _datum_badge(d: pd.Timestamp) -> str:
    """Datum als farbiges Badge je nach Dringlichkeit."""
    date_str = d.strftime("%d.%m.%Y")
    if d < heute_montag:
        return f'<span class="datum-badge overdue">⚠ {date_str}</span>'
    if d < naechste_kw:
        return f'<span class="datum-badge soon">⏰ {date_str}</span>'
    return f'<span class="datum-badge">{date_str}</span>'

page_start = cur_page * PAGE_SIZE
page_rows  = belege_filtered.iloc[page_start : page_start + PAGE_SIZE]

for _, row in page_rows.iterrows():
    beleg_id       = str(row["buchhaltungsbeleg"])
    current_status = ampel_status.get(beleg_id, "keine")

    row_cols = table_container.columns(COL_W)

    # Ampel-Buttons
    with row_cols[0]:
        btn_cols = st.columns([1, 1, 1, 2])
        for i, (status_key, (emoji, label)) in enumerate(AMPEL.items()):
            is_active = (current_status == status_key)
            if btn_cols[i].button(
                emoji,
                key=f"w1_ampel_{beleg_id}_{status_key}",
                type="primary" if is_active else "secondary",
                help=f"{label} (klicken zum Zurücksetzen)" if is_active else label,
                use_container_width=False,
            ):
                new_status = "keine" if is_active else status_key
                speichere_ampel_status(beleg_id, new_status)
                ampel_status[beleg_id] = new_status
                st.toast(
                    f"{'Status entfernt' if new_status == 'keine' else label} — {beleg_id}",
                    icon="💾",
                )
                st.rerun()

    # Datum als farbiges Badge
    _cell(row_cols[1], _datum_badge(row["nettofaelligkeit"]))
    _cell(row_cols[2], f"<code>{beleg_id}</code>")
    _cell(row_cols[3], str(row.get("kreditor_name", "—")))
    _cell(row_cols[4], fmt_eur(row["offener_betrag"]))

    if row.get("verknuepft", True):
        endkunden = str(row.get("debitor_name", ""))
        _cell(row_cols[5], endkunden if endkunden not in ("", "nan") else "—")
    else:
        grund   = str(row.get("grund", ""))
        branche = str(row.get("branche", ""))
        tag = grund
        if branche and branche not in ("", "nan"):
            tag += f" · {branche}"
        _cell(row_cols[5], f'<span style="color:#94A3B8;font-style:italic">{tag}</span>')

st.markdown('<div class="tbl-sep-w1" style="margin-top:0.4rem;"></div>', unsafe_allow_html=True)


# ── Auswertungen (Tabs) ───────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.5rem">
  <span class="section-title">📊 Auswertungen</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

tab_kred, tab_kreuz = st.tabs(["Aufschlüsselung pro Kreditor",
                                "Kreuz-Aufschlüsselung: Kreditor × Endkunde/Grund"])

with tab_kred:
    if not belege_filtered.empty:
        kred_summe = (
            belege_filtered.groupby("kreditor_name")
            .agg(Betrag=("offener_betrag", "sum"), Belege=("buchhaltungsbeleg", "count"))
            .sort_values("Betrag", ascending=False)
            .reset_index()
            .rename(columns={"kreditor_name": "Kreditor"})
        )
        kred_summe["Betrag"] = kred_summe["Betrag"].apply(fmt_eur)
        st.dataframe(kred_summe, use_container_width=True, hide_index=True)
    else:
        st.info("Keine Daten verfügbar.")

with tab_kreuz:
    if not belege_filtered.empty:
        def get_endkunde_grund(row):
            if row.get("verknuepft", True):
                val = str(row.get("debitor_name", ""))
                return val if val not in ("", "nan") else "Unbekannt"
            else:
                val = str(row.get("grund", ""))
                return val if val not in ("", "nan") else "Unbekannt"

        bf_pivot = belege_filtered.copy()
        bf_pivot["endkunde_grund"] = bf_pivot.apply(get_endkunde_grund, axis=1)
        try:
            pivot_df = bf_pivot.pivot_table(
                index="kreditor_name", columns="endkunde_grund",
                values="offener_betrag", aggfunc="sum", fill_value=0.0,
            )
            pivot_df["Gesamt"]       = pivot_df.sum(axis=1)
            pivot_df.loc["Gesamt"]   = pivot_df.sum(axis=0)
            pivot_fmt = pivot_df.map(fmt_eur).reset_index().rename(
                columns={"kreditor_name": "Kreditor"}
            )
            st.dataframe(pivot_fmt, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Fehler bei Tabellen-Generierung: {e}")
    else:
        st.info("Keine Daten verfügbar.")


# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.2rem">
  <span class="section-title">⬇️ Export</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

col_dl, _ = st.columns([1, 4])
with col_dl:
    st.download_button(
        label="⬇️ Fälligkeiten als CSV exportieren",
        data=belege_filtered.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
        file_name="faelligkeiten_w1.csv",
        mime="text/csv",
    )
