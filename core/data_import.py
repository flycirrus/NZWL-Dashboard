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
TABELLE_AMPEL = "beleg_ampel_status"
AMPEL_JSON_FALLBACK = str(Path(__file__).resolve().parent.parent / "data" / "output" / "ampel_status_v2.json")

MARIADB_CONFIG = {
    "host": "10.1.60.189",
    "port": 3306,
    "database": "cashflowctrl",
}

MARIADB_USERS = [
    {"user": "nzwl_dev", "password": "LOdYr7_38.Wu"},
    {"user": "nzwl_app", "password": "0_8WmKck_SA1"},
]


def _get_db_conn():
    """Gibt eine pymysql-Verbindung zurueck oder None bei Fehler."""
    import pymysql
    for creds in MARIADB_USERS:
        try:
            return pymysql.connect(
                host=MARIADB_CONFIG["host"],
                port=MARIADB_CONFIG["port"],
                database=MARIADB_CONFIG["database"],
                user=creds["user"],
                password=creds["password"],
                connect_timeout=3,
            )
        except Exception:
            continue
    return None


def _ensure_ampel_table(conn):
    """Erstellt die Ampel-Tabelle in MariaDB falls nicht vorhanden."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS beleg_ampel_status (
                buchhaltungsbeleg VARCHAR(50) NOT NULL,
                ampel_status      ENUM('keine','rot','gelb','gruen') NOT NULL DEFAULT 'keine',
                geaendert_am      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                geaendert_von     VARCHAR(100) DEFAULT NULL,
                PRIMARY KEY (buchhaltungsbeleg)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()


def lade_ampel_status() -> dict:
    """
    Laedt den Ampel-Status aller Belege.
    Windows: MariaDB-Tabelle 'beleg_ampel_status'
    Mac/Fallback: JSON-Datei
    Gibt dict {buchhaltungsbeleg: status_string} zurueck.
    Diese Tabelle wird von der Kernlogik NIEMALS ueberschrieben.
    """
    if os.name == "nt":
        conn = _get_db_conn()
        if conn:
            try:
                _ensure_ampel_table(conn)
                df = pd.read_sql(
                    f"SELECT buchhaltungsbeleg, ampel_status FROM {TABELLE_AMPEL}",
                    conn,
                )
                conn.close()
                return dict(zip(df["buchhaltungsbeleg"].astype(str), df["ampel_status"]))
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
    # Fallback: JSON
    if os.path.exists(AMPEL_JSON_FALLBACK):
        try:
            with open(AMPEL_JSON_FALLBACK, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def speichere_ampel_status(beleg_id: str, status: str, user: str = None) -> bool:
    """
    Speichert den Ampel-Status eines einzelnen Belegs.
    status: 'keine' | 'rot' | 'gelb' | 'gruen'
    Windows: MariaDB | Mac/Fallback: JSON-Datei
    """
    if os.name == "nt":
        conn = _get_db_conn()
        if conn:
            try:
                _ensure_ampel_table(conn)
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO beleg_ampel_status
                            (buchhaltungsbeleg, ampel_status, geaendert_von)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            ampel_status  = VALUES(ampel_status),
                            geaendert_von = VALUES(geaendert_von),
                            geaendert_am  = CURRENT_TIMESTAMP
                    """, (str(beleg_id), status, user))
                    conn.commit()
                conn.close()
                return True
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
    # Fallback: JSON
    try:
        existing = {}
        if os.path.exists(AMPEL_JSON_FALLBACK):
            with open(AMPEL_JSON_FALLBACK, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing[str(beleg_id)] = status
        os.makedirs(os.path.dirname(AMPEL_JSON_FALLBACK), exist_ok=True)
        with open(AMPEL_JSON_FALLBACK, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


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


