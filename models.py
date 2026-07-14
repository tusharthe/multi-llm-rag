"""Model registry: builds the chat models and embedding model the app uses.

Every chat model here -- OpenAI, Anthropic, Gemini, or their local Ollama
stand-ins -- implements the SAME LangChain interface: `.invoke(...)` returns
an `AIMessage` with a `.content` string. That is what lets the rest of the
app (the LangGraph graph, the Streamlit UI) treat "OpenAI" and "a local
llama3.2 model" identically -- it never sees which concrete class it holds.

The registry is dynamic and built fresh each call:
- In dev mode (USE_OLLAMA=true), all three provider slots are local Ollama
  models, only if the Ollama server responds.
- In production mode (USE_OLLAMA=false), a provider slot is included only if
  its API key is set in the environment.
Either way the app must keep working with any non-empty subset of providers.
"""

import os
import urllib.request
from typing import Dict, Optional

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

# The three provider labels the UI always shows, regardless of backend.
PROVIDER_NAMES = ["OpenAI", "Anthropic", "Gemini"]

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def _use_ollama() -> bool:
    """Whether to route every provider slot through local Ollama models."""
    return os.getenv("USE_OLLAMA", "false").strip().lower() == "true"


def _ollama_base_url() -> str:
    """The Ollama server URL, from OLLAMA_BASE_URL or the local default."""
    return os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)


def _ollama_reachable(base_url: str) -> bool:
    """Check that an Ollama server actually responds at base_url.

    Uses a short timeout and the standard library only (no extra dependency)
    because this is just a liveness probe, not a real API call.
    """
    try:
        urllib.request.urlopen(f"{base_url}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _ollama_chat_models(base_url: str) -> Dict[str, BaseChatModel]:
    """Build the three provider slots as local Ollama models.

    Each slot's model tag is env-overridable so any locally pulled model can
    stand in for a provider (see .env.example for the defaults).
    """
    from langchain_ollama import ChatOllama

    slot_to_model = {
        "OpenAI": os.getenv("OLLAMA_OPENAI_MODEL", "llama3.2:3b"),
        "Anthropic": os.getenv("OLLAMA_ANTHROPIC_MODEL", "qwen2.5:3b"),
        "Gemini": os.getenv("OLLAMA_GEMINI_MODEL", "gemma3:4b"),
    }
    return {
        name: ChatOllama(model=model_tag, base_url=base_url, temperature=0)
        for name, model_tag in slot_to_model.items()
    }


def _cloud_chat_models() -> Dict[str, BaseChatModel]:
    """Build whichever real provider clients have an API key set.

    A provider whose key is missing is simply left out of the dict -- the
    caller never sees a None or a broken client, only the providers that are
    actually configured.
    """
    models: Dict[str, BaseChatModel] = {}

    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        models["OpenAI"] = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    if os.getenv("ANTHROPIC_API_KEY"):
        from langchain_anthropic import ChatAnthropic

        models["Anthropic"] = ChatAnthropic(model="claude-haiku-4-5", temperature=0)

    if os.getenv("GOOGLE_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        models["Gemini"] = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

    return models


def get_chat_models() -> Dict[str, BaseChatModel]:
    """Return {provider_name: chat_model} for every provider usable right now.

    Returns:
        A dict with 0-3 entries keyed by "OpenAI", "Anthropic", "Gemini". An
        empty dict means no model is currently usable (Ollama unreachable in
        dev mode, or no cloud keys set in production mode) -- callers must
        handle that case in the UI rather than assuming at least one exists.
    """
    if _use_ollama():
        base_url = _ollama_base_url()
        if not _ollama_reachable(base_url):
            return {}
        return _ollama_chat_models(base_url)
    return _cloud_chat_models()


def get_embeddings() -> Optional[Embeddings]:
    """Return the embedding model used to build/query the Chroma index.

    Uses the SAME USE_OLLAMA switch as the chat models, because the two must
    always match: querying an OpenAI-embedded index with Ollama embeddings
    (or vice versa) silently produces meaningless similarity scores, since
    each model's vector space is different.

    Returns:
        An Embeddings instance, or None if the configured backend is not
        currently usable (Ollama unreachable, or OpenAI key missing).
    """
    if _use_ollama():
        base_url = _ollama_base_url()
        if not _ollama_reachable(base_url):
            return None
        from langchain_ollama import OllamaEmbeddings

        model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        return OllamaEmbeddings(model=model, base_url=base_url)

    if not os.getenv("OPENAI_API_KEY"):
        return None
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model="text-embedding-3-small")
