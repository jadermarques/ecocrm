import streamlit as st
import uuid
from api_client import APIClient

st.title("Bot Studio")

tab1, tab2, tab3 = st.tabs(["🧪 Test Lab", "📜 Run History", "🧩 Templates"])

client = APIClient()

with tab1:
    st.header("Test Lab")
    
    if "run_id" not in st.session_state:
        st.session_state.run_id = str(uuid.uuid4())
        
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Configuration")
        persona = st.text_area("Persona / System Prompt", "You are a helpful CRM assistant.")
        model = st.selectbox("Model", ["gpt-4o", "gpt-3.5-turbo", "claude-3.5-sonnet"])
        if st.button("Start New Session"):
            st.session_state.run_id = str(uuid.uuid4())
            # Create run in backend
            client.create_run(st.session_state.run_id, f"Run {st.session_state.run_id[:8]}", persona)
            st.success("New session started!")

    with col2:
        st.subheader("Chat Simulator")
        
        # Load valid history if exists
        run_data = client.get_run(st.session_state.run_id)
        current_events = run_data.get("events", []) if run_data else []
        
        # Display chat
        for event in current_events:
            with st.chat_message(event["role"]):
                st.write(event["content"])
        
        # Input
        if prompt := st.chat_input("Say something..."):
            # Optimistic update
            with st.chat_message("user"):
                st.write(prompt)
                
            # Backend call
            # 1. Ensure run exists
            client.create_run(st.session_state.run_id, "Auto Run", persona)
            # 2. Send message
            client.send_message(st.session_state.run_id, prompt, "user")
            
            # 3. Simulate bot response (Since worker is async, we might not get it immediately in a real app without polling)
            # For MVP, we'll just show a success or echo if the worker isn't fully hooked up to reply yet.
            with st.chat_message("assistant"):
                st.info("Message sent to backend. (Worker response pending...)")

with tab2:
    st.header("Run History")
    st.info("Feature explicitly requested but implementation pending backend support for listing runs.")

with tab3:
    st.header("Templates")
    st.info("Prompt templates library.")
