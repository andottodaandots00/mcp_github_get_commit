from typing import List, Dict, Any, Optional, Union, Iterator
from pathlib import Path

from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType, BaseMetaExtractor
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker, BaseChunk
from docling_core.types.doc import DoclingDocument
from langchain_core.documents import Document


class CustomMetaExtractor(BaseMetaExtractor):
    """Custom metadata extractor for LangChain integration.

    Extracts rich metadata from Docling chunks including:
    - Source file path
    - Page numbers
    - Section headings hierarchy
    - Element types (text, table, picture, etc.)
    - Full Docling metadata for advanced use cases
    """

    def extract_chunk_meta(self, file_path: str, chunk: BaseChunk) -> Dict[str, Any]:
        """Extract metadata from a chunk.

        Args:
            file_path: Path to the source document
            chunk: Docling BaseChunk with metadata

        Returns:
            Dictionary containing source, page_number, headings, element_type, and full_dl_meta
        """
        # Default values
        page_number = None
        element_type = "unknown"
        headings = []
        full_dl_meta = None

        # Access chunk metadata safely
        if hasattr(chunk, 'meta') and chunk.meta:
            headings = getattr(chunk.meta, 'headings', [])

            # Export full metadata for advanced use cases
            if hasattr(chunk.meta, 'export_json_dict'):
                try:
                    full_dl_meta = chunk.meta.export_json_dict()
                except Exception:
                    pass  # Graceful fallback

            if hasattr(chunk.meta, 'doc_items') and chunk.meta.doc_items:
                item = chunk.meta.doc_items[0]

                # Get element type
                if hasattr(item, 'label'):
                    element_type = str(item.label) if item.label else "unknown"

                # Get page number
                if hasattr(item, 'prov') and item.prov:
                    page_number = item.prov[0].page_no

        return {
            "source": file_path,
            "page_number": page_number,
            "headings": headings,
            "element_type": element_type,
            "full_dl_meta": full_dl_meta
        }

    def extract_dl_doc_meta(self, file_path: str, dl_doc: DoclingDocument) -> Dict[str, Any]:
        """Extract metadata from the document level.

        Args:
            file_path: Path to the source document
            dl_doc: DoclingDocument instance

        Returns:
            Dictionary containing source, title, num_pages, and origin metadata
        """
        origin_meta = None
        if hasattr(dl_doc, 'origin') and dl_doc.origin:
            origin_meta = {
                "filename": dl_doc.origin.filename if hasattr(dl_doc.origin, 'filename') else None,
                "mimetype": dl_doc.origin.mimetype if hasattr(dl_doc.origin, 'mimetype') else None,
            }

        return {
            "source": file_path,
            "title": getattr(dl_doc, 'name', None),
            "num_pages": len(list(dl_doc.pages)) if hasattr(dl_doc, 'pages') and dl_doc.pages else 0,
            "origin": origin_meta
        }

def create_langchain_loader(
    file_path: Union[str, Path, List[str]],
    converter: Optional[DocumentConverter] = None,
    export_type: ExportType = ExportType.DOC_CHUNKS,
    chunker: Optional[HybridChunker] = None
) -> DoclingLoader:
    """
    Create a configured DoclingLoader instance with custom metadata extraction.
    """
    # Normalize file_path to List[str] or str as required by DoclingLoader
    if isinstance(file_path, list):
        paths = [str(p) for p in file_path]
    elif isinstance(file_path, Path):
        paths = [str(file_path)]
    else:
        paths = [str(file_path)]

    # Note: DoclingLoader argument naming might vary by version,
    # but based on standard usage it accepts file_path (or file_paths), converter, etc.
    # Assuming standard initialization based on user requirement.
    return DoclingLoader(
        file_path=paths,
        converter=converter,
        export_type=export_type,
        chunker=chunker,
        meta_extractor=CustomMetaExtractor()
    )

def load_documents_for_rag(
    pdf_paths: List[Path],
    converter: Optional[DocumentConverter] = None
) -> List[Document]:
    """
    Load documents from PDF paths using the custom loader configuration.

    Args:
        pdf_paths: List of PDF file paths to load
        converter: Optional pre-configured Docling converter

    Returns:
        List of LangChain Document objects with rich metadata
    """
    # Convert paths to strings provided to the loader creator
    str_paths = [str(p) for p in pdf_paths]

    loader = create_langchain_loader(
        file_path=str_paths,
        converter=converter,
        export_type=ExportType.DOC_CHUNKS
    )

    return loader.load()


def lazy_load_documents_for_rag(
    pdf_paths: List[Path],
    converter: Optional[DocumentConverter] = None
) -> Iterator[Document]:
    """
    Lazily load documents for memory-efficient processing of large document sets.

    Args:
        pdf_paths: List of PDF file paths to load
        converter: Optional pre-configured Docling converter

    Yields:
        LangChain Document objects one at a time
    """
    str_paths = [str(p) for p in pdf_paths]

    loader = create_langchain_loader(
        file_path=str_paths,
        converter=converter,
        export_type=ExportType.DOC_CHUNKS
    )

    yield from loader.lazy_load()
