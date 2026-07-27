import streamlit as st

from pages.sidebar import render_sidebar

st.set_page_config(page_title="Multi-LLM RAG Chat", layout="wide")

# Render Sidebar and get uploaded files from sidebar
sidebar_uploads = render_sidebar("Current chat")

# Page Custom Styling
st.markdown("""
<style>
    .stApp { background-color: #FAFAFA; }

    /* Top Navigation Header */
    .chat-top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 12px;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .chat-title { font-size: 24px; font-weight: 800; color: #0F172A; margin: 0; }
    .connected-info { font-size: 13px; color: #64748B; margin-top: 2px; }
    .doc-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 12px;
        color: #475569;
    }

    /* Message Bubbles */
    .user-msg-container {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 16px;
        max-width: 85%;
        margin-left: auto;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    .file-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #EEF2FF;
        color: #4F46E5;
        border: 1px solid #C7D2FE;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
        margin-top: 10px;
        text-transform: uppercase;
    }

    .retrieved-accordion {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 13px;
        color: #475569;
        margin-bottom: 12px;
    }

    .assistant-msg-container {
        background-color: #FFFFFF;
        border: 1px solid #FCA5A5;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        position: relative;
    }

    .ai-engine-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #FEF2F2;
        color: #991B1B;
        font-size: 11px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        letter-spacing: 0.5px;
        margin-bottom: 12px;
    }

    .action-row {
        display: flex;
        gap: 16px;
        font-size: 12px;
        color: #64748B;
        margin-top: 14px;
        padding-top: 10px;
        border-top: 1px solid #F1F5F9;
        cursor: pointer;
    }

    /* Right Config Panel */
    .config-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 16px;
    }
    .config-title { font-size: 14px; font-weight: 700; color: #1E293B; margin-bottom: 12px; }
    
    .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 8px; }
    .stat-box {
        background-color: #FAFAFA;
        border: 1px solid #F1F5F9;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .stat-val { font-size: 16px; font-weight: 800; color: #991B1B; }
    .stat-lbl { font-size: 10px; font-weight: 700; color: #94A3B8; text-transform: uppercase; }

    /* Visual Context Card */
    .visual-box {
        background-color: #FAFAFA;
        border: 1px dashed #CBD5E1;
        border-radius: 8px;
        height: 100px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        color: #94A3B8;
        font-size: 11px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {
            "role": "user",
            "content": "What were the top revenue drivers in Q3 according to the report, and how do they compare to Q2? Please list specific segments.",
            "file": "Q4_Earnings_Report.pdf"
        },
        {
            "role": "assistant",
            "content": """Based on the analysis of **Q4_Earnings_Report.pdf**, the primary revenue drivers for the quarter show a significant shift toward enterprise services:
            \n1. **Enterprise Cloud Subscriptions:** Grew by **24% YoY**, generating $4.2M. This surpassed Q2 performance by $1.1M due to late-stage contract closings.
            \n2. **Hardware Services:** Increased a modest 5% quarter-over-quarter.""",
            "sources": "Retrieved 3 context segments from Logistics_Docs"
        }
    ]

# Layout: 2 Columns (Middle Chat Area + Right Config Panel)
col_chat, col_config = st.columns([2.8, 1.2])

# -----------------------------------------------------------------------------
# MIDDLE SECTION: CHAT
# -----------------------------------------------------------------------------
with col_chat:
    # Header Top Bar
    head_col1, head_col2 = st.columns([3, 1.5])
    with head_col1:
        st.markdown("""
            <div>
                <div class="chat-title">Multi-LLM RAG Chat</div>
                <div class="connected-info">Connected to <b>Llama 3 (70B)</b> • Retrieval: <i>Vector Store Alpha</i></div>
            </div>
        """, unsafe_allow_html=True)

    with head_col2:
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("🔄 Clear", use_container_width=True):
                st.session_state["messages"] = []
                st.rerun()
        with btn_c2:
            st.button("📄 Export PDF", type="primary", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Active Files Preview Bar (If files were uploaded in sidebar or inline)
    if sidebar_uploads:
        file_names = ", ".join([f.name for f in sidebar_uploads])
        st.markdown(
            f'<div class="doc-pill">📄 Active Context Files: <b>{file_names}</b></div><br>', unsafe_allow_html=True)

    # Render Messages
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            file_html = f'<br><div class="file-chip">📄 {msg["file"]}</div>' if "file" in msg and msg["file"] else ""
            st.markdown(f"""
                <div class="user-msg-container">
                    <div>{msg['content']}</div>
                    {file_html}
                </div>
            """, unsafe_allow_html=True)

        elif msg["role"] == "assistant":
            if "sources" in msg:
                st.markdown(f"""
                    <div class="retrieved-accordion">
                        🛡️ {msg['sources']}
                    </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="assistant-msg-container">
                    <div class="ai-engine-badge">⚡ AI ANALYSIS ENGINE</div>
                    <div>{msg['content']}</div>
                    <div class="action-row">
                        <span>👍 Helpful</span>
                        <span>📋 Copy</span>
                        <span>🔄 Regenerate</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Bottom Chat Input Area (With Inline File Upload + Input)
    st.markdown("---")

    with st.container():
        # Chat input bar
        user_prompt = st.chat_input("Ask a question about your documents...")

        # In-chat attachment option
        inline_file = st.file_uploader("Attach file directly to prompt", type=[
                                       "pdf", "docx", "txt"], key="inline_upload", label_visibility="collapsed")

        if user_prompt:
            attached_filename = inline_file.name if inline_file else (
                sidebar_uploads[0].name if sidebar_uploads else None)

            # Append User Message
            st.session_state["messages"].append({
                "role": "user",
                "content": user_prompt,
                "file": attached_filename
            })

            # Mock Assistant Reply
            st.session_state["messages"].append({
                "role": "assistant",
                "content": f"I analyzed your request: '{user_prompt}'. Synthesizing insights from indexed vector database...",
                "sources": "Retrieved 2 context segments from Active_Docs"
            })
            st.rerun()

# -----------------------------------------------------------------------------
# RIGHT SECTION: MODEL CONFIG & SESSION STATS
# -----------------------------------------------------------------------------
with col_config:
    st.markdown('<div class="config-title">⚙️ Model Config</div>',
                unsafe_allow_html=True)

    # Model Selection Card
    with st.container():
        st.selectbox("Selected Model", [
                     "GPT-4o (OpenAI)", "Claude 3.5 Sonnet", "Llama 3 70B"])
        st.slider("Top-P (Nucleus Sampling)", 0.0, 1.0, 0.9)
        st.slider("Max Tokens", 256, 8192, 4096)

    st.markdown("<br>", unsafe_allow_html=True)

    # Session Statistics Card
    st.markdown('<div class="config-title">SESSION STATISTICS</div>',
                unsafe_allow_html=True)
    st.markdown("""
        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-val">1.2s</div>
                <div class="stat-lbl">Latency</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">450</div>
                <div class="stat-lbl">Total Tokens</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">8</div>
                <div class="stat-lbl">Chunks Read</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">$0.02</div>
                <div class="stat-lbl">Cost Est.</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visual Context Box
    st.markdown('<div class="config-title">Visual Context</div>',
                unsafe_allow_html=True)
    st.markdown("""
        <div class="visual-box">
            <span class="material-symbols-outlined" style="font-size:28px;">bar_chart</span>
            <span>Revenue Chart Detected</span>
        </div>
        <div style="text-align:center; margin-top:8px;">
            <a href="#" style="font-size:11px; color:#E53E3E; font-weight:700; text-decoration:none;">EXPAND INSIGHTS ↗</a>
        </div>
    """, unsafe_allow_html=True)
