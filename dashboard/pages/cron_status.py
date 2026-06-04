import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

sys_path = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.append(str(sys_path))
from dashboard.auth import check_permission

if not check_permission(["admin", "vorbereiter", "geschaeftsleitung"]):
    st.error("Zugriff verweigert.")
    st.stop()

st.title("Automatische Kernlogik — Cron-Status")

# --- Protokoll-Datei finden ---
if os.name == "nt":
    log_pfad = Path(r"Z:\99 output\cron_protokoll.json")
else:
    log_pfad = Path(__file__).resolve().parent.parent.parent.parent / "NZWL_AGENT" / "output" / "cron_protokoll.json"
    if not log_pfad.exists():
        log_pfad = Path.home() / "Desktop" / "NZWL_AGENT" / "output" / "cron_protokoll.json"


def lade_cron_protokoll():
    if not log_pfad.exists():
        return []
    try:
        with open(log_pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


protokoll = lade_cron_protokoll()

if not protokoll:
    st.info(
        "Noch keine Cron-Laeufe protokolliert.\n\n"
        f"Erwartete Protokoll-Datei: `{log_pfad}`\n\n"
        "Die Datei wird automatisch beim ersten Cron-Lauf erstellt."
    )
    st.stop()

# --- Metriken ---
st.markdown("### Uebersicht")

total = len(protokoll)
ok_count = sum(1 for e in protokoll if e.get("status") == "OK")
fehler_count = total - ok_count
letzter = protokoll[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Laeufe gesamt", total)
col2.metric("Erfolgreich", ok_count, delta=f"{ok_count/total*100:.0f}%" if total > 0 else None)
col3.metric("Fehlgeschlagen", fehler_count, delta=f"-{fehler_count}" if fehler_count > 0 else "0", delta_color="inverse")

letzter_zeit = letzter.get("gestartet_am", "?")
letzter_status = letzter.get("status", "?")
status_emoji = "OK" if letzter_status == "OK" else "FEHLER"
col4.metric("Letzter Lauf", letzter_zeit, delta=status_emoji)

# --- Tabelle: Alle Laeufe (neueste zuerst) ---
st.markdown("---")
st.markdown("### Protokoll aller Laeufe")

rows = []
for e in reversed(protokoll):
    schritte_text = []
    for s in e.get("schritte", []):
        symbol = "OK" if s["status"] == "OK" else "FEHLER"
        schritte_text.append(f"{symbol} {s['name']}")

    rows.append({
        "Datum": e.get("gestartet_am", "?"),
        "Status": "OK" if e.get("status") == "OK" else "FEHLER",
        "Dauer (s)": e.get("dauer_sekunden", "?"),
        "Server": e.get("server", "?"),
        "Umgebung": e.get("umgebung", "?"),
        "Schritte": " | ".join(schritte_text),
        "Fehler": e.get("fehler") or "",
    })

df = pd.DataFrame(rows)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.TextColumn(width="small"),
        "Dauer (s)": st.column_config.NumberColumn(format="%.1f", width="small"),
        "Fehler": st.column_config.TextColumn(width="large"),
    },
)

# --- Detail: Letzter Lauf ---
st.markdown("---")
st.markdown("### Detail: Letzter Lauf")

for schritt in letzter.get("schritte", []):
    status_label = "OK" if schritt["status"] == "OK" else "FEHLER"
    with st.expander(f"{status_label} {schritt['name']} ({schritt.get('gestartet', '?')} - {schritt.get('beendet', '?')})", expanded=schritt["status"] != "OK"):
        if schritt.get("fehler"):
            st.error(schritt["fehler"])
        ausgabe = schritt.get("ausgabe", "")
        if ausgabe.strip():
            st.code(ausgabe, language="text")
        else:
            st.caption("Keine Ausgabe")

# --- Naechste geplante Laeufe ---
st.markdown("---")
st.markdown("### Zeitplan")
st.markdown("""
| Aufgabe | Uhrzeit | Frequenz |
|---------|---------|----------|
| `NZWL_Kernlogik_0400` | **04:00** | Taeglich |
| `NZWL_Kernlogik_1200` | **12:00** | Taeglich |

Beide Aufgaben fuehren die komplette Kette durch:
1. `git pull` — neuester Code vom Repository
2. **Kernlogik** — Kreditor-Debitor-Verknuepfung + DB-Schreiben
3. **Excel-Export** — formatierte Ausgabe-Datei
""")

# --- Export ---
csv_data = df.to_csv(index=False, sep=";").encode("utf-8-sig")
st.download_button(
    label="Protokoll als CSV exportieren",
    data=csv_data,
    file_name=f"cron_protokoll_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
)
