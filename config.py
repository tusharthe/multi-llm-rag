import os

from dotenv import load_dotenv

load_dotenv()


class RuntimeConfig:
    def __init__(self):

        # --------- OLLAMA base + models ---------
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")

        self.ollama_openai_model = os.getenv("OLLAMA_OPENAI_MODEL")
        self.ollama_anthropic_model = os.getenv("OLLAMA_ANTHROPIC_MODEL")
        self.ollama_gemini_model = os.getenv("OLLAMA_GEMINI_MODEL")
        self.ollama_embed_model = os.getenv("OLLAMA_EMBED_MODEL")

        # --------- Default generation params ---------
        self.default_temperature = float(
            os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        self.default_num_predict = int(os.getenv("DEFAULT_NUM_PREDICT", "256"))

        # --------- Cloud model names ---------
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.openai_embed_model = os.getenv(
            "OPENAI_EMBED_MODEL", "text-embedding-3-small")

        # --------- API keys ---------
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = os.getenv(
            "GOOGLE_API_KEY")  # Gemini uses Google API key

        # ---- USE OLLAMA ----
        # // For local development use ollama models. For production use the remote models
        self.use_ollama = os.getenv(
            "USE_OLLAMA", "false").strip().lower() == "true"

        self.top_k = int(os.getenv("TOP_K", "4"))
        self.top_p = float(os.getenv("TOP_P", "9"))

        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))

        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        # --------- UI‑overrideable params (can be changed by Streamlit) ---------
        # Start them from env defaults, but treat these as "live" knobs:
        self.temperature = self.default_temperature
        self.num_predict = self.default_num_predict


# Single shared instance
config = RuntimeConfig()
