"""Command-line interface for PDF to Markdown conversion.

This module provides a CLI with argparse for batch PDF processing and
launching the Gradio web UI. Supports single file and directory conversion
with progress tracking.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pipeline import IntegratedPipeline, PipelineResult
from config.settings import ConversionConfig


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser with subcommands.

    Returns:
        ArgumentParser configured with 'convert' and 'serve' subcommands.
    """
    parser = argparse.ArgumentParser(
        description="PDF to Markdown conversion pipeline with GPU-accelerated OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert subcommand
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert PDF(s) to Markdown"
    )
    convert_parser.add_argument(
        "input",
        type=str,
        help="Path to PDF file or directory containing PDFs"
    )
    convert_parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory (default: output)"
    )
    convert_parser.add_argument(
        "--device",
        type=str,
        default="auto",
        choices=["auto", "cuda", "cpu"],
        help="Device to use for OCR (default: auto)"
    )
    convert_parser.add_argument(
        "--ocr-backend",
        type=str,
        default="torch",
        choices=["torch", "onnxruntime"],
        help="OCR backend engine (default: torch)"
    )
    convert_parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR processing"
    )
    convert_parser.add_argument(
        "--image-scale",
        type=float,
        default=2.0,
        help="Image scaling factor (default: 2.0)"
    )
    convert_parser.add_argument(
        "--parallel",
        action="store_true",
        help="Enable parallel processing across GPUs"
    )
    convert_parser.add_argument(
        "--num-gpus",
        type=int,
        default=2,
        help="Number of GPUs for parallel processing (default: 2)"
    )

    # LangChain subcommand
    langchain_parser = subparsers.add_parser(
        "langchain",
        help="Load PDFs into LangChain for RAG"
    )
    langchain_parser.add_argument(
        "input",
        help="PDF file or directory"
    )
    langchain_parser.add_argument(
        "--output", "-o",
        help="Output JSON file for documents"
    )
    langchain_parser.add_argument(
        "--export-type",
        choices=["chunks", "markdown"],
        default="chunks",
        help="Export documents as chunks or full markdown (default: chunks)"
    )

    # Serve subcommand
    serve_parser = subparsers.add_parser(
        "serve",
        help="Launch Gradio web interface"
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to run server on (default: 7860)"
    )
    serve_parser.add_argument(
        "--share",
        action="store_true",
        help="Create public shareable link"
    )
    serve_parser.add_argument(
        "--server-name",
        type=str,
        default="127.0.0.1",
        help="Server bind address (default: 127.0.0.1)"
    )

    # AI Enhance subcommand
    ai_parser = subparsers.add_parser(
        "ai-enhance",
        help="Enhance document with Gradient AI"
    )
    ai_parser.add_argument(
        "input",
        help="Path to Markdown file to enhance"
    )
    ai_parser.add_argument(
        "-o", "--output",
        help="Output path for enhanced file (default: input file + _enhanced.md)"
    )
    ai_parser.add_argument(
        "--model",
        default="llama3.3-70b-instruct",
        help="Gradient model to use (default: llama3.3-70b-instruct)"
    )
    ai_parser.add_argument(
        "--api-key",
        help="Gradient Access Key (overrides env var)"
    )

    # RAG subcommand
    rag_parser = subparsers.add_parser(
        "rag",
        help="RAG (Retrieval-Augmented Generation) operations"
    )
    rag_parser.add_argument(
        "action",
        choices=["index", "query"],
        help="Action: 'index' to add documents, 'query' to search"
    )
    rag_parser.add_argument(
        "input",
        help="PDF file/directory (for index) or query string (for query)"
    )
    rag_parser.add_argument(
        "--db-path",
        default="./docling.db",
        help="Path to Milvus database (default: ./docling.db)"
    )
    rag_parser.add_argument(
        "--collection",
        default="docling_docs",
        help="Collection name (default: docling_docs)"
    )
    rag_parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=4,
        help="Number of results to retrieve (default: 4)"
    )
    rag_parser.add_argument(
        "--embedding-model",
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="HuggingFace embedding model"
    )

    return parser


