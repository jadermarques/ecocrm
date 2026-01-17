import streamlit as st
import os

# Configuration
st.set_page_config(
    page_title="ECOCRM Portal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Theme refinement (optional details)
st.markdown("""
<style>
    /* Add any specific overrides here */
</style>
""", unsafe_allow_html=True)

# Navigation Setup
pages = {
    "Dashboard": [
        st.Page("pages/dashboard_home.py", title="Home", icon="🏠", default=True),
    ],
    "Modules": [
        st.Page("pages/bot_studio.py", title="Bot Studio", icon="🤖"),
        st.Page("pages/kb_rag.py", title="Knowledge Base", icon="📚"),
    ],
    "System": [
        st.Page("pages/admin.py", title="Administration", icon="⚙️"),
        st.Page("pages/user_management.py", title="User Management", icon="👥"),
    ]
}

pg = st.navigation(pages)

# Sidebar Info
with st.sidebar:
    st.markdown("### 🚀 ECOCRM")
    st.caption(f"Env: {os.getenv('APP_ENV', 'local')}")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

pg.run()
