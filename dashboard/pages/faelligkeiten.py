import streamlit as st
import sys
import os
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten, lade_ampel_status, speichere_ampel_status, lade_notizen, speichere_notiz

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

# ── Ampel: nur 3 Status (kein Schwarz) ───────────────────────────────────────
# Klick auf bereits aktiven Button → setzt auf "keine" (leer) zurück
AMPEL = {
    "rot":   ("🔴", "Stop / Prüfen"),
    "gelb":  ("🟡", "In Prüfung"),
    "gruen": ("🟢", "Freigegeben"),
}

PAGE_SIZE = 20



# ── Titel & Daten laden ───────────────────────────────────────────────────────
st.title("Fälligkeiten — Was muss wann bezahlt werden?")

# ── Version-Banner: V01 (veraltete Ansicht) ───────────────────────────────────
st.markdown("""
<div style="
    border: 2px solid #9CA3AF;
    border-left: 6px solid #6B7280;
    border-radius: 10px;
    background: repeating-linear-gradient(
        -45deg,
        #F9FAFB, #F9FAFB 12px,
        #F3F4F6 12px, #F3F4F6 24px
    );
    padding: 0;
    margin-bottom: 1.2rem;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
">
    <div style="
        background: #6B7280;
        color: white;
        text-align: center;
        font-weight: 800;
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        padding: 4px 0;
    ">🗂️ &nbsp; VERSION 01 — VERALTETE ANSICHT &nbsp; 🗂️</div>
    <div style="
        background: rgba(255,255,255,0.85);
        padding: 0.75rem 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.8rem;
    ">
        <span style="font-size:1.4rem;">📦</span>
        <div>
            <span style="font-size:0.98rem;font-weight:700;color:#374151;display:block;">
                Dies ist <u>Fälligkeiten Version 01</u> — die ursprüngliche Ansicht.
            </span>
            <span style="font-size:0.85rem;color:#6B7280;">
                Eine überarbeitete Version ist verfügbar: &nbsp;
                <strong style="color:#1F4E79;">→ Fälligkeiten V.02</strong> in der linken Navigation.
            </span>
        </div>
    </div>
    <div style="
        background: #9CA3AF;
        color: white;
        text-align: center;
        font-weight: 700;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        padding: 3px 0;
    ">Diese Seite bleibt zum Vergleich erhalten · Not for productive use</div>
</div>
""", unsafe_allow_html=True)
# ─────────────────────────────────────────────────────────────────────────────

daten        = lade_ergebnis_daten()
detail       = daten["detail"]
nv_raw       = daten.get("nicht_verknuepft", pd.DataFrame())
ampel_status = lade_ampel_status()
notizen      = lade_notizen()  # Alle gespeicherten Notizen laden

if detail.empty:
    st.warning("Keine Detail-Daten geladen.")
    st.stop()

if "nettofaelligkeit" not in detail.columns:
    st.warning(
        "Fälligkeitsdaten sind noch nicht vorhanden. "
        "Bitte auf dem Server die Kernlogik neu ausführen."
    )
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
belege["grund"] = ""
belege["branche"] = ""

if not nv_raw.empty and "nettofaelligkeit" in nv_raw.columns:
    nv = nv_raw.copy()
    nv["nettofaelligkeit"] = pd.to_datetime(nv["nettofaelligkeit"], errors="coerce")
    nv = nv.dropna(subset=["nettofaelligkeit"])
    if not nv.empty:
        nv["debitor_name"] = ""
        nv["verknuepft"] = False
        for c in belege.columns:
            if c not in nv.columns:
                nv[c] = "" if belege[c].dtype == object else 0
        belege = pd.concat([belege, nv[belege.columns]], ignore_index=True)

if belege.empty:
    st.info("Keine Belege mit Fälligkeitsdatum vorhanden.")
    st.stop()

# ── KW berechnen ──────────────────────────────────────────────────────────────
heute        = pd.Timestamp.now().normalize()
aktuelle_kw  = heute.isocalendar().week
aktuelles_j  = heute.year

belege["kw"]   = belege["nettofaelligkeit"].dt.isocalendar().week.astype(int)
belege["jahr"] = belege["nettofaelligkeit"].dt.year.astype(int)
belege["kw_label"] = belege.apply(
    lambda r: f"KW {r['kw']:02d} / {r['jahr']}", axis=1
)

