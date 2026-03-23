# System Instructions: NZWL Zahlungsplanung & Liquiditätssteuerung

## Project Overview

Build a **payment planning and liquidity management dashboard** for Neue ZWL Zahnradwerk Leipzig GmbH and ZWL Slovakia s.r.o. The app allows users to monitor open creditor and debitor positions, plan payments based on due dates and discount deadlines, approve payments by role, and track liquidity per calendar week.

The Python core logic (data import, calculation, business rules) is provided separately in `/core/`. The UI must **only call functions from the core** — never rewrite or duplicate business logic.

All data is imported manually from SAP Excel exports. No cloud, no direct SAP connection. The app runs 100% locally on the NZWL network.

---

## Navigation Structure

### Top Navigation Tabs
- Dashboard (home / default view)
- Offene Posten (open positions)
- Zahlungsplanung (payment planning)
- Liquidität (liquidity overview)
- Berichte (reports)

### Header Elements
- Dark / Light mode toggle
- Settings
- Search
- User profile with name, avatar and role badge
- Active company selector: **NZWL Leipzig** | **ZWL Slovakia** | **Beide**

---

## Dashboard Page

### Key Metrics Section (4 Cards)

**Card 1: Gesamtverbindlichkeiten (Total Open Liabilities)**
- Display total open creditor liabilities
- Split: NZWL Leipzig vs ZWL Slovakia
- Show change vs previous month

**Card 2: Fällig diese Woche (Due This Week)**
- Total amount due within current calendar week
- Highlight if critical (red if > spending limit)

**Card 3: Skontopotenzial (Discount Potential)**
- Total available discount if paid within discount deadline
- Amount saved vs total

**Card 4: Liquiditätsstatus (Liquidity Status)**
- Current liquidity balance
- Indicator: sufficient / tight / critical

### Liquiditätsübersicht Chart (Liquidity Overview)
- Bar chart showing expected inflows (Debitoren) vs planned outflows (Kreditoren) per calendar week
- Time period selector: Diese Woche, Nächste 4 Wochen, Nächste 8 Wochen, Dieses Jahr
- Split bars: NZWL Leipzig (blue) vs ZWL Slovakia (green)
- Display calendar week (KW) on X-axis
- Display amounts in EUR on Y-axis
- Include legend

### Zahlungsvorschlag Chart (Payment Proposal Chart)
- Donut chart showing payment allocation by category
- Display total amount to pay in center
- Display already approved amount in center
- Break down by supplier categories:
  - Sonstige Dienstleistung / Reparatur
  - Ersatzteile
  - Hilfsmaterial
  - Kooperation
  - Speditionen
  - Energie
  - Werkzeuge
- Time period selector: Diese Woche, Dieser Monat, Nächste 4 Wochen
- Include legend with category names and amounts

### Letzte Aktivitäten (Recent Activity Table)
- Filter dropdown: Diese Woche, Dieser Monat, Alle
- "Alle anzeigen" link to full Offene Posten page
- Table columns:
  - Lieferant / Kreditor name (with avatar showing initials)
  - Kreditor-Nr.
  - Status (Freigegeben / Ausstehend / Abgelehnt / Überfällig)
  - Fälligkeit (due date)
  - Betrag EUR (amount)
- Color coding:
  - 🔴 Red = Überfällig (overdue)
  - 🟠 Orange = Fällig in < 7 Tagen
  - 🟢 Green = Freigegeben / paid
  - 🔵 Blue = Ausstehend (pending)
- Show 8-10 most recent entries

### Zahlungslimit Widget (Spending Limit)
- Display monthly payment / spending limit
- Show current amount approved for payment
- Show remaining limit
- Progress bar indicating usage percentage
- Warning indicator when > 80% used

### Kreditoren Übersicht Widget (Creditor Overview)
- List top 5 creditors by open amount
- Show: Kreditor name, Kreditor-Nr., open amount, next due date
- "Alle anzeigen" link

---

## Offene Posten Page (Open Positions)

### Features
- Full list of all open creditor positions
- Search by creditor name, Kreditor-Nr., or document number
- Filter by:
  - Gesellschaft (NZWL Leipzig / ZWL Slovakia / Beide)
  - Status (Freigegeben / Ausstehend / Überfällig / Alle)
  - Fälligkeit range (date picker)
  - Kategorie / Zahlungsziel
  - Skonto verfügbar (yes/no)
- Sort by: Fälligkeit, Betrag, Kreditor, Status
- Pagination

### Open Position List Display
- Avatar with creditor initials
- Kreditor / Lieferant name
- Kreditor-Nr.
- Dokumentennummer (invoice reference)
- Zahlungsziel (payment term: e.g. "80 Tage netto", "14T 2% 30T netto")
- Skontoziel (discount deadline)
- Fälligkeit (due date)
- Status badge (color coded)
- Betrag EUR
- Gesellschaft badge (NZWL / ZWL SK)
- Checkbox for batch selection

