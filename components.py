"""Small reusable UI fragments shared by the pages.

Each helper returns an HTML string (composable inside a larger block) or draws
straight to the page. Styling comes from ``assets/styles.css`` -- nothing here
carries its own colours beyond the tokens exported by ``theme``.
"""

from __future__ import annotations

import streamlit as st

from theme import MODEL_IDS, avatar, icon


def page_header(title: str, subtitle: str) -> None:
    """Draw the standard page title + one-line description."""
    st.html(
        f'<div class="page-title">{title}</div>'
        f'<div class="page-subtitle">{subtitle}</div>'
    )


def section_label(text: str) -> None:
    """Draw an uppercase Geist Mono section divider label."""
    st.html(f'<div class="section-label">{text}</div>')


def model_header(label: str, available: bool = True) -> str:
    """Return the avatar + name + model-id block used on model cards."""
    model_id = MODEL_IDS.get(label, "--")
    status = (
        '<span class="pill pill-success"><span class="status-dot"></span>Ready</span>'
        if available
        else '<span class="pill pill-muted"><span class="status-dot off"></span>Offline</span>'
    )
    return f"""
    <div class="arena-head">
        <div style="display:flex; align-items:center; gap:10px;">
            {avatar(label)}
            <div>
                <p class="model-name">{label}</p>
                <p class="model-id">{model_id}</p>
            </div>
        </div>
        {status}
    </div>
    """


def metric_card(label: str, value: str, foot: str = "", trend_up: bool = False) -> str:
    """Return a dashboard metric tile (16px radius, Level-1 elevation)."""
    foot_class = "metric-foot up" if trend_up else "metric-foot"
    foot_html = f'<div class="{foot_class}">{foot}</div>' if foot else ""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {foot_html}
    </div>
    """


def stat_box(label: str, value: str) -> str:
    """Return one cell of the compact 2x2 session-statistics grid."""
    return f"""
    <div class="stat-box">
        <div class="stat-val">{value}</div>
        <div class="stat-lbl">{label}</div>
    </div>
    """


def empty_state(material_icon: str, title: str, body: str) -> None:
    """Draw a dashed-outline placeholder for a page with no data yet."""
    st.html(
        f"""
        <div class="empty-state">
            {icon(material_icon, 34)}
            <div class="empty-title">{title}</div>
            <div style="font-size:13px;">{body}</div>
        </div>
        """
    )
