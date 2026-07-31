"""
Überfällig-Analyse – V.02
Aging-Auswertung der überfälligen Kreditoren-Posten nach Dauer:
  1–30 / 31–60 / 61–90 / > 90 Tage.
Reine Dashboard-View — keine Änderung an der Core-Logik.
Datenquelle & Aufbereitung analog zu faelligkeiten_w1.py.
"""
import streamlit as st
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --nzwl-blue:      #1F4E79;
    --nzwl-blue-mid:  #2E75B6;
    --nzwl-blue-light:#D6E4F0;
    --nzwl-surface:   #F8FAFC;
    --nzwl-card:      #FFFFFF;
    --nzwl-border:    #E2E8F0;
    --nzwl-muted:     #64748B;
}
.page-hero {
    background: linear-gradient(135deg, #1F4E79 0%, #2E75B6 100%);
    border-radius: 14px;
    padding: 1.4rem 1.8rem 1.2rem;
    color: white; margin-bottom: 1.4rem;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 4px 18px rgba(31,78,121,0.22);
}
.page-hero h1 { font-size: 1.55rem; font-weight: 800; margin: 0; letter-spacing:-0.01em; }
.page-hero p  { font-size: 0.85rem; opacity: 0.75; margin: 0.25rem 0 0; }
.hero-badge {
    background: rgba(255,255,255,0.15); border-radius: 8px;
    padding: 0.4rem 0.85rem; font-size: 0.8rem; font-weight: 600;
    white-space: nowrap; text-align: center;
}
.hero-badge small {
    display: block; opacity: 0.65; font-size: 0.67rem;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.15rem;
}
.section-header { display: flex; align-items: center; gap: 0.6rem; margin: 1.5rem 0 0.8rem; }
.section-header-line { flex: 1; height: 1px; background: var(--nzwl-border); }
.section-title {
    font-size: 0.95rem; font-weight: 700; color: var(--nzwl-blue);
    text-transform: uppercase; letter-spacing: 0.08em; white-space: nowrap;
}
/* ── Alters-Kacheln ── */
.age-card {
    border-radius: 10px; padding: 0.8rem 0.8rem 0.7rem; text-align: center;
    border: 1.5px solid var(--nzwl-border); background: var(--nzwl-card);
    transition: all 0.18s ease; margin-bottom: 0.45rem;
    border-top-width: 4px;
}
.age-card:hover { box-shadow: 0 3px 10px rgba(31,78,121,0.12); }
.age-card.gruen  { border-top-color:#16A34A; }
.age-card.gelb   { border-top-color:#D97706; }
.age-card.orange { border-top-color:#EA580C; }
.age-card.rot    { border-top-color:#DC2626; }
.age-card.active { background: var(--nzwl-blue); border-color: var(--nzwl-blue); }
.age-card.active .age-label,
.age-card.active .age-count { color: rgba(255,255,255,0.72) !important; }
.age-card.active .age-value { color: #fff !important; }
.age-label {
    font-size: 0.66rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--nzwl-muted); margin-bottom: 0.25rem;
}
.age-value { font-size: 1.15rem; font-weight: 800; color: var(--nzwl-blue); line-height: 1.2; }
.age-count { font-size: 0.72rem; color: var(--nzwl-muted); margin-top: 0.1rem; }
.age-dot { font-size: 0.9rem; }
/* ── Filter-Badge ── */
.filter-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: var(--nzwl-blue); color: white; border-radius: 99px;
    padding: 0.2rem 0.85rem; font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.04em; margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Formatierung (identisch zu faelligkeiten_w1) ──────────────────────────────
def _fmt_num(value: float, decimals: int = 2) -> str:
    fmt = f"{value:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_eur(betrag: float) -> str:
    return f"{_fmt_num(betrag, 2)} €"

def fmt_mio(betrag: float) -> str:
    abs_b = abs(betrag)
    if abs_b >= 1_000_000_000: return f"{_fmt_num(betrag / 1_000_000_000, 2)} Mrd. €"
    if abs_b >= 1_000_000:     return f"{_fmt_num(betrag / 1_000_000, 2)} M€"
    if abs_b >= 1_000:         return f"{_fmt_num(betrag / 1_000, 1)} T€"
    return fmt_eur(betrag)


# ── Alters-Stufen (Buchhaltungs-Standard 30/60/90) ────────────────────────────
ALTER_ORDER = ["1–30 Tage", "31–60 Tage", "61–90 Tage", "> 90 Tage"]
ALTER_CLS   = {"1–30 Tage": "gruen", "31–60 Tage": "gelb",
               "61–90 Tage": "orange", "> 90 Tage": "rot"}
ALTER_DOT   = {"1–30 Tage": "🟢", "31–60 Tage": "🟡",
               "61–90 Tage": "🟠", "> 90 Tage": "🔴"}

def alter_bucket(tage: int) -> str:
    if tage <= 30: return "1–30 Tage"
    if tage <= 60: return "31–60 Tage"
    if tage <= 90: return "61–90 Tage"
    return "> 90 Tage"


# ── Daten laden ───────────────────────────────────────────────────────────────
daten  = lade_ergebnis_daten()
detail = daten["detail"]
nv_raw = daten.get("nicht_verknuepft", pd.DataFrame())

if detail.empty:
    st.warning("⚠️ Keine Detail-Daten geladen.")
    st.stop()
if "nettofaelligkeit" not in detail.columns:
    st.warning("ℹ️ Fälligkeitsdaten noch nicht vorhanden — bitte Kernlogik auf dem Server ausführen.")
    st.stop()

df = detail.copy()
df["nettofaelligkeit"] = pd.to_datetime(df["nettofaelligkeit"], errors="coerce")
df = df.dropna(subset=["nettofaelligkeit"])

# Pro Buchhaltungsbeleg eine Zeile (Betrag ist je Beleg, nicht je BOM-Zeile)
belege = df.groupby("buchhaltungsbeleg", as_index=False).agg({
    "kreditor_name":    "first",
    "offener_betrag":   "first",
    "nettofaelligkeit": "first",
    "debitor_name": lambda x: ", ".join(sorted({
        teil.strip()
        for v in x.dropna()
        for teil in str(v).split(",")
        if teil.strip() and teil.strip() not in ("nan", "NaT", "")
    })),
})

# Nicht-verknüpfte Belege ergänzen (konsistent mit Fälligkeiten-Seite)
if not nv_raw.empty and "nettofaelligkeit" in nv_raw.columns:
    nv = nv_raw.copy()
    nv["nettofaelligkeit"] = pd.to_datetime(nv["nettofaelligkeit"], errors="coerce")
    nv = nv.dropna(subset=["nettofaelligkeit"])
    if not nv.empty:
        nv["debitor_name"] = ""
        for c in belege.columns:
            if c not in nv.columns:
                nv[c] = "" if belege[c].dtype == object else 0
        belege = pd.concat([belege, nv[belege.columns]], ignore_index=True)

# ── Überfälligkeit berechnen ──────────────────────────────────────────────────
heute = pd.Timestamp.now().normalize()
belege["tage_ueberfaellig"] = (heute - belege["nettofaelligkeit"]).dt.days
ueberfaellig = belege[belege["tage_ueberfaellig"] > 0].copy()

# ── Zeitstempel ───────────────────────────────────────────────────────────────
zeitstempel = "—"
if "aktualisiert_am" in detail.columns:
    try:
        zeitstempel = pd.to_datetime(detail["aktualisiert_am"]).max().strftime("%d.%m.%Y, %H:%M Uhr")
    except Exception:
        pass

# ── Page Hero ─────────────────────────────────────────────────────────────────
gesamt_betrag = ueberfaellig["offener_betrag"].sum()
st.markdown(f"""
<div class="page-hero">
  <div>
    <h1>⏰ Überfällig-Analyse – V.02</h1>
    <p>Wie lange sind Zahlungen schon überfällig? · NZWL Leipzig &amp; ZWL Slovakia</p>
  </div>
  <div style="display:flex;gap:0.8rem;align-items:center;">
    <div class="hero-badge"><small>Überfällige Belege</small>{len(ueberfaellig):,}</div>
    <div class="hero-badge"><small>Überfälliges Volumen</small>{fmt_mio(gesamt_betrag)}</div>
    <div class="hero-badge"><small>Datenstand</small>{zeitstempel}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if ueberfaellig.empty:
    st.success("✅ Aktuell sind keine Posten überfällig.")
    st.stop()

ueberfaellig["alter"] = ueberfaellig["tage_ueberfaellig"].apply(alter_bucket)

# ── Alters-Kacheln ────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-title">📊 Überfälligkeit nach Dauer</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)
st.caption("Kachel anklicken zum Filtern der Tabelle — nochmals klicken zum Zurücksetzen")

if "ua_alter_filter" not in st.session_state:
    st.session_state["ua_alter_filter"] = "Alle"

alter_summe = (
    ueberfaellig.groupby("alter")["offener_betrag"]
    .agg(["sum", "count"])
    .reindex(ALTER_ORDER, fill_value=0)
)

cols = st.columns(len(ALTER_ORDER) + 1)
for i, stufe in enumerate(ALTER_ORDER):
    is_active = st.session_state["ua_alter_filter"] == stufe
    card_cls  = f"age-card {ALTER_CLS[stufe]}" + (" active" if is_active else "")
    count = int(alter_summe.loc[stufe, "count"])
    summe = alter_summe.loc[stufe, "sum"]
    cols[i].markdown(f"""
    <div class="{card_cls}">
        <div class="age-dot">{ALTER_DOT[stufe]}</div>
        <div class="age-label">{stufe}</div>
        <div class="age-value">{fmt_mio(summe)}</div>
        <div class="age-count">{count} Belege</div>
    </div>
    """, unsafe_allow_html=True)
    btn_label = "✓ Aktiv" if is_active else "Filtern"
    btn_type  = "primary" if is_active else "secondary"
    if cols[i].button(btn_label, key=f"ua_age_{stufe}",
                      use_container_width=True, type=btn_type):
        st.session_state["ua_alter_filter"] = "Alle" if is_active else stufe
        st.rerun()

# Gesamt-Kachel
cols[-1].markdown(f"""
<div class="age-card" style="border-top-color:#1F4E79;border-style:dashed;">
    <div class="age-dot">Σ</div>
    <div class="age-label">Gesamt überfällig</div>
    <div class="age-value">{fmt_mio(gesamt_betrag)}</div>
    <div class="age-count">{len(ueberfaellig)} Belege</div>
</div>
""", unsafe_allow_html=True)
if cols[-1].button(
    "✓ Alle" if st.session_state["ua_alter_filter"] == "Alle" else "Alle",
    key="ua_age_alle", use_container_width=True,
):
    st.session_state["ua_alter_filter"] = "Alle"
    st.rerun()

alter_filter = st.session_state["ua_alter_filter"]

# ── Kreditor-Filter ───────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.2rem">
  <span class="section-title">🔎 Filter</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)
f1, f2 = st.columns(2)
kred_liste  = ["Alle"] + sorted(ueberfaellig["kreditor_name"].dropna().unique().tolist())
kred_filter = f1.selectbox("🏢 Kreditor", kred_liste)

# Filter anwenden
gefiltert = ueberfaellig.copy()
if alter_filter != "Alle":
    gefiltert = gefiltert[gefiltert["alter"] == alter_filter]
if kred_filter != "Alle":
    gefiltert = gefiltert[gefiltert["kreditor_name"] == kred_filter]

if alter_filter != "Alle" or kred_filter != "Alle":
    teile = [alter_filter] if alter_filter != "Alle" else []
    if kred_filter != "Alle":
        teile.append(kred_filter)
    st.markdown(
        f'<div class="filter-badge">🔍 Filter aktiv: {" · ".join(teile)}</div>',
        unsafe_allow_html=True,
    )

# ── Detailtabelle ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="section-header" style="margin-top:1.2rem">
  <span class="section-title">📋 Überfällige Belege — {alter_filter}</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)
st.caption(
    f"**{len(gefiltert)} Belege**  ·  Summe: **{fmt_eur(gefiltert['offener_betrag'].sum())}**"
    "  ·  Spaltenkopf klicken zum Sortieren"
)

tabelle = gefiltert.sort_values("tage_ueberfaellig", ascending=False).copy()
tabelle_anzeige = pd.DataFrame({
    "Fällig am":       tabelle["nettofaelligkeit"].dt.date,
    "Tage überfällig": tabelle["tage_ueberfaellig"].astype(int),
    "Stufe":           tabelle["alter"],
    "Beleg-Nr.":       tabelle["buchhaltungsbeleg"].astype(str),
    "Kreditor":        tabelle["kreditor_name"].fillna("—"),
    "Betrag (€)":      tabelle["offener_betrag"].round(2),
    "Endkunde":        tabelle["debitor_name"].replace({"": "—", "nan": "—"}).fillna("—"),
})
st.dataframe(
    tabelle_anzeige,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fällig am":       st.column_config.DateColumn("Fällig am", format="DD.MM.YYYY"),
        "Tage überfällig": st.column_config.NumberColumn("Tage überfällig", format="%d T"),
        "Betrag (€)":      st.column_config.NumberColumn("Betrag (€)", format="%.2f"),
    },
)

# ── Aufschlüsselung pro Kreditor × Alters-Stufe ───────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.4rem">
  <span class="section-title">🏢 Aufschlüsselung: Kreditor × Alters-Stufe</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)

pivot = ueberfaellig.pivot_table(
    index="kreditor_name", columns="alter", values="offener_betrag",
    aggfunc="sum", fill_value=0.0,
)
for stufe in ALTER_ORDER:
    if stufe not in pivot.columns:
        pivot[stufe] = 0.0
pivot = pivot[ALTER_ORDER]
pivot["Gesamt"] = pivot.sum(axis=1)
pivot = pivot.sort_values("Gesamt", ascending=False)
pivot.loc["— Gesamt —"] = pivot.sum(axis=0)

pivot_anzeige = pivot.map(fmt_eur).reset_index().rename(columns={"kreditor_name": "Kreditor"})
st.dataframe(pivot_anzeige, use_container_width=True, hide_index=True)

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section-header" style="margin-top:1.2rem">
  <span class="section-title">⬇️ Export</span>
  <div class="section-header-line"></div>
</div>
""", unsafe_allow_html=True)
export_df = gefiltert[[
    "nettofaelligkeit", "tage_ueberfaellig", "alter",
    "buchhaltungsbeleg", "kreditor_name", "offener_betrag", "debitor_name",
]].sort_values("tage_ueberfaellig", ascending=False)
st.download_button(
    label="⬇️ Überfällige Belege als CSV exportieren",
    data=export_df.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="ueberfaellig_analyse.csv",
    mime="text/csv",
)
