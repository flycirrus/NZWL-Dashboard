import streamlit as st
import sys
import os
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten, lade_ampel_status, speichere_ampel_status

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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.tbl-header { font-size: 0.78rem; font-weight: 700; color: #888;
              text-transform: uppercase; letter-spacing: 0.05em;
              padding-bottom: 0.3rem; }
.tbl-sep    { border-top: 1px solid #e0e0e0; margin: 0.15rem 0 0.25rem 0; }

/* Zebra-Zellen: gleichmäßige Höhe und Zeilenoptik */
.tbl-cell       { font-size: 0.88rem; padding: 0.35rem 0.4rem;
                  line-height: 1.4; border-radius: 3px; }
.tbl-cell.even  { background: rgba(31, 78, 121, 0.05); }
.tbl-cell.odd   { background: transparent; }

/* Inaktive Ampel-Buttons: kein Rahmen, kein Hintergrund — nur das Emoji */
div[data-testid="stButton"] button[kind="secondary"] {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0.05rem 0.15rem !important;
    min-height: unset !important;
    font-size: 1.15rem !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    background: rgba(0, 0, 0, 0.07) !important;
    border-radius: 4px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Titel & Daten laden ───────────────────────────────────────────────────────
st.title("Fälligkeiten — Was muss wann bezahlt werden?")

daten        = lade_ergebnis_daten()
detail       = daten["detail"]
ampel_status = lade_ampel_status()

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
def woche_label(d):
    diff = (d - heute).days
    if diff < 0:    return "Überfällig"
    if diff < 7:    return "Diese Woche"
    if diff < 14:   return "Nächste Woche"
    if diff < 21:   return "In 2 Wochen"
    if diff < 28:   return "In 3 Wochen"
    return "Später (4+ Wochen)"

WOCHEN_ORDER = ["Überfällig","Diese Woche","Nächste Woche","In 2 Wochen","In 3 Wochen","Später (4+ Wochen)"]
belege["zeitraum"] = belege["nettofaelligkeit"].apply(woche_label)

# ── KPI-Karten ────────────────────────────────────────────────────────────────
st.markdown("### Zahlungen nach Zeitraum")
wochen_summe = (
    belege.groupby("zeitraum")["offener_betrag"]
    .agg(["sum","count"])
    .reindex(WOCHEN_ORDER, fill_value=0)
)
kpi_cols = st.columns(len(WOCHEN_ORDER))
for i, woche in enumerate(WOCHEN_ORDER):
    kpi_cols[i].metric(
        woche,
        fmt_mio(wochen_summe.loc[woche, "sum"]),
        f"{int(wochen_summe.loc[woche, 'count'])} Belege",
    )

st.markdown("---")

# ── Filter ────────────────────────────────────────────────────────────────────
f1, f2 = st.columns(2)

# Filter 1: Zeitraum
zeitraum_filter = f1.selectbox(
    "Zeitraum anzeigen",
    ["Alle"] + WOCHEN_ORDER,
)

# Filter 2: Kalenderwoche
kw_optionen = sorted(belege["kw_label"].unique(), key=lambda x: (int(x.split("/")[1]), int(x.split()[1])))
aktuelle_kw_label = f"KW {aktuelle_kw:02d} / {aktuelles_j}"
default_kw = aktuelle_kw_label if aktuelle_kw_label in kw_optionen else "Alle"
kw_filter = f2.selectbox(
    "Kalenderwoche",
    ["Alle"] + kw_optionen,
    index=(["Alle"] + kw_optionen).index(default_kw) if default_kw in ["Alle"] + kw_optionen else 0,
)

# Filter anwenden
belege_filtered = belege.copy()
if zeitraum_filter != "Alle":
    belege_filtered = belege_filtered[belege_filtered["zeitraum"] == zeitraum_filter]
if kw_filter != "Alle":
    belege_filtered = belege_filtered[belege_filtered["kw_label"] == kw_filter]

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
filter_key = f"{zeitraum_filter}|{kw_filter}"
if st.session_state.get("faellig_last_filter") != filter_key:
    st.session_state["faellig_page"]        = 0
    st.session_state["faellig_last_filter"] = filter_key
    # Sortierung bei Filterwechsel zurücksetzen
    st.session_state["faellig_sort_col"] = "nettofaelligkeit"
    st.session_state["faellig_sort_asc"] = True

cur_page = min(st.session_state.get("faellig_page", 0), total_pages - 1)

# ── Überschrift ───────────────────────────────────────────────────────────────
st.subheader(f"Rechnungen — {zeitraum_filter}" + (f" | {kw_filter}" if kw_filter != "Alle" else ""))
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

# ── Tabellenkopf mit Sort-Buttons ────────────────────────────────────────────
# Spalten: [Ampel | Fällig am | Beleg | Kreditor | Betrag | Endkunden]
COL_W = [3, 2, 2, 4, 2, 5]
hdr   = st.columns(COL_W)

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

# [5] Endkunden
if hdr[5].button(_sort_label("debitor_name", "Endkunden"), key="srt_endkunden", use_container_width=True):
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

def _cell(col, text, zeile_gerade: bool = False):
    css = "even" if zeile_gerade else "odd"
    col.markdown(f'<div class="tbl-cell {css}">{text}</div>', unsafe_allow_html=True)

for zeilen_idx, (_, row) in enumerate(page_rows.iterrows()):
    gerade      = (zeilen_idx % 2 == 0)
    beleg_id    = str(row["buchhaltungsbeleg"])
    current_status = ampel_status.get(beleg_id, "keine")

    row_cols = st.columns(COL_W)

    # Ampel: 3 Buttons eng nebeneinander (kein use_container_width)
    # Aktiver Button = "primary", inaktive = "secondary" (borderless per CSS)
    # Klick auf bereits aktiven → zurücksetzen auf "keine"
    with row_cols[0]:
        # [1,1,1,2]: Buttons links verpackt, rechts Leerraum
        btn_cols = st.columns([1, 1, 1, 2])
        for i, (status_key, (emoji, label)) in enumerate(AMPEL.items()):
            is_active = (current_status == status_key)
            if btn_cols[i].button(
                emoji,
                key=f"ampel_{beleg_id}_{status_key}",
                type="primary" if is_active else "secondary",
                help=f"{label} (nochmals klicken zum Zurücksetzen)" if is_active else label,
                use_container_width=False,  # kompakt: kein Strecken
            ):
                # Nochmals klicken → auf "keine" setzen
                new_status = "keine" if is_active else status_key
                speichere_ampel_status(beleg_id, new_status)
                ampel_status[beleg_id] = new_status
                st.toast(
                    f"{'Status entfernt' if new_status == 'keine' else label} — Beleg {beleg_id}",
                    icon="💾",
                )
                st.rerun()

    _cell(row_cols[1], row["nettofaelligkeit"].strftime("%d.%m.%Y"), gerade)
    _cell(row_cols[2], f"<code>{beleg_id}</code>",                    gerade)
    _cell(row_cols[3], str(row.get("kreditor_name", "—")),            gerade)
    _cell(row_cols[4], fmt_eur(row["offener_betrag"]),                 gerade)
    endkunden = str(row.get("debitor_name", ""))
    _cell(row_cols[5], endkunden if endkunden not in ("", "nan") else "—", gerade)

st.markdown('<div class="tbl-sep" style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)

# ── Aufschlüsselung pro Kreditor ──────────────────────────────────────────────
st.markdown("---")
st.subheader("Aufschlüsselung pro Kreditor")
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

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "⬇️  Fälligkeiten als CSV",
    data=belege_filtered.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="faelligkeiten.csv",
    mime="text/csv",
)
