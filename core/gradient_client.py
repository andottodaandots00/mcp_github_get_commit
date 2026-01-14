"""AI Client for Document Processing Enhancement.

This module provides AI client implementations for document enhancement:
1. GradientLLMClient - Uses DigitalOcean Gradient SDK (requires pip install gradient)
2. DirectInferenceClient - Uses direct REST API calls (SDK-free) with an explicit API key.

Integration with converter.py:
    The enhance_content_with_ai() function uses these clients to:
    - Clean OCR errors in extracted text
    - Improve table formatting
    - Enhance markdown quality

Usage:
    >>> from core.gradient_client import DirectInferenceClient
    >>> client = DirectInferenceClient(api_key="<your-key>")
    >>> response = client.chat_completion(
    ...     messages=[{"role": "user", "content": "Clean this text: ..."}],
    ... )
"""

import os
import logging
import requests
from typing import List, Dict, Optional, Generator, Union, Any

# Configure logging
logger = logging.getLogger(__name__)

# =============================================================================
# API CONFIGURATION (requires explicit key)
# =============================================================================
DEFAULT_API_KEY: Optional[str] = None
DEFAULT_API_URL = "https://inference.do-ai.run/v1/chat/completions"
DEFAULT_MODEL = "openai-gpt-oss-120b"


def get_api_key() -> str:
    """Get API key from environment variables."""
    return (
        os.environ.get("DEEPINFRA_API_KEY")
        or os.environ.get("DOCLING_API_KEY")
        or os.environ.get("GRADIENT_MODEL_ACCESS_KEY")
        or (DEFAULT_API_KEY or "")
    )


