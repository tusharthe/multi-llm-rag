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
TOKENS_LIGHT = Path(__file__).parent / "assets" / "tokens-light.css"
TOKENS_DARK = Path(__file__).parent / "assets" / "tokens-dark.css"

# ---------------------------------------------------------------------------
# Design tokens -- mirror of the dark :root block in assets/tokens-dark.css,
# exposed for the cases where a value has to be interpolated into
# Python-built markup. (Light values live in assets/tokens-light.css and are
# only injected as CSS, never read here.)
# ---------------------------------------------------------------------------

PRIMARY = "#d92d34"
PRIMARY_FIXED = "#ffdad6"
ON_PRIMARY_FIXED_VARIANT = "#93000d"

SURFACE_LOWEST = "#2e2a2c"
SURFACE_LOW = "#232023"
SURFACE_HIGH = "#3d383b"

ON_SURFACE = "#ece7e4"
ON_SURFACE_VARIANT = "#c9b8b4"
OUTLINE_VARIANT = "#5a4440"

TERTIARY = "#6fc3d8"
SUCCESS = "#4caf7d"
WARNING = "#e09a4a"
MUTED = "#a8a29e"

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


def effective_theme() -> str:
    """Return the active Streamlit theme: ``"light"`` or ``"dark"``.

    This is the *effective* theme -- ``config.toml`` base plus the user's
    override from the ⋮ menu → Settings → Appearance. Reading it (instead of
    hardcoding tokens) is what lets the app's custom CSS follow Light/Dark
    switches with zero mismatch against native widgets.
    """
    try:
        theme_type = st.context.theme.get("type")
    except Exception:
        theme_type = None
    return theme_type if theme_type in ("light", "dark") else "dark"


def inject_css() -> None:
    """Inject tokens + ``assets/styles.css`` into the page. Call once, from ``app.py``.

    The token file matches :func:`effective_theme`, so custom cards follow
    the same Light/Dark switch as native Streamlit widgets. Runs every script
    run, and Streamlit reruns on theme change, so flipping the theme in
    Settings re-themes the whole app.

    Uses ``st.markdown(unsafe_allow_html=True)`` rather than ``st.html``:
    ``st.html`` sanitises ``<style>`` elements out of its payload, so the
    stylesheet never reaches the DOM. ``st.html`` is still the right call for
    ordinary markup, which is what the helpers below return.
    """
    tokens_path = TOKENS_LIGHT if effective_theme() == "light" else TOKENS_DARK
    tokens = tokens_path.read_text(encoding="utf-8")
    css = STYLESHEET.read_text(encoding="utf-8")
    st.markdown(f"<style>{tokens}\n{css}</style>", unsafe_allow_html=True)


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
