import streamlit as st
from sidebar import render_sidebar

# 1. Page Configuration
st.set_page_config(page_title="Multi-LLM Arena", layout="wide")

# 2. Render Shared Sidebar with "Arena" Active
render_sidebar("Arena")

# 3. Custom CSS for Arena Layout
st.markdown("""
<style>
    /* Main Canvas Background */
    .stApp {
        background-color: #fafafa;
    }

    /* Page Header Styles */
    .arena-title {
        font-size: 28px;
        font-weight: 800;
        color: #111827;
        margin: 0;
    }
    
    .arena-subtitle {
        font-size: 11px;
        font-weight: 700;
        color: #6B7280;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-top: 2px;
    }

    /* Current Prompt Container */
    .prompt-box {
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 18px 24px;
        margin-top: 20px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    }

    .prompt-tag {
        font-size: 10px;
        font-weight: 800;
        color: #6B7280;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .prompt-text {
        font-size: 15px;
        font-weight: 700;
        color: #111827;
        line-height: 1.4;
        margin: 0;
    }

    .metric-badge {
        background-color: #F9FAFB;
        border: 1px solid #F3F4F6;
        border-radius: 8px;
        padding: 8px 12px;
        text-align: right;
    }

    .metric-lbl {
        font-size: 10px;
        font-weight: 700;
        color: #9CA3AF;
        text-transform: uppercase;
    }

    .metric-val {
        font-size: 14px;
        font-weight: 800;
        color: #B91C1C;
    }

    /* Comparison Cards */
    .arena-card {
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 14px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        height: 100%;
        min-height: 480px;
        position: relative;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }

    .arena-card.winner-card {
        border: 1.5px solid #DC2626;
    }

    .card-top {
        padding: 18px 20px 12px 20px;
    }

    /* Model Header Info */
    .model-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 14px;
        border-bottom: 1px solid #F3F4F6;
        margin-bottom: 14px;
    }

    .model-info-left {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .model-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #1F2937;
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 800;
    }

    .model-name {
        font-size: 14px;
        font-weight: 800;
        color: #111827;
        margin: 0;
    }

    .model-provider {
        font-size: 10px;
        font-weight: 700;
        color: #9CA3AF;
        text-transform: uppercase;
        margin: 0;
    }

    /* Winner Pill Badge */
    .winner-pill {
        background-color: #DCFCE7;
        color: #15803D;
        font-size: 10px;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        letter-spacing: 0.5px;
    }

    /* Card Content Formatting */
    .card-body-text {
        font-size: 13px;
        color: #374151;
        line-height: 1.6;
    }

    .card-body-text ul {
        padding-left: 16px;
        margin-top: 8px;
        margin-bottom: 12px;
    }

    .card-body-text li {
        margin-bottom: 6px;
    }

    .insight-italic {
        font-style: italic;
        color: #6B7280;
        margin-top: 12px;
        font-size: 12px;
    }

    /* Card Footer Stats */
    .card-footer-stats {
        border-top: 1px solid #F3F4F6;
        padding: 12px 20px;
        display: flex;
        gap: 24px;
        background-color: #FAFAFA;
        border-bottom-left-radius: 14px;
        border-bottom-right-radius: 14px;
    }

    .card-stat-box {
        display: flex;
        flex-direction: column;
    }

    .card-stat-lbl {
        font-size: 10px;
        color: #9CA3AF;
        font-weight: 600;
    }

    .card-stat-val {
        font-size: 12px;
        font-weight: 800;
        color: #111827;
    }

    /* Floating Right Floating Utility Toolbar */
    .floating-toolbar {
        position: fixed;
        right: 24px;
        bottom: 24px;
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 6px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        z-index: 99;
    }

    .toolbar-btn {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #4B5563;
        cursor: pointer;
        transition: background-color 0.15s ease;
    }

    .toolbar-btn:hover {
        background-color: #F3F4F6;
        color: #111827;
    }

    .toolbar-btn.active-tool {
        background-color: #FEF2F2;
        color: #DC2626;
    }

    /* Bottom Prompt Action Bar */
    .bottom-prompt-bar {
        background-color: #ffffff;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 8px 12px 8px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 28px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
</style>
""", unsafe_allow_html=True)

# 4. Header Actions Row
head_left, head_right = st.columns([3, 1.2])

with head_left:
    st.markdown('<h1 class="arena-title">Multi-LLM Arena</h1>',
                unsafe_allow_html=True)
    st.markdown('<div class="arena-subtitle">BENCHMARKING RAG PERFORMANCE</div>',
                unsafe_allow_html=True)

with head_right:
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Reset Chat", use_container_width=True):
            st.rerun()
    with btn_col2:
        st.button("Export PDF", type="primary", use_container_width=True)