### Batch Actions
- Select multiple positions
- Approve selected for payment
- Export selected to Excel

### Position Detail View
- Click to expand full details
- Show: all fields + linked material, Stückliste reference, Endkunde connection
- Action buttons: Freigeben (approve), Ablehnen (reject), Kommentar hinzufügen

---

## Zahlungsplanung Page (Payment Planning)

### Payment Proposal Table
- Generated from Python core calculation
- Shows proposed payments sorted by priority (Fälligkeit + Skonto logic)
- Columns:
  - Priorität (1, 2, 3...)
  - Kreditor name
  - Kreditor-Nr.
  - Betrag
  - Fälligkeit
  - Skontobetrag (if applicable)
  - Zahlungsziel
  - Gesellschaft
  - Freigabe-Status

### Freigabe Workflow (Approval Workflow)
- **Vorbereiter role**: can prepare and suggest payment list
- **Geschäftsleitung role**: final approval — single click to approve/reject each position or approve all
- **FiBu role**: receives approved payment list, confirms execution of transfer
- Approved payments are locked for editing
- All actions are logged with timestamp and user

### Zahlungsanweisung (Payment Instruction Export)
- After Geschäftsleitung approval: generate payment instruction document
- Export as Excel / PDF
- Automatically sent to FiBu role dashboard
- Includes: Kreditor, IBAN (if available), Betrag, Referenz, Datum

### Sammelzahlung (Batch Payment)
- Option to group multiple positions per creditor into one payment
- Show: total per creditor, individual invoices, due dates
- Approve as single payment instruction

---

## Liquidität Page (Liquidity Overview)

### Weekly Liquidity View
- Table view: Calendar Week vs Expected In/Out
- Columns: KW, Erwartete Einzahlungen (Debitoren), Geplante Auszahlungen (Kreditoren), Netto Liquidität
- Color: green if positive, red if negative
- Both companies side by side or toggled

### Liquiditäts-Trend Chart
- Line chart showing liquidity balance over time
- Compare current vs previous period
- Time period selector: 4 Wochen, 8 Wochen, 3 Monate

### Debitoren Übersicht (Incoming Payments)
- List of expected incoming payments from customers
- Source: SAP Offene Posten Debitoren + Lieferplan VL10A
- Columns: Debitor / Endkunde, Betrag, erwartetes Datum, Status
- Filter by Gesellschaft

---

## Berichte Page (Reports)

### Wochenreport (Weekly Report)
- Select calendar week
- Display:
  - Total approved payments
  - Total overdue positions
  - Discount captured vs missed
  - Number of transactions processed
  - Liquidity status at start vs end of week

### Monatsreport (Monthly Report)
- Select month and year
- Display:
  - Total Kreditoren paid
  - Total Debitoren received
  - Net liquidity change
  - Top creditor categories by amount
  - Number of positions processed per Gesellschaft

### Revisionsprotokoll (Audit Log)
- Complete log of all actions taken in the system
- Columns: Zeitstempel, Benutzer, Rolle, Aktion, Position / Betrag, Kommentar
- Filter by user, role, action type, date range
- Export to Excel / PDF

### Export Options
- Export to CSV
- Export to PDF
- Select date range for export
- Select Gesellschaft filter before export

---

## Data Model

### User
```json
{
  "id": "string",
  "name": "string",
  "email": "string",
  "role": "vorbereiter | geschaeftsleitung | fibu | viewer | admin",
  "gesellschaft": "nzwl | zwl_sk | beide",
  "avatar": "string | null",
  "monthlyPaymentLimit": "number",
  "createdAt": "timestamp"
}
```

### Kreditor Position (Open Creditor Position)
```json
{
  "id": "string",
  "kreditorId": "string",
  "kreditorName": "string",
  "dokumentenNr": "string",
  "gesellschaft": "nzwl | zwl_sk",
  "betrag": "number",
  "waehrung": "EUR",
  "faelligkeit": "timestamp",
  "zahlungsziel": "string",
  "skontoziel": "timestamp | null",
  "skontobetrag": "number | null",
  "kategorie": "string",
  "status": "ausstehend | freigegeben | abgelehnt | ueberfaellig | bezahlt",
  "materialId": "string | null",
  "endkundeId": "string | null",
  "createdAt": "timestamp"
}
```

### Zahlung (Payment / Approval)
```json
{
  "id": "string",
  "kreditorPositionId": "string",
  "betrag": "number",
  "typ": "einzelzahlung | sammelzahlung",
  "status": "vorbereitet | freigegeben | ausgefuehrt | storniert",
  "vorbereiterId": "string",
  "geschaeftsleitungId": "string | null",
  "fibuConfirmedId": "string | null",
  "freigegebenAm": "timestamp | null",
  "ausgefuehrtAm": "timestamp | null",
  "kommentar": "string | null",
  "createdAt": "timestamp"
}
```