# ── Zeitraum-Klassifizierung ──────────────────────────────────────────────────
# Wochengrenzen auf ISO-Basis (Montag–Sonntag) — damit KPI-Karten
# und Zeitraum-Filter deckungsgleich mit dem KW-Filter sind.
heute_montag   = heute - pd.Timedelta(days=heute.weekday())  # Montag dieser KW
naechste_kw    = heute_montag + pd.Timedelta(weeks=1)
in_2_wochen    = heute_montag + pd.Timedelta(weeks=2)
in_3_wochen    = heute_montag + pd.Timedelta(weeks=3)
in_4_wochen    = heute_montag + pd.Timedelta(weeks=4)

def woche_label(d):
    if d < heute_montag:  return "Überfällig"
    if d < naechste_kw:   return "Diese Woche"
    if d < in_2_wochen:   return "Nächste Woche"
    if d < in_3_wochen:   return "In 2 Wochen"
    if d < in_4_wochen:   return "In 3 Wochen"
    return "Später (4+ Wochen)"

WOCHEN_ORDER = ["Überfällig","Diese Woche","Nächste Woche","In 2 Wochen","In 3 Wochen","Später (4+ Wochen)"]
belege["zeitraum"] = belege["nettofaelligkeit"].apply(woche_label)

# ── Ampel-Kennzahlen ──────────────────────────────────────────────────────────
st.markdown("### Ampel-Status Übersicht")
ampel_status_alle = lade_ampel_status()
belege["ampel"] = belege["buchhaltungsbeleg"].astype(str).map(
    lambda b: ampel_status_alle.get(b, "keine")
)
# Ampel-Zählung folgt dem aktiven Zeitraum-Filter (nicht immer Gesamt)
_zf = st.session_state.get("zeitraum_filter", "Alle")
_belege_ampel = belege if _zf == "Alle" else belege[belege["zeitraum"] == _zf]
if _zf != "Alle":
    st.caption(f"🔍 Ampel-Status für Zeitraum: **{_zf}**")

ampel_def = [
    ("rot",   "🔴", "Stop / Prüfen"),
    ("gelb",  "🟡", "In Prüfung"),
    ("gruen", "🟢", "Freigegeben"),
    ("keine", "⚪", "Kein Status"),
]
amp_cols = st.columns(4)
for col_i, (status_key, emoji, label) in enumerate(ampel_def):
    sub = _belege_ampel[_belege_ampel["ampel"] == status_key]
    amp_cols[col_i].metric(
        label=f"{emoji} {label}",
        value=f"{len(sub)} Belege",
        delta=fmt_mio(sub["offener_betrag"].sum()) if len(sub) > 0 else "—",
        delta_color="off",
    )

st.markdown("---")

# ── KPI-Karten (klickbar als Zeitraum-Filter) ─────────────────────────────────
if "zeitraum_filter" not in st.session_state:
    st.session_state["zeitraum_filter"] = "Alle"

st.markdown("### Zahlungen nach Zeitraum")
st.caption("🔗 Kachel anklicken zum Filtern — nochmals klicken zum Zurücksetzen")
wochen_summe = (
    belege.groupby("zeitraum")["offener_betrag"]
    .agg(["sum", "count"])
    .reindex(WOCHEN_ORDER, fill_value=0)
)
kpi_cols = st.columns(len(WOCHEN_ORDER) + 1)
for i, woche in enumerate(WOCHEN_ORDER):
    is_active = st.session_state["zeitraum_filter"] == woche
    kpi_cols[i].metric(
        woche,
        fmt_mio(wochen_summe.loc[woche, "sum"]),
        f"{int(wochen_summe.loc[woche, 'count'])} Belege",
    )
    if kpi_cols[i].button(
        "✓ Aktiv" if is_active else "Filtern",
        key=f"kpi_btn_{woche}",
        use_container_width=True,
    ):
        if is_active:
            st.session_state["zeitraum_filter"] = "Alle"
        else:
            st.session_state["zeitraum_filter"] = woche
            # KW-Filter zurücksetzen, damit Zeitraum-Filter allein greift
            st.session_state["kw_filter_override"] = "Alle"
        st.session_state["faellig_page"] = 0
        st.rerun()
