# Core processing modules for PDF to Markdown conversion
"""
Core processing modules:
- converter.py: Main document conversion orchestrator
- table_processor.py: Table extraction and CSV export
- image_processor.py: Image extraction and base64 encoding
- langchain_loader.py: LangChain DoclingLoader integration
- rag_pipeline.py: RAG pipeline with Milvus vector store
- gradient_client.py: Gradient SDK client for AI enhancement
- parallel.py: Multi-GPU parallel processing
"""

# Lazy imports to avoid circular dependencies
__all__ = [
    # Converter
    "convert_pdf",
    "convert_batch",
    "ConversionResult",
    "enhance_content_with_ai",
    # Table processing
    "extract_tables",
    "TableResult",
    # Image processing
    "extract_images",
    "ImageResult",
    # LangChain integration
    "create_langchain_loader",
    "load_documents_for_rag",
    "lazy_load_documents_for_rag",
    "CustomMetaExtractor",
    # RAG pipeline
    "DocumentRAGPipeline",
    # Gradient SDK
    "GradientLLMClient",
    "GRADIENT_SDK_AVAILABLE",
    # Parallel processing
    "batch_convert_parallel",
]

def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name in ("convert_pdf", "convert_batch", "ConversionResult", "enhance_content_with_ai"):
        from .converter import convert_pdf, convert_batch, ConversionResult, enhance_content_with_ai
        return locals()[name]
    elif name in ("extract_tables", "TableResult"):
        from .table_processor import extract_tables, TableResult
        return locals()[name]
    elif name in ("extract_images", "ImageResult"):
        from .image_processor import extract_images, ImageResult
        return locals()[name]
    elif name in ("create_langchain_loader", "load_documents_for_rag", "lazy_load_documents_for_rag", "CustomMetaExtractor"):
        from .langchain_loader import (
            create_langchain_loader,
            load_documents_for_rag,
            lazy_load_documents_for_rag,
            CustomMetaExtractor
        )
        return locals()[name]
    elif name == "DocumentRAGPipeline":
        from .rag_pipeline import DocumentRAGPipeline
        return DocumentRAGPipeline
    elif name in ("GradientLLMClient", "GRADIENT_SDK_AVAILABLE"):
        from .gradient_client import GradientLLMClient, GRADIENT_SDK_AVAILABLE
        return locals()[name]
    elif name == "batch_convert_parallel":
        from .parallel import batch_convert_parallel
        return batch_convert_parallel
    else:
        raise AttributeError(f"module 'core' has no attribute '{name}'")
