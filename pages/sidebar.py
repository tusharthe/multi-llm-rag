import streamlit as st


def render_sidebar(active_page="Current chat"):
    # Custom CSS rules for sidebar & upload box
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] { display: none !important; }
            [data-testid="stSidebarHeader"] { padding-top: 0rem !important; padding-bottom: 0rem !important; }
            [data-testid="stSidebarUserContent"] { padding-top: 1rem !important; }
            header[data-testid="stHeader"] { background-color: transparent; }

            .menu-label {
                font-size: 11px;
                font-weight: 700;
                color: #8E8E93;
                letter-spacing: 0.8px;
                text-transform: uppercase;
                margin-top: 20px;
                margin-bottom: 10px;
                padding-left: 4px;
            }

            [data-testid="stSidebar"] button[kind="tertiary"] {
                justify-content: flex-start !important;
                text-align: left !important;
                padding-left: 14px !important;
                font-weight: 500 !important;
                color: #2D3748 !important;
                border-radius: 8px !important;
            }

            .nav-item-active {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background-color: #EAEAEA;
                border-left: 3.5px solid #E53E3E;
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
                padding: 10px 14px;
                color: #E53E3E;
                font-weight: 600;
                font-size: 14px;
                margin-bottom: 6px;
            }

            .nav-item-left { display: flex; align-items: center; gap: 10px; }
            .nav-badge { background-color: #FFFFFF; color: #1E1E1E; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 12px; }

            /* Knowledge Source Area */
            .sidebar-divider { border-top: 1px solid #E2E8F0; margin: 20px 0 14px 0; }
            .status-indicator { font-size: 11px; font-weight: 600; color: #16A34A; display: flex; align-items: center; gap: 6px; }
            .status-dot { width: 7px; height: 7px; background-color: #16A34A; border-radius: 50%; display: inline-block; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" />', unsafe_allow_html=True)

    # 1. Brand Header
    st.sidebar.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
            <div style="background-color: #B22222; color: white; width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 24px;">
                <span class="material-symbols-outlined">hub</span>
            </div>
            <div>
                <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: #1E1E1E;">RAG Hub Pro</h3>
                <p style="margin: 0; font-size: 12px; color: #6E6E6E;">Multi-Document Gen</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 2. New Chat Button
    if st.sidebar.button("New Chat", icon=":material/add:", type="primary", use_container_width=True):
        st.session_state["messages"] = []  # Reset active chat state
        st.switch_page("pages/current_chat.py")

    # 3. MENU Links
    st.sidebar.markdown('<div class="menu-label">MENU</div>',
                        unsafe_allow_html=True)

    # Navigation items
    navs = [
        ("Current chat", "chat_bubble_outline", "pages/current_chat.py"),
        ("History", "history", "pages/history.py"),
        ("Analytics", "bar_chart", "pages/analytics.py"),
        ("Arena", "swords", "pages/arena.py"),
        ("Model Settings", "tune", "pages/settings.py")
    ]

    for label, icon, path in navs:
        if active_page == label:
            st.sidebar.markdown(
                f"""
                <div class="nav-item-active">
                    <div class="nav-item-left">
                        <span class="material-symbols-outlined">{icon}</span>
                        <span>{label}</span>
                    </div>
                    {'<span class="nav-badge">12</span>' if label == "History" else ''}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            if st.sidebar.button(label, icon=f":material/{icon}:", type="tertiary", use_container_width=True):
                st.switch_page(path)

    # 4. KNOWLEDGE SOURCE (Sidebar File Upload & RAG Sliders)
    st.sidebar.markdown(
        '<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="menu-label">KNOWLEDGE SOURCE</div>', unsafe_allow_html=True)

    # Drag & drop upload box
    sidebar_files = st.sidebar.file_uploader(
        "Drag & drop PDF here",
        type=["pdf", "docx", "csv"],
        accept_multiple_files=True,
        key="sidebar_uploader",
        help="LIMIT 200MB - PDF, DOCX, CSV"
    )

    # RAG Hyperparameters
    st.sidebar.slider("Temperature", min_value=0.0,
                      max_value=1.0, value=0.7, step=0.1)
    st.sidebar.slider("Chunk Size", min_value=128,
                      max_value=2048, value=512, step=64)

    # Footer Status
    st.sidebar.markdown(
        """
        <div style="margin-top: 15px;">
            <div class="status-indicator">
                <span class="status-dot"></span> VECTOR INDEX: ACTIVE
            </div>
            <div style="font-size: 11px; color: #94A3B8; margin-top: 2px;">v2.4.0</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    return sidebar_files
