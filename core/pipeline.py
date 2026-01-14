"""Integrated PDF to Markdown Pipeline.

Combines all frameworks in unified conversion flow:
GPU setup, Docling conversion, LangChain DoclingLoader, and
Gradient AI enhancement into a single conversion flow.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from langchain_core.documents import Document

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    ThreadedPdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode,
    RapidOcrOptions,
)
from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.pipeline.threaded_standard_pdf_pipeline import ThreadedStandardPdfPipeline

from config.settings import ConversionConfig
from gpu.manager import (
    setup_gpu_environment,
    get_accelerator_device,
    get_optimal_batch_sizes,
)
from .gradient_enhancer import GradientEnhancer

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of PDF conversion operation."""

    source_pdf: Path
    output_folder: Path
    markdown_file: Optional[Path]
    table_files: List[Path] = field(default_factory=list)
    num_pages: int = 0
    num_tables: int = 0
    num_images: int = 0
    num_chunks: int = 0
    ai_enhancements: int = 0
    success: bool = False
    error_message: Optional[str] = None
    duration_seconds: float = 0.0

    @property
    def output_path(self) -> Optional[Path]:
        """Alias for markdown_file for backward compatibility."""
        return self.markdown_file


class IntegratedPipeline:
    """Integrated PDF to Markdown conversion pipeline.

    Orchestrates:
    1. GPU acceleration setup
    2. LangChain DoclingLoader for document processing
    3. Gradient AI enhancement
    4. Markdown generation with tables and images
    """

    def __init__(self, config: Optional[ConversionConfig] = None):
        """Initialize the integrated pipeline.

        Args:
            config: Conversion configuration (defaults to ConversionConfig())
        """
        self.config = config or ConversionConfig()
        logger.info("Initializing IntegratedPipeline with config: %s", self.config)

        # Setup GPU environment
        setup_gpu_environment(self.config.gpu)
        self.accelerator_device = get_accelerator_device(self.config.gpu.device)
        logger.info("GPU acceleration device: %s", self.accelerator_device)

        # Determine optimal batch sizes for the target hardware
        self.batch_sizes = get_optimal_batch_sizes(16.0)

        # Initialize Gradient enhancer if enabled
        self.enhancer: Optional[GradientEnhancer] = None
        if self.config.gradient.enabled:
            try:
                self.enhancer = GradientEnhancer(self.config.gradient)
                if not self.enhancer.is_available:
                    logger.warning("Gradient requested but unavailable - skipping AI enhancement")
                else:
                    logger.info("Gradient enhancer initialized")
            except Exception as e:
                logger.warning("Failed to initialize Gradient enhancer: %s", e)
                self.enhancer = None

        # Configure DocumentConverter with GPU and OCR options
        pipeline_options = ThreadedPdfPipelineOptions(
            do_ocr=self.config.ocr.enabled,
            do_table_structure=True,
            table_structure_options=TableStructureOptions(
                mode=TableFormerMode.ACCURATE if self.config.table_mode == "accurate" else TableFormerMode.FAST
            ),
            ocr_options=RapidOcrOptions(backend=self.config.ocr.backend),
        )

        if hasattr(pipeline_options, "images_scale"):
            pipeline_options.images_scale = self.config.image_scale

        # Set batch sizes using GPU manager recommendations
        if hasattr(pipeline_options, "ocr_batch_size"):
            pipeline_options.ocr_batch_size = self.batch_sizes.get("ocr", self.config.gpu.ocr_batch_size)
        if hasattr(pipeline_options, "table_batch_size"):
            pipeline_options.table_batch_size = self.batch_sizes.get("table", self.config.gpu.table_batch_size)
        if hasattr(pipeline_options, "layout_batch_size"):
            pipeline_options.layout_batch_size = self.batch_sizes.get("layout", self.config.gpu.layout_batch_size)

        # Create DocumentConverter with accelerator options
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=ThreadedStandardPdfPipeline,
                    pipeline_options=pipeline_options,
                    accelerator_options=AcceleratorOptions(
                        num_threads=self.config.gpu.num_threads,
                        device=self.accelerator_device,
                    )
                )
            }
        )
        logger.info("DocumentConverter created with GPU acceleration")

    def convert(
        self,
        pdf_path: Path,
        output_dir: Optional[Path] = None,
    ) -> PipelineResult:
        """Convert a PDF to Markdown using the integrated pipeline.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Output directory (defaults to config.output_dir)

        Returns:
            PipelineResult with conversion metrics
        """
        start_time = datetime.now()
        pdf_path = Path(pdf_path)

        # Determine output directory
        base_output = Path(output_dir) if output_dir else Path(self.config.output_dir)
        pdf_output_dir = base_output / pdf_path.stem if self.config.create_pdf_folder else base_output

        if not pdf_path.exists():
            duration = (datetime.now() - start_time).total_seconds()
            return PipelineResult(
                success=False,
                source_pdf=pdf_path,
                output_folder=pdf_output_dir,
                markdown_file=None,
                num_pages=0,
                num_tables=0,
                num_images=0,
                chunk_count=0,
                ai_enhancements=0,
                error_message=f"PDF file not found: {pdf_path}",
                duration_seconds=duration,
            )

        # Create output folder per PDF
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Converting PDF: %s -> %s", pdf_path, pdf_output_dir)

        try:
            export_type = ExportType.DOC_CHUNKS if self.config.langchain.enabled else ExportType.MARKDOWN

            # Use LangChain DoclingLoader with our configured converter
            loader = DoclingLoader(
                file_path=str(pdf_path),
                converter=self.converter,
                export_type=export_type,
            )

            # Load documents (this performs the conversion)
            docs: List[Document] = loader.load()
            logger.info("Loaded %d document chunks from %s", len(docs), pdf_path.name)

            # Metrics tracking
            num_pages = 0
            num_tables = 0
            num_images = 0
            ai_enhancements = 0
            num_chunks = len(docs)

            # Collect markdown content
            markdown_parts: List[str] = []
            markdown_parts.append(f"# {pdf_path.stem}\n\n")
            markdown_parts.append(f"*Converted from PDF: {pdf_path.name}*\n\n")
            markdown_parts.append(f"*Conversion date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            markdown_parts.append("---\n\n")

            # Track page numbers
            current_page = 0

            # Process each document chunk
            for doc in docs:
                metadata = doc.metadata or {}
                content = doc.page_content or ""
                element_type = metadata.get("element_type", "text")

                page_number_raw = metadata.get("page") or metadata.get("page_number") or metadata.get("page_index")
                page_number = current_page
                if page_number_raw is not None:
                    try:
                        page_number = int(page_number_raw)
                    except (TypeError, ValueError):
                        page_number = current_page

                # Update page tracking
                if isinstance(page_number, int) and page_number > current_page:
                    current_page = page_number
                    markdown_parts.append(f"\n## Page {page_number}\n\n")

                # Apply AI enhancement per chunk if available
                enhancer_available = self.enhancer and self.enhancer.is_available

                if element_type == "table":
                    num_tables += 1
                    if enhancer_available and self.config.enhance_tables:
                        try:
                            enhanced_content = self.enhancer.enhance_table(content)
                            if enhanced_content != content:
                                content = enhanced_content
                                ai_enhancements += 1
                        except Exception as e:
                            logger.warning("Failed to enhance table: %s", e)

                    markdown_parts.append(f"### Table {num_tables}\n\n")
                    markdown_parts.append(content)
                    markdown_parts.append("\n\n")

                elif element_type in {"title", "heading", "header", "section-header"}:
                    heading_level = metadata.get("heading_level") or metadata.get("level") or metadata.get("depth")
                    if heading_level is None:
                        heading_level = 1 if element_type == "title" else 2
                    try:
                        heading_level = max(1, min(6, int(heading_level)))
                    except (TypeError, ValueError):
                        heading_level = 2
                    markdown_parts.append(f"{'#' * heading_level} {content.strip()}\n\n")

                elif element_type == "picture":
                    num_images += 1
                    description = content.strip() if content else f"Image {num_images}"
                    markdown_parts.append(f"> Image {num_images}: {description}\n\n")

                else:  # text or other types
                    if enhancer_available and self.config.enhance_text and len(content.strip()) > 50:
                        try:
                            enhanced_content = self.enhancer.enhance_text(content)
                            if enhanced_content != content:
                                content = enhanced_content
                                ai_enhancements += 1
                        except Exception as e:
                            logger.warning("Failed to enhance text: %s", e)

                    markdown_parts.append(content)
                    markdown_parts.append("\n\n")

            # Update page count
            num_pages = current_page if current_page > 0 else 1

            # Write markdown file
            output_file = pdf_output_dir / f"{pdf_path.stem}.md"
            markdown_content = "".join(markdown_parts)
            output_file.write_text(markdown_content, encoding="utf-8")
            logger.info("Wrote markdown to %s", output_file)

            # Write metadata if requested
            if self.config.include_metadata:
                metadata_payload = {
                    "source": str(pdf_path),
                    "converted_at": datetime.utcnow().isoformat(),
                    "chunk_count": num_chunks,
                    "ai_enhancements": ai_enhancements,
                    "gpu_device": str(self.accelerator_device),
                    "langchain_enabled": self.config.langchain.enabled,
                    "gradient_enabled": self.config.gradient.enabled,
                    "gradient_available": bool(self.enhancer and self.enhancer.is_available),
                    "num_tables": num_tables,
                    "num_images": num_images,
                    "num_pages": num_pages,
                    "export_type": export_type.value,
                    "table_files": [],
                }
                metadata_file = pdf_output_dir / "metadata.json"
                metadata_file.write_text(json.dumps(metadata_payload, indent=2), encoding="utf-8")

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            return PipelineResult(
                success=True,
                source_pdf=pdf_path,
                output_folder=pdf_output_dir,
                markdown_file=output_file,
                num_pages=num_pages,
                num_tables=num_tables,
                num_images=num_images,
                num_chunks=num_chunks,
                ai_enhancements=ai_enhancements,
                error_message=None,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error("Conversion failed for %s: %s", pdf_path, e, exc_info=True)
            duration = (datetime.now() - start_time).total_seconds()

            return PipelineResult(
                success=False,
                source_pdf=pdf_path,
                output_folder=pdf_output_dir,
                markdown_file=None,
                num_pages=0,
                num_tables=0,
                num_images=0,
                num_chunks=0,
                ai_enhancements=0,
                error_message=str(e),
                duration_seconds=duration,
            )

    def convert_batch(
        self,
        pdf_paths: List[Path],
        output_dir: Optional[Path] = None,
    ) -> List[PipelineResult]:
        """Convert a batch of PDFs, optionally using parallel execution."""

        if not pdf_paths:
            return []

        target_output = Path(output_dir) if output_dir else Path(self.config.output_dir)
        pdf_paths = [Path(p) for p in pdf_paths]

        if self.config.gpu.enable_parallel and len(pdf_paths) > 1:
            from .parallel import batch_convert_parallel

            return batch_convert_parallel(
                pdf_paths,
                config=self.config,
                output_dir=target_output,
                num_gpus=self.config.gpu.num_gpus,
            )

        results: List[PipelineResult] = []
        for pdf in pdf_paths:
            results.append(self.convert(pdf, output_dir=target_output))
        return results

    def close(self):
        """Clean up resources."""
        if self.enhancer:
            try:
                self.enhancer.close()
                logger.info("Gradient enhancer closed")
            except Exception as e:
                logger.warning("Error closing enhancer: %s", e)

        # Clean up converter resources if needed
        self.converter = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def convert_pdf(
    pdf_path: Path,
    config: Optional[ConversionConfig] = None,
    output_dir: Optional[Path] = None,
) -> PipelineResult:
    """Convenience function for single PDF conversion.

    Args:
        pdf_path: Path to the PDF file
        config: Conversion configuration (optional)

    Returns:
        PipelineResult with conversion metrics

    Example:
        >>> result = convert_pdf(Path("document.pdf"))
        >>> if result.success:
        ...     print(f"Converted to {result.output_path}")
    """
    with IntegratedPipeline(config) as pipeline:
        return pipeline.convert(pdf_path, output_dir=output_dir)


def convert_batch(
    pdf_paths: List[Path],
    config: Optional[ConversionConfig] = None,
    output_dir: Optional[Path] = None,
) -> List[PipelineResult]:
    """Convenience function for batch PDF conversion."""

    with IntegratedPipeline(config) as pipeline:
        return pipeline.convert_batch(pdf_paths, output_dir=output_dir)
