"""
PDF to Markdown Converter - Main Entry Point

Unified entry point that dispatches to CLI or Gradio interfaces.

Usage:
    # CLI mode
    python main.py convert input.pdf -o output/
    python main.py convert /path/to/pdfs/ -o output/

    # Gradio UI mode
    python main.py serve --port 7860 --share

    # Help
    python main.py --help
    python main.py convert --help
    python main.py serve --help

Author: Kaggle Pipeline Implementation
Date: 2026-01-14
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from interfaces.cli import main as cli_main


if __name__ == "__main__":
    sys.exit(cli_main())