kpi_cols[-1].metric(" ", " ")
if kpi_cols[-1].button(
    "✓ Alle" if st.session_state["zeitraum_filter"] == "Alle" else "Alle",
    key="kpi_btn_alle", use_container_width=True,
):
    st.session_state["zeitraum_filter"] = "Alle"
    st.session_state["faellig_page"] = 0
    st.rerun()

st.markdown("---")

# ── Filter ────────────────────────────────────────────────────────────────────
zeitraum_filter = st.session_state.get("zeitraum_filter", "Alle")
f1, f2, f3, f4 = st.columns(4)

kw_optionen = sorted(belege["kw_label"].unique(), key=lambda x: (int(x.split("/")[1]), int(x.split()[1])))

# KW-Filter: wenn Zeitraum-Filter aktiv ist oder ein Override gesetzt wurde → "Alle"
_kw_override = st.session_state.pop("kw_filter_override", None)
if _kw_override is not None:
    kw_default_idx = 0  # "Alle"
else:
    aktuelle_kw_label = f"KW {aktuelle_kw:02d} / {aktuelles_j}"
    # Nur auf aktuelle KW vorauswählen wenn KEIN Zeitraum-Filter aktiv
    if zeitraum_filter == "Alle" and aktuelle_kw_label in kw_optionen:
        kw_default_idx = (["Alle"] + kw_optionen).index(aktuelle_kw_label)
    else:
        kw_default_idx = 0  # "Alle"

kw_filter = f1.selectbox(
    "Kalenderwoche",
    ["Alle"] + kw_optionen,
    index=kw_default_idx,
)
_kred_liste = ["Alle"] + sorted(belege["kreditor_name"].dropna().unique().tolist())
kreditor_filter = f2.selectbox("Kreditor", _kred_liste)
verknuepfung_filter = f3.selectbox(
    "Verknüpfung",
    ["Alle", "Verknüpft (mit Debitor)", "Nicht verknüpft"],
)

# Optionen für Endkunde / Grund dynamisch laden
all_customers = set()
for val in belege[belege["verknuepft"] == True]["debitor_name"].dropna():
    for name in str(val).split(","):
        name = name.strip()
        if name and name not in ("nan", "NaT", ""):
            all_customers.add(name)
sorted_customers = sorted(all_customers)

all_reasons = sorted(belege[belege["verknuepft"] == False]["grund"].dropna().unique())

if verknuepfung_filter == "Verknüpft (mit Debitor)":
    eg_options = ["Alle"] + sorted_customers
elif verknuepfung_filter == "Nicht verknüpft":
    eg_options = ["Alle"] + all_reasons
else:
    eg_options = ["Alle"] + sorted_customers + all_reasons

endkunde_grund_filter = f4.selectbox("Endkunde / Grund", eg_options)

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
    def _matches_filter(row):
        if row["verknuepft"]:
            return endkunde_grund_filter in str(row["debitor_name"])
        else:
            return endkunde_grund_filter in str(row["grund"])
    belege_filtered = belege_filtered[belege_filtered.apply(_matches_filter, axis=1)]

# ── Sortierung anwenden ──────────────────────────────────────────────────────
# Sortierbare Spalten: name im DF → Anzeigename
SORT_SPALTEN = {
    "nettofaelligkeit": "Fällig am",
    "kreditor_name":    "Kreditor",
    "offener_betrag":   "Betrag",
    "debitor_name":     "Endkunden",
}
if "faellig_sort_col" not in st.session_state:
    st.session_state["faellig_sort_col"] = "nettofaelligkeit"  # Default: nach Datum
    st.session_state["faellig_sort_asc"] = True

belege_filtered = belege_filtered.sort_values(
    st.session_state["faellig_sort_col"],
    ascending=st.session_state["faellig_sort_asc"],
).reset_index(drop=True)
total       = len(belege_filtered)
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

# Seite zurücksetzen bei Filterwechsel
filter_key = f"{zeitraum_filter}|{kw_filter}|{verknuepfung_filter}|{endkunde_grund_filter}"
if st.session_state.get("faellig_last_filter") != filter_key:
    st.session_state["faellig_page"]        = 0
    st.session_state["faellig_last_filter"] = filter_key
    # Sortierung bei Filterwechsel zurücksetzen
    st.session_state["faellig_sort_col"] = "nettofaelligkeit"
    st.session_state["faellig_sort_asc"] = True