### Kreditor (Creditor Master Data)
```json
{
  "id": "string",
  "kreditorNr": "string",
  "name": "string",
  "ansprechpartner": "string | null",
  "email": "string | null",
  "zahlungszielNetto": "number",
  "skontozielNetto": "number | null",
  "adresse": "string | null",
  "gesellschaft": "nzwl | zwl_sk",
  "createdAt": "timestamp"
}
```

### Liquiditaet (Liquidity Entry per KW)
```json
{
  "id": "string",
  "kalenderwoche": "string (YYYY-KWxx)",
  "gesellschaft": "nzwl | zwl_sk",
  "erwarteteEinzahlungen": "number",
  "geplanteAuszahlungen": "number",
  "nettoLiquiditaet": "number",
  "createdAt": "timestamp"
}
```

### AuditLog
```json
{
  "id": "string",
  "zeitstempel": "timestamp",
  "userId": "string",
  "userName": "string",
  "rolle": "string",
  "aktion": "string",
  "referenzId": "string | null",
  "betrag": "number | null",
  "kommentar": "string | null"
}
```

---

## SAP Data Sources (Input Files)

The Python core imports the following SAP export files from `/data/input/`:

| File | Content | Key Fields |
|------|---------|------------|
| `SAP_OPOS_Vertrieb.xlsx` | Offene Posten Kreditoren | Kreditor-ID, Zahlungsziel, Fälligkeit, Skontoziel, Betrag |
| `SAP_Stuecklisten.xlsx` | Strukturstücklisten CS12 | Material-ID, Rohteil-ID, Stückzahl, Makro |
| `SAP_Materialbelege_Vertrieb.xlsx` | Materialbewegungen | Bewegungsart (600–680 Debitoren, 100–103 Kreditoren), Datum, Wert |
| `SAP_FM_Lieferungen_offen.xlsx` | Lieferplan VL10A | Kunde-ID, Material-ID, Datum, Menge, EUR |
| `SAP_Stammdaten_Kreditoren.xlsx` | Kreditoren Stammdaten | ID, Name, E-Mail, Zahlungsziel, Adresse |
| `SAP_offen_Posten_Debitoren.xlsx` | Offene Posten Debitoren | Debitor-ID, Betrag, Fälligkeit, Nettoziel |

---

## Roles & Permissions

| Role | Permissions |
|------|------------|
| **Vorbereiter** | Import data, view all positions, prepare payment proposals, add comments |
| **Geschäftsleitung** | All Vorbereiter rights + final approve / reject payments, set payment rules |
| **FiBu** | View approved payment instructions, confirm execution of transfers |
| **Viewer** | Read-only access to dashboard and reports |
| **Administrator** | User management, system settings, all access |

**Rule:** Payment instructions can only be triggered by Geschäftsleitung.

---

## Core Python Integration

### Import Pattern
```python
from core.data_import import load_sap_files
from core.calculations import calculate_payments, calculate_liquidity
from core.models import KreditorPosition, Zahlung
from core.export import export_excel, export_pdf
```

### The UI Must Never:
- Rewrite calculation logic (Fälligkeit, Skonto, Priorität)
- Rewrite data import / parsing logic
- Duplicate data models from `/core/models.py`

### The UI Calls Core Functions:
- `load_sap_files(path)` → returns consolidated DataFrame
- `calculate_payments(df, rules)` → returns prioritized payment list
- `calculate_liquidity(df, weeks)` → returns liquidity per KW
- `export_excel(data, filename)` → generates Excel file
- `export_pdf(data, filename)` → generates PDF report

---

## Folder Structure

```
nzwl-zahlungsplanung/
├── core/
│   ├── __init__.py
│   ├── data_import.py        # SAP Excel import & consolidation
│   ├── data_processing.py    # Cleaning & validation
│   ├── calculations.py       # Fälligkeit, Skonto, liquidity logic
│   ├── models.py             # Data models
│   └── export.py             # Excel/CSV/PDF export
├── dashboard/
│   ├── __init__.py
│   ├── app.py                # Streamlit main app
│   ├── auth.py               # Role-based login
│   ├── pages/
│   │   ├── dashboard.py      # Main dashboard
│   │   ├── offene_posten.py  # Open positions
│   │   ├── zahlungsplanung.py # Payment planning
│   │   ├── liquiditaet.py    # Liquidity overview
│   │   └── berichte.py       # Reports
│   └── components/
│       ├── charts.py         # Reusable chart components
│       ├── tables.py         # Reusable table components
│       └── cards.py          # Metric cards
├── data/
│   ├── input/                # SAP export files go here
│   ├── output/               # Generated reports
│   └── dummy/                # Anonymized test data
├── tests/
│   ├── test_calculations.py
│   ├── test_data_import.py
│   └── test_export.py
├── .github/
│   └── workflows/
│       └── push.yml          # Auto-push after tests pass
├── .gitignore
├── requirements.txt
├── README.md
├── run.sh                    # Mac/Linux one-click start
└── run.bat                   # Windows one-click start
```

