"""Generate the NZWL Dashboard User Guide PDF with embedded screenshots."""
from pathlib import Path
from fpdf import FPDF

DOCS = Path(__file__).parent
SHOTS = DOCS / "screenshots"
OUT = DOCS / "NZWL_Dashboard_Benutzerhandbuch_Phase1.pdf"

# ── Brand colours ──
DARK_BLUE  = (31, 78, 121)   # #1F4E79
MID_BLUE   = (46, 117, 182)  # #2E75B6
DARK_TEXT   = (45, 55, 72)
LIGHT_BG    = (240, 242, 246)
WHITE       = (255, 255, 255)
RED         = (192, 0, 0)
GREEN       = (56, 118, 29)
ORANGE      = (214, 158, 46)
GRAY        = (160, 174, 192)


class PDF(FPDF):
    def header(self):
        if self.page_no() <= 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 6, "NZWL Dashboard  |  Benutzerhandbuch Phase 1  |  Stand: 31.05.2026", align="L")
        self.ln(8)

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Vertraulich  |  Nur fuer internen Gebrauch  |  Seite {self.page_no()}", align="C")

    # ── helpers ──
    def section_title(self, num, title):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*DARK_BLUE)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*MID_BLUE)
        self.set_line_width(0.6)
        x = self.l_margin
        self.line(x, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(6)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*MID_BLUE)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_TEXT)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_TEXT)
        x = self.l_margin
        self.set_x(x)
        self.cell(6, 5.5, "-")
        self.multi_cell(self.w - self.r_margin - self.get_x(), 5.5, text)

    def info_box(self, title, text, color=MID_BLUE):
        x = self.l_margin
        w = self.w - self.l_margin - self.r_margin
        # Measure text height first
        self.set_font("Helvetica", "", 9)
        text_h = self.get_string_width(text)
        lines = max(1, int(text_h / (w - 12)) + 1)
        box_h = 8 + lines * 4.5 + 4
        if box_h < 18:
            box_h = 18
        # Check page space
        if self.get_y() + box_h + 4 > self.h - self.b_margin:
            self.add_page()
        y = self.get_y()
        # Background
        if color == ORANGE:
            self.set_fill_color(255, 251, 235)
        elif color == GREEN:
            self.set_fill_color(240, 255, 244)
        elif color == RED:
            self.set_fill_color(255, 245, 245)
        else:
            self.set_fill_color(235, 248, 255)
        self.set_draw_color(*color)
        self.rect(x, y, w, box_h, style="DF")
        self.set_line_width(1.2)
        self.line(x, y, x, y + box_h)
        self.set_line_width(0.2)
        # Title
        self.set_xy(x + 4, y + 2)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*color)
        self.cell(w - 8, 5, title, new_x="LMARGIN", new_y="NEXT")
        # Body
        self.set_x(x + 4)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*DARK_TEXT)
        self.multi_cell(w - 8, 4.5, text)
        self.set_y(y + box_h + 2)

    def table_header(self, cols, widths):
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align="L")
        self.ln()
        self.set_text_color(*DARK_TEXT)

    def table_row(self, cells, widths, even=False):
        self.set_font("Helvetica", "", 9)
        if even:
            self.set_fill_color(247, 250, 252)
        else:
            self.set_fill_color(*WHITE)
        for i, cell in enumerate(cells):
            self.cell(widths[i], 6.5, cell, border=1, fill=True, align="L")
        self.ln()

    def add_screenshot(self, img_name, caption="", max_h=75):
        from PIL import Image as PILImage
        path = SHOTS / img_name
        if not path.exists():
            self.body(f"[Screenshot {img_name} nicht gefunden]")
            return
        # Calculate actual rendered dimensions
        with PILImage.open(path) as img:
            iw, ih = img.size
        content_w = self.w - self.l_margin - self.r_margin
        rendered_h = (ih / iw) * content_w
        if rendered_h > max_h:
            rendered_h = max_h
            render_w = (iw / ih) * max_h
        else:
            render_w = content_w
        # Check if enough space; if not, new page
        avail = self.h - self.get_y() - self.b_margin - 16
        if avail < rendered_h + 10:
            self.add_page()
        x = self.l_margin + (content_w - render_w) / 2
        y = self.get_y()
        # Border
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.rect(x - 0.5, y - 0.5, render_w + 1, rendered_h + 1)
        # Place image with explicit dimensions
        self.image(str(path), x=x, y=y, w=render_w, h=rendered_h)
        # Force cursor below image
        self.set_y(y + rendered_h + 3)
        self.set_x(self.l_margin)
        if caption:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(*GRAY)
            self.cell(content_w, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_text_color(*DARK_TEXT)
        self.ln(4)

    def numbered_step(self, num, title, text):
        x = self.l_margin
        y = self.get_y()
        content_w = self.w - self.l_margin - self.r_margin
        # Circle with number
        self.set_fill_color(*DARK_BLUE)
        self.ellipse(x, y, 7, 7, style="F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(x + 1.2, y + 0.5)
        self.cell(4.5, 6, str(num), align="C")
        # Title
        self.set_xy(x + 10, y)
        self.set_text_color(*DARK_TEXT)
        self.set_font("Helvetica", "B", 10)
        self.cell(content_w - 10, 7, title, new_x="LMARGIN", new_y="NEXT")
        # Body text
        self.set_x(x + 10)
        self.set_font("Helvetica", "", 9.5)
        self.multi_cell(content_w - 10, 5, text)
        self.ln(3)


def build():
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(18, 15, 18)

    # ══════════════════════════════════════
    #  COVER PAGE
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.ln(50)
    # Logo box
    cx = pdf.w / 2
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(cx - 18, pdf.get_y(), 36, 36, style="F")
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(*WHITE)
    pdf.set_xy(cx - 18, pdf.get_y() + 5)
    pdf.cell(36, 26, "ZWL", align="C")
    pdf.ln(40)

    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(*DARK_BLUE)
    pdf.cell(0, 12, "Zahlungsplanung &", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 12, "Liquiditaetssteuerung", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 15)
    pdf.set_text_color(*MID_BLUE)
    pdf.cell(0, 10, "Benutzerhandbuch  -  Phase 1", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(15)

    # Badge
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*DARK_BLUE)
    badge_w = 75
    pdf.set_x(cx - badge_w / 2)
    pdf.set_fill_color(235, 245, 251)
    pdf.set_draw_color(*MID_BLUE)
    pdf.cell(badge_w, 8, "NZWL Leipzig  |  ZWL Slovakia", border=1, fill=True, align="C")
    pdf.ln(30)

    # Meta info
    meta_lines = [
        ("Dokument:", "NZWL Dashboard - User Guide Phase 1"),
        ("Version:", "1.0"),
        ("Stand:", "31. Mai 2026"),
        ("Erstellt fuer:", "ZWL-Kreis - Geschaeftsfuehrung & operative Mitarbeiter"),
        ("Vertraulichkeit:", "Nur fuer internen Gebrauch"),
    ]
    for label, val in meta_lines:
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(74, 85, 104)
        pdf.cell(30, 6, label, align="R")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(113, 128, 150)
        pdf.cell(0, 6, f"  {val}", new_x="LMARGIN", new_y="NEXT")

    # ══════════════════════════════════════
    #  TABLE OF CONTENTS
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title("", "Inhaltsverzeichnis")
    toc = [
        "Ueberblick - Was ist das NZWL Dashboard?",
        "Zugang & Anmeldung",
        "Rollen & Berechtigungen",
        "Navigation & Gesellschaftsfilter",
        "Seite: Dashboard (Startseite & Kennzahlen)",
        "Seite: Faelligkeiten (Hauptarbeitsseite)",
        "Das Ampel-System (Traffic Lights)",
        "Seite: Kreditor-Debitor (Detailansicht)",
        "Seite: Nicht verknuepft (Analyse)",
        "Seite: Admin-Bereich",
        "Daten exportieren (CSV)",
        "Hinweise & FAQ",
        "Phase-2-Ausblick",
    ]
    for i, entry in enumerate(toc, 1):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(10, 8, f"{i}.")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        pdf.cell(0, 8, entry, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(237, 242, 247)
        pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())

    # ══════════════════════════════════════
    #  1. ÜBERBLICK
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(1, "Ueberblick")
    pdf.body(
        "Das NZWL Dashboard ist eine webbasierte Anwendung fuer den ZWL-Kreis "
        "zur Ueberwachung und Steuerung von Kreditoren-Verbindlichkeiten. "
        "Das System verknuepft automatisch offene Rechnungen (Kreditoren) mit den "
        "zugehoerigen Endkunden (Debitoren) und zeigt auf einen Blick, welche "
        "Zahlungen wann faellig sind."
    )

    pdf.sub_title("Kernfunktionen Phase 1")
    features = [
        ("Dashboard", "Kennzahlen, Top-Kreditoren-Diagramme, Match-Quote"),
        ("Faelligkeiten", "Alle Belege mit Ampel-Status, Filter, Sortierung, Sammel-Aktionen"),
        ("Kreditor-Debitor", "Detailansicht: Rohteil > Fertigteil > Endkunde"),
        ("Nicht verknuepft", "Analyse nicht zuordenbarer Belege nach Grund und Branche"),
        ("Ampel-System", "Belege per Klick als Rot/Gelb/Gruen markieren - revisionssicher"),
        ("Admin-Bereich", "Nutzerverwaltung, Ampel-Historie, System-Rollback"),
        ("CSV-Export", "Alle Seiten mit Download-Option"),
        ("Gesellschaftsfilter", "Daten nach NZWL oder ZWL SK einschraenken"),
    ]
    w1, w2 = 40, pdf.w - pdf.l_margin - pdf.r_margin - 40
    pdf.table_header(["Funktion", "Beschreibung"], [w1, w2])
    for i, (f, d) in enumerate(features):
        pdf.table_row([f, d], [w1, w2], even=i % 2 == 0)

    pdf.ln(4)
    pdf.info_box(
        "Datenquelle",
        "Die Daten stammen aus der Kernlogik - einem automatisierten Prozess, der SAP-Daten analysiert "
        "und Kreditoren mit Debitoren ueber eine 4-Schritt-Kette verknuepft.",
        MID_BLUE,
    )
    pdf.ln(2)
    pdf.info_box(
        "Demo-System",
        "Phase 1 laeuft im Testbetrieb. Auf dem Login-Bildschirm erscheint ein entsprechender Hinweis.",
        ORANGE,
    )

    # ══════════════════════════════════════
    #  2. ZUGANG & ANMELDUNG
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(2, "Zugang & Anmeldung")

    pdf.sub_title("Dashboard aufrufen")
    pdf.body(
        "Oeffnen Sie einen Webbrowser (Chrome oder Edge empfohlen) und navigieren Sie "
        "zur internen Server-Adresse:"
    )
    pdf.info_box(
        "Dashboard-URL",
        "http://<Server-IP>:8501 - Die genaue Adresse erhalten Sie von Ihrem Projektleiter.",
        GREEN,
    )

    pdf.ln(4)
    pdf.sub_title("Login-Bildschirm")
    pdf.add_screenshot("login.png", "Abb. 1: Login-Seite mit Demo-Hinweis")

    pdf.add_page()
    pdf.sub_title("Anmeldevorgang")
    pdf.numbered_step(1, "Benutzername eingeben", "Tragen Sie Ihren persoenlichen Benutzernamen ein.")
    pdf.numbered_step(2, "Passwort eingeben", "Tragen Sie Ihr Passwort ein.")
    pdf.numbered_step(3, "\"Einloggen\" klicken", "Bei Erfolg gelangen Sie direkt zum Dashboard.")

    pdf.ln(2)
    pdf.sub_title("Demo-Zugangsdaten")
    w_cols = [35, 25, 50, pdf.w - pdf.l_margin - pdf.r_margin - 110]
    pdf.table_header(["Benutzer", "Passwort", "Rolle", "Beschreibung"], w_cols)
    demo_users = [
        ("admin", "pwd", "Administrator", "Vollzugriff inkl. Admin-Bereich"),
        ("vorbereiter", "pwd", "Vorbereiter", "Bereitet Zahlungen vor"),
        ("leitung", "pwd", "Geschaeftsleitung", "Genehmigt Zahlungen"),
        ("fibu", "pwd", "Finanzbuchhaltung", "Fuehrt Zahlungen aus"),
    ]
    for i, row in enumerate(demo_users):
        pdf.table_row(list(row), w_cols, even=i % 2 == 0)

    # ══════════════════════════════════════
    #  3. ROLLEN
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(3, "Rollen & Berechtigungen")
    pdf.body(
        "Das System kennt vier Benutzerrollen. Jede Rolle hat Zugriff auf bestimmte Funktionen. "
        "Der Administrator hat Zugriff auf alles, inklusive Nutzerverwaltung, Ampel-Historie und Rollback."
    )

    wc = [35, 25, 30, 27, 30, 27]
    pdf.table_header(["Rolle", "Dashboard", "Faelligk.", "Kred-Deb", "Nicht vkn.", "Admin"], wc)
    roles = [
        ("Vorbereiter", "Lesen", "Ampel", "Lesen", "Lesen", "-"),
        ("Gesch.leitung", "Lesen", "Ampel", "Lesen", "Lesen", "-"),
        ("FiBu", "Lesen", "Ampel", "Lesen", "Lesen", "-"),
        ("Admin", "Kernlogik", "Ampel+Bulk", "Lesen", "Lesen", "Voll"),
    ]
    for i, row in enumerate(roles):
        pdf.table_row(list(row), wc, even=i % 2 == 0)

    # ══════════════════════════════════════
    #  4. NAVIGATION
    # ══════════════════════════════════════
    pdf.ln(6)
    pdf.section_title(4, "Navigation & Gesellschaftsfilter")
    pdf.body(
        "Nach dem Login erscheint links die Seitenleiste mit Navigation, "
        "Gesellschaftsfilter und Utility-Buttons."
    )
    pdf.sub_title("Seitenleiste")
    items = [
        "Name & Rolle - zeigt den angemeldeten Benutzer",
        "Gesellschaft - Dropdown: Beide / NZWL / ZWL_SK",
        "Navigation - Radiobuttons zum Seitenwechsel",
        "Cache leeren - laedt die Quelldaten neu vom Server",
        "Logout - Abmeldung",
    ]
    for item in items:
        pdf.bullet(item)

    pdf.ln(4)
    pdf.sub_title("Gesellschaftsfilter")
    wg = [30, pdf.w - pdf.l_margin - pdf.r_margin - 30]
    pdf.table_header(["Auswahl", "Zeigt Daten von"], wg)
    pdf.table_row(["Beide", "NZWL Leipzig und ZWL Slovakia gemeinsam"], wg, True)
    pdf.table_row(["NZWL", "Nur NZWL Leipzig GmbH"], wg, False)
    pdf.table_row(["ZWL_SK", "Nur ZWL Slovakia s.r.o."], wg, True)

    pdf.ln(2)
    pdf.info_box(
        "Hinweis",
        "Wenn Ihr Konto nur einer Gesellschaft zugeordnet ist, wird automatisch nur diese angezeigt.",
        MID_BLUE,
    )

    # ══════════════════════════════════════
    #  5. DASHBOARD
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(5, "Seite: Dashboard (Startseite)")
    pdf.body(
        "Die Startseite gibt einen Ueberblick ueber die aktuelle Finanzsituation "
        "des ZWL-Kreises mit Kennzahlen, Diagrammen und Kreditoren-Tabelle."
    )
    pdf.add_screenshot("dashboard.png", "Abb. 2: Dashboard mit Kennzahlen und Faelligkeiten nach Woche")

    # Text content on new page after screenshot
    pdf.add_page()
    pdf.sub_title("Kennzahlen")
    wk = [45, pdf.w - pdf.l_margin - pdf.r_margin - 45]
    pdf.table_header(["Kennzahl", "Beschreibung"], wk)
    kpis = [
        ("Gesamtverbindlichkeiten", "Summe aller offenen Kreditoren-Belege"),
        ("Kreditoren (vkn./ges.)", "Verknuepfte vs. gesamte Kreditoren"),
        ("Buchungsbelege (OPOS)", "Gesamtzahl der Buchhaltungsbelege"),
        ("Match-Quote", "Prozentualer Anteil verknuepfter Positionen"),
    ]
    for i, (k, d) in enumerate(kpis):
        pdf.table_row([k, d], wk, even=i % 2 == 0)

    pdf.ln(3)
    pdf.sub_title("Faelligkeiten nach Woche")
    pdf.body(
        "Fuenf Karten zeigen die Betraege nach Zeitraum: Ueberfaellig, Diese Woche, "
        "Naechste Woche, In 2 Wochen, Spaeter. Durch Klick auf \"Filtern\" werden die "
        "untenstehenden Diagramme auf diesen Zeitraum eingeschraenkt."
    )

    pdf.sub_title("Top-10-Diagramme")
    pdf.bullet("Top 10 Kreditoren nach Betrag - Balkendiagramm der groessten Verbindlichkeiten")
    pdf.bullet("Top 10 Kreditoren nach Endkunden - Welche Kreditoren die meisten Endkunden betreffen")
    pdf.ln(2)
    pdf.body("Am Seitenende: Verknuepfungsstatistik und Kreditor-Uebersicht mit CSV-Download.")

    # ══════════════════════════════════════
    #  6. FÄLLIGKEITEN
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(6, "Seite: Faelligkeiten (Hauptarbeitsseite)")
    pdf.body(
        "Dies ist die zentrale Arbeitsseite. Hier werden alle Belege mit ihrem "
        "Ampel-Status, Faelligkeitsdatum und Endkunden-Zuordnung angezeigt."
    )
    pdf.add_screenshot("faelligkeiten.png", "Abb. 3: Faelligkeiten-Seite mit Ampel-Status und Zeitraum-Filtern")

    pdf.add_page()
    pdf.sub_title("Ampel-Status Uebersicht")
    pdf.body(
        "Vier Karten zeigen die Verteilung: Rot (Stop/Pruefen), Gelb (In Pruefung), "
        "Gruen (Freigegeben), Kein Status. Jede Karte zeigt Beleganzahl und Betrag."
    )

    pdf.sub_title("Zeitraum- und Detailfilter")
    pdf.body(
        "Sechs klickbare Karten filtern nach Zeitraum (Ueberfaellig bis Spaeter). "
        "Zusaetzlich vier Dropdown-Filter: Kalenderwoche, Kreditor, Verknuepfung, Endkunde/Grund."
    )

    pdf.sub_title("Belegtabelle")
    wt = [20, 25, 20, 35, 25, pdf.w - pdf.l_margin - pdf.r_margin - 125]
    pdf.table_header(["Ampel", "Faellig am", "Beleg", "Kreditor", "Betrag", "Endkunde/Grund"], wt)
    pdf.table_row(["Klickbar", "Sortierbar", "Beleg-Nr", "Sortierbar", "Sortierbar", "Sortierbar"], wt, True)
    pdf.ln(2)
    pdf.body(
        "Die Tabelle ist paginiert (20 Zeilen pro Seite). Blaettern mit den Buttons \"Zurueck\" "
        "und \"Weiter\". Sortierung durch Klick auf die Pfeil-Symbole in den Spaltenkoepfen."
    )

    pdf.sub_title("Sammel-Aktionen")
    pdf.info_box(
        "Alle gefilterten Belege auf einmal aendern",
        "Im Bereich \"Sammel-Aktionen\" koennen Sie den Status fuer alle gefilterten Belege setzen: "
        "Alle Stop | Alle in Pruefung | Alle Freigeben | Alle Zuruecksetzen",
        GREEN,
    )

    pdf.ln(2)
    pdf.sub_title("Auswertungen (Tabs am Seitenende)")
    pdf.bullet("Aufschluesselung pro Kreditor - Tabelle mit Betrag und Beleganzahl je Kreditor")
    pdf.bullet("Kreuz-Aufschluesselung: Kreditor x Endkunde/Grund - Pivot-Tabelle mit EUR-Betraegen")

    # ══════════════════════════════════════
    #  7. AMPEL-SYSTEM
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(7, "Das Ampel-System (Traffic Lights)")
    pdf.body(
        "Das Ampel-System ist das zentrale Steuerungselement fuer die Zahlungsfreigabe "
        "in Phase 1. Jeder Beleg kann mit einem von vier Status versehen werden."
    )

    wa = [15, 25, 30, pdf.w - pdf.l_margin - pdf.r_margin - 70]
    pdf.table_header(["", "Status", "Bedeutung", "Typische Verwendung"], wa)
    ampels = [
        ("Rot", "Rot", "Stop / Pruefen", "Zahlung stoppen - Beleg muss geprueft werden"),
        ("Gelb", "Gelb", "In Pruefung", "Entscheidung steht noch aus"),
        ("Gruen", "Gruen", "Freigegeben", "Zahlung kann ausgefuehrt werden"),
        ("Weiss", "Kein", "Nicht bearbeitet", "Beleg wurde noch nicht bewertet"),
    ]
    for i, (emoji, st, bed, verw) in enumerate(ampels):
        pdf.table_row([emoji, st, bed, verw], wa, even=i % 2 == 0)

    pdf.ln(4)
    pdf.sub_title("So setzen Sie einen Ampel-Status")
    pdf.numbered_step(1, "Faelligkeiten-Seite oeffnen", "Navigieren Sie ueber die Seitenleiste zu \"Faelligkeiten\".")
    pdf.numbered_step(2, "Beleg finden", "Nutzen Sie die Filter oder blaettern Sie durch die Tabelle.")
    pdf.numbered_step(3, "Ampel-Farbe klicken", "In der Spalte \"Ampel\" sehen Sie drei Kreise. Der aktive Status leuchtet farbig, die anderen sind ausgegraut. Klicken Sie auf die gewuenschte Farbe.")
    pdf.numbered_step(4, "Status zuruecksetzen", "Klicken Sie erneut auf die bereits aktive Farbe - der Status wird zurueckgesetzt.")

    pdf.ln(3)
    pdf.info_box(
        "Revisionssicherheit",
        "Jede Ampel-Aenderung wird automatisch protokolliert - mit Belegnummer, Status, Zeitstempel "
        "und Benutzername. Die Historie kann nicht geloescht werden (Append-Only).",
        GREEN,
    )

    # ══════════════════════════════════════
    #  8. KREDITOR-DEBITOR
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(8, "Seite: Kreditor-Debitor (Detailansicht)")
    pdf.body(
        "Diese Seite zeigt die vollstaendige Verknuepfungskette von Kreditoren-Rechnungen "
        "zu den zugehoerigen Endkunden."
    )
    pdf.add_screenshot("kreditor_debitor.png", "Abb. 4: Kreditor-Debitor Detailansicht mit Filtern und KPIs")

    pdf.add_page()
    pdf.sub_title("Filter")
    pdf.bullet("Kreditor - nach Kreditor-Name filtern")
    pdf.bullet("Debitor (Endkunde) - nach Endkunden filtern")
    pdf.bullet("Quelle - nach Datenquelle filtern")

    pdf.ln(3)
    pdf.sub_title("Zwei Ansichten")
    wv = [55, pdf.w - pdf.l_margin - pdf.r_margin - 55]
    pdf.table_header(["Ansicht", "Beschreibung"], wv)
    pdf.table_row(["Pro Buchungsbeleg (gruppiert)", "Eine Zeile pro Beleg mit aggregierten Daten"], wv, True)
    pdf.table_row(["Alle Detail-Zeilen", "Jede Verknuepfung: Beleg > Rohteil > Fertigteil > Debitor"], wv, False)

    # ══════════════════════════════════════
    #  9. NICHT VERKNÜPFT
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(9, "Seite: Nicht verknuepft (Analyse)")
    pdf.body(
        "Diese Seite analysiert, warum bestimmte Belege keinem Endkunden zugeordnet "
        "werden konnten. Das hilft bei der Datenbereinigung und Prozessoptimierung."
    )
    pdf.add_screenshot("nicht_verknuepft.png", "Abb. 5: Analyse nicht verknuepfter Belege mit Donut-Diagramm und Branchenverteilung")

    pdf.add_page()
    pdf.sub_title("Analyse-Bereiche")
    wn = [42, 30, pdf.w - pdf.l_margin - pdf.r_margin - 72]
    pdf.table_header(["Bereich", "Darstellung", "Inhalt"], wn)
    analyse = [
        ("Nach Grund", "Donut + Tabelle", "Warum kein Match: Materialfehler, BOM, etc."),
        ("Nach Branche", "Balken + Tabelle", "Verteilung nach Branche mit Betraegen"),
        ("Branche x Grund", "Pivot-Tabelle", "Kreuzaufschluesselung Anzahl x Betrag"),
        ("Top 15 Kreditoren", "Tabelle", "Groesste nicht verknuepfte Kreditoren"),
    ]
    for i, row in enumerate(analyse):
        pdf.table_row(list(row), wn, even=i % 2 == 0)

    # ══════════════════════════════════════
    #  10. ADMIN
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(10, "Seite: Admin-Bereich")
    pdf.info_box(
        "Nur fuer Administratoren",
        "Diese Seite ist ausschliesslich fuer Benutzer mit der Rolle Admin sichtbar.",
        RED,
    )
    pdf.ln(2)
    pdf.add_screenshot("admin.png", "Abb. 6: Admin-Bereich mit Nutzerverwaltung")

    pdf.add_page()
    pdf.sub_title("Tab 1: Nutzerverwaltung")
    pdf.bullet("Tabelle aller Benutzer (Name, E-Mail, Rolle, Gesellschaft)")
    pdf.bullet("Formular zum Anlegen neuer Benutzer (Demo: nur fuer aktuelle Sitzung)")

    pdf.ln(3)
    pdf.sub_title("Tab 2: Beleg-Statusverlauf (Ampel-Historie)")
    pdf.body(
        "Zeigt alle jemals durchgefuehrten Ampel-Aenderungen. Filter nach Belegnummer, "
        "Benutzer und Status. Export als CSV-Datei moeglich."
    )

    pdf.sub_title("System-Wiederherstellung (Rollback)")
    pdf.numbered_step(1, "Datum und Uhrzeit waehlen", "Waehlen Sie den Zeitpunkt, zu dem Sie den Zustand wiederherstellen moechten.")
    pdf.numbered_step(2, "Vorschau pruefen", "Das System zeigt, welche Belege sich aendern wuerden.")
    pdf.numbered_step(3, "Bestaetigen und ausfuehren", "Haekchen setzen und \"Rollback ausfuehren\" klicken.")

    pdf.ln(2)
    pdf.info_box(
        "Achtung",
        "Der Rollback wird im Audit-Log dokumentiert. Jede Aenderung wird als "
        "\"[Admin-Name] (Rollback auf Datum)\" protokolliert.",
        ORANGE,
    )

    # ══════════════════════════════════════
    #  11. CSV EXPORT
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(11, "Daten exportieren (CSV)")
    pdf.body("Auf mehreren Seiten stehen CSV-Downloads zur Verfuegung:")
    we = [35, 50, pdf.w - pdf.l_margin - pdf.r_margin - 85]
    pdf.table_header(["Seite", "Export-Button", "Inhalt"], we)
    exports = [
        ("Dashboard", "Kreditor-Uebersicht als CSV", "Kreditoren mit Betraegen und Endkunden"),
        ("Faelligkeiten", "Faelligkeiten als CSV", "Gefilterte Belege mit Status"),
        ("Kreditor-Debitor", "Als CSV herunterladen", "Detail-Verknuepfungen"),
        ("Admin (Historie)", "Historie als CSV exportieren", "Komplette Ampel-Historie"),
    ]
    for i, row in enumerate(exports):
        pdf.table_row(list(row), we, even=i % 2 == 0)

    pdf.ln(3)
    pdf.info_box(
        "CSV-Format",
        "Die Dateien verwenden Semikolon (;) als Trennzeichen und deutsches Zahlenformat "
        "(Komma als Dezimalzeichen). Sie koennen direkt in Microsoft Excel geoeffnet werden.",
        MID_BLUE,
    )

    # ══════════════════════════════════════
    #  12. FAQ
    # ══════════════════════════════════════
    pdf.ln(6)
    pdf.section_title(12, "Hinweise & FAQ")

    faqs = [
        ("Wie aktualisiere ich die Daten?",
         "Klicken Sie in der Seitenleiste auf \"Cache leeren\". Auf dem Dashboard gibt es "
         "zusaetzlich \"Daten neu laden\". Auf dem Server kann die Kernlogik direkt aus dem "
         "Dashboard gestartet werden."),
        ("Warum ist eine Ampel-Farbe ausgegraut?",
         "Ausgegraute Farben bedeuten, dass dieser Status nicht aktiv ist. Die leuchtende "
         "Farbe zeigt den aktuellen Status."),
        ("Kann ich eine Ampel-Aenderung rueckgaengig machen?",
         "Einzelner Beleg: Klicken Sie erneut auf die aktive Farbe. Mehrere Belege: Nutzen "
         "Sie die Rollback-Funktion im Admin-Bereich."),
        ("Was bedeutet \"Nicht verknuepft\"?",
         "Ein Beleg ist nicht verknuepft, wenn die Kernlogik keinen Endkunden (Debitor) "
         "dafuer ermitteln konnte. Gruende werden auf der gleichnamigen Seite analysiert."),
        ("Welchen Browser soll ich verwenden?",
         "Google Chrome oder Microsoft Edge (empfohlen). Firefox wird ebenfalls unterstuetzt. "
         "Internet Explorer wird nicht unterstuetzt."),
        ("An wen wende ich mich bei Fragen?",
         "Bitte kontaktieren Sie Ihren Projektleiter oder die IT-Abteilung."),
    ]
    for q, a in faqs:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*DARK_BLUE)
        w = pdf.w - pdf.l_margin - pdf.r_margin
        pdf.multi_cell(w, 6, q)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*DARK_TEXT)
        pdf.multi_cell(w, 5.5, a)
        pdf.ln(4)

    # ══════════════════════════════════════
    #  13. PHASE 2
    # ══════════════════════════════════════
    pdf.add_page()
    pdf.section_title(13, "Phase-2-Ausblick")
    pdf.body("Folgende Funktionen sind fuer die naechste Ausbaustufe vorgesehen:")

    wp = [45, pdf.w - pdf.l_margin - pdf.r_margin - 45]
    pdf.table_header(["Funktion", "Beschreibung"], wp)
    phase2 = [
        ("Zahlungsplanung", "Zweistufiger Freigabeprozess: Vorbereiter > GL > FiBu"),
        ("Liquiditaet", "Zufluss (Debitoren) vs. Abfluss (Kreditoren) mit Prognose"),
        ("Berichte", "Audit-Log-Export, Wochen-/Monatsberichte als Excel & PDF"),
        ("SAP-Anbindung", "Automatischer Datenimport (kein manueller Export mehr)"),
        ("Benutzerverwaltung", "Persistente Benutzer mit sicherer Passwortspeicherung"),
        ("Benachrichtigungen", "E-Mail bei Freigaben, Ablehnungen, ueberfaelligen Belegen"),
    ]
    for i, row in enumerate(phase2):
        pdf.table_row(list(row), wp, even=i % 2 == 0)

    # ── save ──
    pdf.output(str(OUT))
    print(f"PDF saved: {OUT}")
    print(f"Pages: {pdf.page_no()}")


if __name__ == "__main__":
    build()
