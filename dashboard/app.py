import streamlit as st
import sys
from pathlib import Path

# Ensure core module is accessible
sys.path.append(str(Path(__file__).resolve().parent.parent))
from dashboard.auth import init_session_state, login, logout

# Page configuration
st.set_page_config(
    page_title="NZWL Zahlungsplanung & Liquiditätssteuerung",
    page_icon="💶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Brand Guidelines
st.markdown("""
<style>
    :root {
        --primary-color: #1F4E79;
        --secondary-color: #2E75B6;
    }
    /* Hide default Streamlit page navigation */
    [data-testid="stSidebarNav"] {display: none !important;}

    /* ── Sidebar: modernes Design ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a3a5c 0%, #1F4E79 60%, #1a3a5c 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: rgba(255,255,255,0.9) !important;
    }

    /* Sidebar-Titel */
    .sidebar-brand {
        padding: 0.5rem 0.9rem 0.35rem;
        border-bottom: 1px solid rgba(255,255,255,0.12);
        margin-bottom: 0.5rem;
    }
    .sidebar-brand-title {
        font-size: 0.98rem;
        font-weight: 800;
        letter-spacing: 0.03em;
        color: white !important;
        text-transform: uppercase;
    }
    .sidebar-brand-sub {
        font-size: 0.67rem;
        color: rgba(255,255,255,0.45) !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Benutzer-Chip */
    .sidebar-user {
        background: rgba(255,255,255,0.07);
        border-radius: 7px;
        padding: 0.4rem 0.7rem;
        margin: 0 0.5rem 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .sidebar-avatar {
        width: 26px; height: 26px;
        border-radius: 50%;
        background: rgba(255,255,255,0.16);
        display: flex; align-items: center; justify-content: center;
        font-size: 0.72rem; font-weight: 700;
        color: white !important;
        flex-shrink: 0;
    }
    .sidebar-user-name {
        font-size: 0.78rem;
        font-weight: 600;
        color: white !important;
        line-height: 1.2;
    }
    .sidebar-user-role {
        font-size: 0.63rem;
        color: rgba(255,255,255,0.48) !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* Gruppen-Label */
    .nav-group-label {
        font-size: 0.59rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(255,255,255,0.35) !important;
        padding: 0.45rem 0.9rem 0.1rem;
    }

    /* Nav-Buttons */
    [data-testid="stSidebar"] div[data-testid="stButton"] button {
        width: 100% !important;
        text-align: left !important;
        background: transparent !important;
        border: none !important;
        border-radius: 5px !important;
        padding: 0.18rem 0.9rem !important;
        font-size: 0.82rem !important;
        font-weight: 400 !important;
        color: rgba(255,255,255,0.68) !important;
        box-shadow: none !important;
        transition: background 0.12s ease, color 0.12s ease !important;
        margin: 0rem 0.35rem !important;
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        line-height: 1.25 !important;
        min-height: unset !important;
        height: auto !important;
    }
    /* Buttontext linksbündig — alle Kinder-Elemente */
    [data-testid="stSidebar"] div[data-testid="stButton"] button *,
    [data-testid="stSidebar"] div[data-testid="stButton"] button p,
    [data-testid="stSidebar"] div[data-testid="stButton"] button div,
    [data-testid="stSidebar"] div[data-testid="stButton"] button span {
        text-align: left !important;
        display: block !important;
        width: 100% !important;
        margin: 0 !important;
    }
    [data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
        background: rgba(255,255,255,0.08) !important;
        color: rgba(255,255,255,0.92) !important;
    }
    /* Aktiver Nav-Button */
    [data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {
        background: rgba(255,255,255,0.12) !important;
        color: white !important;
        font-weight: 600 !important;
        border-left: 2px solid rgba(255,255,255,0.65) !important;
        border-radius: 0 5px 5px 0 !important;
        padding-left: calc(0.9rem - 2px) !important;
    }

    /* Gruppen-Label: weniger Abstand */
    .nav-group-label {
        padding-top: 0.3rem !important;
        padding-bottom: 0.05rem !important;
    }

    /* Expander „Alte Seiten“ — dark Sidebar-Stil */
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.10) !important;
        border-radius: 6px !important;
        margin: 0.3rem 0.35rem 0.1rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        color: rgba(255,255,255,0.42) !important;
        font-size: 0.70rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.09em !important;
        padding: 0.3rem 0.6rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: rgba(255,255,255,0.70) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary svg {
        fill: rgba(255,255,255,0.35) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] > div {
        padding: 0.1rem 0 0.2rem !important;
    }
    /* Buttons INNERHALB des Expanders: etwas kleiner + eingerueckt */
    [data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stButton"] button {
        font-size: 0.75rem !important;
        color: rgba(255,255,255,0.50) !important;
        padding: 0.15rem 0.7rem !important;
        font-style: italic !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stButton"] button:hover {
        color: rgba(255,255,255,0.80) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stButton"] button[kind="primary"] {
        color: white !important;
        font-style: normal !important;
        font-weight: 600 !important;
        border-left: 2px solid rgba(255,255,255,0.40) !important;
    }

    /* Selectbox in Sidebar */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label {
        color: rgba(255,255,255,0.45) !important;
        font-size: 0.67rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin-bottom: 0.15rem !important;
    }
    /* Dropdown-Trigger: dunkler Hintergrund damit weißer Text sichtbar ist */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div:first-child {
        background: rgba(10,30,60,0.55) !important;
        border: 1px solid rgba(255,255,255,0.18) !important;
        border-radius: 6px !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: rgba(255,255,255,0.90) !important;
        background-color: transparent !important;
    }
    /* Dropdown-Menü (geöffnet) */
    [data-testid="stSidebar"] [data-baseweb="popover"] {
        background: #1F4E79 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="popover"] li {
        color: rgba(255,255,255,0.85) !important;
        background: transparent !important;
    }
    [data-testid="stSidebar"] [data-baseweb="popover"] li:hover {
        background: rgba(255,255,255,0.12) !important;
    }

    /* Footer-Buttons (Cache / Logout) */
    .sidebar-footer {
        border-top: 1px solid rgba(255,255,255,0.10);
        padding-top: 0.35rem;
        margin-top: 0.35rem;
    }
    [data-testid="stSidebar"] .sidebar-footer div[data-testid="stButton"] button {
        color: rgba(255,255,255,0.42) !important;
        font-size: 0.75rem !important;
        padding: 0.22rem 0.9rem !important;
    }
    [data-testid="stSidebar"] .sidebar-footer div[data-testid="stButton"] button:hover {
        color: rgba(255,255,255,0.75) !important;
        background: rgba(255,255,255,0.06) !important;
    }

    /* Smooth fade-in animation for main content */
    @keyframes pageFadeIn {
        from {
            opacity: 0.3;
            transform: translateY(6px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .main .block-container {
        animation: pageFadeIn 0.3s ease-out;
    }

    /* ── Global NZWL CSS Components (to prevent visual flashing / FOUC) ── */
    .tbl-header { font-size: 0.78rem; font-weight: 700; color: #888;
                  text-transform: uppercase; letter-spacing: 0.05em;
                  padding-bottom: 0.3rem;
                  padding-left: 0.4rem; }
    .tbl-sep    { border-top: 1px solid #e0e0e0; margin: 0.15rem 0 0.25rem 0; }

    /* Zeilen-Zellen: vertikal zentriert, einzeilig = gleiche Höhe für alle Streifen */
    .tbl-cell {
        font-size: 0.88rem;
        padding: 0.2rem 0.4rem;
        line-height: 1.4;
        display: flex;
        align-items: center;
        min-height: 3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }

    /* Ampel-Spalte: verschachtelte Sub-Columns vertikal zentrieren */
    div[data-testid="stHorizontalBlock"]
      div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
        min-height: 3rem !important;
    }
    div[data-testid="stHorizontalBlock"]
      div[data-testid="stHorizontalBlock"]
      div[data-testid="stColumn"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* Nativer Zeilen-Hintergrund für gerade Tabellenzeilen (Zebra-Muster) */
    div[data-testid="element-container"]:nth-child(even) div[data-testid="stHorizontalBlock"]:has(.tbl-cell) {
        background: rgba(31, 78, 121, 0.05) !important;
        border-radius: 4px;
    }

    /* Hover-Effekt für alle Datenzeilen */
    div[data-testid="stHorizontalBlock"]:has(.tbl-cell):hover {
        background: rgba(31, 78, 121, 0.09) !important;
        transition: background 0.15s ease !important;
    }

    /* Ampel-Buttons: nur im ersten Column-Container der Datenzeilen stylen */
    div[data-testid="stHorizontalBlock"]:has(.tbl-cell) > div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0.1rem 0.2rem !important;
        min-height: unset !important;
        font-size: 1.25rem !important;
        line-height: 1 !important;
        transition: filter 0.15s ease, opacity 0.15s ease !important;
    }
    /* Inaktiv → echtes Grau (kein Farbstich) */
    div[data-testid="stHorizontalBlock"]:has(.tbl-cell) > div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button[kind="secondary"] {
        filter: grayscale(100%) opacity(0.35) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.tbl-cell) > div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button[kind="secondary"]:hover {
        filter: grayscale(80%) opacity(0.65) !important;
    }
    /* Aktiv → volle Farbe + leuchten */
    div[data-testid="stHorizontalBlock"]:has(.tbl-cell) > div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button[kind="primary"] {
        filter: none !important;
        opacity: 1 !important;
    }

    /* Sortier-Buttons in der Tabellen-Header-Zeile: exakt wie Text-Header stylen und linksbündig ausrichten */
    div[data-testid="stHorizontalBlock"]:has(.tbl-header) div[data-testid="stButton"] button {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        color: #888 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        padding: 0.2rem 0.4rem !important;
        min-height: unset !important;
        height: auto !important;
        line-height: 1.4 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        text-align: left !important;
        width: 100% !important;
    }

    /* Flex-Inhalt des Buttons ebenfalls linksbündig zwingen */
    div[data-testid="stHorizontalBlock"]:has(.tbl-header) div[data-testid="stButton"] button * {
        text-align: left !important;
        justify-content: flex-start !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.tbl-header) div[data-testid="stButton"] button:hover {
        color: #1F4E79 !important;
        background: rgba(31, 78, 121, 0.08) !important;
        border-radius: 4px !important;
    }

    /* Ampel-Spalte: Buttons vertikal zentrieren */
    div[data-testid="stColumn"] div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    div[data-testid="stColumn"] div[data-testid="stHorizontalBlock"]
      div[data-testid="stColumn"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
</style>
""", unsafe_allow_html=True)

init_session_state()

if st.session_state.user is None:
    # Hide the sidebar entirely on the login screen
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)
    # Login Screen
    st.title("NZWL Dashboard Login")

    # ── Version Badge ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        border: 1px solid rgba(31,78,121,0.25);
        border-radius: 10px;
        background: linear-gradient(135deg, rgba(31,78,121,0.06) 0%, rgba(46,117,182,0.08) 100%);
        padding: 14px 24px;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 14px;
        box-shadow: 0 2px 8px rgba(31,78,121,0.08);
    ">
        <span style="font-size: 1.5rem; flex-shrink: 0;">💶</span>
        <div>
            <div style="
                font-size: 1.05rem;
                font-weight: 700;
                color: #1F4E79;
                letter-spacing: 0.02em;
            ">MVP Version 1</div>
            <div style="
                font-size: 0.82rem;
                color: #4a6fa5;
                margin-top: 2px;
            ">NZWL Zahlungsplanung &amp; Liquiditätssteuerung</div>
        </div>
        <div style="
            margin-left: auto;
            background: #1F4E79;
            color: white;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            padding: 4px 12px;
            border-radius: 20px;
        ">v1.0</div>
    </div>
    """, unsafe_allow_html=True)
    # ──────────────────────────────────────────────────────────────────────────

    with st.form("login_form"):
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Einloggen")
        
        if submit:
            if login(username, password):
                st.rerun()
            else:
                st.error("Ungültiger Benutzername oder Passwort.")
    st.info("Demo-Logins: admin/pwd, vorbereiter/pwd, leitung/pwd, fibu/pwd")
else:
    # Navigation configuration (absolute paths)
    _pages_dir = Path(__file__).parent / "pages"
    pages = {
        "Dashboard V.02":            str(_pages_dir / "dashboard_w1.py"),
        "Dashboard V01 (alt)":      str(_pages_dir / "dashboard.py"),
        "Fälligkeiten V.02":        str(_pages_dir / "faelligkeiten_w1.py"),
        "Faelligkeiten V01 (alt)":  str(_pages_dir / "faelligkeiten.py"),
        "Kreditor-Debitor":         str(_pages_dir / "offene_posten.py"),
        "Nicht verknüpft":          str(_pages_dir / "nicht_verknuepft.py"),
        "Überfällig-Analyse":       str(_pages_dir / "ueberfaellig_analyse.py"),
        "Zahlungsplanung":           str(_pages_dir / "zahlungsplanung.py"),
        "Liquiditaet":               str(_pages_dir / "liquiditaet.py"),
        "Berichte":                  str(_pages_dir / "berichte.py"),
    }
    
    if st.session_state.role == "admin":
        pages["Admin-Bereich"] = str(_pages_dir / "admin.py")
        pages["Cron-Status"] = str(_pages_dir / "cron_status.py")

    # ── Sidebar initialisieren ────────────────────────────────────────────────
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = list(pages.keys())[0]
    # Sicherstellen, dass die Selektion noch gültig ist
    if st.session_state["nav_selection"] not in pages:
        st.session_state["nav_selection"] = list(pages.keys())[0]

    with st.sidebar:
        # ── Brand-Header ──────────────────────────────────────────────────────
        _user     = st.session_state.user
        _initials = "".join(w[0].upper() for w in _user["name"].split()[:2])
        st.markdown(f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">NZWL Dashboard</div>
            <div class="sidebar-brand-sub">Zahlungsplanung &amp; Liquidität</div>
        </div>
        <div class="sidebar-user">
            <div class="sidebar-avatar">{_initials}</div>
            <div>
                <div class="sidebar-user-name">{_user['name']}</div>
                <div class="sidebar-user-role">{st.session_state.role}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Gesellschaft-Selector ─────────────────────────────────────────────
        ges_opts = ["Beide", "NZWL", "ZWL_SK"]
        user_ges = _user["gesellschaft"]
        if user_ges == "nzwl":   ges_opts = ["NZWL"]
        elif user_ges == "zwl_sk": ges_opts = ["ZWL_SK"]
        st.selectbox("Gesellschaft", ges_opts, key="selected_gesellschaft")

        # ── Navigation ───────────────────────────────────────────────────────
        NAV_GROUPS = {
            "Dashboard V.02":           "Analyse",
            "Dashboard V01 (alt)":     "Analyse",
            "Fälligkeiten V.02":       "Fälligkeiten",
            "Faelligkeiten V01 (alt)": "Fälligkeiten",
            "Kreditor-Debitor":        "Offene Posten",
            "Nicht verknüpft":         "Offene Posten",
            "Überfällig-Analyse":      "Offene Posten",
            "Zahlungsplanung":         "Planung",
            "Liquiditaet":             "Planung",
            "Berichte":                "Berichte",
            "Admin-Bereich":           "System",
            "Cron-Status":             "System",
        }

        last_group = None
        for page_name in pages.keys():
            if "(alt)" in page_name:
                continue  # Alt-Seiten kommen in den Expander weiter unten

            grp = NAV_GROUPS.get(page_name, "")
            if grp != last_group:
                st.markdown(f'<div class="nav-group-label">{grp}</div>',
                            unsafe_allow_html=True)
                last_group = grp

            is_active = st.session_state["nav_selection"] == page_name
            btn_type  = "primary" if is_active else "secondary"

            if st.button(
                page_name,
                key=f"nav_{page_name}",
                type=btn_type,
                use_container_width=True,
            ):
                st.session_state["nav_selection"] = page_name
                st.rerun()

        # ── Alte Seiten (Expander) ───────────────────────────────────────────────────
        alt_pages = {k: v for k, v in pages.items() if "(alt)" in k}
        if alt_pages:
            any_alt_active = st.session_state["nav_selection"] in alt_pages
            with st.expander("Alte Seiten", expanded=any_alt_active):
                for page_name in alt_pages.keys():
                    is_active = st.session_state["nav_selection"] == page_name
                    btn_type  = "primary" if is_active else "secondary"
                    if st.button(
                        page_name,
                        key=f"nav_{page_name}",
                        type=btn_type,
                        use_container_width=True,
                    ):
                        st.session_state["nav_selection"] = page_name
                        st.rerun()

        # ── Footer-Buttons ────────────────────────────────────────────────────
        st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
        if st.button("Cache leeren", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    selection = st.session_state["nav_selection"]

    # Load selected page
    page_path = pages[selection]
    with open(page_path, "r", encoding="utf-8") as f:
        code_content = f.read()
        
    with st.spinner(f"Lade Ansicht '{selection}'..."):
        exec(compile(code_content, page_path, "exec"), {"__file__": page_path})
