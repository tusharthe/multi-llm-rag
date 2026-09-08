"""RAG From Scratch (Chat with Your Documents + Citations) -- Streamlit entry point.

Owns the three things that must happen exactly once per script run:

1. ``st.set_page_config`` (must be the first Streamlit call),
2. the global stylesheet and the shared sidebar,
3. the page registry + ``st.navigation`` router.

Individual pages under ``app_pages/`` render only their own content -- they
never set page config or build a sidebar. The directory is deliberately NOT
called ``pages/``: that name triggers Streamlit's legacy auto-discovery, which
would fight the explicit ``st.navigation`` registry below.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="RAG From Scratch (Chat with Your Documents + Citations)",
    page_icon=":material/document_search:",
    layout="wide",
    initial_sidebar_state="expanded",
)

import chat_history as chat  # noqa: E402  (must follow set_page_config)
from sidebar import render_sidebar  # noqa: E402
from theme import inject_css  # noqa: E402

# ---------------------------------------------------------------------------
# Page registry. Keys are stable ids used by the sidebar for st.switch_page;
# `position="hidden"` suppresses Streamlit's own nav so ours is the only one.
# ---------------------------------------------------------------------------

PAGES = {
    "chat": st.Page(
        "app_pages/current_chat.py",
        title="Current chat",
        icon=":material/forum:",
        url_path="chat",
        default=True,
    ),
    "arena": st.Page(
        "app_pages/arena.py",
        title="Arena",
        icon=":material/compare_arrows:",
        url_path="arena",
    ),
    "history": st.Page(
        "app_pages/history.py",
        title="History",
        icon=":material/history:",
        url_path="history",
    ),
    "analytics": st.Page(
        "app_pages/analytics.py",
        title="Analytics",
        icon=":material/bar_chart:",
        url_path="analytics",
    ),
    "settings": st.Page(
        "app_pages/settings.py",
        title="Model settings",
        icon=":material/tune:",
        url_path="settings",
    ),
}


def ensure_active_chat() -> None:
    """Guarantee ``current_chat_id`` points at a chat that actually exists.

    One code path covers three cases:

    * fresh session -> open the most recently updated chat (``list_chats`` is
      already sorted newest-first), so restarting the app resumes where the
      user left off instead of stacking up empty records;
    * stale id (the chat was deleted) -> fall back to the most recent one
      rather than crashing on ``load_chat``;
    * no chats at all -> create the first one.
    """
    chats = chat.list_chats()
    known_ids = {item["chat_id"] for item in chats}

    if st.session_state.get("current_chat_id") in known_ids:
        return

    if chats:
        st.session_state["current_chat_id"] = chats[0]["chat_id"]
    else:
        st.session_state["current_chat_id"] = chat.new_chat()["chat_id"]


def init_session_defaults() -> None:
    """Seed session-level UI state (generation params are widget-backed)."""
    st.session_state.setdefault("upload_file_messages", {})


inject_css()
init_session_defaults()
ensure_active_chat()

# --- Top bar: project title + GitHub + Share (sits above page content) ---
def _render_top_bar() -> None:
    st.html(
        """
        <div class="topbar">
            <div class="topbar-title">
                <span class="topbar-title-main">RAG From Scratch</span>
                <span class="topbar-title-sub">Chat with Your Documents + Citations</span>
            </div>
            <div class="topbar-actions">
                <a class="topbar-btn" href="https://github.com" target="_blank" rel="noopener" title="Open GitHub">
                    <span class="material-symbols-outlined" style="font-size:16px;">code</span>
                    GitHub
                </a>
                <button class="topbar-btn topbar-btn--primary" onclick="navigator.clipboard.writeText(window.location.href).then(()=>{const t=document.getElementById('topbar-share-toast'); if(t){t.style.opacity='1'; setTimeout(()=>t.style.opacity='0', 1800)}}); if(navigator.share){navigator.share({title: document.title, url: window.location.href}).catch(()=>{});}" title="Copy link / Share">
                    <span class="material-symbols-outlined" style="font-size:16px;">share</span>
                    Share
                </button>
                <span id="topbar-share-toast" class="topbar-toast">Link copied</span>
            </div>
        </div>
        """
    )

_render_top_bar()

nav = st.navigation(list(PAGES.values()), position="hidden")

# Titles are unique, so they identify the running page without relying on how
# Streamlit rewrites the default page's url_path.
active_key = next(
    (key for key, page in PAGES.items() if page.title == nav.title),
    "chat",
)

render_sidebar(PAGES, active_key)

nav.run()
