"""
Pydantic Configuration Models for Kaggle Document Conversion Pipeline.

This module provides structured configuration models using Pydantic v2 with:
- Environment variable support via pydantic-settings
- Type validation and coercion
- Rich field metadata and descriptions
- Secure handling of sensitive data (API keys)

Usage:
    from config_models import ProcessingConfig, get_settings

    # Load from environment variables
    config = ProcessingConfig()

    # Or with explicit values
    config = ProcessingConfig(
        kaggle=KaggleConfig(input_dir="/custom/path"),
        gpu=GPUConfig(device="cuda:0"),
    )
"""

from __future__ import annotations

import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, List, Literal, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# Enums
# =============================================================================


class AcceleratorDevice(str, Enum):
    """Supported acceleration devices for GPU processing."""

    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Metal Performance Shaders
    XPU = "xpu"  # Intel discrete GPUs


class OCRBackend(str, Enum):
    """Supported OCR engine backends."""

    EASYOCR = "easyocr"
    TESSERACT = "tesseract"
    RAPIDOCR = "rapidocr"


# =============================================================================
# KaggleConfig - Main Kaggle Environment Configuration
# =============================================================================


class KaggleConfig(BaseSettings):
    """
    Main configuration for Kaggle notebook environment.

    Supports environment variables with prefix KAGGLE_ (e.g., KAGGLE_INPUT_DIR).

    Attributes:
        input_dir: Directory containing input PDF files for processing.
        output_dir: Directory where converted outputs will be saved.
        max_workers: Maximum number of parallel workers (None = auto-detect).
        enable_ai: Enable AI-powered enhancement features.
        create_zip: Create a ZIP archive of output files.
        model_api_key: API key for AI model services (stored securely).

    Example:
        >>> config = KaggleConfig()
        >>> config.input_dir
        PosixPath('/kaggle/working/input_pdfs')

        >>> # Override via environment
        >>> os.environ["KAGGLE_INPUT_DIR"] = "/custom/input"
        >>> config = KaggleConfig()
    """

    model_config = SettingsConfigDict(
        env_prefix="KAGGLE_",
        env_nested_delimiter="_",
        extra="ignore",
        validate_default=True,
    )

    input_dir: Annotated[
        Path,
        Field(
            default=Path("/kaggle/working/input_pdfs"),
            description="Directory containing input PDF files for processing.",
            examples=["/kaggle/working/input_pdfs", "/data/pdfs"],
        ),
    ]

    output_dir: Annotated[
        Path,
        Field(
            default=Path("/kaggle/working/output"),
            description="Directory where converted outputs will be saved.",
            examples=["/kaggle/working/output", "/data/output"],
        ),
    ]

    max_workers: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Maximum number of parallel workers. None = auto-detect based on CPU cores.",
            ge=1,
            examples=[1, 4, 8],
        ),
    ]

    enable_ai: Annotated[
        bool,
        Field(
            default=False,
            description="Enable AI-powered enhancement features for document processing.",
        ),
    ]

    create_zip: Annotated[
        bool,
        Field(
            default=True,
            description="Create a ZIP archive of all output files after processing.",
        ),
    ]

    model_api_key: Annotated[
        Optional[SecretStr],
        Field(
            default=None,
            description="API key for AI model services. Stored securely and masked in logs.",
        ),
    ]

    @field_validator("input_dir", "output_dir", mode="before")
    @classmethod
    def coerce_to_path(cls, v: Any) -> Path:
        """Coerce string values to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @field_validator("max_workers")
    @classmethod
    def validate_max_workers(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_workers is reasonable if provided."""
        if v is not None and v > 64:
            raise ValueError("max_workers should not exceed 64 for stability.")
        return v

    def get_effective_workers(self) -> int:
        """Get the effective number of workers, auto-detecting if not set."""
        if self.max_workers is not None:
            return self.max_workers
        # Auto-detect based on CPU count
        cpu_count = os.cpu_count() or 4
        return max(1, cpu_count - 1)


# =============================================================================
# GPUConfig - GPU-Specific Settings
# =============================================================================


