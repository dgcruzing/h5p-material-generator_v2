"""API client implementations for LLM providers."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union

# Import API clients
from groq import Groq
from openai import OpenAI
import anthropic
from google.generativeai import GenerativeModel, configure as google_configure

from h5p_generator.config import API_KEYS, DEFAULT_MODELS, TOKEN_LIMITS

logger = logging.getLogger(__name__)


class LLMClientException(Exception):
    """Base exception for LLM client errors."""

    pass


class APIKeyMissingException(LLMClientException):
    """Exception raised when API key is missing."""

    pass


class APIRequestException(LLMClientException):
    """Exception raised when API request fails."""

    pass


class JSONParsingException(LLMClientException):
    """Exception raised when JSON parsing fails."""

    pass


class BaseLLMClient(ABC):
    """Base class for LLM API clients."""

    @abstractmethod
    def generate_content(
        self, prompt: str, max_tokens: int = 8000
    ) -> List[Dict[str, Any]]:
        """Generate content from the LLM."""
        pass


class GroqClient(BaseLLMClient):
    """Client for Groq API."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize Groq client."""
        self.api_key: Optional[str] = api_key or API_KEYS.get("groq")
        if not self.api_key:
            raise APIKeyMissingException("Groq API key is required")

        self.model = model or DEFAULT_MODELS.get("groq")
        self.client: Groq = Groq(api_key=self.api_key)

    def generate_content(
        self, prompt: str, max_tokens: int = 8000
    ) -> List[Dict[str, Any]]:
        """Generate content using Groq API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational content creator. Follow the provided instructions precisely.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            logger.info(f"Raw Groq content received: {content[:500]}...")

            if not content:
                raise JSONParsingException("Groq response content is empty.")

            try:
                # Clean potential markdown code fences if present
                if content.strip().startswith("```json"):
                    logger.info("Stripping ```json fence from Groq response")
                    content = content.strip()[7:-3].strip()
                elif content.strip().startswith("```"):
                    logger.info("Stripping ``` fence from Groq response")
                    content = content.strip()[3:-3].strip()

                return json.loads(content)
            except json.JSONDecodeError as e:
                raise JSONParsingException(
                    f"Failed to parse JSON from Groq response: {e}\nRaw content after cleaning: {content[:500]}"
                )

        except Exception as e:
            raise APIRequestException(f"Groq API request failed: {e}")


# Similar implementations for OpenAIClient, AnthropicClient, and GoogleGeminiClient...


class LLMClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_client(
        provider: str, api_key: str = None, model: str = None
    ) -> BaseLLMClient:
        """Create appropriate LLM client based on provider."""
        if provider.lower() == "groq":
            return GroqClient(api_key, model)
        elif provider.lower() == "openai":
            return OpenAIClient(api_key, model)
        elif provider.lower() == "claude":
            return AnthropicClient(api_key, model)
        elif provider.lower() == "google gemini":
            return GoogleGeminiClient(api_key, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Placeholder implementations (assuming they exist but are not shown)
class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize OpenAI client."""
        self.api_key: Optional[str] = api_key or API_KEYS.get("openai")
        if not self.api_key:
            raise APIKeyMissingException("OpenAI API key is required")
        self.model = model or DEFAULT_MODELS.get("openai")
        self.client: OpenAI = OpenAI(api_key=self.api_key)

    def generate_content(
        self, prompt: str, max_tokens: int = 8000
    ) -> List[Dict[str, Any]]:
        """Generate content using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational content creator. Follow the provided instructions precisely.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            content = response.choices[0].message.content
            if not content:
                raise JSONParsingException("OpenAI response content is empty.")

            try:
                # Clean potential markdown code fences if present
                if content.strip().startswith("```json"):
                    content = content.strip()[7:-3].strip()
                elif content.strip().startswith("```"):
                    content = content.strip()[3:-3].strip()

                return json.loads(content)
            except json.JSONDecodeError as e:
                raise JSONParsingException(
                    f"Failed to parse JSON from OpenAI response: {e}\nRaw content: {content[:500]}"
                )

        except Exception as e:
            raise APIRequestException(f"OpenAI API request failed: {e}")


class AnthropicClient(BaseLLMClient):
    """Client for Anthropic (Claude) API."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize Anthropic client."""
        self.api_key: Optional[str] = api_key or API_KEYS.get("anthropic")
        if not self.api_key:
            raise APIKeyMissingException("Anthropic API key is required")
        self.model = model or DEFAULT_MODELS.get("anthropic")
        self.client: anthropic.Anthropic = anthropic.Anthropic(api_key=self.api_key)

    def generate_content(
        self, prompt: str, max_tokens: int = 8000
    ) -> List[Dict[str, Any]]:
        """Generate content using Anthropic API."""
        try:
            # Note: Anthropic uses 'max_tokens' directly in the messages.create call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                system="You are an educational content creator. Follow the provided instructions precisely.",
                messages=[{"role": "user", "content": prompt}],
            )

            # Anthropic returns content in blocks
            if (
                response.content
                and isinstance(response.content, list)
                and hasattr(response.content[0], "text")
            ):
                content = response.content[0].text
            else:
                raise JSONParsingException(
                    "Anthropic response format unexpected or content block missing."
                )

            if not content:
                raise JSONParsingException("Anthropic response content is empty.")

            try:
                # Clean potential markdown code fences if present
                if content.strip().startswith("```json"):
                    content = content.strip()[7:-3].strip()
                elif content.strip().startswith("```"):
                    content = content.strip()[3:-3].strip()

                return json.loads(content)
            except json.JSONDecodeError as e:
                raise JSONParsingException(
                    f"Failed to parse JSON from Anthropic response: {e}\nRaw content: {content[:500]}"
                )

        except Exception as e:
            raise APIRequestException(f"Anthropic API request failed: {e}")


