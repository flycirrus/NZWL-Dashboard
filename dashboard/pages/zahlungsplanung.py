import streamlit as st
import sys
import os
import json
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten
from core.calculations import (
    klassifiziere_faelligkeit, ampel_zusammenfassung,
    AMPEL_ROT, AMPEL_GELB, AMPEL_GRUEN,
    FARBE_ROT, FARBE_GELB, FARBE_GRUEN,
    FARBE_ROT_BG, FARBE_GELB_BG, FARBE_GRUEN_BG,
)


# ── Ampel Speicher-Logik ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AMPEL_FILE = os.path.join(BASE_DIR, "data", "output", "ampel_freigabe.json")


def load_ampel_freigabe():
    if os.path.exists(AMPEL_FILE):
        try:
            with open(AMPEL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_ampel_freigabe(status_dict):
    os.makedirs(os.path.dirname(AMPEL_FILE), exist_ok=True)
    with open(AMPEL_FILE, "w", encoding="utf-8") as f:
        json.dump(status_dict, f, ensure_ascii=False, indent=2)


FREIGABE_OPTIONS = ["Stop", "Pruefung", "Freigegeben"]

freigabe_status = load_ampel_freigabe()


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


st.title("Zahlungsplanung & Freigabe")

daten = lade_ergebnis_daten()
detail = daten["detail"]

if detail.empty:
    st.warning("Keine Detail-Daten geladen.")
    st.stop()

if "nettofaelligkeit" not in detail.columns:
    st.warning("Faelligkeitsdaten fehlen. Bitte Kernlogik auf dem Server ausfuehren.")
    st.stop()

# ── Belege aufbereiten ────────────────────────────────────────────────────────
df = detail.copy()
df["nettofaelligkeit"] = pd.to_datetime(df["nettofaelligkeit"], errors="coerce")
df = df.dropna(subset=["nettofaelligkeit"])

belege = df.groupby("buchhaltungsbeleg", as_index=False).agg({
    "kreditor_name": "first",
    "kreditor": "first",
    "offener_betrag": "first",
    "nettofaelligkeit": "first",
    "debitor_name": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
})

if belege.empty:
    st.info("Keine Belege mit Faelligkeitsdatum vorhanden.")
    st.stop()

belege["ampel"] = klassifiziere_faelligkeit(belege["nettofaelligkeit"])

# ── Ampel-KPI-Karten + klickbare Buttons ─────────────────────────────────────
if "zp_ampel_filter" not in st.session_state:
    st.session_state["zp_ampel_filter"] = "Alle"

ampel = ampel_zusammenfassung(detail)

st.markdown("### Zahlungs-Ampel")

a1, a2, a3 = st.columns(3)

ampel_buttons = [
    (AMPEL_ROT, FARBE_ROT, FARBE_ROT_BG, "Ueberfaellig", a1),
    (AMPEL_GELB, FARBE_GELB, FARBE_GELB_BG, "Faellig bald (7 Tage)", a2),
    (AMPEL_GRUEN, FARBE_GRUEN, FARBE_GRUEN_BG, "OK / Freigegeben", a3),
]

for ampel_key, farbe, farbe_bg, label, col in ampel_buttons:
    werte = ampel[ampel_key]
    is_active = st.session_state["zp_ampel_filter"] == ampel_key
    border_w = "3px" if is_active else "1px"

    col.markdown(f"""
    <div style="
        background: {farbe_bg};
        border: {border_w} solid {farbe};
        border-left: 5px solid {farbe};
        border-radius: 8px;
        padding: 16px 20px;
        text-align: center;
        margin-bottom: 8px;
        cursor: pointer;
    ">
        <div style="font-size: 36px; font-weight: 700; color: {farbe};">{werte['anzahl']}</div>
        <div style="font-size: 14px; font-weight: 600; color: #555555;">{label}</div>
        <div style="font-size: 16px; color: #1A1A1A; margin-top: 4px;">{fmt_mio(werte['betrag'])}</div>
    </div>
    """, unsafe_allow_html=True)

    btn_text = "Aktiv" if is_active else "Filtern"
    if col.button(btn_text, key=f"zp_ampel_{ampel_key}", use_container_width=True):
        st.session_state["zp_ampel_filter"] = "Alle" if is_active else ampel_key
        st.rerun()

# Alle-Button
if st.session_state["zp_ampel_filter"] != "Alle":
    if st.button("Filter zuruecksetzen (Alle anzeigen)"):
        st.session_state["zp_ampel_filter"] = "Alle"
        st.rerun()

st.markdown("---")

# ── Filter anwenden ──────────────────────────────────────────────────────────
aktiver_filter = st.session_state["zp_ampel_filter"]
if aktiver_filter != "Alle":
    belege_filtered = belege[belege["ampel"] == aktiver_filter].copy()
    st.info(f"Filter aktiv: {aktiver_filter}")
else:
    belege_filtered = belege.copy()

# ── Kreditor-Filter ──────────────────────────────────────────────────────────
kred_optionen = ["Alle"] + sorted(belege_filtered["kreditor_name"].dropna().unique().tolist())
kred_filter = st.selectbox("Kreditor filtern", kred_optionen, key="zp_kred_filter")
if kred_filter != "Alle":
    belege_filtered = belege_filtered[belege_filtered["kreditor_name"] == kred_filter]

# ── Expander nach Faelligkeitszeitraum ───────────────────────────────────────
heute = pd.Timestamp.now().normalize()

belege_filtered = belege_filtered.copy()
belege_filtered["_zeitraum"] = belege_filtered["nettofaelligkeit"].apply(
    lambda d: "Ueberfaellig" if d < heute
    else "Faellig diese Woche" if d < heute + pd.Timedelta(days=7)
    else "Naechste Woche" if d < heute + pd.Timedelta(days=14)
    else "In 2-4 Wochen" if d < heute + pd.Timedelta(days=28)
    else "Spaeter (4+ Wochen)"
)

zeitraum_config = [
    ("Ueberfaellig", FARBE_ROT),
    ("Faellig diese Woche", FARBE_GELB),
    ("Naechste Woche", "#2E75B6"),
    ("In 2-4 Wochen", "#1F4E79"),
    ("Spaeter (4+ Wochen)", "#555555"),
]

for zeitraum_key, farbe in zeitraum_config:
    subset = belege_filtered[belege_filtered["_zeitraum"] == zeitraum_key].sort_values("nettofaelligkeit")
    anzahl = len(subset)
    betrag = subset["offener_betrag"].sum() if not subset.empty else 0
    expand_default = zeitraum_key == "Ueberfaellig" and anzahl > 0

    with st.expander(f"{zeitraum_key} — {anzahl} Belege, {fmt_mio(betrag)}", expanded=expand_default):
        if subset.empty:
            st.caption("Keine Belege in diesem Zeitraum.")
        else:
            anzeige = subset[["nettofaelligkeit", "buchhaltungsbeleg", "kreditor_name",
                              "offener_betrag", "debitor_name"]].copy()

            # Freigabe-Status hinzufuegen
            anzeige["Freigabe"] = anzeige["buchhaltungsbeleg"].apply(
                lambda b: freigabe_status.get(str(b), "Stop")
            )

            anzeige["nettofaelligkeit"] = anzeige["nettofaelligkeit"].dt.strftime("%d.%m.%Y")
            anzeige["offener_betrag"] = anzeige["offener_betrag"].apply(fmt_eur)

            anzeige = anzeige[["Freigabe", "nettofaelligkeit", "buchhaltungsbeleg",
                                "kreditor_name", "offener_betrag", "debitor_name"]]
            anzeige.columns = ["Freigabe", "Faellig am", "Beleg", "Kreditor", "Offener Betrag", "Endkunden"]

            edited = st.data_editor(
                anzeige,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Freigabe": st.column_config.SelectboxColumn(
                        "Freigabe",
                        help="Ampel fuer den Freigabeprozess",
                        width="medium",
                        options=FREIGABE_OPTIONS,
                        required=True,
                    ),
                    "Faellig am": st.column_config.Column(disabled=True),
                    "Beleg": st.column_config.Column(disabled=True),
                    "Kreditor": st.column_config.Column(disabled=True),
                    "Offener Betrag": st.column_config.Column(disabled=True),
                    "Endkunden": st.column_config.Column(disabled=True),
                },
                key=f"zp_editor_{zeitraum_key}",
            )

            changed = False
            for _, row in edited.iterrows():
                beleg_id = str(row["Beleg"])
                new_val = row["Freigabe"]
                if freigabe_status.get(beleg_id, "Stop") != new_val:
                    freigabe_status[beleg_id] = new_val
                    changed = True

            if changed:
                save_ampel_freigabe(freigabe_status)
                st.toast("Freigabe-Status gespeichert!", icon="OK")

# ── Zusammenfassung Freigabe ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("Freigabe-Zusammenfassung")

count_stop = sum(1 for b in belege_filtered["buchhaltungsbeleg"] if freigabe_status.get(str(b), "Stop") == "Stop")
count_pruef = sum(1 for b in belege_filtered["buchhaltungsbeleg"] if freigabe_status.get(str(b), "Stop") == "Pruefung")
count_frei = sum(1 for b in belege_filtered["buchhaltungsbeleg"] if freigabe_status.get(str(b), "Stop") == "Freigegeben")

s1, s2, s3 = st.columns(3)
s1.metric("Stop", f"{count_stop} Belege")
s2.metric("In Pruefung", f"{count_pruef} Belege")
s3.metric("Freigegeben", f"{count_frei} Belege")

# ── Download ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "Zahlungsplan als CSV",
    data=belege_filtered.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="zahlungsplanung.csv",
    mime="text/csv",
)
