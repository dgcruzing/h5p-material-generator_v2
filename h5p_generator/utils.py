"""Utility functions for H5P Material Generator."""
import os
import pdfplumber
from typing import Optional, Tuple
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_file) -> Tuple[bool, str]:
    """
    Extract text from a PDF file.

    Args:
        pdf_file: File object or path to PDF

    Returns:
        Tuple of (success, text/error_message)
    """
    try:
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

        if not text.strip():
            return False, "No text could be extracted from the PDF"

        return True, text
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return False, f"Error extracting text: {e}"

def create_directory_if_not_exists(directory_path: str) -> None:
    """Create directory if it doesn't exist."""
    try:
        os.makedirs(directory_path, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        raise

def validate_json_format(json_string: str) -> Tuple[bool, Optional[list]]:
    """
    Validate if a string is valid JSON and matches expected format.

    Args:
        json_string: String to validate

    Returns:
        Tuple of (valid, parsed_json/None)
    """
    try:
        parsed = json.loads(json_string)

        # Check if it's a list
        if not isinstance(parsed, list):
            return False, None

        # Check if it contains at least one item
        if len(parsed) == 0:
            return False, None

        return True, parsed
    except json.JSONDecodeError:
        return False, None