---

## Default Categories

### Kreditor / Expense Categories
- Sonstige Dienstleistung / Reparatur
- Ersatzteile
- Hilfsmaterial
- Kooperation
- Speditionen
- Energie
- Werkzeuge
- Sonstige Werkzeuge

### Debitor / Income Categories
- Bauteil-Lieferung (Invoice-based)
- Lieferschein-basiert (VL10A)

### Budget / Planning Categories
- Investitionen
- Logistik / Transport
- Material & Produktion
- Energie & Betrieb
- Dienstleistungen

---

## Core Functionalities

### Data Import & Consolidation
- Import all SAP export files from `/data/input/`
- Validate data completeness and consistency
- Consolidate NZWL Leipzig and ZWL Slovakia data separately
- Link: Rechnung → Material ID → Stückliste (CS12) → Endkunde
- Flag missing or inconsistent records

### Payment Calculation & Prioritization
- Calculate due dates per creditor position
- Calculate discount deadlines and discount amounts
- Priority scoring: overdue first, then discount deadline, then net due date
- Generate payment proposal list based on priority rules
- Calculate available liquidity after planned payments

### Approval Workflow
- Vorbereiter prepares proposal list
- Geschäftsleitung approves / rejects individual positions or full list
- FiBu receives approved payment instruction, confirms execution
- Full audit trail of every action

### Liquidity Tracking
- Calculate expected inflows from Debitoren (open positions + Lieferplan)
- Calculate planned outflows from approved Kreditoren payments
- Show net liquidity per calendar week
- Alert if liquidity becomes critical

### Reporting & Export
- Generate weekly and monthly reports
- Export payment instructions to Excel and PDF
- Automated e-mail report to creditors after payment approval
- Full revision-proof audit log export

---

## MVP Features (Phase 1 — Python Core + Dashboard)

- Data import from all SAP Excel sources
- Payment calculation and prioritization logic
- Liquidity overview per calendar week
- Dashboard with key metrics (liabilities, due this week, discount potential, liquidity)
- Open positions table with filters
- Payment proposal list
- Simple single-user dashboard (Streamlit)
- Export to Excel / CSV
- Revision log (basic)
- Both companies (NZWL + ZWL SK) supported

## Phase 2 Features

- Multi-user login with role-based access (Vorbereiter, Geschäftsleitung, FiBu, Viewer, Admin)
- Full approval workflow with Geschäftsleitung freigabe
- Automated e-mail report to creditors and FiBu after payment approval
- Payment instruction PDF generation
- Enhanced analytics and reporting
- Audit log with full export

## Features Excluded from MVP

- Direct SAP / ERP / Hana connection
- Automated data refresh (manual import only)
- Cloud hosting or external data transfer
- Currency conversion
- Bank account sync or real payment processing
- Mobile app

---

## Technical Requirements

### Data Storage
- Phase 1: File-based (Excel / CSV input, local output)
- Phase 2: Local SQLite database for persistence across sessions
- Structure data for potential future migration

### Charts
- Interactive charts with tooltips
- Responsive sizing
- Calendar week filtering

### Forms & Validation
- Input validation on all forms
- Error messages for invalid inputs
- Confirmation dialogs for approve / reject actions

### Performance
- Fast load on 5,000+ creditor positions
- Smooth filtering and sorting
- Excel import < 10 seconds for full dataset

### Security
- Role-based access control
- No sensitive data transmitted externally
- All data stays within NZWL internal network

---

## Design Guidelines

- Language: **German throughout** (labels, buttons, messages)
- Color scheme: Dark blue (`#1F4E79`) and white — professional, corporate
- Status colors:
  - 🔴 Red: Überfällig (overdue)
  - 🟠 Orange: Fällig bald (due soon < 7 days)
  - 🟢 Green: Freigegeben / OK
  - 🔵 Blue: Ausstehend (pending)
- Responsive layout
- Clean sidebar navigation
- Company badge always visible (NZWL / ZWL SK)

---

## Summary

Build a payment planning and liquidity management dashboard for NZWL Leipzig and ZWL Slovakia. Core features: open creditor position overview, payment prioritization based on due dates and discount deadlines, approval workflow by role, liquidity tracking per calendar week, automated payment instruction export, and audit logging. Python core logic is pre-built — the UI only calls core functions. All data stored locally, no cloud, no SAP direct connection. Phase 1: single-user Streamlit dashboard. Phase 2: multi-user with roles, e-mail automation, and full approval workflow.