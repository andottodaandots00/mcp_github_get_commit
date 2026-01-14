"""
Gradio Web UI for Interactive PDF to Markdown Conversion.

Provides a user-friendly web interface for uploading PDFs and downloading
converted markdown outputs with tables and images.
"""

import gradio as gr
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple, List, Optional
import sys
import shutil
import traceback

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.converter import convert_pdf, ConversionResult
from config.settings import ConversionConfig


def convert_with_progress(
    files: List,
    enable_parallel: bool,
    num_gpus: int,
    progress: gr.Progress = gr.Progress()
) -> Tuple[str, str, str]:
    """
    Convert uploaded PDFs and return results.

    Args:
        files: List of uploaded PDF file objects from Gradio
        enable_parallel: Whether to use parallel processing
        num_gpus: Number of GPUs to use if parallel enabled
        progress: Gradio progress tracker for UI updates

    Returns:
        Tuple of (status_message, markdown_preview, zip_path):
            - status_message: Success/error summary text
            - markdown_preview: Content of first converted markdown
            - zip_path: Path to downloadable ZIP file

    Raises:
        Exception: Propagates conversion errors with user-friendly messages
    """
    if not files:
        return "❌ No files uploaded. Please select PDF files to convert.", "", ""

    try:
        # Create config
        config = ConversionConfig()

        # Create temp output directory
        temp_dir = Path(tempfile.mkdtemp(prefix="gradio_convert_"))
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Update config with temp output base dir so parallel workers use it
        config.output.base_dir = output_dir

        # Track results
        results = []
        success_count = 0
        error_count = 0

        if enable_parallel and len(files) > 1:
            try:
                from core.parallel import batch_convert_parallel

                # Bridge parallel progress to Gradio
                completed_count = 0

                def on_parallel_progress(pdf_path, result):
                    nonlocal completed_count
                    if result:
                        completed_count += 1
                    # Ensure progress updates
                    progress(completed_count / len(files), desc=f"Converted {Path(pdf_path).name}")

                parallel_results = batch_convert_parallel(
                    pdf_paths=[Path(f) for f in files],
                    config=config,
                    num_gpus=num_gpus,
                    progress_callback=on_parallel_progress
                )

                results = parallel_results

                for res in results:
                    if res.success:
                        success_count += 1
                    else:
                        error_count += 1

            except ImportError:
                print("Parallel module not found, falling back to sequential.")
                # Fallback to sequential
                results = []

        if not results:
            # Convert each file sequentially (fallback or default)
            for i, file in enumerate(files):
                try:
                    # Update progress
                    progress((i + 1) / len(files), desc=f"Converting {Path(file).name}...")

                    # Call convert_pdf
                    result = convert_pdf(
                        pdf_path=Path(file),
                        output_base_dir=output_dir,
                        config=config
                    )

                    results.append(result)
                    if result.success:
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    error_count += 1
                    error_msg = f"Failed to convert {Path(file).name}: {str(e)}"
                    results.append(ConversionResult(
                        source_pdf=Path(file),
                        success=False,
                        output_folder=Path(),
                        markdown_file=Path(),
                        table_files=[],
                        num_pages=0,
                        num_tables=0,
                        num_images=0,
                        error_message=error_msg,
                        duration_seconds=0.0
                    ))

        # Build status message
        status_lines = [
            f"✅ Conversion Complete!",
            f"",
            f"📊 Summary:",
            f"  • Total files: {len(files)}",
            f"  • Successful: {success_count}",
            f"  • Failed: {error_count}",
            f""
        ]

        # Add individual file status
        for result in results:
            if result.success:
                status_lines.append(
                    f"✅ {result.source_pdf.name}: {result.num_pages} pages "
                    f"in {result.duration_seconds:.2f}s"
                )
            else:
                status_lines.append(f"❌ {result.source_pdf.name}: {result.error_message}")

        status_message = "\n".join(status_lines)

        # Read first markdown for preview
        markdown_preview = ""
        first_success = next((r for r in results if r.success and r.markdown_file), None)

        if first_success and first_success.markdown_file and first_success.markdown_file.exists():
            try:
                markdown_preview = first_success.markdown_file.read_text(encoding='utf-8')
                # Limit preview to first 5000 characters
                if len(markdown_preview) > 5000:
                    markdown_preview = markdown_preview[:5000] + "\n\n... (preview truncated)"
            except Exception as e:
                markdown_preview = f"⚠️ Could not read markdown preview: {str(e)}"
        else:
            markdown_preview = "⚠️ No successful conversions to preview."

        # Create ZIP of all outputs
        zip_path = temp_dir / "converted_pdfs.zip"

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for result in results:
                if result.success and result.output_folder:
                    # Add all files from output folder
                    for file_path in result.output_folder.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(output_dir)
                            zipf.write(file_path, arcname)

        return status_message, markdown_preview, str(zip_path)

    except Exception as e:
        error_trace = traceback.format_exc()
        error_msg = (
            f"❌ Conversion failed with error:\n\n"
            f"{str(e)}\n\n"
            f"Technical details:\n{error_trace}"
        )
        return error_msg, "", ""