class GoogleGeminiClient(BaseLLMClient):
    """Client for Google Gemini API."""

    def __init__(self, api_key: str = None, model: str = None):
        """Initialize Google Gemini client."""
        self.api_key: Optional[str] = api_key or API_KEYS.get("google_gemini")
        if not self.api_key:
            raise APIKeyMissingException("Google Gemini API key is required")
        self.model_name = model or DEFAULT_MODELS.get("google_gemini")

        # Configure the API key globally for this client instance
        try:
            google_configure(api_key=self.api_key)
        except Exception as e:
            raise APIKeyMissingException(
                f"Failed to configure Google Gemini API key: {e}"
            )

        self.model: GenerativeModel = GenerativeModel(self.model_name)

    def generate_content(
        self, prompt: str, max_tokens: int = 8000
    ) -> List[Dict[str, Any]]:
        """Generate content using Google Gemini API."""
        # Note: Gemini's API might handle max_tokens differently (often part of generation_config)
        # For simplicity here, we're not explicitly limiting response tokens, relying on prompt design.
        # A system prompt equivalent can be included at the start of the user prompt.
        system_prompt = "You are an educational content creator. Follow the provided instructions precisely."
        full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            # Adjust generation config if needed, e.g., for temperature, token limits
            generation_config = {
                "temperature": 0.7,
                # "max_output_tokens": max_tokens, # Uncomment if API supports this directly
            }
            response = self.model.generate_content(
                full_prompt, generation_config=generation_config
            )

            # Accessing the text part of the response
            if response.parts:
                content = response.text  # Access concatenated text directly
            elif hasattr(response, "text"):
                content = response.text
            else:
                # Attempt to find text if structure is different
                try:
                    content = response.candidates[0].content.parts[0].text
                except (IndexError, AttributeError):
                    raise JSONParsingException(
                        "Google Gemini response format unexpected or text part missing."
                    )

            if not content:
                raise JSONParsingException("Google Gemini response content is empty.")

            try:
                # Clean potential markdown code fences if present
                if content.strip().startswith("```json"):
                    content = content.strip()[7:-3].strip()
                elif content.strip().startswith("```"):
                    content = content.strip()[3:-3].strip()

                return json.loads(content)
            except json.JSONDecodeError as e:
                raise JSONParsingException(
                    f"Failed to parse JSON from Google Gemini response: {e}\nRaw content: {content[:500]}"
                )

        except Exception as e:
            # Catch potential errors from the API call itself
            raise APIRequestException(f"Google Gemini API request failed: {e}")