cur_page = min(st.session_state.get("faellig_page", 0), total_pages - 1)

# ── Überschrift: dynamisch mit echten KWs ────────────────────────────────────
def _zeitraum_kw_label(zeitraum: str) -> str:
    """Gibt die KW(s) zurück, die dem gewählten Zeitraum entsprechen."""
    if zeitraum == "Alle":
        return ""
    # Alle Belege in diesem Zeitraum → welche KWs sind das?
    subset = belege[belege["zeitraum"] == zeitraum]
    if subset.empty:
        return ""
    kws = subset["nettofaelligkeit"].dt.isocalendar().week.astype(int).unique()
    jahre = subset["nettofaelligkeit"].dt.year.unique()
    kws_sorted = sorted(set(kws))
    if len(kws_sorted) == 0:
        return ""
    elif len(kws_sorted) == 1:
        return f" · KW {kws_sorted[0]:02d}"
    else:
        return f" · KW {kws_sorted[0]:02d}–{kws_sorted[-1]:02d}"

_kw_suffix = _zeitraum_kw_label(zeitraum_filter) if kw_filter == "Alle" else f" | {kw_filter}"
st.subheader(f"Rechnungen — {zeitraum_filter}{_kw_suffix}")
st.caption(
    f"{total} Belege  |  Gesamt: {fmt_eur(belege_filtered['offener_betrag'].sum())}  |  "
    f"Seite {cur_page+1} von {total_pages}"
)

# ── Pagination ────────────────────────────────────────────────────────────────
if total_pages > 1:
    pc1, pc2, pc3 = st.columns([1, 4, 1])
    if pc1.button("◀ Zurück", disabled=(cur_page == 0), key="pg_back"):
        st.session_state["faellig_page"] = cur_page - 1
        st.rerun()
    pc2.markdown(
        f"<div style='text-align:center;padding-top:0.5rem;color:#888;'>"
        f"{cur_page*PAGE_SIZE+1}–{min((cur_page+1)*PAGE_SIZE,total)} von {total}</div>",
        unsafe_allow_html=True,
    )
    if pc3.button("Weiter ▶", disabled=(cur_page >= total_pages - 1), key="pg_next"):
        st.session_state["faellig_page"] = cur_page + 1
        st.rerun()

# ── Sammel-Aktion (Bulk Status Update) ────────────────────────────────────────
with st.expander("⚡ Sammel-Aktionen (Status für alle gefilterten Belege ändern)", expanded=False):
    col_bulk_lbl, col_bulk_btns = st.columns([2, 3])
    with col_bulk_lbl:
        st.markdown("<p style='margin-top:0.4rem;font-weight:bold;font-size:0.95rem;'>Aktion wählen:</p>", unsafe_allow_html=True)
    with col_bulk_btns:
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        if b_col1.button("🔴 Alle Stop", key="bulk_rot", use_container_width=True):
            for _, r in belege_filtered.iterrows():
                speichere_ampel_status(str(r["buchhaltungsbeleg"]), "rot")
            st.toast(f"Status für {len(belege_filtered)} Belege auf ROT gesetzt!", icon="💾")
            st.rerun()
        if b_col2.button("🟡 Alle in Prüfung", key="bulk_gelb", use_container_width=True):
            for _, r in belege_filtered.iterrows():
                speichere_ampel_status(str(r["buchhaltungsbeleg"]), "gelb")
            st.toast(f"Status für {len(belege_filtered)} Belege auf GELB gesetzt!", icon="💾")
            st.rerun()
        if b_col3.button("🟢 Alle Freigeben", key="bulk_gruen", use_container_width=True):
            for _, r in belege_filtered.iterrows():
                speichere_ampel_status(str(r["buchhaltungsbeleg"]), "gruen")
            st.toast(f"Status für {len(belege_filtered)} Belege auf GRÜN gesetzt!", icon="💾")
            st.rerun()
        if b_col4.button("⚪ Alle Zurücksetzen", key="bulk_reset", use_container_width=True):
            for _, r in belege_filtered.iterrows():
                speichere_ampel_status(str(r["buchhaltungsbeleg"]), "keine")
            st.toast(f"Status für {len(belege_filtered)} Belege zurückgesetzt!", icon="💾")
            st.rerun()

