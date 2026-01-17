import streamlit as st
from api_client import APIClient

st.title("🏠 Welcome to ECOCRM")
st.caption("Your AI-powered CRM platform")

# Quick Actions at the top for immediate access
st.subheader("Quick Actions")
c1, c2, c3 = st.columns(3)
if c1.button("🤖 New Bot Test", use_container_width=True):
    st.switch_page("pages/bot_studio.py")
if c2.button("📄 Upload Document", use_container_width=True):
    st.switch_page("pages/kb_rag.py")
if c3.button("👥 Manage Users", use_container_width=True):
    st.switch_page("pages/admin.py")

st.divider()

# System Status
st.subheader("System Status")
client = APIClient()
is_healthy, health_data = client.get_health()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Platform API", "Online" if is_healthy else "Offline", delta="Healthy" if is_healthy else "-")

with col2:
    st.metric("Environment", health_data.get("env", "Unknown") if health_data else "Unknown")

with col3:
    st.metric("Active Workers", "1") # Placeholder

