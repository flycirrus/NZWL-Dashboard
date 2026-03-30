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
</style>
""", unsafe_allow_html=True)

init_session_state()

if st.session_state.user is None:
    # Login Screen
    st.title("NZWL Dashboard Login")
    with st.form("login_form"):
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        submit = st.form_submit_button("Einloggen")
        
        if submit:
            if login(username, password):
                st.experimental_rerun()
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
        
        st.divider()
        selection = st.radio("Navigation", list(pages.keys()))
        
        st.divider()
        if st.button("Logout"):
            logout()
            st.experimental_rerun()

    # Load selected page
    page_path = pages[selection]
    with open(page_path, "r", encoding="utf-8") as f:
        exec(compile(f.read(), page_path, "exec"), {"__file__": page_path})
