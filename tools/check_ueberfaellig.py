"""
Prüfskript: Gleicht die "Überfällig"-Summe der Fälligkeiten-Seite mit der
Gesamtsumme der Überfällig-Analyse ab — aus derselben Datenquelle wie das
Dashboard (auf dem Windows-Server = MariaDB, auf dem Mac = JSON).

Aufruf auf dem Server:  venv\\Scripts\\python.exe tools\\check_ueberfaellig.py
(oder einfach Pruefung_Ueberfaellig.bat doppelklicken)
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from core.data_import import lade_ergebnis_daten


def _fmt(v: float) -> str:
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def build_belege(detail: pd.DataFrame, nv_raw: pd.DataFrame) -> pd.DataFrame:
    """Identisch zu faelligkeiten_w1.py / ueberfaellig_analyse.py."""
    df = detail.copy()
    df["nettofaelligkeit"] = pd.to_datetime(df["nettofaelligkeit"], errors="coerce")
    df = df.dropna(subset=["nettofaelligkeit"])
    belege = df.groupby("buchhaltungsbeleg", as_index=False).agg({
        "kreditor_name":    "first",
        "offener_betrag":   "first",
        "nettofaelligkeit": "first",
        "debitor_name": lambda x: ", ".join(sorted({
            t.strip() for v in x.dropna() for t in str(v).split(",")
            if t.strip() and t.strip() not in ("nan", "NaT", "")
        })),
    })
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
    return belege


def main() -> None:
    quelle = "MariaDB (Server)" if os.name == "nt" else "JSON-Snapshot (Mac/lokal)"
    print("=" * 64)
    print("  NZWL — Abgleich Überfällig-Summe")
    print(f"  Datenquelle: {quelle}")
    print("=" * 64)

    daten  = lade_ergebnis_daten()
    detail = daten["detail"]
    nv_raw = daten.get("nicht_verknuepft", pd.DataFrame())
    if detail.empty:
        print("\n[FEHLER] Keine Detail-Daten geladen. Läuft die MariaDB / Kernlogik?")
        return

    belege = build_belege(detail, nv_raw)
    heute        = pd.Timestamp.now().normalize()
    heute_montag = heute - pd.Timedelta(days=heute.weekday())
    print(f"\nHeute: {heute.date()}   ·   Montag dieser Woche: {heute_montag.date()}")

    # ── Weg A: FÄLLIGKEITEN V.02 — über die Wochen-Logik (woche_label) ──────────
    naechste_kw = heute_montag + pd.Timedelta(weeks=1)
    in_2_wochen = heute_montag + pd.Timedelta(weeks=2)
    in_3_wochen = heute_montag + pd.Timedelta(weeks=3)
    in_4_wochen = heute_montag + pd.Timedelta(weeks=4)

    def woche_label(d):
        if d < heute_montag: return "Überfällig"
        if d < naechste_kw:  return "Diese Woche"
        if d < in_2_wochen:  return "Nächste Woche"
        if d < in_3_wochen:  return "In 2 Wochen"
        if d < in_4_wochen:  return "In 3 Wochen"
        return "Später (4+ Wochen)"

    zeitraum = belege["nettofaelligkeit"].apply(woche_label)
    faell = belege[zeitraum == "Überfällig"]
    a_n, a_s = len(faell), faell["offener_betrag"].sum()
    print("\n--- Weg A · FÄLLIGKEITEN V.02  (Kachel 'Überfällig' via Wochen-Logik) ---")
    print(f"    Belege : {a_n}")
    print(f"    Summe  : {_fmt(a_s)} €")

    # ── Weg B: ÜBERFÄLLIG-ANALYSE — über den Direktfilter (< heute_montag) ──────
    ueberf = belege[belege["nettofaelligkeit"] < heute_montag]
    b_n, b_s = len(ueberf), ueberf["offener_betrag"].sum()
    print("\n--- Weg B · ÜBERFÄLLIG-ANALYSE  (Kachel 'Gesamt überfällig' via Filter) ---")
    print(f"    Belege : {b_n}")
    print(f"    Summe  : {_fmt(b_s)} €")

    # Aufschlüsselung nach Alters-Stufe (nur zur Info)
    tage = (heute - ueberf["nettofaelligkeit"]).dt.days
    def bucket(t):
        if t <= 30: return "1-30 Tage"
        if t <= 60: return "31-60 Tage"
        if t <= 90: return "61-90 Tage"
        return "> 90 Tage"
    print("\n    davon nach Dauer:")
    for stufe in ["1-30 Tage", "31-60 Tage", "61-90 Tage", "> 90 Tage"]:
        mask = tage.apply(bucket) == stufe
        print(f"      {stufe:<12}: {int(mask.sum()):>5} Belege  /  {_fmt(ueberf.loc[mask, 'offener_betrag'].sum())} €")

    # ── Verdikt: unabhängig berechnete Zahlen vergleichen ──────────────────────
    match = (a_n == b_n) and abs(a_s - b_s) < 0.01
    print("\n" + "=" * 64)
    if match:
        print("  ERGEBNIS: ✅ ÜBEREINSTIMMUNG — beide Wege liefern dieselbe Zahl.")
        print(f"            {a_n} Belege  /  {_fmt(a_s)} €")
    else:
        print("  ERGEBNIS: ❌ ABWEICHUNG!")
        print(f"            Weg A: {a_n} / {_fmt(a_s)} €")
        print(f"            Weg B: {b_n} / {_fmt(b_s)} €")
    print("=" * 64)


if __name__ == "__main__":
    main()
