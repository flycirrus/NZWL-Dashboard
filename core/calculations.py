"""
Calculations Module for NZWL Zahlungsplanung & Liquiditaetssteuerung.

Faelligkeitslogik: klassifiziert Belege nach Ampel-Status (Rot/Gelb/Gruen).
"""

import pandas as pd
from datetime import datetime, timedelta


AMPEL_ROT = "Ueberfaellig"
AMPEL_GELB = "Faellig bald"
AMPEL_GRUEN = "OK"

FARBE_ROT = "#C00000"
FARBE_GELB = "#E65100"
FARBE_GRUEN = "#38761D"

FARBE_ROT_BG = "#FCEBEB"
FARBE_GELB_BG = "#FFF3E0"
FARBE_GRUEN_BG = "#D9EAD3"


def klassifiziere_faelligkeit(nettofaelligkeit: pd.Series, tage_gelb: int = 7) -> pd.Series:
    """
    Klassifiziert Faelligkeitsdaten in Ampel-Kategorien.

    - Rot (Ueberfaellig): Nettofaelligkeit liegt in der Vergangenheit
    - Gelb (Faellig bald): Nettofaelligkeit innerhalb der naechsten `tage_gelb` Tage
    - Gruen (OK): Nettofaelligkeit liegt weiter in der Zukunft
    """
    heute = pd.Timestamp.now().normalize()
    grenze_gelb = heute + pd.Timedelta(days=tage_gelb)

    dates = pd.to_datetime(nettofaelligkeit, errors="coerce")

    def _klassifiziere(d):
        if pd.isna(d):
            return AMPEL_GRUEN
        if d < heute:
            return AMPEL_ROT
        if d < grenze_gelb:
            return AMPEL_GELB
        return AMPEL_GRUEN

    return dates.apply(_klassifiziere)


def ampel_zusammenfassung(df: pd.DataFrame, faelligkeit_col: str = "nettofaelligkeit",
                          betrag_col: str = "offener_betrag",
                          beleg_col: str = "buchhaltungsbeleg") -> dict:
    """
    Berechnet Ampel-KPIs: Anzahl und Betrag pro Kategorie.
    Dedupliziert nach Beleg, damit jede Rechnung nur einmal zaehlt.

    Returns: {
        "Ueberfaellig": {"anzahl": int, "betrag": float},
        "Faellig bald": {"anzahl": int, "betrag": float},
        "OK":           {"anzahl": int, "betrag": float},
    }
    """
    ergebnis = {
        AMPEL_ROT:   {"anzahl": 0, "betrag": 0.0},
        AMPEL_GELB:  {"anzahl": 0, "betrag": 0.0},
        AMPEL_GRUEN: {"anzahl": 0, "betrag": 0.0},
    }

    if df.empty or faelligkeit_col not in df.columns:
        return ergebnis

    tmp = df.copy()
    tmp["_ampel"] = klassifiziere_faelligkeit(tmp[faelligkeit_col])

    if beleg_col in tmp.columns:
        tmp = tmp.drop_duplicates(subset=[beleg_col])

    for ampel_key in [AMPEL_ROT, AMPEL_GELB, AMPEL_GRUEN]:
        subset = tmp[tmp["_ampel"] == ampel_key]
        ergebnis[ampel_key]["anzahl"] = len(subset)
        if betrag_col in subset.columns:
            ergebnis[ampel_key]["betrag"] = subset[betrag_col].sum()

    return ergebnis


def calculate_payments(df, rules=None):
    """
    Calculates prioritized payment proposals based on due dates, discount deadlines,
    and custom rules.
    """
    pass


def calculate_liquidity(df, weeks=4):
    """
    Calculates the expected net liquidity for the given number of calendar weeks.
    """
    pass
