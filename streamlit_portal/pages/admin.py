import streamlit as st
import pandas as pd
from api_client import APIClient

st.title("Administration")
client = APIClient()

tab1, tab2, tab_prov, tab_models, tab3, tab4 = st.tabs(["Configuration", "Users & Roles", "AI Providers", "AI Models", "Logs", "Health"])

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
        users = client.list_users()
        if users:
            df = pd.DataFrame(users)
            st.dataframe(df[["id", "email", "full_name", "role", "is_active", "is_superuser"]])
        else:
            st.info("No users found.")

# --- AI PROVIDERS ---
with tab_prov:
    st.header("AI Providers")
    
    with st.expander("➕ Add New Provider"):
        with st.form("add_provider_form"):
            p_name = st.text_input("Name (e.g., OpenAI)")
            p_base_url = st.text_input("Base URL (Optional)")
            p_notes = st.text_area("Notes")
            if st.form_submit_button("Create Provider"):
                res = client.create_ai_provider({"name": p_name, "base_url": p_base_url, "notes": p_notes})
                if res:
                    st.success("Provider created!")
                    st.rerun()
                else:
                    st.error("Failed to create provider.")
    
    providers = client.list_ai_providers()
    if providers:
        for p in providers:
            with st.expander(f"{p['name']} (ID: {p['id']}) - {'Enabled' if p['is_enabled'] else 'Disabled'}"):
                st.write(f"**Base URL:** {p['base_url']}")
                st.write(f"**Notes:** {p['notes']}")
                if st.button("Delete Provider", key=f"del_prov_{p['id']}"):
                    if client.delete_ai_provider(p['id']):
                        st.success("Deleted!")
                        st.rerun()

# --- AI MODELS ---
with tab_models:
    st.header("AI Models")
    
    # Load Providers for Dropdown
    providers = client.list_ai_providers()
    prov_map = {p['name']: p['id'] for p in providers} if providers else {}
    
    with st.expander("➕ Add New Model"):
        with st.form("add_model_form"):
            c1, c2 = st.columns(2)
            m_name = c1.text_input("Model Name (e.g., gpt-4o)")
            m_prov = c2.selectbox("Provider", options=list(prov_map.keys()))
            
            c3, c4 = st.columns(2)
            m_modality = c3.selectbox("Modality", ["text", "embeddings", "image", "audio"])
            m_ctx = c4.number_input("Context Window", min_value=0, value=128000)
            
            st.subheader("Costs (per 1M tokens)")
            c5, c6 = st.columns(2)
            cost_in = c5.number_input("Input Cost", min_value=0.0, format="%.4f")
            cost_out = c6.number_input("Output Cost", min_value=0.0, format="%.4f")
            
            if st.form_submit_button("Create Model"):
                payload = {
                    "name": m_name,
                    "provider_id": prov_map.get(m_prov),
                    "modality": m_modality,
                    "context_window_tokens": m_ctx,
                    "input_cost_per_1m": cost_in,
                    "output_cost_per_1m": cost_out
                }
                res = client.create_ai_model(payload)
                if res and 'id' in res:
                    st.success("Model created!")
                    st.rerun()
                else:
                    st.error("Failed to create model.")
    
    models = client.list_ai_models()
    if models:
        # Display as table
        data = []
        for m in models:
            p_name = m['provider']['name'] if m.get('provider') else "Unknown"
            data.append({
                "ID": m['id'],
                "Name": m['name'],
                "Provider": p_name,
                "Input Cost": m['input_cost_per_1m'],
                "Output Cost": m['output_cost_per_1m'],
                "Enabled": m['is_enabled']
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True)
        
        # Simple deletion UI below logic
        st.divider()
        del_id = st.number_input("Enter Model ID to Delete", min_value=0)
        if st.button("Delete Model") and client.delete_ai_model(del_id):
             st.success("Deleted!")
             st.rerun()

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
