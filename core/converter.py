"""
Main PDF to Markdown Conversion Orchestrator

This module provides the primary conversion functions for transforming PDFs
into high-quality Markdown with correct Docling API usage.

Key Features:
- GPU-accelerated PDF conversion
- Correct use of doc.iterate_items() API
- Table extraction to CSV + inline markdown
- Image extraction with base64 encoding
- Comprehensive error handling
- Progress tracking and metadata generation

Author: Kaggle Pipeline Implementation
Date: 2026-01-14
"""

import logging
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
import time

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
# CRITICAL: All pipeline options in ONE import!
from docling.datamodel.pipeline_options import (
    ThreadedPdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    RapidOcrOptions
)
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
from docling.pipeline.threaded_standard_pdf_pipeline import ThreadedStandardPdfPipeline
from docling_core.types.doc import (
    DoclingDocument,
    TableItem,
    TextItem,
    SectionHeaderItem,
    PictureItem,
    NodeItem
)

from .table_processor import extract_tables, TableResult
from .image_processor import (
    extract_images,
    generate_image_references,
    ImageResult,
    create_image_placeholder
)

try:
    from .gradient_client import GradientLLMClient
    GRADIENT_AVAILABLE = True
except ImportError:
    GRADIENT_AVAILABLE = False

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import ConversionConfig
from gpu.manager import get_accelerator_device, get_optimal_batch_sizes

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a single PDF conversion operation.

    Attributes:
        source_pdf: Path to the source PDF file
        output_folder: Path to the output folder created
        markdown_file: Path to the generated markdown file
        table_files: List of paths to extracted CSV files
        num_pages: Number of pages in the PDF
        num_tables: Number of tables extracted
        num_images: Number of images extracted
        success: Whether the conversion succeeded
        error_message: Error message if conversion failed
        duration_seconds: Time taken for conversion
        output_path: Path to the markdown file (alias for backward compatibility)
    """
    source_pdf: Path
    output_folder: Path
    markdown_file: Path
    table_files: List[Path]
    num_pages: int
    num_tables: int
    num_images: int
    success: bool
    error_message: Optional[str] = None
    duration_seconds: float = 0.0

    @property
    def output_path(self) -> Path:
        """Alias for markdown_file for backward compatibility."""
        return self.markdown_file


def enhance_content_with_ai(
    content: str,
    content_type: str,
    config: ConversionConfig
) -> str:
    """Enhance content using Gradient AI."""
    if not GRADIENT_AVAILABLE:
        return content

    if not config.gradient.enabled:
        return content

    if not config.gradient.model_access_key:
        logger.warning("Gradient AI enabled but no API key provided")
        return content

    try:
        client = GradientLLMClient(
            access_key=config.gradient.model_access_key.get_secret_value()
        )

        prompts = {
            'table': "Clean and format this table data. Fix any OCR errors:\n",
            'text': "Clean and correct any OCR errors in this text:\n"
        }

        enhanced = client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a document processing assistant."},
                {"role": "user", "content": prompts.get(content_type, '') + content}
            ],
            model=config.gradient.default_model,
            temperature=config.gradient.temperature,
            max_tokens=config.gradient.max_tokens
        )

        return enhanced
    except Exception as e:
        logger.warning(f"AI enhancement failed: {e}")
        return content


def create_docling_converter(config: ConversionConfig) -> DocumentConverter:
    """Create a DocumentConverter with GPU acceleration and OCR support.

    Configures the converter per MASTER_CHECKLIST Phase 3 specifications:
    - GPU acceleration with optimal batch sizes
    - RapidOCR with torch backend and language support
    - Table structure extraction (accurate mode, cell matching enabled)
    - Page and picture image extraction at 2x scale (144 DPI)

    Args:
        config: ConversionConfig with GPU, OCR, and output settings

    Returns:
        Configured DocumentConverter instance

    Raises:
        RuntimeError: If converter creation fails

    Reference:
        MASTER_CHECKLIST.md Phase 3, Task 3.1 - create_docling_converter function
    """
    try:
        logger.info("Creating DocumentConverter with GPU acceleration")

        # Get GPU configuration
        accelerator_device = get_accelerator_device(config.gpu.device)
        batch_sizes = get_optimal_batch_sizes(16.0)  # T4 16GB: ocr=32, layout=64, table=4

        # Configure accelerator options (default 8 threads optimal for Kaggle T4)
        accelerator_options = AcceleratorOptions(
            num_threads=8,  # Optimal for Kaggle T4 x2
            device=accelerator_device
        )

        # Configure OCR with RapidOCR
        # CRITICAL: Only 'backend' parameter accepted, no 'use_gpu'
        # GPU usage controlled by accelerator_options.device
        ocr_options = RapidOcrOptions(
            backend=config.ocr.torch_backend  # "torch" or "onnxruntime"
        )

        # Configure table extraction (accurate mode with cell matching)
        table_structure_options = TableStructureOptions(
            do_cell_matching=True,  # Enable for better table structure
            mode=TableFormerMode.ACCURATE  # Highest quality
        )

        # Configure pipeline options with all features enabled
        # CRITICAL: Apply batch sizes for optimal T4 GPU performance
        pipeline_options = ThreadedPdfPipelineOptions(
            do_ocr=True,
            do_table_structure=True,
            table_structure_options=table_structure_options,
            ocr_options=ocr_options,
            accelerator_options=accelerator_options,
            images_scale=config.image_scale,  # 2.0 = 144 DPI
            generate_page_images=True,
            generate_picture_images=True,
            # GPU batch sizes for T4 16GB (optimal for Kaggle T4x2)
            ocr_batch_size=batch_sizes['ocr'],        # 32 for T4 16GB
            layout_batch_size=batch_sizes['layout'],  # 64 for T4 16GB
            table_batch_size=batch_sizes['table']     # 4 for T4 16GB
        )

        # Create converter with configured pipeline
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=ThreadedStandardPdfPipeline,
                    pipeline_options=pipeline_options
                )
            }
        )

        logger.info(f"DocumentConverter created successfully")
        logger.info(f"  Device: {accelerator_device}")
        logger.info(f"  OCR Backend: {config.ocr.torch_backend}")
        logger.info(f"  Batch Sizes: OCR={batch_sizes['ocr']}, Layout={batch_sizes['layout']}, Table={batch_sizes['table']}")
        logger.info(f"  Image Scale: {config.image_scale}x")

        return converter

    except Exception as e:
        logger.error(f"Failed to create DocumentConverter: {e}")
        raise RuntimeError(f"Converter creation failed: {e}")


def generate_yaml_frontmatter(metadata: Dict[str, Any]) -> str:
    """Generate YAML frontmatter block for markdown file.

    Args:
        metadata: Dictionary of metadata key-value pairs

    Returns:
        YAML frontmatter string wrapped in --- delimiters

    Example:
        >>> metadata = {"title": "Document", "pages": 10}
        >>> print(generate_yaml_frontmatter(metadata))
        ---
        title: Document
        pages: 10
        ---
    """
    lines = ["---"]
    for key, value in metadata.items():
        if isinstance(value, str):
            # Escape special characters and quote strings
            value = value.replace('"', '\\"')
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")  # Blank line after frontmatter
    return "\n".join(lines)


def assemble_markdown(
    doc: DoclingDocument,
    tables: List[TableResult],
    images: List[ImageResult],
    config: ConversionConfig
) -> str:
    """Assemble complete markdown from DoclingDocument and extracted resources.

    CRITICAL: Uses doc.iterate_items() API correctly.

    Process:
    1. Generate YAML frontmatter with metadata
    2. Iterate through document items using doc.iterate_items()
    3. Handle each item type:
       - SectionHeaderItem: Format as markdown header
       - TextItem: Add as paragraph
       - TableItem: Insert pre-rendered markdown from tables list
       - PictureItem: Create placeholder for later reference
    4. Append image references block at end

    Args:
        doc: DoclingDocument from conversion
        tables: List of extracted TableResult objects
        images: List of extracted ImageResult objects
        config: ConversionConfig for formatting options

    Returns:
        Complete markdown string with frontmatter, content, and image references
    """
    markdown_parts = []

    # Generate metadata
    metadata = {
        "title": doc.name or "Untitled Document",
        "source": str(doc.origin.filename) if doc.origin else "Unknown",
        "pages": len(list(doc.pages)) if hasattr(doc, 'pages') else 0,
        "tables": len(tables),
        "images": len(images),
        "conversion_date": datetime.now().isoformat()
    }

    # Add YAML frontmatter
    markdown_parts.append(generate_yaml_frontmatter(metadata))

    # Track table and image indices for matching
    table_index = 0
    image_index = 0

    # CRITICAL: Use doc.iterate_items() - returns (item, level) tuples
    logger.info("Assembling markdown using doc.iterate_items()")

    try:
        for item, level in doc.iterate_items():
            # Handle section headers
            if isinstance(item, SectionHeaderItem):
                header_level = min(level + 1, 6)  # H1-H6
                header_prefix = "#" * header_level
                markdown_parts.append(f"\n{header_prefix} {item.text}\n")

            # Handle text items
            elif isinstance(item, TextItem):
                if item.text and item.text.strip():
                    markdown_parts.append(f"{item.text}\n")

            # Handle tables
            elif isinstance(item, TableItem):
                if table_index < len(tables):
                    table_result = tables[table_index]
                    markdown_content = table_result.markdown

                    # AI Enhancement
                    if config.gradient and config.gradient.enabled:
                         markdown_content = enhance_content_with_ai(markdown_content, "table", config)

                    markdown_parts.append(f"\n{markdown_content}\n")
                    # CSV link is already included in table_result.markdown
                    table_index += 1
                else:
                    logger.warning(f"Table item found but no matching TableResult")

            # Handle pictures
            elif isinstance(item, PictureItem):
                if image_index < len(images):
                    image_result = images[image_index]
                    placeholder = create_image_placeholder(
                        image_result.image_id,
                        image_result.alt_text
                    )
                    markdown_parts.append(f"\n{placeholder}\n")
                    image_index += 1
                else:
                    logger.warning(f"Picture item found but no matching ImageResult")

    except Exception as e:
        logger.error(f"Error during markdown assembly: {e}")
        markdown_parts.append(f"\n\n*Error assembling document: {e}*\n")

    # Append image references block at end
    if images:
        image_references = generate_image_references(images)
        markdown_parts.append("\n")
        markdown_parts.append(image_references)

    return "".join(markdown_parts)


def convert_pdf(
    pdf_path: Path,
    output_base_dir: Path,
    config: ConversionConfig,
    converter: Optional[DocumentConverter] = None
) -> ConversionResult:
    """Convert a single PDF to Markdown with tables and images.

    Workflow:
    1. Create output folder (pdf_name/)
    2. Create DocumentConverter if not provided
    3. Convert PDF to DoclingDocument
    4. Extract tables to CSV files
    5. Extract images as base64
    6. Assemble markdown with all content
    7. Write markdown file
    8. Write metadata.json
    9. Return ConversionResult

    Args:
        pdf_path: Path to source PDF file
        output_base_dir: Base directory for all outputs
        config: ConversionConfig with all settings
        converter: Optional pre-configured DocumentConverter (reuse for batch)

    Returns:
        ConversionResult with success status and file paths
    """
    start_time = time.time()
    pdf_name = pdf_path.stem
    output_folder = output_base_dir / pdf_name

    logger.info(f"Converting PDF: {pdf_path.name}")

    try:
        # Create output folder
        output_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output folder: {output_folder}")

        # Create or use provided converter
        if converter is None:
            converter = create_docling_converter(config)

        # Convert PDF to DoclingDocument
        logger.info("Starting PDF conversion")
        conversion_result = converter.convert(str(pdf_path))
        doc = conversion_result.document

        # Count pages
        num_pages = len(list(doc.pages)) if hasattr(doc, 'pages') else 0
        logger.info(f"Converted {num_pages} pages")

        # Extract tables
        logger.info("Extracting tables")
        tables = extract_tables(doc, output_folder)
        num_tables = len(tables)
        table_files = [t.csv_path for t in tables]
        logger.info(f"Extracted {num_tables} tables")

        # Extract images
        logger.info("Extracting images")
        images = extract_images(doc, config)
        num_images = len(images)
        logger.info(f"Extracted {num_images} images")

        # Assemble markdown
        logger.info("Assembling markdown")
        markdown_content = assemble_markdown(doc, tables, images, config)

        # Write markdown file
        markdown_file = output_folder / f"{pdf_name}.md"
        markdown_file.write_text(markdown_content, encoding='utf-8')
        logger.info(f"Wrote markdown: {markdown_file}")

        # Write metadata
        metadata = {
            "source_pdf": str(pdf_path),
            "conversion_date": datetime.now().isoformat(),
            "page_count": num_pages,
            "table_count": num_tables,
            "image_count": num_images,
            "markdown_file": markdown_file.name,
            "table_files": [f.name for f in table_files],
            "config": {
                "gpu_device": config.gpu.device,
                "ocr_enabled": config.ocr.use_gpu,
                "ocr_backend": config.ocr.backend,
                "image_scale": config.image_scale
            }
        }

        metadata_file = output_folder / "metadata.json"
        metadata_file.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        logger.info(f"Wrote metadata: {metadata_file}")

        duration = time.time() - start_time

        return ConversionResult(
            source_pdf=pdf_path,
            output_folder=output_folder,
            markdown_file=markdown_file,
            table_files=table_files,
            num_pages=num_pages,
            num_tables=num_tables,
            num_images=num_images,
            success=True,
            duration_seconds=duration
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Conversion failed for {pdf_path.name}: {e}")

        return ConversionResult(
            source_pdf=pdf_path,
            output_folder=output_folder,
            markdown_file=Path(),
            table_files=[],
            num_pages=0,
            num_tables=0,
            num_images=0,
            success=False,
            error_message=str(e),
            duration_seconds=duration
        )


def convert_batch(
    pdf_paths: List[Path],
    output_base_dir: Path,
    config: ConversionConfig,
    progress_callback: Optional[Callable[[int, int, ConversionResult], None]] = None
) -> List[ConversionResult]:
    """Convert multiple PDFs in batch mode.

    Creates a single DocumentConverter and reuses it for all PDFs
    to avoid repeated GPU initialization overhead.

    Args:
        pdf_paths: List of paths to PDF files
        output_base_dir: Base directory for all outputs
        config: ConversionConfig with all settings
        progress_callback: Optional callback(current, total, result) for progress tracking

    Returns:
        List of ConversionResult objects, one per PDF

    Example:
        >>> def on_progress(current, total, result):
        ...     print(f"[{current}/{total}] {result.source_pdf.name}: {'✓' if result.success else '✗'}")
        >>> results = convert_batch(pdf_list, output_dir, config, on_progress)
    """
    logger.info(f"Starting batch conversion of {len(pdf_paths)} PDFs")

    results = []
    converter = None

    try:
        # Create converter once for all PDFs
        converter = create_docling_converter(config)

        for idx, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Processing PDF {idx}/{len(pdf_paths)}: {pdf_path.name}")

            # Convert single PDF
            result = convert_pdf(pdf_path, output_base_dir, config, converter)
            results.append(result)

            # Call progress callback if provided
            if progress_callback:
                try:
                    progress_callback(idx, len(pdf_paths), result)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_duration = sum(r.duration_seconds for r in results)

        logger.info(f"Batch conversion complete: {successful} succeeded, {failed} failed")
        logger.info(f"Total time: {total_duration:.2f}s, Average: {total_duration/len(results):.2f}s per PDF")

    except Exception as e:
        logger.error(f"Batch conversion error: {e}")

    return results
