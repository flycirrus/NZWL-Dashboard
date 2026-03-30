# NZWL Brand Guidelines
## Neue ZWL Zahnradwerk Leipzig GmbH

---

## Brand Name

**NZWL** — Neue ZWL Zahnradwerk Leipzig GmbH

### Acceptable Usage
- NZWL (short form, always uppercase)
- Neue ZWL Zahnradwerk Leipzig GmbH (full legal name)
- NZWL Leipzig (when distinguishing from ZWL Slovakia)
- ZWL Slovakia / ZWL SK (for the Slovak subsidiary)

### Unacceptable Usage
- Nzwl (mixed case)
- nzwl (all lowercase)
- New ZWL (English translation)
- NZW (abbreviated incorrectly)

---

## Logo Usage

### Logo Description
The NZWL logo consists of a gear/cog wheel icon (representing precision manufacturing) combined with the "NZWL" wordmark. Two versions exist:
- **Standard version**: Dark logo on light background
- **Inverted version**: White logo on dark/blue background

### Clear Space
Maintain clear space around the logo equal to the height of the "N" in NZWL on all sides.

### Minimum Size
- Digital: 120px width minimum
- Print: 25mm width minimum

### Logo Don'ts
- Do not stretch or distort the logo
- Do not rotate the logo
- Do not change logo colors outside approved variations
- Do not add effects (shadows, gradients, outlines)
- Do not place the logo on busy or low-contrast backgrounds
- Do not use the gear icon without the wordmark in official documents

---

## Color Palette

### Primary Color

**NZWL Dark Blue**
- HEX: `#1F4E79`
- RGB: 31, 78, 121
- HSL: 210°, 59%, 30%
- Use as: Primary brand color, headers, navigation, key UI elements, sidebar, buttons

### Secondary Colors

**NZWL Mid Blue**
- HEX: `#2E75B6`
- RGB: 46, 117, 182
- Use as: Accents, hover states, secondary buttons, chart colors, links, subheadings

**NZWL Light Blue**
- HEX: `#D6E4F0`
- RGB: 214, 228, 240
- Use as: Table row highlights, card backgrounds, subtle fills, info badges

**NZWL Navy**
- HEX: `#0D2B45`
- RGB: 13, 43, 69
- Use as: Dark backgrounds, footer, high-contrast text areas

### Company Accent Colors
Used to distinguish the two entities in the dashboard:

**NZWL Leipzig**
- HEX: `#1F4E79` (Dark Blue — primary)
- Badge background: `#D6E4F0`
- Badge text: `#1F4E79`

**ZWL Slovakia**
- HEX: `#38761D` (Dark Green)
- Badge background: `#D9EAD3`
- Badge text: `#38761D`

### Status Colors

**Überfällig (Overdue)**
- HEX: `#C00000` (Red)
- Background: `#FCEBEB`

**Fällig bald (Due Soon < 7 days)**
- HEX: `#E65100` (Orange)
- Background: `#FFF3E0`

**Freigegeben / OK (Approved)**
- HEX: `#38761D` (Green)
- Background: `#D9EAD3`

**Ausstehend (Pending)**
- HEX: `#2E75B6` (Mid Blue)
- Background: `#D6E4F0`

### Neutral Colors

**White**
- HEX: `#FFFFFF`
- Use as: Card backgrounds, page backgrounds, text on dark surfaces

**Light Gray**
- HEX: `#F5F7FA`
- Use as: Page background, subtle dividers, alternating table rows

**Mid Gray**
- HEX: `#E0E0E0`
- Use as: Borders, input field borders, dividers

**Dark Gray**
- HEX: `#555555`
- Use as: Secondary text, labels, metadata

**Near Black**
- HEX: `#1A1A1A`
- Use as: Primary headings, main body text

---

## Typography

### Primary Font
**Arial** (universally available, no web font dependency required)
Fallbacks: Helvetica Neue, Helvetica, sans-serif

### Font Weights
- **Bold (700)**: Main headings, KPI values, critical labels
- **Semi-Bold (600)**: Subheadings, table headers, card titles
- **Regular (400)**: Body text, table rows, descriptions
- **Light (300)**: Captions, footnotes, secondary metadata (use sparingly)

### Font Sizes
- H1: 28px / 1.75rem — Page titles
- H2: 22px / 1.375rem — Section headings
- H3: 18px / 1.125rem — Card headings, widget titles
- Body: 16px / 1rem — Standard text
- Small: 14px / 0.875rem — Table content, labels
- Caption: 12px / 0.75rem — Footnotes, badges, timestamps

### Line Height
- Headings: 1.2
- Body text: 1.6
- Table rows: 1.4

### Language
- **All UI text in German** — labels, buttons, messages, tooltips
- Exception: Technical terms and SAP field names remain as-is (e.g. "Kreditor-ID", "OPOS", "FiBu")

---

## UI Elements

### Buttons

**Primary Button (Freigeben / Approve)**
- Background: NZWL Dark Blue (`#1F4E79`)
- Text: White (`#FFFFFF`)
- Border Radius: 8px
- Padding: 10px 20px
- Hover: Mid Blue (`#2E75B6`)

**Secondary Button**
- Background: Transparent
- Border: 2px solid NZWL Dark Blue (`#1F4E79`)
- Text: NZWL Dark Blue (`#1F4E79`)
- Border Radius: 8px
- Hover: Light Blue background tint (`#D6E4F0`)

**Danger Button (Ablehnen / Delete)**
- Background: `#C00000`
- Text: White
- Hover: `#A00000`

**Export Button**
- Background: `#38761D` (Green)
- Text: White
- Use for: Excel export, PDF export, Zahlungsanweisung