st.markdown('<div class="tbl-sep" style="margin-top:0.3rem; margin-bottom:0.7rem;"></div>', unsafe_allow_html=True)

# Wrap table inside a container for perfect alternating colors in CSS
table_container = st.container()

# ── Tabellenkopf mit Sort-Buttons ────────────────────────────────────────────
# Spalten: [Ampel | Fällig am | Beleg | Kreditor | Betrag | Endkunden]
COL_W = [3, 2, 2, 4, 2, 5]
hdr   = table_container.columns(COL_W)

# Ampel + Beleg: nicht sortierbar → statische Beschriftung
hdr[0].markdown('<div class="tbl-header">Ampel</div>', unsafe_allow_html=True)
hdr[2].markdown('<div class="tbl-header">Beleg</div>',  unsafe_allow_html=True)

# Sortierbare Spalten als Buttons
# Aktive Spalte zeigt Pfeil ↑/↓, inaktive zeigen ↕
def _sort_label(df_col, anzeige):
    if st.session_state["faellig_sort_col"] == df_col:
        pfeil = "↑" if st.session_state["faellig_sort_asc"] else "↓"
        return f"{anzeige} {pfeil}"
    return f"{anzeige} ↕"

# [1] Fällig am
if hdr[1].button(_sort_label("nettofaelligkeit", "Fällig am"), key="srt_datum", use_container_width=True):
    if st.session_state["faellig_sort_col"] == "nettofaelligkeit":
        st.session_state["faellig_sort_asc"] = not st.session_state["faellig_sort_asc"]
    else:
        st.session_state["faellig_sort_col"] = "nettofaelligkeit"
        st.session_state["faellig_sort_asc"] = True
    st.session_state["faellig_page"] = 0
    st.rerun()

# [3] Kreditor
if hdr[3].button(_sort_label("kreditor_name", "Kreditor"), key="srt_kreditor", use_container_width=True):
    if st.session_state["faellig_sort_col"] == "kreditor_name":
        st.session_state["faellig_sort_asc"] = not st.session_state["faellig_sort_asc"]
    else:
        st.session_state["faellig_sort_col"] = "kreditor_name"
        st.session_state["faellig_sort_asc"] = True
    st.session_state["faellig_page"] = 0
    st.rerun()

# [4] Betrag
if hdr[4].button(_sort_label("offener_betrag", "Betrag"), key="srt_betrag", use_container_width=True):
    if st.session_state["faellig_sort_col"] == "offener_betrag":
        st.session_state["faellig_sort_asc"] = not st.session_state["faellig_sort_asc"]
    else:
        st.session_state["faellig_sort_col"] = "offener_betrag"
        st.session_state["faellig_sort_asc"] = False  # Betrag: erstmal absteigend
    st.session_state["faellig_page"] = 0
    st.rerun()

# [5] Endkunden / Grund
if hdr[5].button(_sort_label("debitor_name", "Endkunden / Grund"), key="srt_endkunden", use_container_width=True):
    if st.session_state["faellig_sort_col"] == "debitor_name":
        st.session_state["faellig_sort_asc"] = not st.session_state["faellig_sort_asc"]
    else:
        st.session_state["faellig_sort_col"] = "debitor_name"
        st.session_state["faellig_sort_asc"] = True
    st.session_state["faellig_page"] = 0
    st.rerun()

st.markdown('<div class="tbl-sep"></div>', unsafe_allow_html=True)

# ── Tabellenzeilen ────────────────────────────────────────────────────────────
page_start = cur_page * PAGE_SIZE
page_rows  = belege_filtered.iloc[page_start : page_start + PAGE_SIZE]

def _cell(col, text):
    """Zelle mit Ellipsis bei langem Text + Tooltip zum Lesen."""
    import re
    plain = re.sub(r'<[^>]*>', '', str(text))
    plain = plain.replace('"', '&quot;')
    col.markdown(
        f'<div class="tbl-cell" title="{plain}">{text}</div>',
        unsafe_allow_html=True,
    )

