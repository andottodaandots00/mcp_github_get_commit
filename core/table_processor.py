"""
Table Processor Module
======================

Extracts tables from Docling documents using the correct API patterns.

CRITICAL API USAGE:
- Uses doc.iterate_items() to get tables (NOT doc.tables)
- Passes doc=doc parameter to export_to_dataframe()
- Pattern based on ai_engine.py line 231

Author: Auto-generated from MASTER_CHECKLIST.md specifications
Date: 2026-01-14
"""

import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import logging

from docling_core.types.doc import DoclingDocument, TableItem

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class TableResult:
    """
    Result object for extracted table data.

    Attributes:
        table_id: Sequential table identifier (1-based)
        csv_path: Absolute path to saved CSV file
        markdown: Markdown representation with CSV link
        row_count: Number of rows in the table
        col_count: Number of columns in the table
        page_number: Source page number (0-based)
    """
    table_id: int
    csv_path: Path
    markdown: str
    row_count: int
    col_count: int
    page_number: int


def fix_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix duplicate column names by appending counter suffix.

    Ensures all column names are unique by renaming duplicates to 'col_N'
    format where N is a sequential counter.

    Args:
        df: Input DataFrame with potential duplicate column names

    Returns:
        DataFrame with unique column names

    Example:
        >>> df = pd.DataFrame({'A': [1], 'B': [2], 'A': [3]})
        >>> fixed = fix_duplicate_columns(df)
        >>> list(fixed.columns)
        ['A', 'B', 'col_2']
    """
    columns = df.columns.tolist()
    seen = {}
    new_columns = []

    for idx, col in enumerate(columns):
        if col in seen:
            # Duplicate found - rename to col_N
            new_columns.append(f"col_{idx}")
            logger.debug(f"Renamed duplicate column '{col}' to 'col_{idx}'")
        else:
            # First occurrence - keep original name
            seen[col] = True
            new_columns.append(col)

    df.columns = new_columns
    return df


def table_to_markdown(df: pd.DataFrame, table_id: int, csv_filename: str) -> str:
    """
    Convert DataFrame to markdown format with CSV reference link.

    Creates a markdown representation with:
    - HTML comment containing CSV filename
    - Markdown table generated from DataFrame
    - Download link to CSV file

    Args:
        df: DataFrame to convert
        table_id: Table identifier for the comment
        csv_filename: Name of the CSV file (without path)

    Returns:
        Complete markdown string with table and CSV link

    Example:
        <!-- TABLE: table_1.csv -->
        | Column A | Column B |
        |----------|----------|
        | Value 1  | Value 2  |

        📊 *[View CSV](tables/table_1.csv)*
    """
    try:
        # Generate HTML comment
        comment = f"<!-- TABLE: {csv_filename} -->\n"

        # Convert DataFrame to markdown (requires tabulate package)
        table_md = df.to_markdown(index=False)

        # Add CSV download link
        csv_link = f"\n\n📊 *[View CSV](tables/{csv_filename})*\n"

        # Combine all parts
        markdown = comment + table_md + csv_link

        logger.debug(f"Generated markdown for table {table_id} ({len(df)} rows)")
        return markdown

    except Exception as e:
        logger.error(f"Failed to convert table {table_id} to markdown: {e}")
        # Fallback to simple representation
        return f"<!-- TABLE: {csv_filename} -->\n\n*Table {table_id}: {len(df)} rows × {len(df.columns)} columns*\n\n📊 *[View CSV](tables/{csv_filename})*\n"


def extract_tables(doc: DoclingDocument, output_folder: Path) -> List[TableResult]:
    """
    Extract all tables from a Docling document using CORRECT API.

    CRITICAL API USAGE:
    - Uses doc.iterate_items() to iterate through document items
    - Filters for TableItem instances
    - Calls item.export_to_dataframe(doc=doc) with required doc parameter

    This pattern is based on ai_engine.py line 231 and AUDIT_REPORT.md.

    Args:
        doc: Parsed DoclingDocument object
        output_folder: Base output directory for the PDF

    Returns:
        List of TableResult objects with extracted table data

    Raises:
        OSError: If unable to create tables directory or save CSV
        ValueError: If table export fails

    Example:
        >>> doc = DoclingDocument.load("document.json")
        >>> results = extract_tables(doc, Path("/output/doc1"))
        >>> len(results)
        3
        >>> results[0].csv_path
        Path('/output/doc1/tables/table_1.csv')
    """
    # Create tables subdirectory
    tables_dir = output_folder / "tables"
    try:
        tables_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created tables directory: {tables_dir}")
    except OSError as e:
        logger.error(f"Failed to create tables directory: {e}")
        raise

    results = []
    table_counter = 0

    try:
        # CRITICAL: Use doc.iterate_items() pattern - NOT doc.tables
        for item, level in doc.iterate_items():
            # Filter for TableItem instances
            if isinstance(item, TableItem):
                table_counter += 1

                try:
                    # CRITICAL: Must pass doc=doc parameter!
                    df = item.export_to_dataframe(doc=doc)

                    if df is None or df.empty:
                        logger.warning(f"Table {table_counter} is empty, skipping")
                        continue

                    # Fix duplicate column names
                    df = fix_duplicate_columns(df)

                    # Generate CSV filename
                    csv_filename = f"table_{table_counter}.csv"
                    csv_path = tables_dir / csv_filename

                    # Save CSV file
                    df.to_csv(csv_path, index=False, encoding='utf-8')
                    logger.info(f"Saved table {table_counter} to {csv_path}")

                    # Generate markdown representation
                    markdown = table_to_markdown(df, table_counter, csv_filename)

                    # Extract page number from provenance
                    page_number = 0
                    if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
                        page_number = item.prov[0].page_no

                    # Create result object
                    result = TableResult(
                        table_id=table_counter,
                        csv_path=csv_path,
                        markdown=markdown,
                        row_count=len(df),
                        col_count=len(df.columns),
                        page_number=page_number
                    )

                    results.append(result)
                    logger.debug(f"Processed table {table_counter}: {result.row_count}×{result.col_count} on page {page_number}")

                except Exception as e:
                    logger.error(f"Failed to process table {table_counter}: {e}", exc_info=True)
                    # Continue processing remaining tables
                    continue

        logger.info(f"Successfully extracted {len(results)} tables from document")
        return results

    except Exception as e:
        logger.error(f"Error during table extraction: {e}", exc_info=True)
        # Return partial results if any were processed
        return results
