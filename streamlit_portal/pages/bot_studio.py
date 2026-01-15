import streamlit as st
import uuid
import json
from api_client import APIClient

st.set_page_config(layout="wide")
st.title("🤖 Bot Studio")

client = APIClient()

tab_agents, tab_tasks, tab_crews, tab_lab = st.tabs(["🕵️ Agents", "📋 Tasks", "🚀 Crews", "🧪 Test Lab"])

# --- AGENTS TAB ---
with tab_agents:
    st.subheader("Manage Agents")
    
    with st.expander("Create New Agent"):
        with st.form("create_agent_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Name")
            role = col2.text_input("Role")
            goal = st.text_area("Goal")
            tools = st.text_area("Tools (JSON Array)", value='["SearchTool", "ScrapeTool"]')
            
            submitted = st.form_submit_button("Create Agent")
            if submitted:
                try:
                    tools_json = json.loads(tools)
                    resp = client.create_agent({
                        "name": name, 
                        "role": role, 
                        "goal": goal, 
                        "tools_json": tools_json
                    })
                    st.success(f"Agent '{name}' created!")
                except json.JSONDecodeError:
                    st.error("Invalid JSON for tools")
                except Exception as e:
                    st.error(f"Error: {e}")

    # List Agents
    agents = client.list_agents()
    if agents:
        st.dataframe(agents, use_container_width=True)
        for agent in agents:
             with st.expander(f"{agent['name']} ({agent['role']})"):
                st.write(f"**Goal:** {agent['goal']}")
                st.json(agent['tools_json'])
                if st.button("Delete", key=f"del_agent_{agent['id']}"):
                    if client.delete_agent(agent['id']):
                        st.success("Deleted!")
                        st.rerun()

# --- TASKS TAB ---
with tab_tasks:
    st.subheader("Manage Tasks")
    
    # Load agents for selection
    agents_list = client.list_agents()
    agent_map = {a['name']: a['id'] for a in agents_list} if agents_list else {}
    
    with st.expander("Create New Task"):
        with st.form("create_task_form"):
            t_name = st.text_input("Task Name")
            t_desc = st.text_area("Description")
            t_output = st.text_area("Expected Output")
            t_agent_name = st.selectbox("Assign to Agent", options=list(agent_map.keys()))
            
            if st.form_submit_button("Create Task"):
                payload = {
                    "name": t_name,
                    "description": t_desc,
                    "expected_output": t_output,
                    "agent_id": agent_map.get(t_agent_name)
                }
                res = client.create_task(payload)
                st.success("Task Created!")
    
    tasks = client.list_tasks()
    if tasks:
        st.dataframe(tasks, use_container_width=True)
        for task in tasks:
            with st.expander(f"{task['name']}"):
                st.write(task['description'])
                if st.button("Delete Task", key=f"del_task_{task['id']}"):
                    client.delete_task(task['id'])
                    st.rerun()

