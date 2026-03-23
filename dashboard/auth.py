import streamlit as st

# Setup mock users
MOCK_USERS = {
    "admin": {"password": "pwd", "name": "Admin User", "role": "admin", "gesellschaft": "beide"},
    "vorbereiter": {"password": "pwd", "name": "Vorbereiter User", "role": "vorbereiter", "gesellschaft": "beide"},
    "leitung": {"password": "pwd", "name": "Geschäftsleitung", "role": "geschaeftsleitung", "gesellschaft": "beide"},
    "fibu": {"password": "pwd", "name": "FiBu User", "role": "fibu", "gesellschaft": "beide"}
}

def init_session_state():
    if "user" not in st.session_state:
        st.session_state.user = None
    if "role" not in st.session_state:
        st.session_state.role = None
        
def login(username, password):
    if username in MOCK_USERS and MOCK_USERS[username]["password"] == password:
        st.session_state.user = MOCK_USERS[username]
        st.session_state.role = MOCK_USERS[username]["role"]
        return True
    return False

def logout():
    st.session_state.user = None
    st.session_state.role = None
    
def check_permission(allowed_roles):
    """Check if the current user has one of the allowed roles."""
    if st.session_state.role in allowed_roles or st.session_state.role == "admin":
        return True
    return False
