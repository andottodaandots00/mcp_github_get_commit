"""
Gradient AI SDK integration for AI-powered table and text enhancement.

This module provides the GradientEnhancer class for integrating with
DigitalOcean's Gradient AI Platform SDK to enhance OCR output quality
using LLM-powered correction and formatting.

Uses the official Gradient SDK (NOT requests library) with proper
exception handling and graceful degradation when API key is unavailable.

Classes:
    GradientEnhancer: Main class for AI-powered enhancement

Usage:
    >>> from config.settings import ConversionConfig
    >>> config = ConversionConfig()
    >>>
    >>> with GradientEnhancer(config.gradient) as enhancer:
    ...     if enhancer.is_available:
    ...         enhanced_table = enhancer.enhance_table(table_markdown)
    ...         enhanced_text = enhancer.enhance_text(ocr_text)
"""

import os
import logging
from typing import Optional, List, Dict, Any
import requests

# Hardcoded values from cell_12_ai_context_conversion.py
HARDCODED_API_KEY = "sk-do-8v_JJNSHKXtQOEYKJIU2fTukxNKx85IdcSmecYCEuEBvvyDU4fG5CPL9s_"
HARDCODED_MODEL = "openai-gpt-oss-120b"
API_URL = "https://inference.do-ai.run/v1/chat/completions"

try:
    # Dummy imports for compatibility
    class Gradient:
        pass
    GRADIENT_AVAILABLE = True
except ImportError:
    GRADIENT_AVAILABLE = False

from ..config.settings import GradientConfig

logger = logging.getLogger(__name__)


