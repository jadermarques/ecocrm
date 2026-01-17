import streamlit as st
import pandas as pd
from api_client import APIClient

# Initialize session state
if "selected_kb" not in st.session_state:
    st.session_state.selected_kb = None
if "confirm_delete" not in st.session_state:
    st.session_state.confirm_delete = None

st.title("Knowledge Base (RAG)")
client = APIClient()

tab1, tab2 = st.tabs(["Upload Docs", "Search & Answer"])

with tab1:
    st.subheader("1. Select Knowledge Base")
    kbs = client.list_kbs()
    
    selected_kb_id = None
    if kbs:
        st.write(f"**{len(kbs)} Knowledge Base(s) found**")
        
        for kb in kbs:
            col1, col2, col3 = st.columns([4, 1, 1])
            
            with col1:
                if st.button(f"📚 {kb['name']} (ID: {kb['id']})", key="select_{}".format(kb['id']), use_container_width=True):
                    st.session_state.selected_kb = kb['id']
            
            with col2:
                if st.button("✏️ Edit", key="edit_{}".format(kb['id'])):
                    st.session_state["editing_kb"] = kb['id']
            
            with col3:
                # Delete button with confirmation
                if st.button("🗑️", key="delete_{}".format(kb['id']), help="Delete KB"):
                    st.session_state.confirm_delete = kb['id']
                
                # Show confirmation dialog
                if st.session_state.confirm_delete == kb['id']:
                    st.warning(f"⚠️ Delete '{kb['name']}'? This cannot be undone!")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, Delete", key="confirm_yes_{}".format(kb['id']), type="secondary"):
                            if client.delete_kb(kb['id']):
                                st.success("✅ KB deleted!")
                                st.session_state.confirm_delete = None
                                st.rerun()
                            else:
                                st.error("❌ Delete failed")
                    with col_no:
                        if st.button("Cancel", key="confirm_no_{}".format(kb['id'])):
                            st.session_state.confirm_delete = None
                            st.rerun()
            
            # Show edit form if this KB is being edited
            if st.session_state.get("editing_kb") == kb['id']:
                with st.form("edit_form_{}".format(kb['id'])):
                    st.subheader("Edit: {}".format(kb['name']))
                    edit_name = st.text_input("KB Name", value=kb['name'])
                    edit_desc = st.text_area("Description", value=kb.get('description', ''))
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save", type="primary"):
                            result = client.update_kb(kb['id'], edit_name, edit_desc)
                            if result and not result.get("error"):
                                st.success("✅ KB updated!")
                                del st.session_state["editing_kb"]
                                st.rerun()
                            else:
                                st.error(f"Failed: {result}")
                    with col_cancel:
                        if st.form_submit_button("Cancel"):
                            del st.session_state["editing_kb"]
                            st.rerun()
        
        # Dropdown for selection
        kb_options = {k['name']: k['id'] for k in kbs}
        selected_kb_name = st.selectbox("Or select from dropdown:", list(kb_options.keys()), key="kb_dropdown")
        selected_kb_id = st.session_state.selected_kb if st.session_state.selected_kb else kb_options[selected_kb_name]
    else:
        st.warning("📭 No Knowledge Bases found.")
        
        with st.expander("➕ Create New Knowledge Base", expanded=True):
            new_kb_name = st.text_input("KB Name", placeholder="e.g., Product Documentation")
            new_kb_desc = st.text_area("Description (optional)", placeholder="Describe what this KB contains...")
            
            if st.button("Create KB", type="primary"):
                if new_kb_name:
                    with st.spinner("Creating..."):
                        result = client.create_kb(new_kb_name, new_kb_desc)
                        
                        if isinstance(result, dict):
                            if result.get("error"):
                                st.error(f"❌ {result['error']}")
                            elif result.get("id"):
                                st.success(f"✅ KB '{new_kb_name}' created!")
                                st.rerun()
                            else:
                                st.warning(f"Unexpected response: {result}")
                        else:
                            st.error(f"Invalid response type: {result}")
                else:
                    st.error("Please enter a KB name.")
        
    st.divider()
    st.subheader("2. Upload Document")
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "md"])
    
    # Always show upload button, but validate KB selection
    if uploaded_file is not None:
        if st.button("Upload", type="primary"):
            if not selected_kb_id:
                st.error("❌ Please select or create a Knowledge Base first!")
            else:
                with st.spinner("Uploading..."):
                    resp = client.upload_kb_file(selected_kb_id, uploaded_file)
                    if resp and not resp.get("error"):
                        st.success(f"✅ File '{uploaded_file.name}' uploaded successfully!")
                        st.rerun()
                    else:
                        st.error(f"Upload failed: {resp}")

    st.subheader("Existing Documents")
    if selected_kb_id:
        kb_data = client.get_kb(selected_kb_id)
        if kb_data and kb_data.get("files"):
            df = pd.DataFrame(kb_data["files"])
            st.dataframe(df)
        else:
            st.info("No documents in this KB.")

with tab2:
    st.header("Ask the Knowledge Base")
    
    # We need a selected KB to query
    if not selected_kb_id and kbs:
        st.warning("Please select a KB in the 'Upload Docs' tab first.")
    
    query = st.text_input("Enter your question:")
    
    if query:
        with st.chat_message("user"):
            st.markdown(query)
            
        with st.chat_message("assistant"):
            if selected_kb_id:
                with st.spinner("Searching..."):
                    res = client.query_kb(selected_kb_id, query)
                    answer = res.get("answer", "No answer found.")
                    sources = res.get("sources", [])
                    
                    st.markdown(answer)
                    if sources:
                        st.caption("Sources:")
                        for s in sources:
                            st.caption(f"- {s}")
            else:
                st.error("Select a KB first.")