# =============================================================================
# DIRECT INFERENCE CLIENT (No SDK required - RECOMMENDED)
# =============================================================================
class DirectInferenceClient:
    """
    Direct REST API client for AI inference.

    Uses the inference.do-ai.run API endpoint directly without requiring
    any SDK installation. Requires a provided API key (env or argument).

    Features:
        - No dependencies beyond requests
        - Explicit API key handling (no hardcoded secrets)
        - Simple REST-based chat completions
        - Robust error handling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: str = DEFAULT_API_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0
    ):
        """
        Initialize the Direct Inference Client.

        Args:
            api_key: API key (uses hardcoded default if not provided)
            api_url: API endpoint URL
            model: Default model to use
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise ValueError(
                "API key is required for DirectInferenceClient. "
                "Set GRADIENT_MODEL_ACCESS_KEY/DOCLING_API_KEY or pass api_key explicitly."
            )

        self.api_url = api_url
        self.model = model
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    @property
    def enabled(self) -> bool:
        """Check if AI features are enabled (API key is set)."""
        return bool(self.api_key)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to self.model)
            temperature: Creativity parameter (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt to prepend

        Returns:
            Generated text response
        """
        # Prepend system prompt if provided
        if system_prompt:
            messages = [{"role": "system", "content": system_prompt}] + messages

        data = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()

        except requests.exceptions.Timeout:
            logger.error(f"AI API call timed out after {self.timeout} seconds")
            return f"[AI Analysis Timeout: Request exceeded {self.timeout} second limit]"
        except requests.exceptions.HTTPError as e:
            logger.error(f"AI API HTTP error: {e.response.status_code} - {e.response.text}")
            return f"[AI Analysis Error: HTTP {e.response.status_code}]"
        except requests.exceptions.RequestException as e:
            logger.error(f"AI API network error: {e}")
            return "[AI Analysis Error: Network connection failed]"
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"AI API response parsing error: {e}")
            return "[AI Analysis Error: Invalid response format]"
        except Exception as e:
            logger.error(f"AI API unexpected error: {e}")
            return f"[AI Analysis Error: {str(e)}]"


# Flag for availability (DirectInferenceClient always available)
DIRECT_CLIENT_AVAILABLE = True


# =============================================================================
# GRADIENT SDK CLIENT (Requires pip install gradient)
# =============================================================================
try:
    from gradient import Gradient, AsyncGradient
    from gradient import (
        APIError,
        RateLimitError,
        APIConnectionError,
        AuthenticationError,
        APIStatusError
    )
    GRADIENT_SDK_AVAILABLE = True
except ImportError:
    GRADIENT_SDK_AVAILABLE = False
    # Create placeholder exceptions for when SDK not installed
    class APIError(Exception): pass
    class RateLimitError(Exception): pass
    class APIConnectionError(Exception): pass
    class AuthenticationError(Exception): pass
    class APIStatusError(Exception): pass

class GradientLLMClient:
    """
    A wrapper client for DigitalOcean's Gradient SDK to handle
    Serverless Inference interactions with improved error handling and type safety.

    Features:
        - Synchronous and async chat completions
        - Streaming support for real-time responses
        - Comprehensive error handling with specific exception types
        - Auto-detection of API key from environment

    Attributes:
        access_key: The Gradient Model Access Key
        _client: Synchronous Gradient client
        _async_client: Asynchronous Gradient client
    """

    def __init__(
        self,
        access_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 2
    ):
        """
        Initialize the Gradient Client.

        Args:
            access_key: Gradient Model Access Key. Defaults to env var GRADIENT_MODEL_ACCESS_KEY.
            base_url: Optional custom base URL.
            timeout: Request timeout in seconds.
            max_retries: Number of retries for failed requests.

        Raises:
            ImportError: If gradient SDK is not installed
            ValueError: If no access key is provided or found in environment
        """
        if not GRADIENT_SDK_AVAILABLE:
            raise ImportError(
                "Gradient SDK is not installed. "
                "Install with: pip install gradient"
            )

        self.access_key = access_key or os.getenv("GRADIENT_MODEL_ACCESS_KEY")
        if not self.access_key:
            # Check for alternate env var names
            self.access_key = os.getenv("DIGITAL_OCEAN_MODEL_ACCESS_KEY")

        if not self.access_key:
            raise ValueError(
                "Gradient Model Access Key is required. "
                "Set GRADIENT_MODEL_ACCESS_KEY environment variable or pass it explicitly."
            )

        self._client = Gradient(
            model_access_key=self.access_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )

        self._async_client = AsyncGradient(
            model_access_key=self.access_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.3-70b-instruct",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Union[str, Generator[str, None, None]]:
        """
        Send a chat completion request to a Gradient model.

        Args:
            messages: List of message dicts (e.g. [{"role": "user", "content": "Hi"}]).
            model: Model identifier string.
            temperature: Creativity parameter (0.0 - 1.0).
            max_tokens: Max tokens to generate.
            stream: Whether to stream the response.

        Returns:
            Generated text string (if stream=False) or Generator of text chunks (if stream=True).
        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens, # type: ignore
                stream=stream
            )

            if stream:
                return self._stream_response_generator(response)
            else:
                return response.choices[0].message.content or ""

        except RateLimitError:
            logger.error("Gradient API Rate Limit Exceeded.")
            raise
        except AuthenticationError:
            logger.error("Gradient Authentication Error: Invalid API key")
            raise
        except APIConnectionError as e:
            logger.error(f"Gradient API Connection Error: {e}")
            raise
        except APIStatusError as e:
            logger.error(f"Gradient API Status Error ({e.status_code}): {e.response}")
            raise
        except APIError as e:
            logger.error(f"Gradient API Error ({e.status_code}): {e.message}")
            raise
        except Exception as e:
            logger.exception("Unexpected error during Gradient chat completion")
            raise

    async def a_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3.3-70b-instruct",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Asynchronous chat completion.
        """
        try:
            response = await self._async_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens # type: ignore
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Async Gradient Error: {e}")
            raise

    def _stream_response_generator(self, stream_response: Any) -> Generator[str, None, None]:
        """Helper to yield content from stream."""
        for chunk in stream_response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    def close(self):
        """Close the underlying client sessions."""
        self._client.close()
        # Async client needs async close, usually handled by context manager or await

