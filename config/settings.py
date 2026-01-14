"""
Configuration settings for PDF to Markdown conversion pipeline.

This module defines the master configuration classes with Pydantic v2
for the integrated conversion pipeline (Docling + LangChain + Gradient).

Phase 1 Implementation: Complete Pydantic configuration with validators
for all framework integration settings.

Classes:
    GradientConfig: Gradient AI SDK settings
    GPUConfig: GPU acceleration and batch size settings
    OCRConfig: OCR engine configuration
    LangChainConfig: LangChain document loader settings
    ConversionConfig: Master configuration aggregating all settings

Usage:
    >>> from config.settings import ConversionConfig
    >>> config = ConversionConfig()
    >>> print(config.gradient.enabled)
    True
    >>> print(config.gpu.device)
    'cuda'
"""

from pathlib import Path
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging

logger = logging.getLogger(__name__)


class GradientConfig(BaseSettings):
    """
    Configuration for Gradient AI SDK integration.

    Settings for interacting with Gradient Public API for
    AI-powered table and text enhancement.

    Attributes:
        enabled: Enable AI-powered enhancements (default: True)
        model_access_key: Gradient model access key from environment
        default_model: Default LLM model to use
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum tokens in response (1-4096)
        max_retries: Number of retries on API errors
        timeout: Request timeout in seconds
    """

    model_config = SettingsConfigDict(
        env_prefix="GRADIENT_",
        case_sensitive=False
    )

    enabled: bool = Field(
        default=True,
        description="Enable AI-powered enhancements"
    )

    model_access_key: Optional[SecretStr] = Field(
        default=None,
        description="Gradient model access key (env: GRADIENT_MODEL_ACCESS_KEY)"
    )

    default_model: str = Field(
        default="llama3.3-70b-instruct",
        description="Default LLM model for enhancement"
    )

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for generation"
    )

    max_tokens: int = Field(
        default=1000,
        ge=1,
        le=4096,
        description="Maximum tokens in response"
    )

    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Number of retries on API errors"
    )

    timeout: float = Field(
        default=60.0,
        ge=1.0,
        le=300.0,
        description="Request timeout in seconds"
    )

    @field_validator('model_access_key', mode='before')
    @classmethod
    def load_from_env(cls, v):
        """Auto-load API key from environment if not provided."""
        if v is None:
            env_key = os.environ.get('GRADIENT_MODEL_ACCESS_KEY')
            if env_key:
                return SecretStr(env_key)
        return v

    @property
    def is_configured(self) -> bool:
        """Check if Gradient is properly configured with API key."""
        return self.model_access_key is not None


class GPUConfig(BaseSettings):
    """
    GPU acceleration and batch size configuration.

    Settings for CUDA device selection, multi-GPU support,
    and batch sizes optimized for T4x2 GPUs (16GB VRAM each).

    Attributes:
        device: Device to use ('auto', 'cuda', or 'cpu')
        num_gpus: Number of GPUs available (default: 2 for T4x2)
        cuda_visible_devices: CUDA device IDs to use
        num_threads: Number of CPU threads
        ocr_batch_size: Batch size for OCR processing
        layout_batch_size: Batch size for layout detection
        table_batch_size: Batch size for table extraction
        enable_parallel: Enable parallel processing for multiple PDFs
    """

    model_config = SettingsConfigDict(
        env_prefix="GPU_",
        case_sensitive=False
    )

    device: Literal["auto", "cuda", "cpu"] = Field(
        default="cuda",
        description="Device to use for acceleration"
    )

    num_gpus: int = Field(
        default=2,
        ge=1,
        le=8,
        description="Number of GPUs available (T4x2)"
    )

    cuda_visible_devices: Optional[str] = Field(
        default="0,1",
        description="CUDA device IDs (comma-separated)"
    )

    num_threads: int = Field(
        default=8,
        ge=1,
        le=32,
        description="Number of CPU threads"
    )

    ocr_batch_size: int = Field(
        default=32,
        ge=1,
        le=128,
        description="Batch size for OCR processing"
    )

    layout_batch_size: int = Field(
        default=64,
        ge=1,
        le=256,
        description="Batch size for layout detection"
    )

    table_batch_size: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Batch size for table extraction"
    )

    enable_parallel: bool = Field(
        default=True,
        description="Enable parallel processing for multiple PDFs"
    )

    @model_validator(mode='after')
    def set_cuda_env_vars(self):
        """Set CUDA_VISIBLE_DEVICES environment variable."""
        if self.device == "cuda" and self.cuda_visible_devices:
            os.environ['CUDA_VISIBLE_DEVICES'] = self.cuda_visible_devices
            logger.info(f"Set CUDA_VISIBLE_DEVICES={self.cuda_visible_devices}")
        return self


class OCRConfig(BaseSettings):
    """
    OCR engine configuration.

    Settings for optical character recognition with GPU acceleration.

    Attributes:
        enabled: Enable OCR for scanned PDFs
        backend: OCR backend to use ('torch' or 'onnxruntime')
        languages: List of language codes for OCR
        use_gpu: Use GPU acceleration for OCR
    """

    model_config = SettingsConfigDict(
        env_prefix="OCR_",
        case_sensitive=False
    )

    enabled: bool = Field(
        default=True,
        description="Enable OCR processing"
    )

    backend: Literal["torch", "onnxruntime"] = Field(
        default="torch",
        description="OCR backend engine"
    )

    languages: List[str] = Field(
        default=["en"],
        description="OCR language codes"
    )

    use_gpu: bool = Field(
        default=True,
        description="Use GPU acceleration for OCR"
    )


