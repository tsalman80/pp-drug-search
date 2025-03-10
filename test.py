import streamlit as st
from streamlit_chromadb_connection.chromadb_connection import ChromadbConnection

configuration = {
    "client": "PersistentClient",
    "path": "./data/chroma_db",    
}

collection_name = "icd10_descriptions"

conn = st.connection("chromadb", type=ChromadbConnection, **configuration)
documents_collection_df = conn.get_collection_data(collection_name, ["documents"])
st.dataframe(documents_collection_df)
