
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


def get_models(
    temperature: float | None = None,
    top_p: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, BaseChatModel]:
    # Read live cfg if caller did not pass an explicit override — so slider
    # changes (cfg.temperature / cfg.top_p / cfg.num_predict) take effect
    # without needing to restart the app.
    if temperature is None:
        temperature = cfg.temperature
    if top_p is None:
        top_p = cfg.top_p
    if max_tokens is None:
        max_tokens = cfg.num_predict
    result: dict[str, BaseChatModel] = {}
    for model_name, model_value in model_list.items():
        needed = model_value[0] if cfg.use_ollama else model_value[3]
        if needed:
            result[model_name] = make_chat(
                model_value[0], model_value[1], model_value[2],
                temperature, top_p, max_tokens)
    return result


def make_chat(
    ollama_name: str,
    prod_class: Type[BaseChatModel],
    prod_model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> BaseChatModel:
    if cfg.use_ollama:
        return ChatOllama(
            model=ollama_name,
            temperature=temperature,
            top_p=top_p,
            num_predict=max_tokens,
            base_url=cfg.ollama_base_url,
        )
    else:
        # ChatGoogleGenerativeAI uses max_output_tokens, the others use max_tokens.
        if prod_class is ChatGoogleGenerativeAI:
            return prod_class(
                model=prod_model,
                temperature=temperature,
                top_p=top_p,
                max_output_tokens=max_tokens,
            )
        return prod_class(
            model=prod_model,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
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
