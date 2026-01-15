import streamlit as st
import pandas as pd
from datetime import date, timedelta
from api_client import APIClient

st.set_page_config(page_title="Data Hub | EcoCRM", page_icon="📊", layout="wide")
client = APIClient()

st.title("📊 Data Hub Analytics")

# Global Filters
with st.sidebar:
    st.header("Filters")
    d_range = st.date_input(
        "Date Range",
        value=(date.today() - timedelta(days=7), date.today()),
        max_value=date.today()
    )
    # Ideally fetch inboxes to select, for now simple text input or optional
    inbox_id = st.number_input("Inbox ID (Optional)", min_value=1, value=0, step=1)
    inbox_id = None if inbox_id == 0 else inbox_id

if len(d_range) == 2:
    start_date, end_date = d_range
else:
    st.error("Please select a date range")
    st.stop()

tab_overview, tab_sla, tab_agents, tab_backlog = st.tabs(["Overview", "SLA / Times", "Agents", "Backlog"])

with tab_overview:
    st.subheader("Overview Volume")
    vol_data = client.get_bi_volume(str(start_date), str(end_date), inbox_id)
    
    if vol_data:
        df_vol = pd.DataFrame(vol_data)
        
        # KPIs
        t_conv = df_vol['conversations_count'].sum()
        t_msg = df_vol['messages_count'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Total Conversations", t_conv)
        c2.metric("Total Messages", t_msg)
        
        # Charts
        st.bar_chart(df_vol, x='day', y=['conversations_count', 'messages_count'])
    else:
        st.info("No volume data found for this period.")

with tab_sla:
    st.subheader("Service Level Agreement (SLA)")
    sla_data = client.get_bi_time_metrics(str(start_date), str(end_date), inbox_id)
    
    if sla_data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg First Response", f"{sla_data.get('avg_first_response', 0):.1f}s")
        c2.metric("Avg Resolution", f"{sla_data.get('avg_resolution', 0):.1f}s")
        c3.metric("Avg Reply Time", f"{sla_data.get('avg_reply_time', 0):.1f}s")
        
        st.json(sla_data) # Show full stats
    else:
        st.info("No SLA data.")

with tab_agents:
    st.subheader("Agent Performance")
    agent_data = client.get_bi_agent_volume(str(start_date), str(end_date))
    
    if agent_data:
        df_agent = pd.DataFrame(agent_data)
        st.dataframe(df_agent, use_container_width=True)
        
        st.bar_chart(df_agent.set_index('user_id')['total_messages'])
    else:
        st.info("No agent data.")

with tab_backlog:
    st.subheader("Current Backlog")
    backlog_data = client.get_bi_backlog(inbox_id)
    
    if backlog_data:
        df_bk = pd.DataFrame(backlog_data)
        
        # Cards
        cols = st.columns(4)
        for i, status in enumerate(['open', 'pending', 'snoozed', 'resolved']):
            count = df_bk[df_bk['status'] == status]['count'].sum()
            cols[i].metric(status.capitalize(), count)
            
        st.table(df_bk)
    else:
        st.info("No backlog snapshot available.")