class GPUConfig(BaseSettings):
    """
    GPU-specific configuration for hardware acceleration.

    Supports environment variables with prefix GPU_ (e.g., GPU_DEVICE).

    Attributes:
        device: Target device for computation ('auto', 'cpu', 'cuda', 'cuda:N', 'mps', 'xpu').
        num_gpus: Number of GPUs to use (None = use all available).
        batch_size: Batch size for GPU processing operations.
        use_flash_attention: Enable Flash Attention 2 for transformer models.
        cuda_memory_fraction: Fraction of GPU memory to allocate (0.0 to 1.0).

    Example:
        >>> gpu = GPUConfig(device="cuda:0", batch_size=8)
        >>> gpu.device
        'cuda:0'
    """

    model_config = SettingsConfigDict(
        env_prefix="GPU_",
        extra="ignore",
        validate_default=True,
    )

    device: Annotated[
        str,
        Field(
            default="auto",
            description="Target device: 'auto', 'cpu', 'cuda', 'cuda:N', 'mps', or 'xpu'.",
            examples=["auto", "cpu", "cuda", "cuda:0", "mps"],
        ),
    ]

    num_gpus: Annotated[
        Optional[int],
        Field(
            default=None,
            description="Number of GPUs to use. None = use all available GPUs.",
            ge=1,
            examples=[1, 2, 4],
        ),
    ]

    batch_size: Annotated[
        int,
        Field(
            default=4,
            description="Batch size for GPU processing operations.",
            ge=1,
            le=128,
            examples=[1, 4, 8, 16],
        ),
    ]

    use_flash_attention: Annotated[
        bool,
        Field(
            default=False,
            description="Enable Flash Attention 2 for faster transformer inference. Requires compatible GPU.",
        ),
    ]

    cuda_memory_fraction: Annotated[
        float,
        Field(
            default=0.9,
            description="Fraction of GPU memory to allocate (0.0 to 1.0). Reserve some for system stability.",
            ge=0.1,
            le=1.0,
            examples=[0.5, 0.8, 0.9, 1.0],
        ),
    ]

    enable_parallel: Annotated[
        bool,
        Field(
            default=True,
            description="Enable multi-GPU parallel processing for batch conversions.",
        ),
    ]

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Validate device string format."""
        import re

        valid_devices = {"auto", "cpu", "mps", "xpu", "cuda"}

        if v in valid_devices:
            return v

        # Allow 'cuda:N' format
        if re.match(r"^cuda(:\d+)?$", v):
            return v

        raise ValueError(
            f"Invalid device '{v}'. Use 'auto', 'cpu', 'mps', 'xpu', 'cuda', or 'cuda:N'."
        )

    @model_validator(mode="after")
    def check_flash_attention_compatibility(self) -> "GPUConfig":
        """Warn if flash attention is enabled for non-CUDA devices."""
        if self.use_flash_attention and self.device not in ("auto", "cuda") and not self.device.startswith("cuda"):
            import warnings
            warnings.warn(
                f"Flash Attention is only supported on CUDA devices, but device is '{self.device}'."
            )
        return self


# =============================================================================
# OCRConfig - OCR Engine Settings
# =============================================================================


class OCRConfig(BaseSettings):
    """
    OCR (Optical Character Recognition) engine configuration.

    Supports environment variables with prefix OCR_ (e.g., OCR_BACKEND).

    Attributes:
        backend: OCR engine to use ('easyocr', 'tesseract', 'rapidocr').
        languages: List of language codes for OCR recognition.
        use_gpu: Enable GPU acceleration for OCR processing.
        confidence_threshold: Minimum confidence score for text detection (0.0 to 1.0).

    Example:
        >>> ocr = OCRConfig(backend="easyocr", languages=["en", "de"])
        >>> ocr.backend
        'easyocr'
    """

    model_config = SettingsConfigDict(
        env_prefix="OCR_",
        extra="ignore",
        validate_default=True,
    )

    backend: Annotated[
        Literal["easyocr", "tesseract", "rapidocr"],
        Field(
            default="easyocr",
            description="OCR engine backend to use for text recognition.",
            examples=["easyocr", "tesseract", "rapidocr"],
        ),
    ]

    languages: Annotated[
        List[str],
        Field(
            default_factory=lambda: ["en"],
            description="List of language codes for OCR recognition (ISO 639-1 or engine-specific).",
            examples=[["en"], ["en", "de", "fr"], ["eng", "deu"]],
            min_length=1,
        ),
    ]

    use_gpu: Annotated[
        bool,
        Field(
            default=True,
            description="Enable GPU acceleration for OCR processing when available.",
        ),
    ]

    confidence_threshold: Annotated[
        float,
        Field(
            default=0.5,
            description="Minimum confidence score for accepting detected text (0.0 to 1.0).",
            ge=0.0,
            le=1.0,
            examples=[0.3, 0.5, 0.7, 0.9],
        ),
    ]

    torch_backend: Annotated[
        Literal["torch", "onnxruntime"],
        Field(
            default="torch",
            description="Backend for RapidOCR inference engine (torch or onnxruntime).",
            examples=["torch", "onnxruntime"],
        ),
    ]

    @field_validator("languages")
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        """Validate and normalize language codes."""
        if not v:
            raise ValueError("At least one language must be specified.")

        # Normalize to lowercase
        return [lang.lower().strip() for lang in v if lang.strip()]

    @field_validator("confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence threshold is reasonable."""
        if v < 0.1:
            import warnings
            warnings.warn(
                f"Low confidence threshold ({v}) may result in noisy OCR output."
            )
        return v