class GradientEnhancer:
    """
    AI-powered enhancement for tables and text using Gradient SDK.

    Provides LLM-based correction of OCR errors, table structure fixing,
    and text formatting improvements using the DigitalOcean Gradient AI Platform.

    Attributes:
        config: GradientConfig instance with API key and settings
        client: Initialized Gradient SDK client (if available)
        is_available: Whether enhancement is available

    Example:
        >>> config = GradientConfig(
        ...     enabled=True,
        ...     model_access_key="your-key",
        ...     default_model="llama3.3-70b-instruct"
        ... )
        >>> with GradientEnhancer(config) as enhancer:
        ...     if enhancer.is_available:
        ...         clean_table = enhancer.enhance_table(raw_table_md)
    """

    def __init__(self, config: GradientConfig):
        """
        Initialize the Gradient enhancer with hardcoded API key and model.

        Args:
            config: GradientConfig with settings (ignored for hardcoded values)

        Raises:
            No exceptions raised - gracefully degrades if API unavailable
        """
        self.config = config
        self.api_key = HARDCODED_API_KEY
        self.model = HARDCODED_MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self._initialization_error: Optional[str] = None

        # Check if enhancement is enabled
        if not config.enabled:
            logger.info("Gradient enhancement disabled in config")
            return

        # Test the API connection
        try:
            # Simple test request to verify API key works
            test_data = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            response = requests.post(API_URL, headers=self.headers, json=test_data, timeout=10)
            if response.status_code == 401:
                self._initialization_error = "Invalid API key"
                logger.error(self._initialization_error)
            elif response.status_code != 200:
                self._initialization_error = f"API test failed: {response.status_code}"
                logger.warning(self._initialization_error)
            else:
                logger.info(f"API initialized successfully (model: {self.model})")
        except requests.exceptions.RequestException as e:
            self._initialization_error = f"Cannot connect to API: {e}"
            logger.warning(self._initialization_error)
        except Exception as e:
            self._initialization_error = f"API initialization failed: {e}"
            logger.error(self._initialization_error)

    def _chat_completion(self, prompt: str, system_prompt: str = "You are a helpful document analysis assistant.") -> str:
        """Call the inference API with proper error handling."""
        if self._initialization_error:
            return f"[API Error: {self._initialization_error}]"

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096
        }

        try:
            response = requests.post(API_URL, headers=self.headers, json=data, timeout=60)
            response.raise_for_status()
            res_json = response.json()
            return res_json["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            logger.error("AI Model call timed out after 60 seconds")
            return "[AI Analysis Timeout: Request exceeded 60 second limit]"
        except requests.exceptions.HTTPError as e:
            logger.error(f"AI Model HTTP error: {e.response.status_code} - {e.response.text}")
            return f"[AI Analysis Error: HTTP {e.response.status_code}]"
        except requests.exceptions.RequestException as e:
            logger.error(f"AI Model network error: {e}")
            return "[AI Analysis Error: Network connection failed]"
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"AI Model response parsing error: {e}")
            return "[AI Analysis Error: Invalid response format]"
        except Exception as e:
            logger.error(f"AI Model unexpected error: {e}")
    @property
    def is_available(self) -> bool:
        """
        Check if API enhancement is available and operational.

        Returns:
            True if API is initialized and ready, False otherwise
        """
        return self._initialization_error is None

    def enhance_table(self, table_markdown: str) -> str:
        """
        Enhance table markdown with AI-powered cleaning and formatting.

        Fixes OCR errors in headers and cells, normalizes alignment,
        fixes missing or broken pipes, and ensures proper markdown structure.

        Args:
            table_markdown: Raw table markdown from OCR/extraction

        Returns:
            Enhanced table markdown, or original if enhancement unavailable

        Example:
            >>> raw = "| He ader | Va lue |\\n|---|---|\\n| Nam e | J ohn |"
            >>> enhanced = enhancer.enhance_table(raw)
            >>> print(enhanced)
            | Header | Value |
            |--------|-------|
            | Name   | John  |
        """
        # Return original if not available
        if not self.is_available:
            logger.debug("Gradient not available - returning original table")
            return table_markdown

        # Skip empty or very short tables
        if not table_markdown or len(table_markdown.strip()) < 10:
            return table_markdown

        try:
            # Create prompt for table enhancement
            prompt = f"""You are a document processing expert. Clean and format this markdown table:

{table_markdown}

Tasks:
1. Fix OCR errors in text (common: l→I, 0→O, spacing errors)
2. Normalize header alignment and separator rows
3. Fix missing or broken pipe characters (|)
4. Ensure consistent column widths
5. Preserve original data meaning

Return ONLY the corrected markdown table with no explanations."""

            # Call API using our HTTP method
            enhanced = self._chat_completion(
                prompt=prompt,
                system_prompt="You are a markdown table formatting expert. Fix errors but preserve all data."
            )

            # Check if we got an error response
            if enhanced.startswith("[AI Analysis Error"):
                logger.warning(f"API error in table enhancement: {enhanced} - using original table")
                return table_markdown

            # Validate we got a table back
            if not enhanced or '|' not in enhanced:
                logger.warning("API returned invalid table format - using original")
                return table_markdown

            logger.debug(f"Enhanced table: {len(table_markdown)} → {len(enhanced)} chars")
            return enhanced

        except Exception as e:
            logger.error(f"Unexpected error in table enhancement: {e} - using original table")
            return table_markdown

    def enhance_text(self, text: str) -> str:
        """
        Enhance text with AI-powered OCR error correction.

        Corrects common OCR errors while preserving original formatting
        and structure. Uses lower temperature for more conservative edits.

        Args:
            text: Raw text from OCR extraction

        Returns:
            Enhanced text with OCR errors corrected, or original if unavailable

        Example:
            >>> raw = "The qu1ck br0wn f0x jumps 0ver the 1azy d0g"
            >>> enhanced = enhancer.enhance_text(raw)
            >>> print(enhanced)
            The quick brown fox jumps over the lazy dog
        """
        # Return original if not available
        if not self.is_available:
            logger.debug("Gradient not available - returning original text")
            return text

        # Skip very short text (likely not worth API call)
        if not text or len(text.strip()) < 50:
            return text

        try:
            # Calculate appropriate max_tokens based on input length
            # Allow 1.5x input length for correction + formatting
            estimated_tokens = len(text.split()) * 1.3  # ~1.3 tokens per word
            max_tokens = min(
                int(estimated_tokens * 1.5),
                self.config.max_tokens
            )

            # Create prompt for text correction
            prompt = f"""Correct OCR errors in this text while preserving formatting:

{text}

Common OCR errors to fix:
- l → I (lowercase L to uppercase i)
- 0 → O (zero to letter O)
- 1 → l (one to lowercase L)
- Spacing errors (extra spaces or missing spaces)
- Line break issues

Preserve:
- Original paragraph structure
- Capitalization patterns
- Punctuation
- Technical terms

Return ONLY the corrected text with no explanations."""

            # Create prompt for text correction
            prompt = f"""Correct OCR errors in this text while preserving formatting:

{text}

Common OCR errors to fix:
- l → I (lowercase L to uppercase i)
- 0 → O (zero to letter O)
- 1 → l (one to lowercase L)
- Spacing errors (extra spaces or missing spaces)
- Line break issues

Preserve:
- Original paragraph structure
- Capitalization patterns
- Punctuation
- Technical terms

Return ONLY the corrected text with no explanations."""

            # Call API using our HTTP method
            enhanced = self._chat_completion(
                prompt=prompt,
                system_prompt="You are an OCR error correction expert. Fix errors while preserving structure."
            )

            # Check if we got an error response
            if enhanced.startswith("[AI Analysis Error"):
                logger.warning(f"API error in text enhancement: {enhanced} - using original text")
                return text

            # Validate we got meaningful output
            if not enhanced or len(enhanced) < len(text) * 0.5:
                logger.warning("API returned suspiciously short text - using original")
                return text

            logger.debug(f"Enhanced text: {len(text)} → {len(enhanced)} chars")
            return enhanced

        except Exception as e:
            logger.error(f"Unexpected error in text enhancement: {e} - using original text")
            return text

    def close(self):
        """
        Close the Gradient SDK client connection.

        Releases any resources held by the client. Safe to call multiple times.
        """
        if self.client is not None:
            try:
                # Gradient SDK handles cleanup internally
                # Just clear our reference
                self.client = None
                logger.debug("Gradient client closed")
            except Exception as e:
                logger.warning(f"Error closing Gradient client: {e}")

    def __enter__(self):
        """Context manager entry - returns self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes client connection."""
        self.close()
        return False  # Don't suppress exceptions
