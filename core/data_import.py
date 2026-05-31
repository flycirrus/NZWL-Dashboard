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

TABELLEN = ["ergebnis_detail", "ergebnis_uebersicht", "ergebnis_statistik", "opos_nicht_verknuepft"]
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
    """Erstellt die Ampel-Historien-Tabelle in MariaDB falls nicht vorhanden und migriert ggf. alte Daten."""
    with conn.cursor() as cur:
        # 1. Sicherstellen, dass die Historie-Tabelle existiert
        cur.execute("""
            CREATE TABLE IF NOT EXISTS beleg_ampel_status_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                buchhaltungsbeleg VARCHAR(50) NOT NULL,
                ampel_status      VARCHAR(20) NOT NULL DEFAULT 'keine',
                geaendert_am      DATETIME DEFAULT CURRENT_TIMESTAMP,
                geaendert_von     VARCHAR(100) DEFAULT NULL,
                INDEX idx_beleg (buchhaltungsbeleg)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        conn.commit()

        # 2. Prüfen, ob die Historie leer ist
        cur.execute("SELECT COUNT(*) FROM beleg_ampel_status_history")
        count_history = cur.fetchone()[0]

        # 3. Wenn Historie leer ist, prüfen ob alte Tabelle existiert und Daten hat
        if count_history == 0:
            try:
                cur.execute("SELECT COUNT(*) FROM beleg_ampel_status")
                count_old = cur.fetchone()[0]
                if count_old > 0:
                    # Migrieren der alten Daten in die Historie
                    cur.execute("""
                        INSERT INTO beleg_ampel_status_history 
                            (buchhaltungsbeleg, ampel_status, geaendert_am, geaendert_von)
                        SELECT 
                            buchhaltungsbeleg, ampel_status, geaendert_am, geaendert_von 
                        FROM beleg_ampel_status
                    """)
                    conn.commit()
            except Exception:
                # Alte Tabelle existiert eventuell nicht, ignorieren
                pass


def lade_ampel_status() -> dict:
    """
    Laedt den aktuellen Ampel-Status aller Belege (jeweils der neueste Eintrag).
    Windows: MariaDB-Tabelle 'beleg_ampel_status_history'
    Mac/Fallback: JSON-Datei
    Gibt dict {buchhaltungsbeleg: status_string} zurueck.
    """
    if os.name == "nt":
        conn = _get_db_conn()
        if conn:
            try:
                _ensure_ampel_table(conn)
                # Abfrage fuer den jeweils neuesten Eintrag pro Beleg
                query = """
                    SELECT h1.buchhaltungsbeleg, h1.ampel_status
                    FROM beleg_ampel_status_history h1
                    INNER JOIN (
                        SELECT buchhaltungsbeleg, MAX(id) as max_id
                        FROM beleg_ampel_status_history
                        GROUP BY buchhaltungsbeleg
                    ) h2 ON h1.id = h2.max_id
                """
                df = pd.read_sql(query, conn)
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
                content = json.load(f)
                if isinstance(content, list):
                    # Historie durchlaufen und den jeweils neuesten Status extrahieren
                    latest = {}
                    for record in content:
                        b_id = str(record.get("buchhaltungsbeleg"))
                        latest[b_id] = record.get("ampel_status", "keine")
                    return latest
                elif isinstance(content, dict):
                    return content
        except Exception:
            pass
    return {}


def speichere_ampel_status(beleg_id: str, status: str, user: str = None) -> bool:
    """
    Speichert den Ampel-Status eines einzelnen Belegs in der Historie.
    status: 'keine' | 'rot' | 'gelb' | 'gruen'
    Windows: MariaDB | Mac/Fallback: JSON-Datei
    """
    if user is None:
        try:
            if "user" in st.session_state and st.session_state.user:
                user = st.session_state.user.get("name", "System")
        except Exception:
            pass
    if user is None:
        user = "System"

    if os.name == "nt":
        conn = _get_db_conn()
        if conn:
            try:
                _ensure_ampel_table(conn)
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO beleg_ampel_status_history
                            (buchhaltungsbeleg, ampel_status, geaendert_von, geaendert_am)
                        VALUES (%s, %s, %s, NOW())
                    """, (str(beleg_id), status, user))
                    conn.commit()
                conn.close()
                return True
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass

    # Fallback: JSON-Historie (Liste von Einträgen)
    try:
        history_records = []
        if os.path.exists(AMPEL_JSON_FALLBACK):
            with open(AMPEL_JSON_FALLBACK, "r", encoding="utf-8") as f:
                try:
                    content = json.load(f)
                    if isinstance(content, list):
                        history_records = content
                    elif isinstance(content, dict):
                        # Migration des alten Formats (Dict) in eine Liste von Einträgen
                        for b_id, stat in content.items():
                            history_records.append({
                                "buchhaltungsbeleg": str(b_id),
                                "ampel_status": stat,
                                "geaendert_am": pd.Timestamp.now().isoformat(),
                                "geaendert_von": "System (Migration)"
                            })
                except Exception:
                    pass

        # Neuen Eintrag hinzufügen
        import datetime
        now_str = datetime.datetime.now().isoformat()
        history_records.append({
            "buchhaltungsbeleg": str(beleg_id),
            "ampel_status": status,
            "geaendert_von": user,
            "geaendert_am": now_str
        })

        os.makedirs(os.path.dirname(AMPEL_JSON_FALLBACK), exist_ok=True)
        with open(AMPEL_JSON_FALLBACK, "w", encoding="utf-8") as f:
            json.dump(history_records, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def lade_ampel_status_historie() -> pd.DataFrame:
    """
    Laedt die vollstaendige Historie aller Ampel-Status-Aenderungen.
    Gibt einen DataFrame mit den Spalten ['buchhaltungsbeleg', 'ampel_status', 'geaendert_am', 'geaendert_von'] zurueck.
    """
    if os.name == "nt":
        conn = _get_db_conn()
        if conn:
            try:
                _ensure_ampel_table(conn)
                df = pd.read_sql("SELECT buchhaltungsbeleg, ampel_status, geaendert_am, geaendert_von FROM beleg_ampel_status_history ORDER BY geaendert_am DESC", conn)
                conn.close()
                return df
            except Exception:
                try:
                    conn.close()
                except Exception:
                    pass
    # Fallback: JSON
    if os.path.exists(AMPEL_JSON_FALLBACK):
        try:
            with open(AMPEL_JSON_FALLBACK, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, list):
                    df = pd.DataFrame(content)
                    if not df.empty:
                        # Sicherstellen, dass alle erwarteten Spalten vorhanden sind
                        for col in ["buchhaltungsbeleg", "ampel_status", "geaendert_am", "geaendert_von"]:
                            if col not in df.columns:
                                df[col] = None
                        # Typen konvertieren
                        df["geaendert_am"] = pd.to_datetime(df["geaendert_am"])
                        return df.sort_values(by="geaendert_am", ascending=False)
                elif isinstance(content, dict):
                    # Altes Format in DataFrame
                    records = []
                    for b_id, stat in content.items():
                        records.append({
                            "buchhaltungsbeleg": str(b_id),
                            "ampel_status": stat,
                            "geaendert_am": pd.Timestamp.now(),
                            "geaendert_von": "System (Migration)"
                        })
                    return pd.DataFrame(records)
        except Exception:
            pass
    return pd.DataFrame(columns=["buchhaltungsbeleg", "ampel_status", "geaendert_am", "geaendert_von"])


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
    keys = ["detail", "uebersicht", "statistik", "nicht_verknuepft"]
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
    keys = ["detail", "uebersicht", "statistik", "nicht_verknuepft"]
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