# --- CREWS TAB ---
with tab_crews:
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.subheader("Create / Edit Crew")
        c_name = st.text_input("Crew Name")
        c_desc = st.text_area("Description")
        c_process = st.selectbox("Process", ["sequential", "hierarchical"])
        
        if st.button("Create Crew"):
            res = client.create_crew({"name": c_name, "description": c_desc, "process": c_process})
            st.success(f"Crew {res['id']} created")
            st.rerun()
            
        st.divider()
        st.subheader("Existing Crews")
        crews = client.list_crews()
        selected_crew_id = None
        
        if crews:
            for c in crews:
                if st.button(f"🆔 {c['id']} - {c['name']}", key=f"sel_crew_{c['id']}"):
                    st.session_state.selected_crew = c['id']
        
        if 'selected_crew' in st.session_state:
            selected_crew_id = st.session_state.selected_crew

    with col_c2:
        if selected_crew_id:
            crew_detail = client.get_crew(selected_crew_id)
            if crew_detail:
                st.header(f"Editing: {crew_detail['name']}")
                st.info(f"Process: {crew_detail['process']}")
                
                st.subheader("Link Tasks (Order Matters)")
                all_tasks = client.list_tasks()
                
                # Simple Multiselect not enough for ordering, use a text area of IDs or multiple selects?
                # For MVP: List all tasks and checkbox + number input
                
                with st.form("link_tasks_form"):
                    links = []
                    sorted_tasks = sorted(all_tasks, key=lambda t: t['id'])
                    
                    st.write("Select tasks and assign order (0 = not included)")
                    for task in sorted_tasks:
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"**{task['name']}**")
                        # Pre-fill if already linked
                        existing_link = next((t for t in crew_detail.get("tasks", []) if t['id'] == task['id']), None)
                        # We don't get 'step_order' back directly in simple 'tasks' list from schema, 
                        # but let's assume simple add for now or user inputs order.
                        
                        order = st.number_input(f"Order for {task['id']}", min_value=0, value=0, key=f"ord_{task['id']}")
                        if order > 0:
                            links.append({"task_id": task['id'], "step_order": int(order)})
                    
                    if st.form_submit_button("Update Task Flow"):
                        client.link_tasks_to_crew(selected_crew_id, links)
                        st.success("Flow updated!")
                        st.rerun()

                st.divider()
                st.subheader("🚀 Publish Version")
                v_tag = st.text_input("Version Tag (e.g., v1.0)", value="v1.0")
                
                # Fetch enabled models
                enabled_models = client.list_enabled_ai_models()
                model_opts = {f"{m['name']} ({m.get('provider', {}).get('name')})": m['id'] for m in enabled_models}
                selected_model_name = st.selectbox("Select Default Model", options=["None"] + list(model_opts.keys()))
                
                sel_model_id = None
                if selected_model_name != "None":
                    sel_model_id = model_opts[selected_model_name]

                if st.button("Publish Snapshot"):
                    v_res = client.publish_crew(selected_crew_id, v_tag, model_id=sel_model_id)
                    if v_res and 'id' in v_res:
                        st.success(f"Version {v_res['version_tag']} published! Snapshot generated.")
                        st.json(v_res['snapshot_json'])
                    else:
                        st.error("Failed to publish.")

# --- TEST LAB (Original) ---
with tab_lab:
    st.header("Test Lab")
    if "run_id" not in st.session_state:
        st.session_state.run_id = str(uuid.uuid4())
        
    l_col1, l_col2 = st.columns([1, 2])
    
    with l_col1:
        st.subheader("Config")
        
        # Crew Selector
        crews = client.list_crews()
        crew_opts = {c['name']: c['id'] for c in crews} if crews else {}
        selected_crew_name = st.selectbox("Select Crew", options=list(crew_opts.keys()))
        
        selected_v_id = None
        if selected_crew_name:
            c_id = crew_opts[selected_crew_name]
            # Fetch detail to get versions
            c_detail = client.get_crew(c_id)
            if c_detail and c_detail.get('versions'):
                versions = c_detail['versions']
                # Sort by id desc
                versions = sorted(versions, key=lambda v: v['id'], reverse=True)
                v_opts = {v['version_tag']: v['id'] for v in versions}
                s_tag = st.selectbox("Version", options=list(v_opts.keys()))
                if s_tag:
                    selected_v_id = v_opts[s_tag]
            else:
                st.warning("No published versions found for this crew.")

        if st.button("New Session"):
            st.session_state.run_id = str(uuid.uuid4())
            # For Manual runs, we might not strictly need persona if using crew, but keep for compatibility
            client.create_run(st.session_state.run_id, f"Run {st.session_state.run_id[:8]}", "Manual Test")
            st.success("Started!")

    with l_col2:
        st.subheader("Chat")
        run_data = client.get_run(st.session_state.run_id)
        current_events = run_data.get("events", []) if run_data else []
        
        for event in current_events:
            # Handle old and new schema
            role = event.get("role")
            content = event.get("content")
            
            # New schema uses payload_json
            if event.get("payload_json"):
                payload = event["payload_json"]
                role = payload.get("role", "assistant")
                content = payload.get("content", "")
                
                # Special event types
                if event.get("event_type") == "run_start":
                    st.caption(f"🚀 Run Started: {payload.get('input')}")
                    continue
                if event.get("event_type") == "run_success":
                    # Usually final answer is in bot_message too, but if separate:
                    # st.success(f"Result: {payload.get('output')}")
                    continue

            if role and content:
                with st.chat_message(role):
                    st.write(content)
        
        if prompt := st.chat_input("Say something..."):
            if not selected_v_id:
                st.error("Please select a Crew Version to run.")
            else:
                with st.chat_message("user"):
                    st.write(prompt)
                
                # Ensure run exists
                client.create_run(st.session_state.run_id, "Auto Run", "Manual")
                
                # Send message with version
                client.send_message(st.session_state.run_id, prompt, "user", crew_version_id=selected_v_id)
                st.rerun()