def _notiz_btn(container, typ: str, nid: str, zeilen_idx: int, suffix: str):
    """
    Zeigt einen Notiz-Button (📝 / 💬) und ggf. ein Inline-Eingabefeld.
    Gibt True zurück, wenn danach ein Rerun nötig ist.
    """
    key_open  = f"notiz_open_{typ}_{nid}_{zeilen_idx}_{suffix}"
    hat_notiz = f"{typ}:{nid}" in notizen
    icon      = "💬" if hat_notiz else "📝"
    tooltip   = notizen[f"{typ}:{nid}"]["text"][:80] + "..." if hat_notiz and len(notizen[f"{typ}:{nid}"]["text"]) > 80 else (notizen[f"{typ}:{nid}"]["text"] if hat_notiz else "Notiz hinzufügen")

    if container.button(icon, key=key_open, help=tooltip, use_container_width=False):
        toggle_key = f"notiz_toggle_{typ}_{nid}"
        st.session_state[toggle_key] = not st.session_state.get(toggle_key, False)
        st.rerun()

def _notiz_editor(typ: str, nid: str, label: str):
    """
    Zeigt das Inline-Notiz-Eingabefeld unter einer Zeile an (wenn Toggle aktiv).
    """
    toggle_key = f"notiz_toggle_{typ}_{nid}"
    if not st.session_state.get(toggle_key, False):
        return

    key_nota = f"{typ}:{nid}"
    vorhandene_notiz = notizen.get(key_nota, {}).get("text", "")
    vorhandene_datum = notizen.get(key_nota, {}).get("datum", "")

    with st.container():
        st.markdown(
            f"<div style='background:#f0f4fa;border-left:4px solid #1F4E79;border-radius:6px;padding:0.6rem 0.9rem;margin:0.2rem 0 0.5rem 0;'>"
            f"<span style='font-size:0.8rem;color:#555;font-weight:600;'>📋 Notiz für {label}</span>"
            + (f"<span style='font-size:0.72rem;color:#888;float:right;'>Gespeichert: {vorhandene_datum}</span>" if vorhandene_datum else "")
            + "</div>",
            unsafe_allow_html=True
        )
        neue_notiz = st.text_area(
            label="",
            value=vorhandene_notiz,
            placeholder="Notiz hier eingeben… (leer lassen zum Löschen)",
            height=90,
            key=f"notiz_text_{typ}_{nid}",
            label_visibility="collapsed",
        )
        btn_s, btn_d, btn_c = st.columns([1, 1, 4])
        if btn_s.button("💾 Speichern", key=f"notiz_save_{typ}_{nid}", type="primary"):
            # Nutzer-Name aus Session-State holen falls vorhanden
            autor = "System"
            try:
                if "user" in st.session_state and st.session_state.user:
                    autor = st.session_state.user.get("name", "System")
            except Exception:
                pass
            speichere_notiz(typ, nid, neue_notiz, autor=autor)
            notizen[key_nota] = {"text": neue_notiz, "autor": autor, "datum": "gerade eben"}
            st.session_state[toggle_key] = False
            st.toast(f"Notiz gespeichert!", icon="💾")
            st.rerun()
        if btn_d.button("🗑️ Löschen", key=f"notiz_del_{typ}_{nid}"):
            speichere_notiz(typ, nid, "")
            notizen.pop(key_nota, None)
            st.session_state[toggle_key] = False
            st.toast("Notiz gelöscht!", icon="🗑️")
            st.rerun()

