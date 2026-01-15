import streamlit as st
import pandas as pd
from api_client import APIClient

st.title("Knowledge Base (RAG)")
client = APIClient()

tab1, tab2 = st.tabs(["Upload Docs", "Search & Answer"])

with tab1:
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a file", type=["txt", "pdf", "md"])
    
    if uploaded_file is not None:
        if st.button("Upload"):
            with st.spinner("Uploading..."):
                resp = client.upload_document(uploaded_file)
                if resp.status_code == 200:
                    st.success(f"File '{uploaded_file.name}' uploaded successfully!")
                else:
                    st.error(f"Upload failed: {resp.text}")

    st.subheader("Existing Documents")
    if st.button("Refresh List"):
        docs = client.list_documents()
        if docs:
            df = pd.DataFrame(docs)
            st.dataframe(df[["id", "filename", "processed", "created_at"]])
        else:
            st.info("No documents found.")

with tab2:
    st.header("Ask the Knowledge Base")
    query = st.text_input("Enter your question:")
    
    if query:
        with st.chat_message("user"):
            st.markdown(query)
            
        with st.chat_message("assistant"):
            st.markdown(f"**Answer:** Placeholder response for '{query}'.")