# =============================================================================
# AIConfig - AI Enhancement Settings
# =============================================================================


class AIConfig(BaseSettings):
    """
    AI enhancement configuration for advanced document processing.

    Supports environment variables with prefix AI_ (e.g., AI_ENABLED).

    Attributes:
        enabled: Enable AI-powered document enhancement features.
        api_endpoint: Base URL for the AI model API service.
        model_name: Name of the AI model to use for processing.
        max_retries: Maximum number of retry attempts for failed API calls.

    Example:
        >>> ai = AIConfig(enabled=True, model_name="llama-3.2")
        >>> ai.api_endpoint
        'https://api.gradient.ai/api'
    """

    model_config = SettingsConfigDict(
        env_prefix="AI_",
        extra="ignore",
        validate_default=True,
    )

    enabled: Annotated[
        bool,
        Field(
            default=False,
            description="Enable AI-powered document enhancement features.",
        ),
    ]

    api_endpoint: Annotated[
        str,
        Field(
            default="https://api.gradient.ai/api",
            description="Base URL for the AI model API service.",
            examples=[
                "https://api.gradient.ai/api",
                "https://api.openai.com/v1",
                "http://localhost:11434/api",
            ],
        ),
    ]

    model_name: Annotated[
        str,
        Field(
            default="llama-3.1",
            description="Name of the AI model to use for document processing.",
            examples=["llama-3.1", "llama-3.2", "gpt-4o", "mistral-7b"],
        ),
    ]

    max_retries: Annotated[
        int,
        Field(
            default=3,
            description="Maximum number of retry attempts for failed API calls.",
            ge=0,
            le=10,
            examples=[1, 3, 5],
        ),
    ]

    @field_validator("api_endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Validate API endpoint URL format."""
        v = v.strip().rstrip("/")

        if not v.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid API endpoint '{v}'. Must start with 'http://' or 'https://'."
            )

        return v

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate and normalize model name."""
        v = v.strip()
        if not v:
            raise ValueError("Model name cannot be empty.")
        return v


# =============================================================================
# ProcessingConfig - Combined Configuration
# =============================================================================


class ProcessingConfig(BaseModel):
    """
    Complete processing configuration combining all sub-configurations.

    This is the main configuration class that aggregates all settings for
    the document conversion pipeline.

    Attributes:
        kaggle: Main Kaggle environment configuration.
        gpu: GPU-specific settings for hardware acceleration.
        ocr: OCR engine configuration.
        ai: AI enhancement settings.

    Example:
        >>> config = ProcessingConfig()
        >>> config.kaggle.input_dir
        PosixPath('/kaggle/working/input_pdfs')

        >>> config = ProcessingConfig(
        ...     kaggle=KaggleConfig(max_workers=4),
        ...     gpu=GPUConfig(device="cuda:0"),
        ... )
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_default=True,
        arbitrary_types_allowed=True,
    )

    kaggle: Annotated[
        KaggleConfig,
        Field(
            default_factory=KaggleConfig,
            description="Main Kaggle environment configuration.",
        ),
    ]

    gpu: Annotated[
        GPUConfig,
        Field(
            default_factory=GPUConfig,
            description="GPU-specific settings for hardware acceleration.",
        ),
    ]

    ocr: Annotated[
        OCRConfig,
        Field(
            default_factory=OCRConfig,
            description="OCR engine configuration.",
        ),
    ]

    ai: Annotated[
        AIConfig,
        Field(
            default_factory=AIConfig,
            description="AI enhancement settings.",
        ),
    ]

    @model_validator(mode="after")
    def sync_ai_settings(self) -> "ProcessingConfig":
        """Sync AI enabled state between kaggle and ai configs."""
        if self.kaggle.enable_ai and not self.ai.enabled:
            # If kaggle.enable_ai is True, ensure ai.enabled is also True
            object.__setattr__(self.ai, "enabled", True)
        return self

    @model_validator(mode="after")
    def validate_gpu_ocr_consistency(self) -> "ProcessingConfig":
        """Ensure GPU settings are consistent between GPU and OCR configs."""
        if self.ocr.use_gpu and self.gpu.device == "cpu":
            import warnings
            warnings.warn(
                "OCR GPU is enabled but GPU device is set to 'cpu'. "
                "OCR will fall back to CPU processing."
            )
        return self

    def to_dict(self) -> dict:
        """Export configuration to a dictionary (masks sensitive data)."""
        return {
            "kaggle": {
                "input_dir": str(self.kaggle.input_dir),
                "output_dir": str(self.kaggle.output_dir),
                "max_workers": self.kaggle.max_workers,
                "enable_ai": self.kaggle.enable_ai,
                "create_zip": self.kaggle.create_zip,
                "model_api_key": "***" if self.kaggle.model_api_key else None,
            },
            "gpu": {
                "device": self.gpu.device,
                "num_gpus": self.gpu.num_gpus,
                "batch_size": self.gpu.batch_size,
                "use_flash_attention": self.gpu.use_flash_attention,
                "cuda_memory_fraction": self.gpu.cuda_memory_fraction,
            },
            "ocr": {
                "backend": self.ocr.backend,
                "languages": self.ocr.languages,
                "use_gpu": self.ocr.use_gpu,
                "confidence_threshold": self.ocr.confidence_threshold,
            },
            "ai": {
                "enabled": self.ai.enabled,
                "api_endpoint": self.ai.api_endpoint,
                "model_name": self.ai.model_name,
                "max_retries": self.ai.max_retries,
            },
        }


# =============================================================================
# Singleton Settings Factory
# =============================================================================


@lru_cache()
def get_settings() -> ProcessingConfig:
    """
    Get cached singleton instance of ProcessingConfig.

    The configuration is loaded once from environment variables and cached
    for subsequent calls. Use clear_settings() to reset the cache.

    Returns:
        ProcessingConfig: Cached configuration instance.

    Example:
        >>> config = get_settings()
        >>> config.kaggle.output_dir
        PosixPath('/kaggle/working/output')
    """
    return ProcessingConfig()


def clear_settings() -> None:
    """
    Clear the cached settings instance.

    Call this function to force reloading configuration from environment
    variables on the next call to get_settings().
    """
    get_settings.cache_clear()


# =============================================================================
# Module-level convenience exports
# =============================================================================


__all__ = [
    # Main configs
    "KaggleConfig",
    "GPUConfig",
    "OCRConfig",
    "AIConfig",
    "ProcessingConfig",
    # Enums
    "AcceleratorDevice",
    "OCRBackend",
    # Factory functions
    "get_settings",
    "clear_settings",
]