for zeilen_idx, (_, row) in enumerate(page_rows.iterrows()):
    beleg_id       = str(row["buchhaltungsbeleg"])
    kreditor_id    = str(row.get("kreditor", beleg_id))  # Kreditor-Nr als ID
    kreditor_name  = str(row.get("kreditor_name", "—"))
    current_status = ampel_status.get(beleg_id, "keine")

    row_cols = table_container.columns(COL_W)

    # ── Ampel: 3 Buttons eng nebeneinander ───────────────────────────────────
    with row_cols[0]:
        btn_cols = st.columns([1, 1, 1, 2])
        for i, (status_key, (emoji, label)) in enumerate(AMPEL.items()):
            is_active = (current_status == status_key)
            if btn_cols[i].button(
                emoji,
                key=f"ampel_{beleg_id}_{status_key}",
                type="primary" if is_active else "secondary",
                help=f"{label} (nochmals klicken zum Zurücksetzen)" if is_active else label,
                use_container_width=False,
            ):
                new_status = "keine" if is_active else status_key
                speichere_ampel_status(beleg_id, new_status)
                ampel_status[beleg_id] = new_status
                st.toast(
                    f"{'Status entfernt' if new_status == 'keine' else label} — Beleg {beleg_id}",
                    icon="💾",
                )
                st.rerun()

    _cell(row_cols[1], row["nettofaelligkeit"].strftime("%d.%m.%Y"))

    # ── Belegnummer + Notiz-Button ────────────────────────────────────────────
    with row_cols[2]:
        b_c1, b_c2 = st.columns([3, 1])
        _cell(b_c1, f"<code>{beleg_id}</code>")
        _notiz_btn(b_c2, "beleg", beleg_id, zeilen_idx, "b")

    # ── Kreditor + Notiz-Button ───────────────────────────────────────────────
    with row_cols[3]:
        k_c1, k_c2 = st.columns([4, 1])
        _cell(k_c1, kreditor_name)
        _notiz_btn(k_c2, "kreditor", kreditor_id, zeilen_idx, "k")

    _cell(row_cols[4], fmt_eur(row["offener_betrag"]))

    # ── Endkunde / Grund + Notiz-Button ──────────────────────────────────────
    with row_cols[5]:
        if row.get("verknuepft", True):
            endkunden_val = str(row.get("debitor_name", ""))
            endkunden_txt = endkunden_val if endkunden_val not in ("", "nan") else "—"
            e_c1, e_c2 = st.columns([4, 1])
            _cell(e_c1, endkunden_txt)
            if endkunden_txt != "—":
                _notiz_btn(e_c2, "endkunde", endkunden_txt, zeilen_idx, "e")
        else:
            grund   = str(row.get("grund", ""))
            branche = str(row.get("branche", ""))
            tag = grund
            if branche and branche not in ("", "nan"):
                tag += f" · {branche}"
            _cell(row_cols[5], f'<span style="color:#999;font-style:italic">{tag}</span>')

    # ── Inline-Notiz-Editoren (werden nur angezeigt wenn Toggle aktiv) ────────
    _notiz_editor("beleg",    beleg_id,    f"Beleg {beleg_id}")
    _notiz_editor("kreditor", kreditor_id, kreditor_name)
    if row.get("verknuepft", True):
        endkunden_val = str(row.get("debitor_name", ""))
        if endkunden_val not in ("", "nan", "—"):
            _notiz_editor("endkunde", endkunden_val, endkunden_val)


st.markdown('<div class="tbl-sep" style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)

# ── Aufschlüsselung & Kreuz-Aufschlüsselung ──────────────────────────────────
st.markdown("---")
st.subheader("Auswertungen")

tab_kred, tab_kreuz = st.tabs(["Aufschlüsselung pro Kreditor", "Kreuz-Aufschlüsselung: Kreditor × Endkunde/Grund"])

with tab_kred:
    if not belege_filtered.empty:
        kred_summe = (
            belege_filtered.groupby("kreditor_name")
            .agg(
                Betrag =("offener_betrag",   "sum"),
                Belege =("buchhaltungsbeleg","count"),
            )
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

        belege_filtered_pivot = belege_filtered.copy()
        belege_filtered_pivot["endkunde_grund"] = belege_filtered_pivot.apply(get_endkunde_grund, axis=1)

        try:
            pivot_df = belege_filtered_pivot.pivot_table(
                index="kreditor_name",
                columns="endkunde_grund",
                values="offener_betrag",
                aggfunc="sum",
                fill_value=0.0
            )
            
            # Gesamtspalte und Gesamtzeile hinzufügen
            pivot_df["Gesamt"] = pivot_df.sum(axis=1)
            pivot_df.loc["Gesamt"] = pivot_df.sum(axis=0)

            # Formatieren der Beträge
            pivot_fmt = pivot_df.map(fmt_eur)
            pivot_fmt = pivot_fmt.reset_index().rename(columns={"kreditor_name": "Kreditor"})
            
            st.dataframe(pivot_fmt, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Fehler bei der Tabellen-Generierung: {e}")
    else:
        st.info("Keine Daten verfügbar.")

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "⬇️  Fälligkeiten als CSV",
    data=belege_filtered.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="faelligkeiten.csv",
    mime="text/csv",
)
