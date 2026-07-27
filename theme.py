"""Design tokens and stylesheet loader for the RAG Hub UI.

The actual CSS lives in ``assets/styles.css`` -- this module only holds the
handful of token values Python needs (e.g. a per-model avatar tint built into
an inline style) and the loader that injects the stylesheet.

Only ``app.py`` should call :func:`inject_css`. It runs once per script run,
before the active page renders, so every page inherits the same styling.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

STYLESHEET = Path(__file__).parent / "assets" / "styles.css"

# ---------------------------------------------------------------------------
# Design tokens -- mirror of the :root block in assets/styles.css, exposed for
# the cases where a value has to be interpolated into Python-built markup.
# ---------------------------------------------------------------------------

PRIMARY = "#b7131a"
PRIMARY_FIXED = "#ffdad6"
ON_PRIMARY_FIXED_VARIANT = "#93000d"

SURFACE_LOWEST = "#ffffff"
SURFACE_LOW = "#f6f3f2"
SURFACE_HIGH = "#eae7e7"

ON_SURFACE = "#1b1c1c"
ON_SURFACE_VARIANT = "#5b403d"
OUTLINE_VARIANT = "#e4beb9"

TERTIARY = "#006578"
SUCCESS = "#15803d"
WARNING = "#b45309"
MUTED = "#8a8686"

#: Per-model accent used for the avatar chip in Arena / Continue mode.
#: The three labels are fixed by the brief -- OpenAI / Anthropic / Gemini --
#: regardless of whether the backend is a cloud provider or an Ollama stand-in.
MODEL_ACCENTS = {
    "OpenAI": "#10a37f",
    "Anthropic": "#d97757",
    "Gemini": "#4285f4",
}

#: Model id shown under each label in the UI (display only).
MODEL_IDS = {
    "OpenAI": "gpt-4o-mini",
    "Anthropic": "claude-haiku-4-5",
    "Gemini": "gemini-2.5-flash",
}


def inject_css() -> None:
    """Inject ``assets/styles.css`` into the page. Call once, from ``app.py``.

    Uses ``st.markdown(unsafe_allow_html=True)`` rather than ``st.html``:
    ``st.html`` sanitises ``<style>`` elements out of its payload, so the
    stylesheet never reaches the DOM. ``st.html`` is still the right call for
    ordinary markup, which is what the helpers below return.
    """
    css = STYLESHEET.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def icon(name: str, size: int = 18, color: str | None = None) -> str:
    """Return an inline Material Symbols ``<span>`` for use inside HTML blocks.

    Streamlit's own widgets take ``:material/name:`` strings instead -- this
    helper is only for markup the app builds itself.
    """
    style = f"font-size:{size}px;"
    if color:
        style += f"color:{color};"
    return f'<span class="material-symbols-outlined" style="{style}">{name}</span>'


def avatar(label: str) -> str:
    """Return the circular model-initial avatar markup for ``label``."""
    accent = MODEL_ACCENTS.get(label, MUTED)
    return f'<div class="model-avatar" style="background:{accent};">{label[0]}</div>'
