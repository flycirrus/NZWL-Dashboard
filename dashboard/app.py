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
                st.rerun()
            else:
                st.error("Ungültiger Benutzername oder Passwort.")
    st.info("Demo-Logins: admin/pwd, vorbereiter/pwd, leitung/pwd, fibu/pwd")
else:
    # Navigation configuration based on role
    pages = {"Übersichten": []}
    
    pages["Übersichten"].append(st.Page("pages/dashboard.py", title="Dashboard", icon="📊", default=True))
    pages["Übersichten"].append(st.Page("pages/offene_posten.py", title="Offene Posten", icon="📋"))
    
    pages["Planung & Liquidität"] = [
        st.Page("pages/zahlungsplanung.py", title="Zahlungsplanung", icon="🗓️"),
        st.Page("pages/liquiditaet.py", title="Liquidität", icon="💧"),
    ]
    
    pages["Auswertungen"] = [
        st.Page("pages/berichte.py", title="Berichte", icon="📈"),
    ]
    
    if st.session_state.role == "admin":
        pages["Administration"] = [
            st.Page("pages/admin.py", title="Nutzerverwaltung", icon="⚙️")
        ]
        
    pg = st.navigation(pages)

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
        
        if st.button("Logout"):
            logout()
            st.rerun()

    pg.run()
