"""
LangChain Integration for OpenRouter API.

This module provides LangChain-compatible wrappers for using OpenRouter
with LangChain and LangGraph workflows.

OpenRouter uses an OpenAI-compatible API, so we can use langchain-openai
with a custom base URL.
"""
from typing import Optional, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage

from ..core.config import settings


def get_openrouter_chat_model(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Optional[ChatOpenAI]:
    """
    Get a LangChain ChatOpenAI model configured for OpenRouter.

    OpenRouter uses an OpenAI-compatible API, so we can use the ChatOpenAI
    class with a custom base URL and API key.

    Args:
        model: Model to use (e.g., "anthropic/claude-3-sonnet", "openai/gpt-4")
               Defaults to settings.OPENROUTER_MODEL
        temperature: Sampling temperature. Defaults to settings.LLM_TEMPERATURE
        max_tokens: Maximum tokens in response. Defaults to settings.LLM_MAX_TOKENS
        **kwargs: Additional arguments passed to ChatOpenAI

    Returns:
        ChatOpenAI instance configured for OpenRouter, or None if not configured

    Usage:
        # Basic usage
        chat = get_openrouter_chat_model()
        if chat:
            response = await chat.ainvoke([HumanMessage(content="Hello!")])

        # With custom model
        chat = get_openrouter_chat_model(model="openai/gpt-4-turbo")

        # In a LangChain chain
        from langchain_core.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("user", "{input}")
        ])
        chain = prompt | chat
        response = await chain.ainvoke({"input": "Hello!"})
    """
    if not settings.OPENROUTER_API_KEY:
        return None

    # Build default headers for OpenRouter
    default_headers = {}
    if settings.OPENROUTER_SITE_URL:
        default_headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
    if settings.OPENROUTER_SITE_NAME:
        default_headers["X-Title"] = settings.OPENROUTER_SITE_NAME

    return ChatOpenAI(
        model=model or settings.OPENROUTER_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=settings.OPENROUTER_BASE_URL,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        default_headers=default_headers if default_headers else None,
        **kwargs
    )


def is_llm_configured() -> bool:
    """Check if OpenRouter is properly configured."""
    return bool(settings.OPENROUTER_API_KEY)


async def quick_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """
    Quick helper for simple LLM completions using LangChain.

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        model: Optional model override
        **kwargs: Additional arguments for the chat model

    Returns:
        The assistant's response content, or None if LLM is not configured
    """
    chat = get_openrouter_chat_model(model=model, **kwargs)
    if not chat:
        return None

    messages: List[BaseMessage] = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    response = await chat.ainvoke(messages)
    return response.content


# Convenience aliases for different model tiers
def get_fast_model(**kwargs) -> Optional[ChatOpenAI]:
    """Get a fast, cost-effective model (Claude 3 Haiku)."""
    return get_openrouter_chat_model(model="anthropic/claude-3-haiku", **kwargs)


def get_balanced_model(**kwargs) -> Optional[ChatOpenAI]:
    """Get a balanced model (Claude 3 Sonnet)."""
    return get_openrouter_chat_model(model="anthropic/claude-3-sonnet", **kwargs)


def get_powerful_model(**kwargs) -> Optional[ChatOpenAI]:
    """Get the most capable model (Claude 3 Opus or GPT-4)."""
    return get_openrouter_chat_model(model="anthropic/claude-3-opus", **kwargs)


# Available models reference (subset of popular options)
POPULAR_MODELS = {
    # Anthropic
    "claude-3-haiku": "anthropic/claude-3-haiku",
    "claude-3-sonnet": "anthropic/claude-3-sonnet",
    "claude-3-opus": "anthropic/claude-3-opus",

    # OpenAI
    "gpt-4-turbo": "openai/gpt-4-turbo",
    "gpt-4": "openai/gpt-4",
    "gpt-3.5-turbo": "openai/gpt-3.5-turbo",

    # Meta
    "llama-3-70b": "meta-llama/llama-3-70b-instruct",
    "llama-3-8b": "meta-llama/llama-3-8b-instruct",

    # Google
    "gemini-pro": "google/gemini-pro",

    # Mistral
    "mistral-large": "mistralai/mistral-large",
    "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
}