# 5. Current Active Prompt Display Banner
st.markdown("""
<div class="prompt-box">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex-grow: 1; padding-right: 20px;">
            <div class="prompt-tag">CURRENT PROMPT</div>
            <p class="prompt-text">"Analyze the Q3 revenue growth drivers for enterprise cloud and compare them against hardware services based on the provided earnings transcript."</p>
        </div>
        <div style="display: flex; gap: 12px;">
            <div class="metric-badge">
                <div class="metric-lbl">Avg. Latency</div>
                <div class="metric-val">1.42s</div>
            </div>
            <div class="metric-badge">
                <div class="metric-lbl">Documents</div>
                <div class="metric-val" style="color: #111827;">2 Files</div>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 6. Side-by-Side Model Cards (3 Columns)
col_gpt, col_claude, col_gemini = st.columns(3)

# --- GPT-4o Card (Winner) ---
with col_gpt:
    st.markdown("""
    <div class="arena-card winner-card">
        <div class="card-top">
            <div class="model-header">
                <div class="model-info-left">
                    <div class="model-avatar" style="background-color: #111827;">O</div>
                    <div>
                        <h4 class="model-name">GPT-4o</h4>
                        <p class="model-provider">OPENAI</p>
                    </div>
                </div>
                <span class="winner-pill">✔ WINNER</span>
            </div>
            <div class="card-body-text">
                <p>Based on the Q3 earnings reports, the primary revenue drivers were:</p>
                <ul>
                    <li><b>Enterprise Cloud:</b> Grew 24% YoY, reaching $4.2B, driven by high demand for AI-integrated SaaS solutions.</li>
                    <li><b>Hardware Services:</b> Showed modest 5% QoQ growth, impacted by global supply chain stabilization.</li>
                </ul>
                <p class="insight-italic">OpenAI provides a balanced technical summary with direct numerical comparisons.</p>
            </div>
        </div>
        <div class="card-footer-stats">
            <div class="card-stat-box">
                <span class="card-stat-lbl">Latency</span>
                <span class="card-stat-val">1.2s</span>
            </div>
            <div class="card-stat-box">
                <span class="card-stat-lbl">Tokens</span>
                <span class="card-stat-val">342</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Claude 3.5 Sonnet Card ---
with col_claude:
    st.markdown("""
    <div class="arena-card">
        <div class="card-top">
            <div class="model-header">
                <div class="model-info-left">
                    <div class="model-avatar" style="background-color: #0F766E;">C</div>
                    <div>
                        <h4 class="model-name">Claude 3.5 Sonnet</h4>
                        <p class="model-provider">ANTHROPIC</p>
                    </div>
                </div>
            </div>
            <div class="card-body-text">
                <p>Revenue analysis for Q3 reveals a significant divergence between segments:</p>
                <p><b>Cloud Dominance:</b> The 24% YoY increase in Cloud subscriptions is the strongest vertical growth seen this fiscal year, vastly outperforming the flat-to-modest growth in traditional hardware services (5% increase).</p>
                <p><b>Contextual Insight:</b> Hardware performance reflects a shift in capital expenditure toward virtualized infrastructure.</p>
            </div>
        </div>
        <div class="card-footer-stats">
            <div class="card-stat-box">
                <span class="card-stat-lbl">Latency</span>
                <span class="card-stat-val">1.8s</span>
            </div>
            <div class="card-stat-box">
                <span class="card-stat-lbl">Tokens</span>
                <span class="card-stat-val">298</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Gemini 1.5 Pro Card ---
with col_gemini:
    st.markdown("""
    <div class="arena-card">
        <div class="card-top">
            <div class="model-header">
                <div class="model-info-left">
                    <div class="model-avatar" style="background-color: #4338CA;">G</div>
                    <div>
                        <h4 class="model-name">Gemini 1.5 Pro</h4>
                        <p class="model-provider">GOOGLE</p>
                    </div>
                </div>
            </div>
            <div class="card-body-text">
                <p>In Q3, Enterprise Cloud ($4.2B) outperformed hardware services ($1.1B). Cloud growth was cited at 24% while hardware lagged at 5% quarter-over-quarter growth.</p>
                <p>The report mentions a strategic pivot where Cloud now accounts for 68% of total gross margin, compared to just 12% for hardware service support contracts.</p>
            </div>
        </div>
        <div class="card-footer-stats">
            <div class="card-stat-box">
                <span class="card-stat-lbl">Latency</span>
                <span class="card-stat-val">1.3s</span>
            </div>
            <div class="card-stat-box">
                <span class="card-stat-lbl">Tokens</span>
                <span class="card-stat-val">412</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 7. Bottom Re-Compare Input Trigger Bar
st.markdown("""
<div class="bottom-prompt-bar">
    <div style="display: flex; align-items: center; gap: 12px; flex-grow: 1;">
        <span class="material-symbols-outlined" style="color: #9CA3AF; font-size: 20px;">attach_file</span>
        <span style="font-size: 13px; color: #4B5563;">What were the top revenue drivers in Q3 according to the report, and how do they cor...</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Action button row below bar to trigger rerun
prompt_col, btn_col = st.columns([4, 1])
with btn_col:
    st.button("Compare Again ⚡", type="primary", use_container_width=True)

# 8. Floating Utility Toolbar (Bottom Right)
st.markdown("""
<div class="floating-toolbar">
    <div class="toolbar-btn" title="Settings"><span class="material-symbols-outlined">tune</span></div>
    <div class="toolbar-btn active-tool" title="Compare"><span class="material-symbols-outlined">auto_awesome</span></div>
    <div class="toolbar-btn" title="Expand"><span class="material-symbols-outlined">open_in_full</span></div>
</div>
""", unsafe_allow_html=True)
