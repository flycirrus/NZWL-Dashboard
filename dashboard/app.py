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
        "Dashboard":       str(_pages_dir / "dashboard.py"),
        "Offene Posten":   str(_pages_dir / "offene_posten.py"),
        "Zahlungsplanung": str(_pages_dir / "zahlungsplanung.py"),
        "Liquidität":      str(_pages_dir / "liquiditaet.py"),
        "Berichte":        str(_pages_dir / "berichte.py"),
    }
    
    if st.session_state.role == "admin":
        pages["Nutzerverwaltung"] = str(_pages_dir / "admin.py")

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
        exec(compile(f.read(), page_path, "exec"), {"__file__": page_path})
