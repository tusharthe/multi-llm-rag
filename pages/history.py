import streamlit as st

from pages.sidebar import render_sidebar

render_sidebar()

# Custom Styling for History Page Components
st.markdown("""
<style>
    /* Background adjustments */
    .stApp {
        background-color: #fafafa;
    }

    /* Top Title Block */
    .page-title {
        font-size: 38px;
        font-weight: 800;
        color: #111111;
        margin-bottom: 2px;
        margin-top: -10px;
    }
    
    .page-subtitle {
        font-size: 15px;
        color: #666666;
        margin-bottom: 28px;
    }

    /* History Cards Base Styling */
    .history-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 18px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .history-card:hover {
        border-color: #cbd5e1;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }

    /* Active Selected Card Outline */
    .history-card.active {
        border: 1.5px solid #e53e3e;
    }

    /* Card Header Layout */
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }

    .title-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .card-title {
        font-size: 19px;
        font-weight: 700;
        color: #111827;
        margin: 0;
    }

    /* Model Pill Badge */
    .model-badge {
        background-color: #f1f5f9;
        color: #64748b;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Actions (Copy / Delete) */
    .card-actions {
        display: flex;
        gap: 12px;
        color: #94a3b8;
        font-size: 18px;
        cursor: pointer;
    }
    
    .card-actions span:hover {
        color: #475569;
    }

    /* Meta Details Row */
    .card-meta {
        display: flex;
        gap: 18px;
        font-size: 13px;
        color: #64748b;
        margin-bottom: 12px;
    }

    .meta-item {
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Message Excerpt Preview */
    .card-excerpt {
        font-size: 14px;
        color: #475569;
        line-height: 1.5;
        margin: 0;
    }

    /* Bottom Floating Bar / Footer */
    .history-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 32px;
        padding-top: 16px;
        border-top: 1px solid #f1f5f9;
        color: #94a3b8;
        font-size: 11px;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

    .draft-summary-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        border: 1px solid #e2e8f0;
        background-color: #ffffff;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        color: #334155;
        cursor: pointer;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Mockup
# -----------------------------------------------------------------------------
history_items = [
    {
        "id": 1,
        "title": "Q4 Financial Reports Analysis",
        "model": "GPT-4O",
        "date": "Oct 26, 11:32 AM",
        "docs": "3 Documents",
        "excerpt": '"Based on the provided Q4 earnings call transcripts, the primary revenue growth was driven by enterprise cloud adoption which saw a 22% increase year-over-year..."',
        "active": True
    },
    {
        "id": 2,
        "title": "Technical Specification Review",
        "model": "CLAUDE 3.5",
        "date": "Oct 25, 04:15 PM",
        "docs": "1 Document",
        "excerpt": '"I reviewed the system architecture document. The primary bottleneck identified in the microservices communication is the latency of the auth middleware..."',
        "active": False
    },
    {
        "id": 3,
        "title": "Customer Survey Insights",
        "model": "GEMINI 1.5",
        "date": "Oct 24, 09:10 AM",
        "docs": "12 CSVs",
        "excerpt": '"Aggregating sentiments from the 2,500 survey responses, common pain points include the onboarding UX and pricing tier transparency for SMEs..."',
        "active": False
    },
    {
        "id": 4,
        "title": "Vendor Risk Assessment",
        "model": "GPT-4O",
        "date": "Oct 22, 01:45 PM",
        "docs": "5 Documents",
        "excerpt": '"The compliance check against SOC2 Type II reports for the new cloud vendor revealed two minor exceptions related to change management logs..."',
        "active": False
    }
]

# -----------------------------------------------------------------------------
# Header Section
# -----------------------------------------------------------------------------
st.markdown('<h1 class="page-title">Chat History</h1>', unsafe_allow_html=True)
st.markdown('<p class="page-subtitle">Manage and revisit your previous multi-document analysis sessions.</p>',
            unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Toolbar Row (Search + Filter + Date)
# -----------------------------------------------------------------------------
col_search, col_filter, col_date = st.columns([6, 1.2, 1.2])

with col_search:
    search_query = st.text_input(
        "Search",
        placeholder="🔍  Search sessions by title, model, or content...",
        label_visibility="collapsed"
    )

with col_filter:
    st.button("⚙️ Filter", use_container_width=True)

with col_date:
    st.button("📅 Date", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Cards Feed
# -----------------------------------------------------------------------------
for item in history_items:
    active_class = " active" if item["active"] else ""

    card_html = f"""
    <div class="history-card{active_class}">
        <div class="card-header">
            <div class="title-group">
                <h3 class="card-title">{item['title']}</h3>
                <span class="model-badge">{item['model']}</span>
            </div>
            <div class="card-actions">
                <span title="Copy">📋</span>
                <span title="Delete">🗑️</span>
            </div>
        </div>
        <div class="card-meta">
            <span class="meta-item">📅 {item['date']}</span>
            <span class="meta-item">📄 {item['docs']}</span>
        </div>
        <p class="card-excerpt">{item['excerpt']}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Bottom Action Pill & Footer
# -----------------------------------------------------------------------------
bot_col1, bot_col2 = st.columns([1, 1])

with bot_col1:
    st.markdown("""
        <div class="draft-summary-btn">
            <span style="color: #e53e3e;">✨</span> Draft summary from history
        </div>
    """, unsafe_allow_html=True)

with bot_col2:
    st.markdown("""
        <div style="text-align: right; color: #94a3b8; font-size: 11px; font-weight: 600; padding-top: 10px;">
            RAG ENGINE V2.1 • POWERED BY STREAMLIT & LANGCHAIN
        </div>
    """, unsafe_allow_html=True)
