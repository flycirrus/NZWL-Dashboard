# NZWL Zahlungsplanung & Liquiditätssteuerung

## Projektübersicht
Dieses Projekt ist ein Dashboard zur **Zahlungsplanung und Liquiditätssteuerung** für die Neue ZWL Zahnradwerk Leipzig GmbH (NZWL) und ZWL Slovakia s.r.o. Das Dashboard ermöglicht es den Anwendern, offene Kreditoren- und Debitorenpositionen zu überwachen, Zahlungen anhand von Fälligkeiten und Skontofristen zu planen, Zahlungen nach Rolle freizugeben und die Liquidität pro Kalenderwoche (KW) im Vorfeld zu verfolgen.

Die Kernlogik für die Datenbereinigung und Berechnung von Fälligkeiten ist pythonbasiert und vom User Interface (Streamlit) getrennt. Die SAP Daten werden manuell aus Excel in den `data/input` Ordner importiert (100% lokale Ausführung).

## Funktionen (Phase 1)
- **Import:** Manueller Import aller SAP Standard-Exceltabellen-Exporte.
- **Berechnung & Priorisierung:** Automatische Berechnung von Fälligkeiten und Skontofristen.
- **Liquiditätstracking:** Liquiditätsansicht pro Kalenderwoche basierend auf offenen Debitoren und geplanten Zahlungsausgängen.
- **Dashboard:** Kennzahlen, Zahlungsvorschlags-Charts und Limitierungskarten.
- **Berichte:** Basis-Reportings und Revisionsprotokolle.
- **Vollständige Lokalität:** Keine Cloud-Verbindungen, keine externe API – DSGVO-konform.

## Installation und Setup

Dieses Dashboard basiert auf **Python 3.10+**. Stellen Sie sicher, dass Python installiert ist, bevor Sie fortfahren.

### Schnellstart (Empfohlen)

**Für Mac / Linux:**
1. Terminal öffnen und in den Projektordner navigieren.
2. Das Skript ausführbar machen:
   ```bash
   chmod +x run.sh
   ```
3. Das Skript ausführen, welches automatisch eine virtuelle Umgebung erstellt, Abhängigkeiten installiert und das Dashboard startet:
   ```bash
   ./run.sh
   ```

**Für Windows:**
1. Doppelklick auf die `run.bat` Datei im Projektordner. Das Skript richtet automatisch eine virtuelle Umgebung ein und startet die App.

### Manuelle Installation

1. Erstellen einer virtuellen Umgebung:
   ```bash
   python -m venv venv
   ```
2. Aktivieren der virtuellen Umgebung:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
3. Abhängigkeiten installieren:
   ```bash
   pip install -r requirements.txt
   ```
4. Dashboard starten:
   ```bash
   streamlit run dashboard/app.py
   ```

## Ordnerstruktur
- `core/`: Enthält die gesamte Python Business Logik (SAP Datenimport, Datenaufbereitung, Berechnungen und Datenmodelle).
- `dashboard/`: Beinhaltet die Streamlit UI Dateien (App, Seiten-Layout, Charts und Tabellen-Komponenten).
- `data/`: In diesem Verzeichnis befinden sich die Ordner `input` (für SAP-Excel-Dateien), `dummy` sowie der `output` für PDF- oder Excel-Exporte.
- `tests/`: Beinhaltet die Pytest Unit- und Integrations-Tests.

## Gestaltungsrichtlinien
Das Design hält sich streng an die Corporate Identity Vorgaben:
- **Sekundärfarbe/Primärfarbe:** NZWL Dark Blue (#1F4E79), Mid Blue (#2E75B6).
- **Gesellschafts-Buttons:** NZWL Leipzig (`Blau`) & ZWL Slovakia (`Grün`).
- **Statusindikatoren:** Rot (überfällig), Orange (bald fällig), Grün (freigegeben), Blau (ausstehend).

---
*Internes Tool der NZWL Gruppe. Es erfolgt keine Cloud-Synchronisierung von Finanz- oder ERP-Daten.*
