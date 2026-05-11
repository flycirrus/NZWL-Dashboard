import streamlit as st
import sys
import os
import json
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from core.data_import import lade_ergebnis_daten

# ── Ampel Speicher-Logik ──────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AMPEL_FILE = os.path.join(BASE_DIR, "data", "output", "ampel_status.json")

def load_ampel_status():
    if os.path.exists(AMPEL_FILE):
        try:
            with open(AMPEL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_ampel_status(status_dict):
    os.makedirs(os.path.dirname(AMPEL_FILE), exist_ok=True)
    with open(AMPEL_FILE, "w", encoding="utf-8") as f:
        json.dump(status_dict, f, ensure_ascii=False, indent=2)

ampel_status = load_ampel_status()
AMPEL_OPTIONS = ["🔴 Stop", "🟡 Prüfung", "🟢 Freigegeben"]


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


st.title("Faelligkeiten — Was muss wann bezahlt werden?")

daten = lade_ergebnis_daten()
detail = daten["detail"]

if detail.empty:
    st.warning("Keine Detail-Daten geladen.")
    st.stop()

# ── Faelligkeitsdaten vorbereiten ─────────────────────────────────────────────
hat_faelligkeit = "nettofaelligkeit" in detail.columns
if not hat_faelligkeit:
    st.warning(
        "Faelligkeitsdaten sind noch nicht vorhanden. "
        "Bitte auf dem Server die Kernlogik neu ausfuehren (git pull + python kreditor_debitor_logik.py), "
        "dann export_mariadb.py und die neuen JSON-Dateien lokal kopieren."
    )
    st.stop()

# Pro Buchhaltungsbeleg nur eine Zeile (Beleg = eine Rechnung)
df = detail.copy()
df["nettofaelligkeit"] = pd.to_datetime(df["nettofaelligkeit"], errors="coerce")
df = df.dropna(subset=["nettofaelligkeit"])

# Aggregieren: pro Beleg die Faelligkeit + Kreditor + Betrag + verknuepfte Endkunden
belege = df.groupby("buchhaltungsbeleg", as_index=False).agg({
    "kreditor_name": "first",
    "kreditor": "first",
    "offener_betrag": "first",
    "nettofaelligkeit": "first",
    "debitor_name": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
    "debitor": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
    "bom_parent": lambda x: ", ".join(sorted(set(str(v) for v in x.dropna() if str(v) != "nan"))),
})

if belege.empty:
    st.info("Keine Belege mit Faelligkeitsdatum vorhanden.")
    st.stop()

# ── Wochen zuordnen ───────────────────────────────────────────────────────────
heute = pd.Timestamp.now().normalize()

def woche_label(d):
    diff = (d - heute).days
    if diff < 0:
        return "Ueberfaellig"
    elif diff < 7:
        return "Diese Woche"
    elif diff < 14:
        return "Naechste Woche"
    elif diff < 21:
        return "In 2 Wochen"
    elif diff < 28:
        return "In 3 Wochen"
    else:
        return "Spaeter (4+ Wochen)"

wochen_order = ["Ueberfaellig", "Diese Woche", "Naechste Woche", "In 2 Wochen", "In 3 Wochen", "Spaeter (4+ Wochen)"]
belege["zeitraum"] = belege["nettofaelligkeit"].apply(woche_label)

# ── KPI-Karten pro Woche ─────────────────────────────────────────────────────
st.markdown("### Zahlungen nach Zeitraum")

wochen_summe = belege.groupby("zeitraum")["offener_betrag"].agg(["sum", "count"]).reindex(wochen_order, fill_value=0)

cols = st.columns(len(wochen_order))
farben = {"Ueberfaellig": "red", "Diese Woche": "orange"}
for i, woche in enumerate(wochen_order):
    betrag = wochen_summe.loc[woche, "sum"] if woche in wochen_summe.index else 0
    anzahl = int(wochen_summe.loc[woche, "count"]) if woche in wochen_summe.index else 0
    cols[i].metric(woche, fmt_mio(betrag), f"{anzahl} Belege")

st.markdown("---")

# ── Filter nach Zeitraum ─────────────────────────────────────────────────────
zeitraum_filter = st.selectbox("Zeitraum anzeigen", ["Alle"] + wochen_order)

if zeitraum_filter != "Alle":
    belege_filtered = belege[belege["zeitraum"] == zeitraum_filter]
else:
    belege_filtered = belege

belege_filtered = belege_filtered.sort_values("nettofaelligkeit")

# ── Detail-Tabelle ────────────────────────────────────────────────────────────
st.subheader(f"Rechnungen — {zeitraum_filter}")
st.caption(f"{len(belege_filtered)} Belege | Gesamt: {fmt_eur(belege_filtered['offener_betrag'].sum())}")

anzeige = belege_filtered[[
    "nettofaelligkeit", "buchhaltungsbeleg", "kreditor_name",
    "offener_betrag", "debitor_name", "bom_parent"
]].copy()

# Ampel-Status (Dropdown) hinzufügen, Default "🔴 Stop"
anzeige["Status"] = anzeige["buchhaltungsbeleg"].apply(lambda b: ampel_status.get(str(b), "🔴 Stop"))

anzeige["nettofaelligkeit"] = anzeige["nettofaelligkeit"].dt.strftime("%d.%m.%Y")
anzeige["offener_betrag"] = anzeige["offener_betrag"].apply(fmt_eur)

# Spalten-Reihenfolge: Status ganz vorne
anzeige = anzeige[["Status", "nettofaelligkeit", "buchhaltungsbeleg", "kreditor_name", "offener_betrag", "debitor_name", "bom_parent"]]
anzeige.columns = ["Status", "Faellig am", "Beleg", "Kreditor", "Offener Betrag", "Endkunden", "Fertigteile"]

st.caption("💡 **Tipp:** Du kannst den Status (Ampel) direkt in der Tabelle anklicken und ändern.")
edited_df = st.data_editor(
    anzeige,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Ampel für den Freigabeprozess",
            width="medium",
            options=AMPEL_OPTIONS,
            required=True
        ),
        "Faellig am": st.column_config.Column(disabled=True),
        "Beleg": st.column_config.Column(disabled=True),
        "Kreditor": st.column_config.Column(disabled=True),
        "Offener Betrag": st.column_config.Column(disabled=True),
        "Endkunden": st.column_config.Column(disabled=True),
        "Fertigteile": st.column_config.Column(disabled=True),
    },
    key=f"ampel_editor_{zeitraum_filter}" # Eigener Key, damit der Wechsel des Filters nicht abstürzt
)

