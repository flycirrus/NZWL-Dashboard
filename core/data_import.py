"""
NZWL Daten-Import — Dual-Mode
  Windows (Server): liest direkt aus MariaDB
  Mac (lokal):      liest JSON-Dateien aus data/input/

Gibt immer ein Dict mit drei DataFrames zurueck:
  - "detail"      (ergebnis_detail)
  - "uebersicht"  (ergebnis_uebersicht)
  - "statistik"   (ergebnis_statistik)
"""
import os
import json
import re
import pandas as pd
import streamlit as st
from pathlib import Path


def _normalize_col(name: str) -> str:
    """Spaltenname normalisieren: Umlaute ersetzen, Kleinbuchstaben, Leerzeichen→Unterstrich."""
    name = str(name)
    replacements = {
        "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
        "Ä": "ae", "Ö": "oe", "Ü": "ue",
    }
    for umlaut, ascii_eq in replacements.items():
        name = name.replace(umlaut, ascii_eq)
    name = name.lower()
    name = re.sub(r"[\s\-]+", "_", name)  # Leerzeichen / Bindestriche → _
    name = re.sub(r"[^a-z0-9_]", "", name)  # sonstige Sonderzeichen entfernen
    return name


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Alle Spaltennamen eines DataFrames normalisieren."""
    df.columns = [_normalize_col(c) for c in df.columns]
    return df

TABELLEN = ["ergebnis_detail", "ergebnis_uebersicht", "ergebnis_statistik"]

MARIADB_CONFIG = {
    "host": "10.1.60.189",
    "port": 3306,
    "database": "cashflowctrl",
}

MARIADB_USERS = [
    {"user": "nzwl_dev", "password": "LOdYr7_38.Wu"},
    {"user": "nzwl_app", "password": "0_8WmKck_SA1"},
]


def _lade_aus_mariadb():
    import pymysql
    conn = None
    for creds in MARIADB_USERS:
        try:
            conn = pymysql.connect(
                host=MARIADB_CONFIG["host"],
                port=MARIADB_CONFIG["port"],
                database=MARIADB_CONFIG["database"],
                user=creds["user"],
                password=creds["password"],
            )
            break
        except Exception:
            continue

    if conn is None:
        return {
            "detail": pd.DataFrame(),
            "uebersicht": pd.DataFrame(),
            "statistik": pd.DataFrame(),
        }

    daten = {}
    keys = ["detail", "uebersicht", "statistik"]
    for tabelle, key in zip(TABELLEN, keys):
        try:
            df = pd.read_sql(f"SELECT * FROM {tabelle}", conn)
            daten[key] = _normalize_columns(df)
        except Exception:
            daten[key] = pd.DataFrame()

    conn.close()
    return daten


def _lade_aus_json(pfad):
    daten = {}
    keys = ["detail", "uebersicht", "statistik"]
    for tabelle, key in zip(TABELLEN, keys):
        datei = os.path.join(pfad, f"{tabelle}.json")
        if os.path.exists(datei):
            with open(datei, "r", encoding="utf-8") as f:
                records = json.load(f)
            df = pd.DataFrame(records)
            daten[key] = _normalize_columns(df)
        else:
            daten[key] = pd.DataFrame()
    return daten


@st.cache_data(ttl=300)
def lade_ergebnis_daten(json_pfad: str = None) -> dict:
    """
    Laedt die Ergebnis-Daten je nach Betriebssystem.
    Windows: MariaDB | Mac: JSON aus json_pfad
    """
    if os.name == "nt":
        return _lade_aus_mariadb()
    else:
        if json_pfad is None:
            json_pfad = str(Path(__file__).resolve().parent.parent / "data" / "input")
        return _lade_aus_json(json_pfad)