def cmd_convert(args: argparse.Namespace) -> int:
    """Execute PDF conversion from command line.

    Args:
        args: Parsed command-line arguments containing input path,
              output directory, and conversion options.

    Returns:
        Exit code: 0 on success, 1 if any conversions failed.
    """
    # Build configuration from arguments (respect defaults where not provided)
    base_cfg = ConversionConfig()
    gpu_cfg = base_cfg.gpu.model_copy(
        update={
            "device": args.device,
            "num_gpus": args.num_gpus,
            "enable_parallel": args.parallel or base_cfg.gpu.enable_parallel,
        }
    )
    ocr_cfg = base_cfg.ocr.model_copy(
        update={
            "enabled": not args.no_ocr,
            "backend": args.ocr_backend,
        }
    )

    config = ConversionConfig(
        gpu=gpu_cfg,
        ocr=ocr_cfg,
        output_dir=Path(args.output),
        image_scale=args.image_scale,
    )

    input_path = Path(args.input)

    # Validate input path
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        return 1

    # Single file conversion
    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            print(f"Error: Input file is not a PDF: {input_path}", file=sys.stderr)
            return 1

        print(f"Converting: {input_path.name}")
        with IntegratedPipeline(config) as pipeline:
            result: PipelineResult = pipeline.convert(input_path)

        if result.success:
            print(f"✓ Success: {result.output_path}")
            print(f"  Pages: {result.num_pages}")
            print(f"  Tables: {result.num_tables}")
            print(f"  Images: {result.num_images}")
            print(f"  AI Enhancements: {result.ai_enhancements}")
            print(f"  Duration: {result.duration_seconds:.2f}s")
            return 0
        else:
            print(f"✗ Failed: {result.error_message}", file=sys.stderr)
            return 1

    # Directory batch conversion
    elif input_path.is_dir():
        pdf_files = list(input_path.glob("*.pdf"))

        if not pdf_files:
            print(f"Error: No PDF files found in: {input_path}", file=sys.stderr)
            return 1

        print(f"Found {len(pdf_files)} PDF files")
        print(f"Output directory: {config.output_dir}")
        print(f"OCR: {'Enabled' if config.ocr.enabled else 'Disabled'}")

        if config.gpu.enable_parallel and len(pdf_files) > 1:
            print(f"Mode: Parallel ({config.gpu.num_gpus} GPUs)")
        else:
            print(f"Mode: Sequential ({config.gpu.device})")
        print()

        with IntegratedPipeline(config) as pipeline:
            if config.gpu.enable_parallel and len(pdf_files) > 1:
                results = pipeline.convert_batch(pdf_files, output_dir=config.output_dir)
            else:
                results = [pipeline.convert(p, output_dir=config.output_dir) for p in pdf_files]

        # Calculate statistics
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_pages = sum(r.num_pages for r in results if r.success)
        total_tables = sum(r.num_tables for r in results if r.success)
        total_images = sum(r.num_images for r in results if r.success)
        total_duration = sum(r.duration_seconds for r in results if r.success)

        # Print summary
        print()
        print("=" * 60)
        print("Conversion Summary")
        print("=" * 60)
        print(f"Total files: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total pages: {total_pages}")
        print(f"Total tables: {total_tables}")
        print(f"Total images: {total_images}")
        print(f"Total duration: {total_duration:.2f}s")
        if successful > 0:
            print(f"Avg time per PDF: {total_duration / successful:.2f}s")

        # List failures if any
        if failed > 0:
            print()
            print("Failed conversions:")
            for result in results:
                if not result.success:
                    print(f"  ✗ {result.source_pdf.name}: {result.error_message}")

        return 1 if failed > 0 else 0

    else:
        print(f"Error: Invalid input path: {input_path}", file=sys.stderr)
        return 1