# Prüfen, ob sich ein Status geändert hat
changed = False
for index, row in edited_df.iterrows():
    beleg_id = str(row["Beleg"])
    new_status = row["Status"]
    if ampel_status.get(beleg_id, "🔴 Stop") != new_status:
        ampel_status[beleg_id] = new_status
        changed = True

if changed:
    save_ampel_status(ampel_status)
    # Erfolgsmeldung zeigen (verschwindet bei Interaktion)
    st.toast("Status gespeichert!", icon="💾")

# ── Aufschluesselung pro Kreditor ─────────────────────────────────────────────
st.markdown("---")
st.subheader("Aufschluesselung pro Kreditor")

kred_summe = belege_filtered.groupby("kreditor_name").agg(
    Betrag=("offener_betrag", "sum"),
    Belege=("buchhaltungsbeleg", "count"),
    Endkunden=("debitor_name", lambda x: ", ".join(sorted(set(
        k.strip() for v in x.dropna() for k in str(v).split(",") if k.strip() and k.strip() != "nan"
    )))),
).sort_values("Betrag", ascending=False).reset_index()

kred_summe["Betrag"] = kred_summe["Betrag"].apply(fmt_eur)
kred_summe = kred_summe.rename(columns={"kreditor_name": "Kreditor"})
st.dataframe(kred_summe, use_container_width=True, hide_index=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "Faelligkeiten als CSV",
    data=belege_filtered.to_csv(index=False, sep=";", decimal=",").encode("utf-8"),
    file_name="faelligkeiten.csv",
    mime="text/csv",
)
