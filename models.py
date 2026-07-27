
from typing import Type
from langchain_core.language_models import BaseChatModel
from langchain_ollama import OllamaEmbeddings, ChatOllama

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

import os
from dotenv import load_dotenv


load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_OPENAI_MODEL = os.getenv("OLLAMA_OPENAI_MODEL")
OLLAMA_ANTHROPIC_MODEL = os.getenv("OLLAMA_ANTHROPIC_MODEL")
OLLAMA_GEMINI_MODEL = os.getenv("OLLAMA_GEMINI_MODEL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL")
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
DEFAULT_NUM_PREDICT = int(os.getenv("DEFAULT_NUM_PREDICT", "256"))

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# // For local development use ollama models. For production use the remote models
USE_OLLAMA = os.getenv("USE_OLLAMA", "false").strip().lower() == "true"


model_list = {  # label →(ollama_model_name, prod_class, prod_model_id, api_key_value)
    "OpenAI": (OLLAMA_OPENAI_MODEL, ChatOpenAI, OPENAI_MODEL, OPENAI_API_KEY),
    "Anthropic": (OLLAMA_ANTHROPIC_MODEL, ChatAnthropic, ANTHROPIC_MODEL, ANTHROPIC_API_KEY),
    "Gemini": (OLLAMA_GEMINI_MODEL, ChatGoogleGenerativeAI, GEMINI_MODEL, GEMINI_API_KEY)
}


def get_models(temperature: float = DEFAULT_TEMPERATURE) -> dict[str, BaseChatModel]:
    result = {}
    for model_name, model_value in model_list.items():
        needed = model_value[0] if USE_OLLAMA else model_value[3]
        if needed:
            result[model_name] = make_chat(
                model_value[0], model_value[1], model_value[2], temperature)
    return result


def make_chat(ollama_name: str, prod_class: Type[BaseChatModel], prod_model: str, temperature: float) -> BaseChatModel:
    if USE_OLLAMA:
        return ChatOllama(
            model=ollama_name,
            temperature=temperature,
            num_predict=DEFAULT_NUM_PREDICT,
            base_url=OLLAMA_BASE_URL,
        )
    else:
        return prod_class(
            model=prod_model,
            temperature=temperature,
            max_tokens=DEFAULT_NUM_PREDICT,
        )


def get_embeddings():
    if USE_OLLAMA:
        return OllamaEmbeddings(model=OLLAMA_EMBED_MODEL)
    else:
        return OpenAIEmbeddings(model=OPENAI_EMBED_MODEL)


if __name__ == "__main__":
    print("Running models.py directly!")
    print(get_models()['OpenAI'].invoke("say hi in 3 words"))
    print(len(get_embeddings().embed_query("hello")))