### Cards / Widgets
- Background: White (`#FFFFFF`)
- Border Radius: 12px
- Border: 1px solid `#E0E0E0`
- Shadow: `0 2px 8px rgba(0, 0, 0, 0.06)`
- Padding: 20px

### KPI Metric Cards
- Background: White
- Left accent border: 4px solid NZWL Dark Blue
- Title: Dark Gray (`#555555`), 13px
- Value: Near Black (`#1A1A1A`), 28px Bold
- Change indicator: Green for positive, Red for negative

### Tables
- Header background: NZWL Dark Blue (`#1F4E79`)
- Header text: White, 14px Semi-Bold
- Row alternating: White / Light Gray (`#F5F7FA`)
- Row hover: Light Blue (`#EAF4FB`)
- Border: 1px solid `#E0E0E0`
- Cell padding: 10px 12px

### Status Badges
- Rounded pill shape: `border-radius: 20px`
- Padding: 4px 12px
- Font size: 12px, Semi-Bold
- Colors: see Status Colors above

### Input Fields
- Border: 1px solid `#E0E0E0`
- Border Radius: 8px
- Focus Border: NZWL Dark Blue (`#1F4E79`)
- Focus Shadow: `0 0 0 3px rgba(31, 78, 121, 0.15)`
- Background: White
- Font size: 14px

### Sidebar Navigation
- Background: NZWL Dark Blue (`#1F4E79`)
- Text: White, 14px
- Active item: Mid Blue (`#2E75B6`) background, White text
- Hover: `rgba(255,255,255,0.1)` overlay
- Icon + label layout

---

## Charts & Data Visualization

### Chart Color Sequence
Use in this order for multi-series charts:
1. `#2E75B6` — Mid Blue (primary series)
2. `#38761D` — Green (ZWL SK or secondary series)
3. `#E65100` — Orange (warnings, overdue)
4. `#7B68EE` — Purple (additional series)
5. `#E0E0E0` — Gray (neutral / comparison)

### Chart Rules
- Always include tooltips showing exact amounts in EUR
- X-axis: Calendar weeks (KW 01, KW 02...) or months (Jan, Feb...)
- Y-axis: Always in EUR, formatted with thousands separator (e.g. 1.250.000 €)
- Include legend for all multi-series charts
- Responsive sizing — adapt to container width

### Donut / Pie Charts
- Center text: Total amount in bold
- Slice colors: use Chart Color Sequence
- Legend below or to the right

---

## Iconography

- Style: Outlined, consistent stroke width (2px)
- Size: 24px standard, 20px small, 32px large
- Color: Match text color, or NZWL Dark Blue for emphasis
- Recommended icon set: Lucide Icons or Heroicons (open source)

### Key Icons Used
- 💳 Payment / Zahlung → credit-card icon
- 📊 Liquidität / Charts → bar-chart icon
- ✅ Freigegeben → check-circle icon
- ❌ Abgelehnt → x-circle icon
- ⏰ Fällig bald → clock icon
- 🔴 Überfällig → alert-circle icon
- 📥 Import / SAP → upload icon
- 📤 Export → download icon
- 🏭 NZWL Leipzig → building icon
- 🌍 ZWL Slovakia → globe icon

---

## Company Branding in Dashboard

### Company Selector
Always display the active company in the header:
- `[🏭 NZWL Leipzig]` — Dark Blue badge
- `[🌍 ZWL Slovakia]` — Green badge
- `[Beide Gesellschaften]` — Split badge (blue + green)

### Company Badges in Tables
Every data row from SAP must show its company source:
- **NZWL** — Blue pill badge (`#D6E4F0` background, `#1F4E79` text)
- **ZWL SK** — Green pill badge (`#D9EAD3` background, `#38761D` text)

---

## Tone of Voice

- **Professionell**: Klar, präzise, vertrauenswürdig — passend für Finanzdaten
- **Direkt**: Keine unnötigen Floskeln — Entscheidungsträger wollen Fakten
- **Deutsch**: Alle Labels, Meldungen und Buttons auf Deutsch
- **Industriell**: Sachlich, keine emotionale Sprache — Manufacturing-Kontext

### Example UI Copy
- ✅ "Zahlung freigeben" (not "Zahlung bestätigen" or "OK")
- ✅ "Überfällig seit 5 Tagen" (not "Diese Rechnung ist zu spät")
- ✅ "Daten werden importiert..." (not "Bitte warten")
- ✅ "Keine offenen Posten gefunden" (not "Alles erledigt!")
- ✅ "Abbrechen" / "Speichern" (not "Nein" / "Ja")

---

## Accessibility

- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- All status colors must not rely on color alone — always pair with icon or text label
- Interactive elements minimum size: 44px × 44px touch target
- Focus states visible on all interactive elements

---

## Dashboard-Specific Design Rules

1. **Company always visible** — active company badge in header at all times
2. **Status always color + text** — never color alone (accessibility)
3. **Amounts always in EUR** — formatted: `1.250.000,00 €`
4. **Dates always in German format** — `TT.MM.JJJJ` or `KW 12 / 2026`
5. **Negative amounts in red** — positive in dark text (not green, to avoid confusion with status)
6. **Audit trail visible** — every approval action shows who/when/role
7. **Data source labeled** — always show which SAP file the data comes from

---

## Summary

NZWL's visual identity is built on precision, trust, and industrial professionalism. The dashboard must reflect these values: clean layout, clear data hierarchy, dark blue as the dominant brand color, German language throughout, and unambiguous status indicators. Both companies (NZWL Leipzig and ZWL Slovakia) must always be clearly distinguishable — blue for Leipzig, green for Slovakia.