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

    # ── Demo / Under-Construction Banner ──────────────────────────────────────
    st.markdown("""
    <div style="
        border: 3px solid #F59E0B;
        border-radius: 10px;
        background: repeating-linear-gradient(
            -45deg,
            #FEF3C7,
            #FEF3C7 14px,
            #FFFBEB 14px,
            #FFFBEB 28px
        );
        padding: 0;
        margin-bottom: 1.5rem;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(245,158,11,0.25);
    ">
        <div style="
            background: #F59E0B;
            color: #1C1917;
            text-align: center;
            font-weight: 800;
            font-size: 0.75rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            padding: 4px 0;
        ">⚠️ &nbsp; ACHTUNG &nbsp; ⚠️</div>
        <div style="
            background: rgba(255,255,255,0.82);
            padding: 16px 24px;
            text-align: center;
        ">
            <span style="font-size: 1.6rem;">🚧</span>
            <span style="
                display: block;
                font-size: 1.15rem;
                font-weight: 700;
                color: #92400E;
                margin: 4px 0 2px;
                letter-spacing: 0.03em;
            ">DEMO-SYSTEM · IN ENTWICKLUNG</span>
            <span style="
                font-size: 0.9rem;
                color: #78350F;
            ">Dieses System befindet sich im Testbetrieb. &nbsp;|&nbsp; Testing &amp; Development only — not for productive use.</span>
        </div>
        <div style="
            background: #F59E0B;
            color: #1C1917;
            text-align: center;
            font-weight: 800;
            font-size: 0.75rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            padding: 4px 0;
        ">🔧 &nbsp; TOOL UNDER CONSTRUCTION &nbsp; 🔧</div>
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
        "Dashboard":        str(_pages_dir / "dashboard.py"),
        "Dashboard W1":     str(_pages_dir / "dashboard_w1.py"),
        "Faelligkeiten":    str(_pages_dir / "faelligkeiten.py"),
        "Faelligkeiten W1": str(_pages_dir / "faelligkeiten_w1.py"),
        "Kreditor-Debitor": str(_pages_dir / "offene_posten.py"),
        "Nicht verknüpft":   str(_pages_dir / "nicht_verknuepft.py"),
        "Zahlungsplanung":  str(_pages_dir / "zahlungsplanung.py"),
        "Liquiditaet":      str(_pages_dir / "liquiditaet.py"),
        "Berichte":         str(_pages_dir / "berichte.py"),
    }
    
    if st.session_state.role == "admin":
        pages["Admin-Bereich"] = str(_pages_dir / "admin.py")

    # Global Sidebar Elements
    with st.sidebar:
        st.title("NZWL Dashboard")
        st.write(f"Angemeldet als: **{st.session_state.user['name']}**")
        st.write(f"Rolle: *{st.session_state.role}*")
        
        # Determine accessible companies based on user settings
        ges_opts = ["Beide", "NZWL", "ZWL_SK"]
        user_ges = st.session_state.user["gesellschaft"]
        if user_ges == "nzwl":
            ges_opts = ["NZWL"]
        elif user_ges == "zwl_sk":
            ges_opts = ["ZWL_SK"]
            
        st.selectbox("Gesellschaft", ges_opts, key="selected_gesellschaft")
        
        st.markdown("---")
        selection = st.radio("Navigation", list(pages.keys()))
        
        st.markdown("---")
        if st.button("🗑️ Cache leeren"):
            st.cache_data.clear()
            st.rerun()
        if st.button("Logout"):
            logout()
            st.rerun()

    # Load selected page
    page_path = pages[selection]
    with open(page_path, "r", encoding="utf-8") as f:
        code_content = f.read()
        
    with st.spinner(f"Lade Ansicht '{selection}'..."):
        exec(compile(code_content, page_path, "exec"), {"__file__": page_path})
