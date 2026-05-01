import streamlit as st
import os
import shutil
import time
from code_chatbot.ingestion.universal_ingestor import process_source
from code_chatbot.ingestion.indexer import Indexer
from code_chatbot.retrieval.rag import ChatEngine
from code_chatbot.analysis.ast_analysis import ASTGraphBuilder
from code_chatbot.retrieval.graph_rag import GraphEnhancedRetriever
import logging
from dotenv import load_dotenv

# Load Env
load_dotenv()

# Basic Setup
st.set_page_config(page_title="CodeCritic AI", page_icon="🧠", layout="wide", initial_sidebar_state="collapsed")
logging.basicConfig(level=logging.INFO)

# --- Custom CSS for Premium Slate UI ---
from components import style
style.apply_custom_css()

# Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = None
if "processed_files" not in st.session_state:
    st.session_state.processed_files = False

# --- Sidebar Configuration ---
from components import sidebar
config = sidebar.render_sidebar()

# Extract config values for easy access in main app
provider = config["provider"]
api_key = config["api_key"]
gemini_model = config["gemini_model"]
use_agent = config["use_agent"]
vector_db_type = config["vector_db_type"]
embedding_provider = config["embedding_provider"]
embedding_api_key = config["embedding_api_key"]

# ============================================================================
# MAIN 3-PANEL LAYOUT
# ============================================================================

st.title("🧠 CodeCritic AI")

if not st.session_state.processed_files:
    # Show onboarding message when no files are processed
    # --- Main Ingestion Section ---
    st.header("🚀 Import Codebase")
    st.caption("Upload your project to get started. Configure advanced settings in the sidebar (open with >).")
    
    if not api_key:
        st.warning(f"⚠️ {provider.capitalize()} API Key is missing. Open the sidebar (top-left) to configure it.")
    
    source_type = st.radio("Source Type", ["ZIP File", "GitHub Repository", "Web Documentation"], horizontal=True)
    
    source_input = None
    if source_type == "ZIP File":
        uploaded_file = st.file_uploader("Upload .zip file", type="zip")
        if uploaded_file:
            import tempfile
            upload_dir = tempfile.gettempdir()
            source_input = os.path.join(upload_dir, "uploaded.zip")
            with open(source_input, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
    elif source_type == "GitHub Repository":
        source_input = st.text_input("GitHub URL", placeholder="https://github.com/owner/repo")
        
    elif source_type == "Web Documentation":
        source_input = st.text_input("Web URL", placeholder="https://docs.python.org/3/")
    
    if source_input and not st.session_state.processed_files:
        if st.button("🚀 Process & Index", type="primary"):
            if not api_key:
                st.error(f"Please configure {provider} API Key in the sidebar.")
            elif provider == "groq" and not embedding_api_key:
                 st.error(f"Please configure {embedding_provider} API Key for embeddings in the sidebar.")
            else:
                # Use the new progress-tracked indexer
                from code_chatbot.ingestion.indexing_progress import index_with_progress
                
                chat_engine, success, repo_files, workspace_root = index_with_progress(
                    source_input=source_input,
                    source_type=source_type,
                    provider=provider,
                    embedding_provider=embedding_provider,
                    embedding_api_key=embedding_api_key,
                    vector_db_type=vector_db_type,
                    use_agent=use_agent,
                    api_key=api_key,
                    gemini_model=gemini_model  # Pass selected model
                )
                
                if success:
                    st.session_state.chat_engine = chat_engine
                    st.session_state.processed_files = True
                    st.session_state.indexed_files = repo_files
                    st.session_state.workspace_root = workspace_root
                    time.sleep(0.5)
                    st.switch_page("pages/1_⚡_Code_Studio.py")
else:
    # Codebase Ready! Redirect to Code Studio
    st.switch_page("pages/1_⚡_Code_Studio.py")
