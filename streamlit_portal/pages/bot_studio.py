import streamlit as st
import uuid
import json
import yaml
from api_client import APIClient

st.set_page_config(layout="wide")
st.title("🤖 Bot Studio")

client = APIClient()

# UI Constants
LBL_CREATION_METHOD = "Creation Method"
LBL_MANUAL_FORM = "Manual Form"
LBL_YAML_UPLOAD = "YAML Upload"
LBL_CHOOSE_YAML = "Choose a YAML file"
LBL_ADVANCED_SETTINGS = "⚙️ Advanced Settings"
LBL_FUNC_CALL_LLM = "Function Calling LLM"
LBL_MAX_RPM = "Max RPM"

tab_agents, tab_tasks, tab_crews, tab_lab = st.tabs(["🕵️ Agents", "📋 Tasks", "🚀 Crews", "🧪 Test Lab"])

# --- AGENTS TAB ---
with tab_agents:
    st.subheader("Manage Agents")
    
    # Method selection
    create_method = st.radio(LBL_CREATION_METHOD, [LBL_MANUAL_FORM, LBL_YAML_UPLOAD], horizontal=True, key="agent_method")
    
    if create_method == LBL_YAML_UPLOAD:
        st.info("📤 Upload a YAML file to create one or multiple agents")
        uploaded_file = st.file_uploader(LBL_CHOOSE_YAML, type=["yaml", "yml"], key="agent_yaml")
        
        if uploaded_file is not None:
            try:
                # Parse and store in session_state
                if 'agent_yaml_data' not in st.session_state or st.session_state.get('last_uploaded_file') != uploaded_file.name:
                    yaml_content = yaml.safe_load(uploaded_file)
                    st.session_state.agent_yaml_data = yaml_content
                    st.session_state.last_uploaded_file = uploaded_file.name
                
                yaml_content = st.session_state.agent_yaml_data
                
                # Support multiple formats:
                # 1. List of agents: [{name: "Agent1", ...}, {name: "Agent2", ...}]
                # 2. Single agent: {name: "Agent1", ...}
                # 3. Dict of agents: {agent1: {role: ..., goal: ...}, agent2: {...}}
                if isinstance(yaml_content, list):
                    agents_to_create = yaml_content
                elif isinstance(yaml_content, dict):
                    # Check if it's a single agent or dict of agents
                    if 'role' in yaml_content and 'goal' in yaml_content:
                        # Single agent
                        agents_to_create = [yaml_content]
                    else:
                        # Dict of agents - convert to list
                        agents_to_create = []
                        for agent_name, agent_config in yaml_content.items():
                            agent_config['name'] = agent_name
                            agents_to_create.append(agent_config)
                else:
                    st.error("❌ Invalid YAML format")
                    agents_to_create = []
                
                st.subheader("Preview")
                for idx, agent_data in enumerate(agents_to_create):
                    with st.expander(f"Agent {idx + 1}: {agent_data.get('name', 'Unnamed')}"):
                        st.json(agent_data)
                
                if st.button("Create Agent(s) from YAML", type="primary", key="create_agents_yaml"):
                    created_count = 0
                    errors = []
                    for agent_data in agents_to_create:
                        # Convert tools list to tools_json if present
                        agent_payload = agent_data.copy()
                        if 'tools' in agent_payload:
                            agent_payload['tools_json'] = agent_payload.pop('tools')
                        
                        resp = client.create_agent(agent_payload)
                        if resp and 'id' in resp:
                            created_count += 1
                        else:
                            errors.append(f"Failed to create {agent_payload.get('name', 'unnamed')}")
                    
                    if created_count > 0:
                        st.success(f"✅ Created {created_count} agent(s)!")
                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                            
                    # Clear session state
                    if 'agent_yaml_data' in st.session_state:
                        del st.session_state.agent_yaml_data
                    if 'last_uploaded_file' in st.session_state:
                        del st.session_state.last_uploaded_file
                    
            except yaml.YAMLError as e:
                st.error(f"❌ Invalid YAML format: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    else:  # Manual Form
        with st.expander("➕ Create New Agent"):
            with st.form("create_agent_form"):
                col1, col2 = st.columns(2)
                
                # Basic fields
                name = col1.text_input("Name *", help="Agent's name")
                role = col2.text_input("Role *", help="Agent's role (e.g., 'Senior Researcher')")
                goal = st.text_area("Goal *", help="What this agent aims to achieve")
                backstory = st.text_area("Backstory", help="Agent's background and personality")
                tools = st.text_area("Tools (JSON Array)", value='[]', help="List of tool names")
                
                # Advanced Settings
                with st.expander(LBL_ADVANCED_SETTINGS):
                    adv_col1, adv_col2 = st.columns(2)
                    
                    # LLM Configuration
                    llm = adv_col1.text_input("LLM", placeholder="gpt-4", help="Language model to use")
                    function_calling_llm = adv_col2.text_input(LBL_FUNC_CALL_LLM, help="LLM for tool calls")
                    
                    # Execution Control
                    max_iter = adv_col1.number_input("Max Iterations", value=20, min_value=1, help="Max iterations before giving best answer")
                    max_rpm = adv_col2.number_input(LBL_MAX_RPM, value=0, min_value=0, help="Max requests per minute (0 = unlimited)")
                    max_execution_time = adv_col1.number_input("Max Execution Time (s)", value=0, min_value=0, help="Max execution time in seconds (0 = unlimited)")
                    
                    # Behavior Flags
                    st.write("**Behavior**")
                    behavior_col1, behavior_col2, behavior_col3 = st.columns(3)
                    verbose = behavior_col1.checkbox("Verbose", help="Enable detailed logs")
                    allow_delegation = behavior_col2.checkbox("Allow Delegation", help="Can delegate tasks to other agents")
                    reasoning = behavior_col3.checkbox("Reasoning", help="Reflect and plan before executing")
                    
                    # Knowledge Sources - Multi-select amigável
                    st.markdown("**📚 Bases de Conhecimento**")
                    try:
                        available_kbs = client.list_kbs()
                        st.write(f"DEBUG: Encontradas {len(available_kbs) if available_kbs else 0} bases")  # DEBUG
                        if available_kbs:
                            kb_options = {f"{kb['name']} (ID: {kb['id']})": kb['id'] for kb in available_kbs}
                            selected_kb_labels = st.multiselect(
                                "Selecione as bases de conhecimento",
                                options=list(kb_options.keys()),
                                help="Selecione uma ou mais bases para este agente consultar"
                            )
                            # Convert selected labels back to IDs
                            selected_kb_ids = [kb_options[label] for label in selected_kb_labels]
                        else:
                            st.info("ℹ️ Nenhuma base de conhecimento disponível. Crie uma na página de Gestão.")
                            selected_kb_ids = []
                    except Exception as e:
                        st.error(f"❌ Erro ao carregar bases: {e}")  # Mudado de warning para error
                        import traceback
                        st.code(traceback.format_exc())  # Mostrar stacktrace completo
                        selected_kb_ids = []
                
                submitted = st.form_submit_button("Create Agent", type="primary")
                if submitted:
                    try:
                        tools_json = json.loads(tools)
                        
                        # Build knowledge_sources from selected IDs
                        knowledge_sources = []
                        for kb_id in selected_kb_ids:
                            kb = next((k for k in available_kbs if k['id'] == kb_id), None)
                            if kb:
                                knowledge_sources.append({
                                    "type": kb.get("strategy", "openai_vector_store"),
                                    "kb_id": kb_id,
                                    "name": kb['name']
                                })
                        
                        agent_data = {
                            "name": name,
                            "role": role,
                            "goal": goal,
                            "backstory": backstory if backstory else None,
                            "tools_json": tools_json,
                            "llm": llm if llm else None,
                            "function_calling_llm": function_calling_llm if function_calling_llm else None,
                            "max_iter": max_iter,
                            "max_rpm": max_rpm if max_rpm > 0 else None,
                            "max_execution_time": max_execution_time if max_execution_time > 0 else None,
                            "verbose": verbose,
                            "allow_delegation": allow_delegation,
                            "reasoning": reasoning,
                            "knowledge_sources": knowledge_sources if knowledge_sources else None,
                        }
                        
                        resp = client.create_agent(agent_data)
                        st.success(f"✅ Agent '{name}' created!")
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON in tools or knowledge sources")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # List Agents
    st.divider()
    st.subheader("Existing Agents")
    agents = client.list_agents()
    
    if agents:
        # Use columns for layout
        for agent in agents:
            with st.expander(f"🕵️ {agent['name']} ({agent['role']})"):
                c1, c2 = st.columns([4, 1])
                
                with c1:
                    st.write(f"**Goal:** {agent['goal']}")
                    if agent.get('backstory'):
                        st.info(f"**Backstory:** {agent['backstory']}")
                    
                    # Display config
                    st.caption(f"**Model:** {agent.get('llm') or 'Default'} | **Max Iter:** {agent.get('max_iter')}")
                    
                    if agent.get('tools_json'):
                        st.write("**Tools:**")
                        st.json(agent['tools_json'])
                        
                with c2:
                    # Edit Button
                    if st.button("✏️ Edit", key=f"edit_agent_{agent['id']}"):
                        st.session_state.editing_agent = agent
                        st.rerun()
                        
                    # Delete Button with Confirmation
                    if st.button("🗑️ Delete", key=f"del_agent_btn_{agent['id']}", type="secondary"):
                        st.session_state[f"confirm_del_agent_{agent['id']}"] = True
                        
                    if st.session_state.get(f"confirm_del_agent_{agent['id']}"):
                        st.warning("Are you sure?")
                        col_confirm, col_cancel = st.columns(2)
                        if col_confirm.button("Yes, Delete", key=f"conf_del_agent_{agent['id']}", type="primary"):
                            if client.delete_agent(agent['id']):
                                st.success("Deleted!")
                                del st.session_state[f"confirm_del_agent_{agent['id']}"]
                                st.rerun()
                        if col_cancel.button("Cancel", key=f"canc_del_agent_{agent['id']}"):
                            del st.session_state[f"confirm_del_agent_{agent['id']}"]
                            st.rerun()

    # Pre-fill form if editing
    if "editing_agent" in st.session_state:
        edit_data = st.session_state.editing_agent
        st.info(f"📝 Editing Agent: {edit_data['name']}")
        
        with st.form("edit_agent_form"):
            col1, col2 = st.columns(2)
            e_name = col1.text_input("Name", value=edit_data['name'])
            e_role = col2.text_input("Role", value=edit_data['role'])
            e_goal = st.text_area("Goal", value=edit_data['goal'])
            e_backstory = st.text_area("Backstory", value=edit_data.get('backstory') or "")
            
            # Tools need to be dumped to string
            tools_val = json.dumps(edit_data.get('tools_json', []))
            e_tools = st.text_area("Tools (JSON Array)", value=tools_val)
            
            # Advanced
            with st.expander(LBL_ADVANCED_SETTINGS, expanded=True):
                adv_col1, adv_col2 = st.columns(2)
                a_llm = adv_col1.text_input("LLM", value=edit_data.get('llm') or "", placeholder="gpt-4o")
                a_func_llm = adv_col2.text_input(LBL_FUNC_CALL_LLM, value=edit_data.get('function_calling_llm') or "", placeholder="gpt-3.5-turbo")
                
                a_max_iter = adv_col1.number_input("Max Iterations", value=edit_data.get('max_iter', 20))
                a_max_rpm = adv_col2.number_input(LBL_MAX_RPM, value=edit_data.get('max_rpm') or 0)
                a_max_exec = adv_col1.number_input("Max Exec Time", value=edit_data.get('max_execution_time') or 0)
                
                b_col1, b_col2, b_col3 = st.columns(3)
                e_verbose = b_col1.checkbox("Verbose", value=edit_data.get('verbose', False))
                e_delegation = b_col2.checkbox("Allow Delegation", value=edit_data.get('allow_delegation', False))
                e_reasoning = b_col3.checkbox("Reasoning", value=edit_data.get('reasoning', False))
                
                # Knowledge Sources - Multi-select amigável (EDIÇÃO)
                st.markdown("**📚 Bases de Conhecimento**")
                try:
                    available_kbs = client.list_kbs()
                    st.write(f"DEBUG: Encontradas {len(available_kbs) if available_kbs else 0} bases")  # DEBUG
                    
                    # Get currently selected KBs from edit_data
                    current_kb_sources = edit_data.get('knowledge_sources', []) or []
                    current_kb_ids = [kb.get('kb_id') for kb in current_kb_sources if isinstance(kb, dict) and kb.get('kb_id')]
                    
                    if available_kbs:
                        kb_options = {f"{kb['name']} (ID: {kb['id']})": kb['id'] for kb in available_kbs}
                        # Pre-select currently associated KBs
                        default_selections = [label for label, kb_id in kb_options.items() if kb_id in current_kb_ids]
                        
                        selected_kb_labels = st.multiselect(
                            "Selecione as bases de conhecimento",
                            options=list(kb_options.keys()),
                            default=default_selections,
                            help="Selecione uma ou mais bases para este agente consultar"
                        )
                        # Convert selected labels back to IDs
                        selected_kb_ids = [kb_options[label] for label in selected_kb_labels]
                    else:
                        st.info("ℹ️ Nenhuma base de conhecimento disponível. Crie uma na página de Gestão.")
                        selected_kb_ids = []
                except Exception as e:
                    st.error(f"❌ Erro ao carregar bases: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    selected_kb_ids = []

            col_save, col_cancel_edit = st.columns([1, 4])
            if col_save.form_submit_button("💾 Save Changes", type="primary"):
                try:
                    # Build knowledge_sources from selected IDs
                    knowledge_sources = []
                    for kb_id in selected_kb_ids:
                        kb = next((k for k in available_kbs if k['id'] == kb_id), None)
                        if kb:
                            knowledge_sources.append({
                                "type": kb.get("strategy", "openai_vector_store"),
                                "kb_id": kb_id,
                                "name": kb['name']
                            })
                    
                    payload = {
                        "name": e_name,
                        "role": e_role,
                        "goal": e_goal,
                        "backstory": e_backstory if e_backstory else None,
                        "tools_json": json.loads(e_tools),
                        "llm": a_llm if a_llm else None,
                        "function_calling_llm": a_func_llm if a_func_llm else None,
                        "max_iter": a_max_iter,
                        "max_rpm": a_max_rpm if a_max_rpm > 0 else None,
                        "max_execution_time": a_max_exec if a_max_exec > 0 else None,
                        "verbose": e_verbose,
                        "allow_delegation": e_delegation,
                        "reasoning": e_reasoning,
                        "knowledge_sources": knowledge_sources if knowledge_sources else None
                    }
                    client.update_agent(edit_data['id'], payload)
                    st.success("✅ Agent updated!")
                    del st.session_state.editing_agent
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error: {ex}")
            
            if col_cancel_edit.form_submit_button("Cancel"):
                del st.session_state.editing_agent
                st.rerun()

# --- TASKS TAB ---
with tab_tasks:
    st.subheader("Manage Tasks")
    
    # Load agents for selection
    agents_list = client.list_agents()
    agent_map = {a['name']: a['id'] for a in agents_list} if agents_list else {}
    
    # Method selection
    create_method_task = st.radio(LBL_CREATION_METHOD, [LBL_MANUAL_FORM, LBL_YAML_UPLOAD], horizontal=True, key="task_method")
    
    if create_method_task == LBL_YAML_UPLOAD:
        st.info("📤 Upload a YAML file to create one or multiple tasks")
        uploaded_file_task = st.file_uploader(LBL_CHOOSE_YAML, type=["yaml", "yml"], key="task_yaml")
        
        if uploaded_file_task is not None:
            try:
                # Parse and store in session_state
                if 'task_yaml_data' not in st.session_state or st.session_state.get('last_uploaded_task_file') != uploaded_file_task.name:
                    yaml_content = yaml.safe_load(uploaded_file_task)
                    st.session_state.task_yaml_data = yaml_content
                    st.session_state.last_uploaded_task_file = uploaded_file_task.name
                
                yaml_content = st.session_state.task_yaml_data
                
                tasks_to_create = []
                if isinstance(yaml_content, list):
                    tasks_to_create = yaml_content
                elif isinstance(yaml_content, dict):
                    # Check if it's a single task or dict of tasks
                    if 'description' in yaml_content and 'expected_output' in yaml_content:
                        tasks_to_create = [yaml_content]
                    else:
                        # Dict of tasks
                        for task_name, task_config in yaml_content.items():
                            task_config['name'] = task_name
                            tasks_to_create.append(task_config)
                
                st.subheader("Preview")
                for idx, task_data in enumerate(tasks_to_create):
                    with st.expander(f"Task {idx + 1}: {task_data.get('name', 'Unnamed')}"):
                        st.json(task_data)
                
                if st.button("Create Task(s) from YAML", type="primary", key="create_tasks_yaml"):
                    created_count = 0
                    errors = []
                    for task_data in tasks_to_create:
                        # Map agent name to ID if present
                        if 'agent' in task_data:
                            agent_name = task_data.pop('agent')
                            task_data['agent_id'] = agent_map.get(agent_name)
                        
                        resp = client.create_task(task_data)
                        if resp and 'id' in resp:
                            created_count += 1
                        else:
                            errors.append(f"Failed to create {task_data.get('name', 'unnamed')}: {resp}")
                    
                    if created_count > 0:
                        st.success(f"✅ Created {created_count} task(s)!")
                    if errors:
                        for err in errors:
                            st.error(f"❌ {err}")

                    # Clear session state
                    if 'task_yaml_data' in st.session_state:
                        del st.session_state.task_yaml_data
                    if 'last_uploaded_task_file' in st.session_state:
                        del st.session_state.last_uploaded_task_file
                    
            except yaml.YAMLError as e:
                st.error(f"❌ Invalid YAML format: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    else:  # Manual Form
        with st.expander("➕ Create New Task"):
            with st.form("create_task_form"):
                t_name = st.text_input("Task Name *")
                t_desc = st.text_area("Description *")
                t_output = st.text_area("Expected Output")
                t_agent_name = st.selectbox("Assign to Agent", options=["None"] + list(agent_map.keys()))
                
                # Advanced Configuration
                with st.expander("⚙️ Advanced Configuration"):
                    task_tools = st.text_area("Task-specific Tools (JSON)", value='[]', help="Tools available only for this task")
                    
                    # Context tasks
                    all_tasks = client.list_tasks()
                    task_names = [t['name'] for t in all_tasks] if all_tasks else []
                    context_tasks = st.multiselect("Context Tasks", options=task_names, help="Other tasks whose outputs will be used as context")
                    
                    async_exec = st.checkbox("Async Execution", help="Execute this task asynchronously")
                    
                    st.write("**Output Configuration**")
                    output_json = st.text_area("Output JSON Schema", value='{}', help="Pydantic model schema for output")
                    
                    st.write("**Guardrails**")
                    guardrail_config = st.text_area("Guardrail Config (JSON)", value='{}', help="Validation function configuration")
                    guardrail_retries = st.number_input("Guardrail Max Retries", value=3, min_value=1)
                
                if st.form_submit_button("Create Task", type="primary"):
                    try:
                        task_tools_json = json.loads(task_tools)
                        output_json_schema = json.loads(output_json)
                        guardrail_json = json.loads(guardrail_config)
                        
                        # Get context task IDs
                        context_ids = [t['id'] for t in all_tasks if t['name'] in context_tasks] if all_tasks else []
                        
                        payload = {
                            "name": t_name,
                            "description": t_desc,
                            "expected_output": t_output,
                            "agent_id": agent_map.get(t_agent_name) if t_agent_name != "None" else None,
                            "tools_json": task_tools_json if task_tools_json else None,
                            "context_task_ids": context_ids if context_ids else None,
                            "async_execution": async_exec,
                            "output_json_schema": output_json_schema if output_json_schema else None,
                            "guardrail_config": guardrail_json if guardrail_json else None,
                            "guardrail_max_retries": guardrail_retries,
                        }
                        res = client.create_task(payload)
                        st.success("✅ Task Created!")
                        st.rerun()
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON in configuration")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    # List Tasks
    st.divider()
    st.subheader("Existing Tasks")
    tasks = client.list_tasks()
    if tasks:
        all_crews = client.list_crews()
        crew_task_ids = []
        for c in all_crews:
            crew_task_ids.extend([l['task_id'] for l in c.get('task_links', [])])
            
        for task in tasks:
            with st.expander(f"📋 {task['name']}"):
                t1, t2 = st.columns([4, 1])
                with t1:
                    st.write(f"**Description:** {task['description']}")
                    st.write(f"**Expected Output:** {task['expected_output']}")
                    
                    # Agent info
                    if task.get('agent_id'):
                        ag = next((a for a in agents_list if a['id'] == task['agent_id']), None)
                        st.caption(f"👤 Assigned to: **{ag['name'] if ag else 'Unknown'}**")
                    else:
                        st.caption("👤 Unassigned")
                        
                with t2:
                    # Edit Button
                    if st.button("✏️ Edit", key=f"edit_task_{task['id']}"):
                        st.session_state.editing_task = task
                        st.rerun()

                    # Delete Button
                    is_linked = task['id'] in crew_task_ids
                    if st.button("🗑️ Delete", key=f"del_task_btn_{task['id']}", type="secondary", disabled=is_linked, help="Cannot delete task linked to a crew" if is_linked else None):
                        st.session_state[f"confirm_del_task_{task['id']}"] = True
                
                if st.session_state.get(f"confirm_del_task_{task['id']}"):
                    st.warning("Are you sure?")
                    tc1, tc2 = st.columns(2)
                    if tc1.button("Yes", key=f"yes_del_task_{task['id']}", type="primary"):
                        if client.delete_task(task['id']):
                            st.success("Deleted!")
                            del st.session_state[f"confirm_del_task_{task['id']}"]
                            st.rerun()
                    if tc2.button("No", key=f"no_del_task_{task['id']}"):
                        del st.session_state[f"confirm_del_task_{task['id']}"]
                        st.rerun()

    # Pre-fill form if editing task
    if "editing_task" in st.session_state:
        t_data = st.session_state.editing_task
        st.info(f"📝 Editing Task: {t_data['name']}")
        
        with st.form("edit_task_form"):
            et_name = st.text_input("Task Name", value=t_data['name'])
            et_desc = st.text_area("Description", value=t_data['description'])
            et_output = st.text_area("Expected Output", value=t_data['expected_output'])
            
            # Find current agent name
            curr_agent_name = "None"
            if t_data.get('agent_id'):
                 ag = next((a for a in agents_list if a['id'] == t_data['agent_id']), None)
                 if ag: curr_agent_name = ag['name']
            
            et_agent_name = st.selectbox("Assign to Agent", options=["None"] + list(agent_map.keys()), index=0 if curr_agent_name == "None" else (list(agent_map.keys()).index(curr_agent_name) + 1))
            
            with st.expander("⚙️ Advanced Configuration", expanded=True):
                 tools_val = json.dumps(t_data.get('tools_json', []))
                 et_tools = st.text_area("Task-specific Tools (JSON)", value=tools_val)
                 
                 et_async = st.checkbox("Async Execution", value=t_data.get('async_execution', False))
                 
                 # Output/Guardrails
                 out_schema_val = json.dumps(t_data.get('output_json_schema') or {})
                 et_output_json = st.text_area("Output JSON Schema", value=out_schema_val)
                 
                 guard_val = json.dumps(t_data.get('guardrail_config') or {})
                 et_guardrail = st.text_area("Guardrail Config", value=guard_val)
                 et_retries = st.number_input("Max Retries", value=t_data.get('guardrail_max_retries', 3))

            c_save, c_cancel = st.columns([1, 4])
            
            if c_save.form_submit_button("💾 Save Changes", type="primary"):
                try:
                     payload = {
                        "name": et_name,
                        "description": et_desc,
                        "expected_output": et_output,
                        "agent_id": agent_map.get(et_agent_name) if et_agent_name != "None" else None,
                        "tools_json": json.loads(et_tools),
                        "async_execution": et_async,
                        "output_json_schema": json.loads(et_output_json),
                        "guardrail_config": json.loads(et_guardrail),
                        "guardrail_max_retries": et_retries
                     }
                     client.update_task(t_data['id'], payload)
                     st.success("Task updated!")
                     del st.session_state.editing_task
                     st.rerun()
                except Exception as ex:
                    st.error(f"Error: {ex}")
            
            if c_cancel.form_submit_button("Cancel"):
                del st.session_state.editing_task
                st.rerun()

# --- CREWS TAB ---
with tab_crews:
    col_c1, col_c2 = st.columns([1, 2])
    
    with col_c1:
        st.subheader("Create / Edit Crew")
        
        # Method selection
        create_method_crew = st.radio(LBL_CREATION_METHOD, [LBL_MANUAL_FORM, LBL_YAML_UPLOAD], horizontal=True, key="crew_method")
        
        if create_method_crew == LBL_YAML_UPLOAD:
            st.info("📤 Upload a YAML file to create one or multiple crews")
            uploaded_file_crew = st.file_uploader(LBL_CHOOSE_YAML, type=["yaml", "yml"], key="crew_yaml")
            
            if uploaded_file_crew is not None:
                try:
                    crew_yaml = yaml.safe_load(uploaded_file_crew)
                    
                    st.subheader("Preview")
                    st.json(crew_yaml)
                    
                    if st.button("Create Crew from YAML", type="primary"):
                        res = client.create_crew(crew_yaml)
                        st.success(f"✅ Crew '{crew_yaml.get('name')}' created!")
                        st.rerun()
                        
                except yaml.YAMLError as e:
                    st.error(f"❌ Invalid YAML format: {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        else:  # Manual Form
            c_name = st.text_input("Crew Name *")
            c_desc = st.text_area("Description")
            c_process = st.selectbox("Process", ["sequential", "hierarchical"])
            
            # Advanced Settings
            with st.expander(LBL_ADVANCED_SETTINGS):
                verbose_crew = st.checkbox("Verbose", value=False)
                max_rpm_crew = st.number_input(LBL_MAX_RPM, value=0, min_value=0, help="Max requests per minute")
                
                st.write("**LLM Configuration**")
                manager_llm = st.text_input("Manager LLM", help="Required for hierarchical process")
                function_calling_llm_crew = st.text_input("Function Calling LLM")
                
                st.write("**Manager Configuration**")
                manager_agent = st.selectbox("Manager Agent", options=["None"] + [a['name'] for a in agents_list])
                
                st.write("**Features**")
                memory_enabled = st.checkbox("Enable Memory", help="Short/long-term memory")
                share_crew = st.checkbox("Share Crew Data", help="Share with CrewAI team for improvements")
                
                knowledge_crew = st.text_area("Knowledge Sources (JSON)", value='[]')
                config_crew = st.text_area("Additional Config (JSON)", value='{}')
                output_log = st.text_input("Output Log File", placeholder="logs/crew.txt")
            
            if st.button("Create Crew", type="primary"):
                try:
                    knowledge_json_crew = json.loads(knowledge_crew)
                    config_json_crew = json.loads(config_crew)
                    
                    crew_data = {
                        "name": c_name,
                        "description": c_desc,
                        "process": c_process,
                        "verbose": verbose_crew,
                        "max_rpm": max_rpm_crew if max_rpm_crew > 0 else None,
                        "manager_llm": manager_llm if manager_llm else None,
                        "function_calling_llm": function_calling_llm_crew if function_calling_llm_crew else None,
                        "manager_agent_id": agent_map.get(manager_agent) if manager_agent != "None" else None,
                        "memory_enabled": memory_enabled,
                        "share_crew": share_crew,
                        "knowledge_sources": knowledge_json_crew if knowledge_json_crew else None,
                        "config_json": config_json_crew if config_json_crew else None,
                        "output_log_file": output_log if output_log else None,
                    }
                    
                    res = client.create_crew(crew_data)
                    if res and 'id' in res:
                        st.success("✅ Crew created!")
                        # No rerun here to let the user see the message
                    else:
                        st.error(f"❌ Failed to create crew: {res}")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            
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
                
                # Actions: Download YAML & Delete
                c_act1, c_act2 = st.columns([1, 1])
                
                with c_act1:
                    # Construct Complete YAML Data
                    try:
                        # 1. Agents (referenced in tasks or manager)
                        crew_agent_ids = set()
                        if crew_detail.get('manager_agent_id'):
                            crew_agent_ids.add(crew_detail['manager_agent_id'])
                        
                        # Tasks are in crew_detail['tasks']
                        # They are sorted by order in the backend if using the .tasks property from BotCrewDetail?
                        # Check api endpoints: get_crew returns BotCrewDetail, which has "tasks" populated manually from links.
                        # Yes: response.tasks = [schemas.BotTask.model_validate(link.task) for link in sorted_links]
                        
                        crew_tasks = crew_detail.get('tasks', [])
                        for t in crew_tasks:
                            if t.get('agent_id'):
                                crew_agent_ids.add(t['agent_id'])
                        
                        export_agents = []
                        for aid in crew_agent_ids:
                             ag = next((a for a in agents_list if a['id'] == aid), None)
                             if ag:
                                 # Clean up internal fields if desired, or dump everything
                                 ag_clean = ag.copy()
                                 if 'created_at' in ag_clean: del ag_clean['created_at']
                                 if 'id' in ag_clean: del ag_clean['id'] # Remove IDs for portability? Or keep?
                                 # Keeping IDs might confuse re-import if IDs conflict. Let's remove ID for "Template" style export.
                                 export_agents.append(ag_clean)
                        
                        export_tasks = []
                        for t in crew_tasks:
                             t_clean = t.copy()
                             if 'created_at' in t_clean: del t_clean['created_at']
                             if 'id' in t_clean: del t_clean['id']
                             if 'agent_id' in t_clean:
                                 # Replace agent_id with agent_name reference? 
                                 # Or keep agent_id if we want to debug? 
                                 # Use name for readability
                                 ag = next((a for a in agents_list if a['id'] == t['agent_id']), None)
                                 if ag:
                                     t_clean['agent'] = ag['name']
                                     del t_clean['agent_id']
                             export_tasks.append(t_clean)
                        
                        crew_clean = crew_detail.copy()
                        if 'created_at' in crew_clean: del crew_clean['created_at']
                        if 'task_links' in crew_clean: del crew_clean['task_links']
                        if 'tasks' in crew_clean: del crew_clean['tasks']
                        if 'versions' in crew_clean: del crew_clean['versions']
                        if 'id' in crew_clean: del crew_clean['id']
                        
                        # Resolve Manager Agent ID
                        if crew_clean.get('manager_agent_id'):
                            mag = next((a for a in agents_list if a['id'] == crew_clean['manager_agent_id']), None)
                            if mag:
                                crew_clean['manager_agent'] = mag['name']
                                del crew_clean['manager_agent_id']
                                
                        full_export = {
                            "crew": crew_clean,
                            "agents": export_agents,
                            "tasks": export_tasks
                        }
                        
                        yaml_str = yaml.dump(full_export, sort_keys=False, allow_unicode=True)
                        
                        st.download_button(
                            label="💾 Download YAML",
                            data=yaml_str,
                            file_name=f"{crew_detail['name'].lower().replace(' ', '_')}.yaml",
                            mime="application/x-yaml"
                        )
                    except Exception as e:
                        st.error(f"Error generating YAML: {e}")

                with c_act2:
                    if st.button("🗑️ Delete Crew", type="secondary", key=f"del_crew_{selected_crew_id}"):
                        st.session_state[f"confirm_del_crew_{selected_crew_id}"] = True
                
                if st.session_state.get(f"confirm_del_crew_{selected_crew_id}"):
                    st.error("This will delete the crew and all its versions. Confirm?")
                    col_confirm, col_cancel = st.columns(2)
                    if col_confirm.button("Yes, Delete Crew", type="primary", key="yes_del_crew"):
                        if client.delete_crew(selected_crew_id):
                            st.success("Crew deleted!")
                            del st.session_state[f"confirm_del_crew_{selected_crew_id}"]
                            del st.session_state.selected_crew
                            st.rerun()
                        else:
                            st.error("Failed to delete crew.")
                            
                    if col_cancel.button("Cancel", key="cancel_del_crew"):
                        del st.session_state[f"confirm_del_crew_{selected_crew_id}"]
                        st.rerun()
                        
                # Tabs for Edit / Links / Publish
                tab_edit_c, tab_links_c, tab_pub_c = st.tabs(["📝 Details", "🔗 Tasks Link", "🚀 Publish"])
                
                with tab_edit_c:
                    with st.form("edit_crew_form"):
                        ec_name = st.text_input("Name", value=crew_detail['name'])
                        ec_desc = st.text_area("Description", value=crew_detail['description'])
                        ec_process = st.selectbox("Process", ["sequential", "hierarchical"], index=0 if crew_detail['process'] == 'sequential' else 1)
                        
                        with st.expander(LBL_ADVANCED_SETTINGS, expanded=False):
                            ec_verbose = st.checkbox("Verbose", value=crew_detail.get('verbose', False))
                            ec_max_rpm = st.number_input(LBL_MAX_RPM, value=crew_detail.get('max_rpm') or 0)
                            
                            # Manager
                            curr_man = "None"
                            if crew_detail.get('manager_agent_id'):
                                ag = next((a for a in agents_list if a['id'] == crew_detail['manager_agent_id']), None)
                                if ag: curr_man = ag['name']
                            
                            ec_manager = st.selectbox("Manager Agent", options=["None"] + list(agent_map.keys()), index=0 if curr_man == "None" else (list(agent_map.keys()).index(curr_man) + 1))
                            
                            # LLM
                            ec_man_llm = st.text_input("Manager LLM", value=crew_detail.get('manager_llm') or "")
                            
                        if st.form_submit_button("Update Details"):
                            payload = {
                                "name": ec_name,
                                "description": ec_desc,
                                "process": ec_process,
                                "verbose": ec_verbose,
                                "max_rpm": ec_max_rpm if ec_max_rpm > 0 else None,
                                "manager_agent_id": agent_map.get(ec_manager) if ec_manager != "None" else None,
                                "manager_llm": ec_man_llm if ec_man_llm else None
                            }
                            client.update_crew(crew_detail['id'], payload)
                            st.success("Crew updated!")
                            st.rerun()

                with tab_links_c:
                    st.subheader("Link Tasks (Order Matters)")
                    all_tasks = client.list_tasks()
                    
                    # Current links
                    curr_links = {l['task_id']: l['step_order'] for l in crew_detail.get('task_links', [])}
                    
                    with st.form("link_tasks_form"):
                        links = []
                        sorted_tasks = sorted(all_tasks, key=lambda t: t['id'])
                        
                        st.write("Select tasks and assign order (0 = not included)")
                        for task in sorted_tasks:
                            c1, c2 = st.columns([3, 1])
                            c1.write(f"**{task['name']}**")
                            
                            val = curr_links.get(task['id'], 0)
                            order = c2.number_input(f"Order", min_value=0, value=val, key=f"ord_{task['id']}")
                            if order > 0:
                                links.append({"task_id": task['id'], "step_order": int(order)})
                        
                        if st.form_submit_button("Update Task Flow"):
                            client.link_tasks_to_crew(selected_crew_id, links)
                            st.success("Flow updated!")
                            st.rerun()

                with tab_pub_c:
                    st.subheader("🚀 Publish Version")
                    v_tag = st.text_input("Version Tag (e.g., v1.0)", value="v1.0")
                    
                    # Fetch enabled models
                    enabled_models = client.list_enabled_ai_models()
                    model_opts = {m["name"] + " (" + m.get("provider", {}).get("name", "Unknown") + ")": m["id"] for m in enabled_models}
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

# --- TEST LAB (Keep original) ---
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
            c_detail = client.get_crew(c_id)
            if c_detail and c_detail.get('versions'):
                versions = c_detail['versions']
                versions = sorted(versions, key=lambda v: v['id'], reverse=True)
                v_opts = {v['version_tag']: v['id'] for v in versions}
                s_tag = st.selectbox("Version", options=list(v_opts.keys()))
                if s_tag:
                    selected_v_id = v_opts[s_tag]
            else:
                st.warning("No published versions found for this crew.")

        if st.button("New Session"):
            st.session_state.run_id = str(uuid.uuid4())
            client.create_run(st.session_state.run_id, f"Run {st.session_state.run_id[:8]}", "Manual Test")
            st.success("Started!")

    with l_col2:
        st.subheader("Chat")
        run_data = client.get_run(st.session_state.run_id)
        current_events = run_data.get("events", []) if run_data else []
        
        for event in current_events:
            role = event.get("role")
            content = event.get("content")
            
            if event.get("payload_json"):
                payload = event["payload_json"]
                role = payload.get("role", "assistant")
                content = payload.get("content", "")
                
                if event.get("event_type") == "run_start":
                    st.caption(f"🚀 Run Started: {payload.get('input')}")
                    continue
                if event.get("event_type") == "run_success":
                    continue

            if role and content:
                # Extrair nome do agente se disponível
                agent_name = payload.get("agent_name", None)
                
                # Determinar o nome a exibir
                if role == "user":
                    display_name = "👤 Usuário"
                else:
                    # Se tem agent_name, exibir; senão, apenas "Agente"
                    display_name = f"🤖 {agent_name}" if agent_name else "🤖 Agente"
                
                with st.chat_message(role):
                    st.caption(display_name)
                    st.write(content)
        
        if prompt := st.chat_input("Say something..."):
            if not selected_v_id:
                st.error("Please select a Crew Version to run.")
            else:
                with st.chat_message("user"):
                    st.write(prompt)
                
                client.create_run(st.session_state.run_id, "Auto Run", "Manual")
                client.send_message(st.session_state.run_id, prompt, "user", crew_version_id=selected_v_id)
                st.rerun()
