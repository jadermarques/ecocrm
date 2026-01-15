import streamlit as st
import os
import requests

st.set_page_config(page_title="ECOCRM Portal", page_icon="🌱")

st.title("ECOCRM Portal")

st.write("Welcome to the ECOCRM Admin Portal.")

st.sidebar.header("Navigation")
st.sidebar.info(f"Environment: {os.getenv('APP_ENV', 'unknown')}")

# Test API connection
api_url = os.getenv("PLATFORM_API_BASE_URL", "http://platform_api:8000")

if st.button("Check API Status"):
    try:
        response = requests.get(f"{api_url}/health", timeout=2)
        if response.status_code == 200:
            st.success(f"API is connected: {response.json()}")
        else:
            st.error(f"API returned status {response.status_code}")
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")
