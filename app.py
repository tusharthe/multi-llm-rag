import chat_history as chat
import streamlit as st

from pages.sidebar import render_sidebar

st.session_state.setdefault("current_chat_id", None)

st.set_page_config(page_title="RAG Hub Pro", layout="wide")

render_sidebar()
