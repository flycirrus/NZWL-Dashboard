# NZWL Payment Planning & Liquidity Management

## Project Overview
This project is a **payment planning and liquidity management dashboard** for Neue ZWL Zahnradwerk Leipzig GmbH (NZWL) and ZWL Slovakia s.r.o. The dashboard allows users to monitor open creditor and debitor positions, plan payments based on due dates and discount deadlines, approve payments based on specific roles, and proactively track liquidity per calendar week.

The core logic for data processing and due date calculations is Python-based and strictly separated from the User Interface (Streamlit). SAP data is manually imported from Excel exports into the `data/input` directory (100% local execution).

## Features (Phase 1 & 2)
- **Import:** Manual import of all SAP standard Excel exports.
- **Calculation & Prioritization:** Automatic calculation of due dates and discount periods.
- **Multi-User & Approval Workflow:** Two-step payment approval process (Preparer -> Management -> Accounting) with dedicated login system.
- **Admin & User Management:** Role-based access control managed by administrators.
- **Liquidity Tracking:** Weekly liquidity overview based on open debitors and planned outgoing payments.
- **Dashboard:** Key metrics, payment proposal charts, and limitation cards.
- **Reports:** Automated Audit Log (Revision Protocol) for all executed payment approvals.
- **Full Localization:** No cloud connections, no external APIs – fully GDPR compliant.

## Installation and Setup

This dashboard requires **Python 3.10+**. Please ensure Python is installed before proceeding.

### Quick Start (Recommended)

**For Mac / Linux:**
1. Open a terminal and navigate to the project folder.
2. Make the script executable:
   ```bash
   chmod +x run.sh
   ```
3. Run the script (this automatically creates a virtual environment, installs dependencies, and starts the dashboard):
   ```bash
   ./run.sh
   ```

**For Windows:**
1. Simply double-click the `run.bat` file in the project folder. The script will automatically set up the virtual environment and launch the app.

### Manual Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - Mac/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```

## Folder Structure
- `core/`: Contains the entire Python business logic (SAP data import, processing, calculations, and data models).
- `dashboard/`: Contains the Streamlit UI files (App, Page Layouts, Charts, and Table Components).
- `data/`: Contains the `input` directory (for SAP Excel files), `dummy` data scripts, and `output` directory for PDF or Excel exports.
- `tests/`: Contains Pytest unit and integration tests.

## Design Guidelines
The design strictly adheres to the Corporate Identity rules:
- **Primary/Secondary Colors:** NZWL Dark Blue (#1F4E79), Mid Blue (#2E75B6).
- **Company Buttons:** NZWL Leipzig (`Blue`) & ZWL Slovakia (`Green`).
- **Status Indicators:** Red (overdue), Orange (due soon), Green (approved), Blue (pending).

---
*Internal tool for the NZWL Group. No financial or ERP data is synced to the cloud.*
