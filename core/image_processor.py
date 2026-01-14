"""
Image Processor Module

Extracts images from Docling documents using the correct iterate_items() API pattern.
Converts images to base64-encoded data URIs for markdown embedding.

CRITICAL API USAGE:
- Use doc.iterate_items() to find PictureItem instances (NOT doc.pictures)
- item.image is a PROPERTY returning PIL Image (NOT a method)
- item.prov[0].page_no for page numbers
"""

import base64
import io
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import logging
from PIL import Image
from docling_core.types.doc import DoclingDocument, PictureItem

logger = logging.getLogger(__name__)


@dataclass
class ImageResult:
    """Container for extracted image data with metadata.

    Attributes:
        image_id: Unique identifier (e.g., "img-001")
        base64_data: Full data URI with base64-encoded image
        alt_text: Alternative text description for accessibility
        width: Image width in pixels
        height: Image height in pixels
        page_number: Source page number (0-indexed)
    """
    image_id: str
    base64_data: str
    alt_text: str
    width: int
    height: int
    page_number: int


def image_to_base64(image_bytes: bytes) -> str:
    """Convert image bytes to base64 data URI.

    Args:
        image_bytes: Raw image bytes (PNG format)

    Returns:
        Complete data URI string: "data:image/png;base64,<encoded_data>"

    Example:
        >>> img_bytes = b'\\x89PNG...'
        >>> uri = image_to_base64(img_bytes)
        >>> uri.startswith('data:image/png;base64,')
        True
    """
    try:
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:image/png;base64,{encoded}"
    except Exception as e:
        logger.error(f"Failed to encode image to base64: {e}")
        raise


def create_image_placeholder(image_id: str, alt_text: str) -> str:
    """Create markdown image placeholder with reference-style link.

    Args:
        image_id: Unique image identifier
        alt_text: Alternative text for the image

    Returns:
        Markdown reference-style image syntax

    Example:
        >>> create_image_placeholder("img-001", "Chart showing sales")
        '![Chart showing sales][img-001]'
    """
    return f"![{alt_text}][{image_id}]"


def generate_image_references(images: List[ImageResult]) -> str:
    """Generate markdown reference block for all images.

    Creates the reference definitions section that maps image IDs to their
    base64 data URIs. This section is typically placed at the end of the
    markdown document.

    Args:
        images: List of ImageResult objects containing image data

    Returns:
        Complete reference block as string with header and all definitions

    Example:
        >>> images = [ImageResult("img-001", "data:image/png;base64,abc", "Alt", 100, 100, 0)]
        >>> refs = generate_image_references(images)
        >>> "<!-- IMAGE REFERENCES -->" in refs
        True
        >>> "[img-001]:" in refs
        True
    """
    if not images:
        return ""

    lines = ["<!-- IMAGE REFERENCES -->"]
    for image in images:
        lines.append(f"[{image.image_id}]: {image.base64_data}")

    return "\n".join(lines)


def extract_images(doc: DoclingDocument, config) -> List[ImageResult]:
    """Extract images from document using CORRECT Docling API.

    CRITICAL API USAGE:
    - Iterates document items using doc.iterate_items() (NOT doc.pictures)
    - Filters for PictureItem instances
    - Accesses image via item.image PROPERTY (NOT method call)
    - Gets page number from item.prov[0].page_no

    Args:
        doc: DoclingDocument instance from successful conversion
        config: Configuration object with min_image_width and min_image_height

    Returns:
        List of ImageResult objects with extracted and encoded images

    Raises:
        AttributeError: If document structure is unexpected
        IOError: If image conversion fails

    Example:
        >>> from config.settings import ConversionConfig
        >>> config = ConversionConfig()
        >>> images = extract_images(doc, config)
        >>> all(img.image_id.startswith("img-") for img in images)
        True
    """
    results = []
    counter = 1

    logger.info("Starting image extraction using doc.iterate_items() pattern")

    try:
        # CRITICAL: Use correct API pattern - iterate_items() returns (item, level) tuples
        for item, level in doc.iterate_items():
            # Filter for PictureItem instances
            if not isinstance(item, PictureItem):
                continue

            # Verify image data exists
            if not hasattr(item, 'image') or item.image is None:
                logger.warning(f"PictureItem at level {level} has no image data")
                continue

            try:
                # CRITICAL: item.image is a PROPERTY returning PIL Image
                img = item.image

                # Validate image is PIL Image instance
                if not isinstance(img, Image.Image):
                    logger.warning(f"Expected PIL Image, got {type(img)}")
                    continue

                # Apply size filters from config
                if img.width < config.min_image_width or img.height < config.min_image_height:
                    logger.debug(
                        f"Skipping image {counter}: size {img.width}x{img.height} "
                        f"below threshold {config.min_image_width}x{config.min_image_height}"
                    )
                    continue

                # Convert PIL Image to PNG bytes
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_bytes = buffer.getvalue()

                # Encode to base64 data URI
                b64_data = image_to_base64(img_bytes)

                # Extract page number from provenance
                page_number = 0
                if hasattr(item, 'prov') and item.prov and len(item.prov) > 0:
                    page_number = item.prov[0].page_no

                # Generate unique image ID
                image_id = f"img-{counter:03d}"

                # Create alt text with metadata
                alt_text = f"Image from page {page_number + 1}"
                if hasattr(item, 'text') and item.text:
                    alt_text = item.text.strip()

                # Create result object
                result = ImageResult(
                    image_id=image_id,
                    base64_data=b64_data,
                    alt_text=alt_text,
                    width=img.width,
                    height=img.height,
                    page_number=page_number
                )

                results.append(result)
                logger.debug(f"Extracted {image_id}: {img.width}x{img.height} from page {page_number}")
                counter += 1

            except Exception as e:
                logger.error(f"Failed to process image at level {level}: {e}")
                continue

        logger.info(f"Successfully extracted {len(results)} images")
        return results

    except Exception as e:
        logger.error(f"Image extraction failed: {e}")
        raise
