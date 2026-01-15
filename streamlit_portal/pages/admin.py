import streamlit as st
import pandas as pd
from api_client import APIClient

st.title("Administration")
client = APIClient()

tab1, tab2, tab3, tab4 = st.tabs(["Configuration", "Users & Roles", "Logs", "Health"])

with tab1:
    st.header("System Configuration")
    if st.button("Fetch Config"):
        config = client.get_config()
        if config:
            st.json(config)
        else:
            st.error("Failed to fetch.")

with tab2:
    st.header("Users Management")
    if st.button("Refresh Users"):
        users = client.get_users()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df[["id", "email", "full_name", "role", "is_active", "is_superuser"]])
        else:
            st.info("No users found.")

with tab3:
    st.header("System Logs")
    if st.button("Load Logs"):
        data = client.get_logs()
        logs = data.get("logs", [])
        for log in logs:
            st.text(log)

with tab4:
    st.header("System Health")
    healthy, data = client.get_health()
    if healthy:
        st.success("System is Healthy")
        st.json(data)
    else:
        st.error(f"System Unhealthy: {data}")
