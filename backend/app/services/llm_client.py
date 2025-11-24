"""
LLM Client Service for OpenRouter API.

This module provides a unified interface for interacting with LLMs via OpenRouter,
which offers access to multiple providers (OpenAI, Anthropic, Meta, etc.) through
a single API.

OpenRouter Documentation: https://openrouter.ai/docs
"""
import httpx
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum

from ..core.config import settings

logger = logging.getLogger(__name__)


class LLMRole(str, Enum):
    """Message roles for chat completions."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Message:
    """A chat message."""
    role: LLMRole
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role.value, "content": self.content}


@dataclass
class LLMResponse:
    """Response from LLM completion."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    raw_response: Optional[dict] = None


class LLMClientError(Exception):
    """Base exception for LLM client errors."""
    pass


class LLMConfigurationError(LLMClientError):
    """Raised when LLM is not properly configured."""
    pass


class LLMAPIError(LLMClientError):
    """Raised when API request fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class OpenRouterClient:
    """
    Client for OpenRouter API.

    OpenRouter provides a unified API to access multiple LLM providers:
    - Anthropic (Claude models)
    - OpenAI (GPT models)
    - Meta (Llama models)
    - Google (Gemini models)
    - And many more

    Usage:
        client = OpenRouterClient()

        # Simple completion
        response = await client.complete("What is the capital of France?")

        # Chat completion with messages
        messages = [
            Message(LLMRole.SYSTEM, "You are a helpful assistant."),
            Message(LLMRole.USER, "Hello!")
        ]
        response = await client.chat(messages)

        # Streaming completion
        async for chunk in client.stream("Tell me a story"):
            print(chunk, end="")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the OpenRouter client.

        Args:
            api_key: OpenRouter API key. Defaults to settings.OPENROUTER_API_KEY
            base_url: API base URL. Defaults to settings.OPENROUTER_BASE_URL
            model: Model to use. Defaults to settings.OPENROUTER_MODEL
            timeout: Request timeout in seconds. Defaults to settings.LLM_TIMEOUT_SECONDS
        """
        self.api_key = api_key or settings.OPENROUTER_API_KEY
        self.base_url = (base_url or settings.OPENROUTER_BASE_URL).rstrip("/")
        self.model = model or settings.OPENROUTER_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS

        # Default request parameters
        self.default_max_tokens = settings.LLM_MAX_TOKENS
        self.default_temperature = settings.LLM_TEMPERATURE

        # Site info for OpenRouter tracking
        self.site_url = settings.OPENROUTER_SITE_URL
        self.site_name = settings.OPENROUTER_SITE_NAME

    @property
    def is_configured(self) -> bool:
        """Check if the client is properly configured with an API key."""
        return bool(self.api_key)

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Optional headers for OpenRouter tracking/identification
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.site_name:
            headers["X-Title"] = self.site_name

        return headers

    def _validate_configuration(self):
        """Validate that the client is properly configured."""
        if not self.api_key:
            raise LLMConfigurationError(
                "OpenRouter API key not configured. "
                "Set OPENROUTER_API_KEY in your .env file. "
                "Get your key at: https://openrouter.ai/keys"
            )

    async def chat(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send a chat completion request.

        Args:
            messages: List of chat messages
            model: Override default model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            **kwargs: Additional parameters to pass to the API

        Returns:
            LLMResponse with the completion

        Raises:
            LLMConfigurationError: If API key is not configured
            LLMAPIError: If the API request fails
        """
        self._validate_configuration()

        payload = {
            "model": model or self.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature if temperature is not None else self.default_temperature,
            **kwargs
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload
                )

                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", response.text)
                    raise LLMAPIError(
                        f"OpenRouter API error: {error_msg}",
                        status_code=response.status_code,
                        response=error_data
                    )

                data = response.json()

                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    finish_reason=data["choices"][0].get("finish_reason", "stop"),
                    raw_response=data
                )

            except httpx.TimeoutException:
                raise LLMAPIError(f"Request timed out after {self.timeout} seconds")
            except httpx.RequestError as e:
                raise LLMAPIError(f"Request failed: {str(e)}")

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Simple completion with a single prompt.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for chat()

        Returns:
            LLMResponse with the completion
        """
        messages = []

        if system_prompt:
            messages.append(Message(LLMRole.SYSTEM, system_prompt))

        messages.append(Message(LLMRole.USER, prompt))

        return await self.chat(messages, **kwargs)

    async def stream(
        self,
        messages: List[Message],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion response.

        Args:
            messages: List of chat messages
            model: Override default model
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-2)
            **kwargs: Additional parameters to pass to the API

        Yields:
            Content chunks as they arrive

        Raises:
            LLMConfigurationError: If API key is not configured
            LLMAPIError: If the API request fails
        """
        self._validate_configuration()

        payload = {
            "model": model or self.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature if temperature is not None else self.default_temperature,
            "stream": True,
            **kwargs
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._get_headers(),
                    json=payload
                ) as response:
                    if response.status_code != 200:
                        content = await response.aread()
                        raise LLMAPIError(
                            f"OpenRouter API error: {content.decode()}",
                            status_code=response.status_code
                        )

                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break

                            import json
                            try:
                                data = json.loads(data_str)
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue

            except httpx.TimeoutException:
                raise LLMAPIError(f"Stream timed out after {self.timeout} seconds")
            except httpx.RequestError as e:
                raise LLMAPIError(f"Stream request failed: {str(e)}")

    async def generate_recommendation_explanation(
        self,
        venue_name: str,
        venue_cuisine: str,
        user_preferences: List[str],
        context: Dict[str, Any],
    ) -> str:
        """
        Generate a personalized explanation for a venue recommendation.

        This is a domain-specific helper for Luna Social.

        Args:
            venue_name: Name of the recommended venue
            venue_cuisine: Cuisine type of the venue
            user_preferences: User's cuisine preferences
            context: Additional context (meal_time, is_weekend, etc.)

        Returns:
            Personalized recommendation explanation
        """
        if not self.is_configured:
            # Fallback to template-based explanation if LLM not configured
            return self._generate_fallback_explanation(
                venue_name, venue_cuisine, user_preferences, context
            )

        system_prompt = """You are a friendly dining assistant for Luna Social,
a social dining app that helps people discover great restaurants and connect
with dining companions. Generate short, engaging, personalized explanations
for restaurant recommendations. Keep responses under 50 words."""

        meal_time = context.get("meal_time", "dining")
        is_weekend = context.get("is_weekend", False)
        time_context = "this weekend" if is_weekend else "today"

        prompt = f"""Generate a brief, friendly recommendation explanation for:
- Restaurant: {venue_name}
- Cuisine: {venue_cuisine}
- User likes: {', '.join(user_preferences[:3]) if user_preferences else 'trying new places'}
- Time: {meal_time} {time_context}

Make it personal and inviting, highlighting why this is a great match."""

        try:
            response = await self.complete(prompt, system_prompt=system_prompt)
            return response.content.strip()
        except LLMAPIError as e:
            logger.warning(f"LLM API error, using fallback: {e}")
            return self._generate_fallback_explanation(
                venue_name, venue_cuisine, user_preferences, context
            )

    def _generate_fallback_explanation(
        self,
        venue_name: str,
        venue_cuisine: str,
        user_preferences: List[str],
        context: Dict[str, Any],
    ) -> str:
        """Generate a template-based fallback explanation."""
        meal_time = context.get("meal_time", "meal")

        if user_preferences and venue_cuisine.lower() in [p.lower() for p in user_preferences]:
            return f"'{venue_name}' serves {venue_cuisine} cuisine - one of your favorites! Perfect for {meal_time}."

        return f"'{venue_name}' is a great choice for {meal_time}. Known for excellent {venue_cuisine} dishes!"

    async def generate_social_match_reason(
        self,
        user_name: str,
        shared_interests: List[str],
        compatibility_score: float,
        mutual_friend_names: Optional[List[str]] = None,
    ) -> str:
        """
        Generate a reason for why two users are a good match for dining together.

        Args:
            user_name: Name of the potential dining companion
            shared_interests: List of shared interests/preferences
            compatibility_score: Compatibility score (0-1)
            mutual_friend_names: Optional list of mutual friend names

        Returns:
            Explanation for the social match
        """
        if not self.is_configured:
            # Fallback
            if shared_interests:
                return f"You both enjoy {shared_interests[0]}!"
            return f"Great compatibility match!"

        # Build prompt with mutual friend names if available
        mutual_friends_context = ""
        if mutual_friend_names and len(mutual_friend_names) > 0:
            if len(mutual_friend_names) == 1:
                mutual_friends_context = f" You share a mutual friend: {mutual_friend_names[0]}."
            else:
                mutual_friends_context = f" You share mutual friends: {', '.join(mutual_friend_names[:2])}."
        
        # Filter out generic "mutual friend(s)" reasons since we're providing names separately
        filtered_interests = [r for r in shared_interests if "mutual friend" not in r.lower()]
        
        interests_text = ', '.join(filtered_interests[:3]) if filtered_interests else "similar dining preferences"
        
        system_prompt = """You are a friendly social dining assistant. Generate brief, conversational 
one-liners about why people would be great dining companions. Never use placeholders like 
[Mutual Friend's Name] - only use actual names if provided, or skip mentioning names if not available."""

        prompt = f"""Generate a brief, friendly one-liner (under 20 words) about why {user_name}
would be a great dining companion. Shared interests: {interests_text}.
Compatibility: {compatibility_score:.0%}.{mutual_friends_context}
Make it conversational and inviting. Do not use placeholders or generic names."""

        try:
            response = await self.complete(prompt, system_prompt=system_prompt)
            return response.content.strip()
        except LLMAPIError:
            if shared_interests:
                return f"You both enjoy {shared_interests[0]}!"
            return f"Great compatibility match!"


# Singleton instance
_llm_client: Optional[OpenRouterClient] = None


def get_llm_client() -> OpenRouterClient:
    """
    Get the singleton LLM client instance.

    Returns:
        OpenRouterClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenRouterClient()
    return _llm_client


def reset_llm_client():
    """Reset the singleton instance (useful for testing)."""
    global _llm_client
    _llm_client = None