def create_gradio_app(config: Optional[ConversionConfig] = None) -> gr.Blocks:
    """
    Create Gradio interface for PDF conversion.

    Args:
        config: Optional ConversionConfig instance (creates default if None)

    Returns:
        gr.Blocks: Configured Gradio application interface
    """
    if config is None:
        config = ConversionConfig()

    # Create Blocks with theme
    with gr.Blocks(
        theme=gr.themes.Soft(),
        title="PDF to Markdown Converter"
    ) as demo:

        # Header
        gr.Markdown("""
        # 📄 PDF to Markdown Converter

        Convert your PDFs to high-quality Markdown with tables and images extracted.

        ## 📋 Instructions:
        1. Upload one or more PDF files using the file upload button
        2. Click "Convert PDFs" to start the conversion process
        3. Review the status and preview the first converted file
        4. Download the ZIP file containing all converted outputs

        ## 📦 Output Structure:
        Each PDF will have its own folder containing:
        - `{pdf_name}.md` - Complete markdown file (all pages)
        - `tables/` - Extracted tables as CSV files with inline markdown
        - `images/` - Extracted images (base64 embedded in markdown)

        ---
        """)

        # File upload
        file_input = gr.File(
            label="Upload PDF Files",
            file_count="multiple",
            file_types=[".pdf"],
            type="filepath"
        )

        with gr.Accordion("Advanced Options", open=False):
            enable_parallel = gr.Checkbox(
                label="Enable Parallel Processing (Multi-GPU)",
                value=False,
                info="Process multiple PDFs simultaneously"
            )
            num_gpus = gr.Slider(
                minimum=1,
                maximum=4,
                step=1,
                value=2,
                label="Number of GPUs",
                visible=False
            )

            def toggle_gpu_visibility(is_checked):
                return gr.update(visible=is_checked)

            enable_parallel.change(fn=toggle_gpu_visibility, inputs=enable_parallel, outputs=num_gpus)

        # Convert button
        convert_btn = gr.Button(
            "🚀 Convert PDFs",
            variant="primary",
            size="lg"
        )

        # Status output
        status_output = gr.Textbox(
            label="Conversion Status",
            lines=10,
            interactive=False,
            placeholder="Status messages will appear here after conversion..."
        )

        # Markdown preview
        markdown_output = gr.Textbox(
            label="Markdown Preview (First File)",
            lines=15,
            interactive=False,
            placeholder="Preview of the first converted markdown file will appear here..."
        )

        # Download file
        download_output = gr.File(
            label="Download Converted Files (ZIP)",
            interactive=False
        )

        # Wire up convert button
        convert_btn.click(
            fn=convert_with_progress,
            inputs=[file_input, enable_parallel, num_gpus],
            outputs=[status_output, markdown_output, download_output]
        )

        # Footer
        gr.Markdown("""
        ---

        ### ⚙️ Configuration:
        - GPU acceleration: Automatic detection (CUDA/ROCm/CPU fallback)
        - OCR engine: RapidOCR for scanned documents
        - Table export: Both CSV files and inline markdown
        - Image format: Base64 embedded with reference-style links

        ### 💡 Tips:
        - Larger PDFs take longer to process (progress bar shows status)
        - Scanned PDFs require OCR and may take additional time
        - Each PDF gets its own folder in the output ZIP
        - Tables are exported as both CSV and markdown format
        """)

    return demo


def launch(
    port: int = 7860,
    share: bool = False,
    server_name: str = "0.0.0.0"
) -> None:
    """
    Launch Gradio web application.

    Args:
        port: Port number to run server on (default: 7860)
        share: Whether to create public share link (default: False)
        server_name: Server host address (default: "0.0.0.0" for all interfaces)

    Example:
        >>> from interfaces.gradio_app import launch
        >>> launch(port=7860, share=True)  # Creates public link
    """
    # Create config
    config = ConversionConfig()

    # Create app
    demo = create_gradio_app(config)

    # Launch with parameters
    demo.launch(
        server_port=port,
        share=share,
        server_name=server_name,
        show_error=True
    )


if __name__ == "__main__":
    # Launch with default settings
    launch()
