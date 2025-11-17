"""
Configuration for IBCo PDF Stripper

System-specific and processing configuration options.
"""

from pathlib import Path
from typing import Dict, Any


# ==============================================================================
# System Configuration
# ==============================================================================

# Target hardware (AMD Threadripper 3970X)
SYSTEM = {
    "cpu_cores": 32,
    "threads": 64,
    "ram_gb": 256,
    "max_workers": 16,  # For parallel PNG conversion
}


# ==============================================================================
# PDF Processing Configuration
# ==============================================================================

PDF_PROCESSING = {
    # Page number extraction regions (as fraction of page height)
    "footer_region": {
        "top": 0.90,     # Start at 90% down the page
        "bottom": 1.0,   # End at bottom
    },
    "header_region": {
        "top": 0.0,      # Start at top
        "bottom": 0.10,  # End at 10% down
    },

    # Default DPI for PNG conversion
    "default_dpi": 300,

    # PNG conversion quality
    "png_quality": 95,

    # Parallel processing
    "parallel_conversion": True,
    "max_parallel_pages": 16,
}


# ==============================================================================
# OCR Configuration (for TOC Screenshots)
# ==============================================================================

OCR_CONFIG = {
    # Tesseract configuration
    "tesseract_config": "--psm 6",  # Assume uniform block of text

    # Pre-processing for better OCR
    "enhance_image": True,
    "convert_to_grayscale": True,
    "increase_contrast": True,

    # Confidence threshold for OCR results
    "min_confidence": 60,
}


# ==============================================================================
# TOC Parsing Configuration
# ==============================================================================

TOC_PARSING = {
    # Common patterns for TOC entries
    # Format: "Section Name .... Page Number"
    # Ordered by specificity (most specific first)
    "patterns": [
        # Pattern 1: Numbered sections with dots/leaders and Arabic page numbers
        r"(\d+\.?\s+.+?)\s*\.{2,}\s*(\d+)",  # "1. Section .... 25"

        # Pattern 2: Lettered sections with dots/leaders and Arabic page numbers
        r"([A-Z]\.?\s+.+?)\s*\.{2,}\s*(\d+)", # "A. Section .... 25"

        # Pattern 3: Section with "Page" prefix (Roman or Arabic)
        r"(.+?)\s+Page\s+([ivxlcdm\d]+)",   # "Section Page 25" or "Section Page iii"

        # Pattern 4: Section with dots/leaders and Roman page numbers
        r"(.+?)\s*\.{2,}\s*([ivxlcdm]+)\s*$",  # "Section .... iii"

        # Pattern 5: Section with dots/leaders and Arabic page numbers (general)
        r"(.+?)\s*\.{2,}\s*(\d+)",           # "Section .... 25"

        # Pattern 6: Section with multiple spaces and Arabic page number
        r"(.+?)\s{3,}(\d+)\s*$",             # "Section   25" (3+ spaces)

        # Pattern 7: Section with multiple spaces and Roman page number
        r"(.+?)\s{3,}([ivxlcdm]+)\s*$",      # "Section   iii" (3+ spaces)

        # Pattern 8: Section with any spacing and page at end (fallback)
        r"(.+?)\s+(\d+)\s*$",                # "Section 25" (general fallback)
    ],

    # Indentation levels (spaces)
    "level_1_indent": 0,     # Main sections (no indent)
    "level_2_indent": 4,     # Subsections (4+ spaces)
    "level_3_indent": 8,     # Sub-subsections (8+ spaces)

    # Section name cleaning
    "remove_numbers": False,  # Keep section numbers (1., A., etc.)
    "remove_dots": True,      # Remove leader dots

    # Sorting
    "sort_by_page": True,     # Sort TOC entries by page number
}


# ==============================================================================
# Output Configuration
# ==============================================================================

OUTPUT_CONFIG = {
    # Directory structure
    "sections_dir": "sections",
    "metadata_file": "cafr_metadata.json",
    "report_file": "cafr_report.txt",

    # File naming
    "page_filename_format": "page_{page:04d}_{section}.png",

    # Section folder naming
    "section_folder_format": "{num:02d}_{name}",

    # Metadata fields to include
    "include_full_metadata": True,
}


# ==============================================================================
# Logging Configuration
# ==============================================================================

LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": None,  # Set to path for file logging
}


# ==============================================================================
# Roman Numeral Conversion
# ==============================================================================

ROMAN_NUMERALS = {
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5,
    'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9, 'x': 10,
    'xi': 11, 'xii': 12, 'xiii': 13, 'xiv': 14, 'xv': 15,
    'xvi': 16, 'xvii': 17, 'xviii': 18, 'xix': 19, 'xx': 20,
    'xxi': 21, 'xxii': 22, 'xxiii': 23, 'xxiv': 24, 'xxv': 25,
    'xxvi': 26, 'xxvii': 27, 'xxviii': 28, 'xxix': 29, 'xxx': 30,
}


# ==============================================================================
# Helper Functions
# ==============================================================================

def get_config(section: str) -> Dict[str, Any]:
    """
    Get configuration for a specific section.

    Args:
        section: Configuration section name

    Returns:
        Configuration dictionary
    """
    configs = {
        "system": SYSTEM,
        "pdf": PDF_PROCESSING,
        "ocr": OCR_CONFIG,
        "toc": TOC_PARSING,
        "output": OUTPUT_CONFIG,
        "logging": LOGGING,
    }

    return configs.get(section, {})


def roman_to_int(roman: str) -> int:
    """
    Convert Roman numeral to integer.

    Args:
        roman: Roman numeral string (e.g., 'iv', 'xii')

    Returns:
        Integer value or -1 if invalid
    """
    return ROMAN_NUMERALS.get(roman.lower(), -1)


def is_roman_numeral(text: str) -> bool:
    """
    Check if text is a valid Roman numeral.

    Args:
        text: Text to check

    Returns:
        True if valid Roman numeral
    """
    return text.lower() in ROMAN_NUMERALS


# ==============================================================================
# Configuration Validation
# ==============================================================================

def validate_config() -> bool:
    """
    Validate configuration values.

    Returns:
        True if configuration is valid
    """
    # Check parallel workers doesn't exceed system cores
    if SYSTEM["max_workers"] > SYSTEM["threads"]:
        print(f"Warning: max_workers ({SYSTEM['max_workers']}) exceeds "
              f"available threads ({SYSTEM['threads']})")

    # Check DPI is reasonable
    if not (72 <= PDF_PROCESSING["default_dpi"] <= 600):
        print(f"Warning: DPI ({PDF_PROCESSING['default_dpi']}) may be "
              f"too low or too high")

    return True


# Run validation on import
if __name__ != '__main__':
    validate_config()
