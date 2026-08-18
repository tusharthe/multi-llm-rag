
from typing import Type
from langchain_core.language_models import BaseChatModel
from langchain_ollama import OllamaEmbeddings, ChatOllama

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import config as cfg


model_list = {  # label →(ollama_model_name, prod_class, prod_model_id, api_key_value)
    "OpenAI": (cfg.ollama_openai_model, ChatOpenAI, cfg.openai_model, cfg.openai_api_key),
    "Anthropic": (cfg.ollama_anthropic_model, ChatAnthropic, cfg.anthropic_model, cfg.anthropic_api_key),
    "Gemini": (cfg.ollama_gemini_model, ChatGoogleGenerativeAI, cfg.gemini_model, cfg.gemini_api_key)
}


def get_models(temperature: float = cfg.temperature) -> dict[str, BaseChatModel]:
    result = {}
    for model_name, model_value in model_list.items():
        needed = model_value[0] if cfg.use_ollama else model_value[3]
        if needed:
            result[model_name] = make_chat(
                model_value[0], model_value[1], model_value[2], temperature)
    return result


def make_chat(ollama_name: str, prod_class: Type[BaseChatModel], prod_model: str, temperature: float) -> BaseChatModel:
    if cfg.use_ollama:
        return ChatOllama(
            model=ollama_name,
            temperature=temperature,
            num_predict=cfg.default_num_predict,
            base_url=cfg.ollama_base_url,
        )
    else:
        return prod_class(
            model=prod_model,
            temperature=temperature,
            max_tokens=cfg.default_num_predict,
        )


def get_embeddings():
    if cfg.use_ollama:
        return OllamaEmbeddings(model=cfg.ollama_embed_model)
    else:
        return OpenAIEmbeddings(model=cfg.openai_embed_model)


if __name__ == "__main__":
    print("Running models.py directly!")
    print(get_models()['OpenAI'].invoke("say hi in 3 words"))
    print(len(get_embeddings().embed_query("hello")))
