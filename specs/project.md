# Document Processing & RAG Pipeline Project

> **Governance**: This project is governed by the principles defined in [`specs/memory/constitution.md`](memory/constitution.md). All development practices, architectural decisions, and code contributions must comply with the constitution's core principles: Reliability First, Resource Responsibility, Configuration Over Code, Observable Operations, and Modular Design.

## Purpose
Automated document processing system that converts various document formats (PDFs, images, tables) into structured text, enhances them using gradient-based techniques, and loads them into a RAG (Retrieval Augmented Generation) pipeline. The system leverages GPU acceleration for performance-critical operations and provides parallel processing capabilities for handling large document batches.

## Tech Stack
- Python 3.8+
- PyTorch (GPU acceleration)
- LangChain (RAG pipeline)
- OpenCV / PIL (Image processing)
- pandas (Table processing)
- CUDA (GPU management)
- pytest (Testing framework)

## Project Conventions

### Code Style
- File naming: snake_case for all Python modules
- Class naming: PascalCase (e.g., `GradientEnhancer`, `ImageProcessor`)
- Function naming: snake_case with descriptive verbs (e.g., `process_image`, `convert_table`)
- Indentation: 4 spaces, no tabs
- Line length: Max 100 characters (PEP 8 compliant)
- Type hints: Required for all public functions and methods
- Docstrings: Google-style docstrings for all classes and functions

### Architecture Patterns
- Pipeline-based processing: Sequential transformation stages in [`core/pipeline.py`](core/pipeline.py)
- Singleton GPU manager: Centralized GPU resource allocation via [`gpu/manager.py`](gpu/manager.py)
- Configuration-driven: All settings externalized in [`config/settings.py`](config/settings.py)
- Modular processors: Each document type has dedicated processor (image, table, gradient)
- Parallel execution: Multi-processing support via [`core/parallel.py`](core/parallel.py)
- RAG integration: Document loading and retrieval in [`core/rag_pipeline.py`](core/rag_pipeline.py)

### Testing Strategy
- Unit tests for each core module in [`tests/`](tests/) directory
- Phase-based testing: [`test_phase1.py`](test_phase1.py) for incremental validation
- GPU mock testing: Tests must run without GPU hardware dependencies
- Integration tests: End-to-end pipeline validation
- Coverage target: 80% minimum for core modules
- Test naming: `test_<module>_<function>_<scenario>`

### Git Workflow
- Branch naming: `feature/<name>`, `fix/<issue>`, `refactor/<component>`
- Commit format: `<type>: <description>` (e.g., `feat: add gradient enhancement`, `fix: GPU memory leak`)
- Merge strategy: Pull requests with code review required
- Tag releases: Semantic versioning (v1.0.0)
- Requirements split: [`requirements.txt`](requirements.txt) for base, [`requirements_gpu.txt`](requirements_gpu.txt) for GPU features

## Domain Context
- **Converter**: Module that transforms document formats ([`core/converter.py`](core/converter.py))
- **Gradient Client**: Interface for gradient-based model operations ([`core/gradient_client.py`](core/gradient_client.py))
- **Gradient Enhancer**: Quality improvement processor ([`core/gradient_enhancer.py`](core/gradient_enhancer.py))
- **Image Processor**: OCR and image document handler ([`core/image_processor.py`](core/image_processor.py))
- **Table Processor**: Structured data extraction ([`core/table_processor.py`](core/table_processor.py))
- **RAG Pipeline**: Retrieval augmented generation integration ([`core/rag_pipeline.py`](core/rag_pipeline.py))
- **GPU Manager**: Resource allocation and monitoring ([`gpu_manager.py`](gpu_manager.py), [`gpu/manager.py`](gpu/manager.py))
- **LangChain Loader**: Document loading utilities ([`core/langchain_loader.py`](core/langchain_loader.py))

## Important Constraints
- GPU availability must be checked before GPU-dependent operations
- Memory management critical: Large documents must be processed in chunks
- All GPU resources must be explicitly released after use
- Configuration validation required at startup via [`config_models.py`](config_models.py)
- No hardcoded file paths: Use configuration system
- Batch processing must support resume from failure
- Thread-safe operations required for parallel processing
- All external API calls must have timeout and retry logic

## External Dependencies
- CUDA Toolkit 11.0+ for GPU operations
- PyTorch with CUDA support (see [`requirements_gpu.txt`](requirements_gpu.txt))
- LangChain framework for RAG capabilities
- OpenAI API (optional) for gradient client operations
- File system access for document I/O
- Sufficient GPU memory (4GB+ recommended) for batch processing