def cmd_langchain(args: argparse.Namespace) -> int:
    """Execute LangChain documents loading.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    try:
        from core.langchain_loader import create_langchain_loader
        from langchain_docling.loader import ExportType

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
            return 1

        # Determine input files
        if input_path.is_file():
            files = [str(input_path)]
        else:
            files = [str(p) for p in input_path.glob("*.pdf")]

        if not files:
            print(f"No PDF files found in {input_path}")
            return 1

        print(f"Loading {len(files)} files into LangChain...")

        export_type = ExportType.MARKDOWN if args.export_type == "markdown" else ExportType.DOC_CHUNKS

        loader = create_langchain_loader(
            file_path=files,
            export_type=export_type
        )

        docs = loader.load()

        if args.output:
            import json
            output_data = [{'page_content': d.page_content, 'metadata': d.metadata} for d in docs]
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"Saved {len(docs)} documents to {args.output}")

        print(f"Successfully loaded {len(docs)} LangChain Documents/Chunks")
        for i, doc in enumerate(docs[:5]): # Show first 5
            source = doc.metadata.get('source', 'unknown')
            content_preview = doc.page_content[:100].replace('\n', ' ')
            print(f"  [{i+1}] Source: {source} | Content: {content_preview}...")

        return 0

    except ImportError as e:
        print(f"Error importing LangChain dependencies: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error during LangChain loading: {e}", file=sys.stderr)
        return 1


def cmd_serve(args: argparse.Namespace) -> int:
    """Launch Gradio web UI.

    Args:
        args: Parsed arguments with port, share, and server_name settings.

    Returns:
        Exit code: 0 on success.
    """
    try:
        from interfaces.gradio_app import create_gradio_app

        print(f"Starting Gradio interface...")
        print(f"Server: {args.server_name}:{args.port}")
        print(f"Share: {args.share}")

        demo = create_gradio_app()
        demo.launch(
            server_port=args.port,
            share=args.share,
            server_name=args.server_name
        )

        return 0

    except ImportError as e:
        print(f"Error: Failed to import Gradio interface: {e}", file=sys.stderr)
        print("Make sure Gradio is installed: pip install gradio", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error launching Gradio: {e}", file=sys.stderr)
        return 1


def cmd_ai_enhance(args: argparse.Namespace) -> int:
    """Execute AI enhancement on a markdown file."""
    try:
        from core.converter import enhance_content_with_ai
        from config.settings import ConversionConfig
        from pydantic import SecretStr

        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
            return 1

        # Prepare configuration
        config = ConversionConfig()
        config.gradient.enabled = True
        config.gradient.default_model = args.model

        if args.api_key:
            config.gradient.model_access_key = SecretStr(args.api_key)

        print(f"Enhancing {input_path.name} with AI (Model: {args.model})...")

        content = input_path.read_text(encoding='utf-8')
        enhanced_content = enhance_content_with_ai(content, "text", config)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path.parent / f"{input_path.stem}_enhanced.md"

        output_path.write_text(enhanced_content, encoding='utf-8')
        print(f"✓ Saved enhanced content to: {output_path}")

        return 0

    except Exception as e:
        print(f"Error during AI enhancement: {e}", file=sys.stderr)
        return 1


def cmd_rag(args: argparse.Namespace) -> int:
    """Execute RAG pipeline operations.

    Args:
        args: Parsed command-line arguments with action, input, and RAG settings.

    Returns:
        Exit code: 0 on success, 1 on failure.
    """
    try:
        from core.rag_pipeline import DocumentRAGPipeline

        # Initialize pipeline
        pipeline = DocumentRAGPipeline(
            embedding_model=args.embedding_model,
            use_gpu=True,
            collection_name=args.collection,
            db_path=args.db_path
        )

        if args.action == "index":
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
                return 1

            # Collect PDF files
            if input_path.is_file():
                pdf_files = [input_path]
            else:
                pdf_files = list(input_path.glob("*.pdf"))

            if not pdf_files:
                print(f"No PDF files found in {input_path}", file=sys.stderr)
                return 1

            print(f"Indexing {len(pdf_files)} PDF file(s)...")
            print(f"Database: {args.db_path}")
            print(f"Collection: {args.collection}")
            print()

            num_chunks = pipeline.add_documents(pdf_files)

            print(f"✓ Successfully indexed {num_chunks} document chunks")
            print(f"  Total documents in collection: {pipeline.document_count}")
            return 0

        elif args.action == "query":
            query = args.input

            if not query.strip():
                print("Error: Query cannot be empty", file=sys.stderr)
                return 1

            print(f"Querying: \"{query}\"")
            print(f"Retrieving top {args.top_k} results...")
            print()

            results = pipeline.query_with_scores(query, k=args.top_k)

            if not results:
                print("No results found. Make sure documents are indexed first.")
                return 0

            print("=" * 60)
            for i, (doc, score) in enumerate(results, 1):
                source = doc.metadata.get('source', 'Unknown')
                page = doc.metadata.get('page_number', '?')
                element_type = doc.metadata.get('element_type', 'unknown')

                print(f"\n[{i}] Score: {score:.4f}")
                print(f"    Source: {Path(source).name} (Page {page}, {element_type})")
                print(f"    Content: {doc.page_content[:200]}...")
                print("-" * 60)

            return 0

        else:
            print(f"Unknown action: {args.action}", file=sys.stderr)
            return 1

    except ImportError as e:
        print(f"Error importing RAG dependencies: {e}", file=sys.stderr)
        print("Install with: pip install langchain-milvus langchain-huggingface", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error during RAG operation: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main CLI entry point.

    Parses command-line arguments and dispatches to the appropriate
    subcommand handler (convert, langchain, ai-enhance, rag, or serve).

    Returns:
        Exit code from subcommand handler.
    """
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "convert":
        return cmd_convert(args)
    elif args.command == "langchain":
        return cmd_langchain(args)
    elif args.command == "ai-enhance":
        return cmd_ai_enhance(args)
    elif args.command == "rag":
        return cmd_rag(args)
    elif args.command == "serve":
        return cmd_serve(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