class LangChainConfig(BaseSettings):
    """
    LangChain document loader configuration.

    Settings for LangChain-Docling integration, document chunking,
    and export type selection.

    Attributes:
        enabled: Enable LangChain DoclingLoader (default: True)
        export_type: Export format ('chunks' or 'markdown')
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks in characters
        embedding_model: Model for embeddings (if needed)
    """

    model_config = SettingsConfigDict(
        env_prefix="LANGCHAIN_",
        case_sensitive=False
    )

    enabled: bool = Field(
        default=True,
        description="Enable LangChain DoclingLoader"
    )

    export_type: Literal["chunks", "markdown"] = Field(
        default="chunks",
        description="Export format for documents"
    )

    chunk_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum chunk size in characters"
    )

    chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=500,
        description="Overlap between chunks in characters"
    )

    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model for vector search"
    )


class ConversionConfig(BaseModel):
    """
    Master configuration for PDF to Markdown conversion pipeline.

    Aggregates all configuration aspects including Gradient AI, GPU settings,
    OCR options, LangChain integration, and output formatting.

    This configuration enables the integrated architecture where:
    - Pydantic validates all settings
    - GPU Manager uses gpu config
    - Docling uses gpu + ocr config
    - LangChain uses langchain config with Docling converter
    - Gradient AI enhances output based on gradient config

    Attributes:
        gradient: Gradient AI SDK settings
        gpu: GPU acceleration settings
        ocr: OCR engine settings
        langchain: LangChain document loader settings
        output_dir: Output directory for converted files
        create_pdf_folder: Create individual folder per PDF
        include_metadata: Include metadata.json in output
        image_scale: Scaling factor for image resolution
        min_image_size: Minimum size threshold for images
        table_mode: Table extraction mode ('accurate' or 'fast')
        export_csv: Export tables as CSV files
        enhance_tables: Enable AI enhancement for tables
        enhance_text: Enable AI enhancement for text
        fix_ocr_errors: Enable AI OCR error correction

    Usage:
        >>> # Default configuration (all AI features enabled)
        >>> config = ConversionConfig()
        >>> config.gradient.enabled
        True
        >>> config.gpu.device
        'cuda'

        >>> # Custom configuration
        >>> config = ConversionConfig(
        ...     gradient=GradientConfig(enabled=False),
        ...     gpu=GPUConfig(device='cpu')
        ... )
    """

    gradient: GradientConfig = Field(
        default_factory=GradientConfig,
        description="Gradient AI SDK settings"
    )

    gpu: GPUConfig = Field(
        default_factory=GPUConfig,
        description="GPU acceleration settings"
    )

    ocr: OCRConfig = Field(
        default_factory=OCRConfig,
        description="OCR engine settings"
    )

    langchain: LangChainConfig = Field(
        default_factory=LangChainConfig,
        description="LangChain document loader settings"
    )

    output_dir: Path = Field(
        default=Path("/kaggle/working/output"),
        description="Output directory for converted files"
    )

    create_pdf_folder: bool = Field(
        default=True,
        description="Create individual folder per PDF"
    )

    include_metadata: bool = Field(
        default=True,
        description="Include metadata.json in output"
    )

    image_scale: float = Field(
        default=2.0,
        ge=1.0,
        le=4.0,
        description="Image scaling factor (2.0 = 144 DPI)"
    )

    min_image_size: int = Field(
        default=50,
        ge=10,
        le=1000,
        description="Minimum image size threshold in pixels"
    )

    table_mode: Literal["accurate", "fast"] = Field(
        default="accurate",
        description="Table extraction mode"
    )

    export_csv: bool = Field(
        default=True,
        description="Export tables as CSV files"
    )

    enhance_tables: bool = Field(
        default=True,
        description="Enable AI enhancement for tables"
    )

    enhance_text: bool = Field(
        default=True,
        description="Enable AI enhancement for text"
    )

    fix_ocr_errors: bool = Field(
        default=True,
        description="Enable AI OCR error correction"
    )

    @model_validator(mode='after')
    def validate_ai_settings(self):
        """Warn if AI features enabled but Gradient not configured."""
        if any([self.enhance_tables, self.enhance_text, self.fix_ocr_errors]):
            if not self.gradient.enabled:
                logger.warning(
                    "AI enhancement features enabled but gradient.enabled=False. "
                    "Set gradient.enabled=True to use AI features."
                )
            elif not self.gradient.is_configured:
                logger.warning(
                    "AI enhancement features enabled but GRADIENT_MODEL_ACCESS_KEY not set. "
                    "Set environment variable to enable AI enhancement."
                )
        return self

    # Backward compatibility properties
    @property
    def device(self) -> str:
        """Alias for gpu.device."""
        return self.gpu.device

    @property
    def ocr_enabled(self) -> bool:
        """Alias for ocr.enabled."""
        return self.ocr.enabled

    @property
    def ocr_backend(self) -> str:
        """Alias for ocr.backend."""
        return self.ocr.backend
