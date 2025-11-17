#!/usr/bin/env python3
"""
IBCo PDF Stripper - CAFR PDF Processing Tool

Processes municipal Comprehensive Annual Financial Report (CAFR) PDFs:
- Loads TOC from screenshot via OCR
- Extracts page numbers from PDF footers
- Maps pages to sections
- Converts pages to organized PNG files
- Generates metadata and reports

Built for the IBCo (Independent Budget & Capital Operations) transparency initiative.
"""

import argparse
import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from multiprocessing import Pool, cpu_count

import pdfplumber
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from tqdm import tqdm

import config


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TOCEntry:
    """Represents a table of contents entry."""
    section_name: str
    page_number: int
    level: int = 1  # 1=main section, 2=subsection
    parent: Optional[str] = None


@dataclass
class PageMetadata:
    """Metadata for a single PDF page."""
    pdf_page_num: int
    footer_page_num: Optional[str]
    section_name: Optional[str]
    section_level: int
    header_text: Optional[str]
    parent_section_name: Optional[str] = None
    png_file: Optional[str] = None


# ==============================================================================
# Multiprocessing Worker Functions
# ==============================================================================

def _convert_page_worker(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Worker function for multiprocessing page conversion.

    Args:
        task: Dictionary with:
            - pdf_path: Path to PDF
            - page_number: Page number to convert
            - output_path: Where to save PNG
            - dpi: DPI for conversion
            - metadata_index: Index in page_metadata list

    Returns:
        Dictionary with output_path and metadata_index
    """
    from pdf2image import convert_from_path
    from pathlib import Path

    # Convert single page
    images = convert_from_path(
        task['pdf_path'],
        dpi=task['dpi'],
        first_page=task['page_number'],
        last_page=task['page_number'],
        thread_count=1
    )

    if not images:
        raise ValueError(f"Failed to convert page {task['page_number']}")

    # Save the image
    output_path = Path(task['output_path'])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    images[0].save(output_path, 'PNG')

    return {
        'output_path': str(output_path),
        'metadata_index': task['metadata_index']
    }


class PDFStripper:
    """
    Main class for processing CAFR PDFs.

    Workflow:
    1. Load TOC from screenshot(s)
    2. Read PDF and extract page numbers
    3. Map pages to sections
    4. Convert pages to PNG files
    5. Generate metadata and reports
    """

    def __init__(self, pdf_path: str, output_dir: str):
        """
        Initialize the PDF Stripper.

        Args:
            pdf_path: Path to the CAFR PDF file
            output_dir: Directory for output files
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.toc_entries: List[TOCEntry] = []
        self.page_metadata: List[PageMetadata] = []

        # Validate inputs
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized PDFStripper for: {self.pdf_path.name}")
        logger.info(f"Output directory: {self.output_dir}")

    def get_page_count(self) -> int:
        """
        Get total number of pages in the PDF.

        Returns:
            Total page count
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            return len(pdf.pages)

    def read_footer_page_number(self, page) -> Optional[str]:
        """
        Extract page number from the bottom 10% of a page.

        CAFR PDFs typically have page numbers centered in the footer.
        Handles both Roman numerals (i, ii, iii) and Arabic numerals (1, 2, 3).

        Args:
            page: pdfplumber page object

        Returns:
            Page number as string (e.g., "i", "ii", "1", "25") or None if not found
        """
        # Get footer region from config
        footer_config = config.PDF_PROCESSING['footer_region']

        # Calculate footer bounding box
        page_height = page.height
        footer_top = page_height * footer_config['top']
        footer_bbox = (0, footer_top, page.width, page_height)

        # Extract text from footer region
        try:
            footer_crop = page.crop(footer_bbox)
            footer_text = footer_crop.extract_text()

            if not footer_text:
                return None

            # Clean up the text
            footer_text = footer_text.strip()

            # Parse page number from footer text
            page_num = self._parse_page_number(footer_text)

            return page_num

        except Exception as e:
            logger.debug(f"Error reading footer on page: {e}")
            return None

    def read_header_text(self, page) -> Optional[str]:
        """
        Extract text from the top 10% of a page.

        CAFR headers usually contain section names, city name, or year.

        Args:
            page: pdfplumber page object

        Returns:
            Header text or None if not found
        """
        # Get header region from config
        header_config = config.PDF_PROCESSING['header_region']

        # Calculate header bounding box
        page_height = page.height
        header_bottom = page_height * header_config['bottom']
        header_bbox = (0, 0, page.width, header_bottom)

        # Extract text from header region
        try:
            header_crop = page.crop(header_bbox)
            header_text = header_crop.extract_text()

            if not header_text:
                return None

            # Clean up the text (remove extra whitespace, newlines)
            header_text = ' '.join(header_text.split())
            return header_text.strip()

        except Exception as e:
            logger.debug(f"Error reading header on page: {e}")
            return None

    def _parse_page_number(self, text: str) -> Optional[str]:
        """
        Parse page number from text string.

        Handles:
        - Roman numerals (i, ii, iii, iv, v, etc.)
        - Arabic numerals (1, 2, 3, etc.)
        - Page numbers with surrounding text/symbols

        Args:
            text: Text potentially containing a page number

        Returns:
            Page number as string or None
        """
        # Remove extra whitespace
        text = text.strip()

        # Pattern 1: Just a number (most common)
        # Match standalone numbers
        match = re.search(r'^\s*(\d+)\s*$', text)
        if match:
            return match.group(1)

        # Pattern 2: Roman numerals (standalone)
        # Match i, ii, iii, iv, v, vi, etc.
        roman_pattern = r'^\s*([ivxlcdm]+)\s*$'
        match = re.search(roman_pattern, text, re.IGNORECASE)
        if match:
            roman = match.group(1).lower()
            # Verify it's a valid Roman numeral we recognize
            if config.is_roman_numeral(roman):
                return roman

        # Pattern 3: Number with dash or other separators
        # e.g., "- 25 -", "~ 3 ~"
        match = re.search(r'[-~]\s*(\d+)\s*[-~]', text)
        if match:
            return match.group(1)

        # Pattern 4: Number anywhere in the text
        # Last resort: extract first number found
        match = re.search(r'(\d+)', text)
        if match:
            return match.group(1)

        # Pattern 5: Roman numeral anywhere in text
        # Look for roman numerals in the text
        match = re.search(r'\b([ivxlcdm]+)\b', text, re.IGNORECASE)
        if match:
            roman = match.group(1).lower()
            if config.is_roman_numeral(roman):
                return roman

        return None

    def load_toc_from_screenshot(self, image_path: str) -> List[TOCEntry]:
        """
        Load TOC from a screenshot using OCR.

        Uses pytesseract to OCR the image and parse TOC entries.
        Handles various TOC formats commonly found in CAFRs.

        Args:
            image_path: Path to TOC screenshot

        Returns:
            List of TOC entries

        Raises:
            FileNotFoundError: If image file doesn't exist
            Exception: If OCR fails
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"TOC screenshot not found: {image_path}")

        logger.info(f"Loading TOC from screenshot: {image_path.name}")

        try:
            # Load image
            image = Image.open(image_path)

            # Pre-process image for better OCR (from config)
            if config.OCR_CONFIG['convert_to_grayscale']:
                image = image.convert('L')

            if config.OCR_CONFIG['increase_contrast']:
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)

            # Perform OCR
            ocr_config = config.OCR_CONFIG['tesseract_config']
            ocr_text = pytesseract.image_to_string(image, config=ocr_config)

            if not ocr_text or not ocr_text.strip():
                logger.warning(f"No text extracted from {image_path.name}")
                logger.warning("OCR may have failed or image quality is poor")
                return []

            logger.debug(f"OCR extracted {len(ocr_text)} characters")

            # Parse TOC entries from OCR text
            toc_entries = self._parse_toc_text(ocr_text)

            logger.info(f"Parsed {len(toc_entries)} TOC entries from {image_path.name}")

            if len(toc_entries) == 0:
                logger.warning("No TOC entries found. Please verify:")
                logger.warning("  1. Screenshot contains table of contents")
                logger.warning("  2. Image quality is good (clear, high resolution)")
                logger.warning("  3. Text is readable in the image")

            return toc_entries

        except ImportError:
            logger.error("pytesseract not installed or tesseract-ocr not found")
            logger.error("Install: sudo apt-get install tesseract-ocr")
            logger.error("Install: pip install pytesseract")
            raise

        except Exception as e:
            logger.error(f"Error processing TOC screenshot: {e}")
            raise

    def _parse_toc_text(self, ocr_text: str) -> List[TOCEntry]:
        """
        Parse TOC entries from OCR text.

        Recognizes common CAFR TOC formats:
        - "Section Name .................. 15"
        - "Section Name    15"
        - "Management's Discussion ... Page 25"
        - "1. Introductory Section ...... 1"
        - "A. Letter of Transmittal ..... 3"
        - Roman numeral pages: "Introductory Section ... i"

        Args:
            ocr_text: Raw OCR text from TOC screenshot

        Returns:
            List of TOCEntry objects sorted by page number
        """
        toc_entries = []
        lines = ocr_text.split('\n')

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Try to parse TOC entry from this line
            entry = self._parse_toc_line(line)
            if entry:
                toc_entries.append(entry)

        # Sort by page number if configured
        if config.TOC_PARSING['sort_by_page'] and toc_entries:
            toc_entries.sort(key=lambda e: e.page_number)

        return toc_entries

    def _parse_toc_line(self, line: str) -> Optional[TOCEntry]:
        """
        Parse a single line of TOC text into a TOCEntry.

        Handles both Arabic numerals (1, 2, 3) and Roman numerals (i, ii, iii)
        in page references.

        Args:
            line: Single line from TOC

        Returns:
            TOCEntry object or None if not a valid entry
        """
        # Get TOC patterns from config
        patterns = config.TOC_PARSING['patterns']

        # Determine indentation level (for subsections)
        leading_spaces = len(line) - len(line.lstrip(' '))
        level = 1  # Default: main section

        if leading_spaces >= config.TOC_PARSING['level_3_indent']:
            level = 3
        elif leading_spaces >= config.TOC_PARSING['level_2_indent']:
            level = 2

        # Try each pattern
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Extract section name and page number
                section_name = match.group(1).strip()
                page_str = match.group(2).strip()

                # Clean section name
                if config.TOC_PARSING['remove_dots']:
                    section_name = re.sub(r'\.+\s*$', '', section_name)
                    section_name = section_name.strip()

                # Convert page string to integer
                page_number = self._convert_page_to_int(page_str)

                if page_number is not None:
                    # Create TOC entry
                    return TOCEntry(
                        section_name=section_name,
                        page_number=page_number,
                        level=level,
                        parent=None  # Will be set later if needed
                    )

        return None

    def _convert_page_to_int(self, page_str: str) -> Optional[int]:
        """
        Convert a page string to an integer.

        Handles:
        - Arabic numerals: "1", "25", "200"
        - Roman numerals: "i", "ii", "iii", "iv", "v", etc.
        - Page prefix: "Page 25"

        Args:
            page_str: Page number string

        Returns:
            Integer page number or None if invalid
        """
        page_str = page_str.strip()

        # Handle "Page 25" or "Page iii" format
        if 'page' in page_str.lower():
            # Extract just the number/numeral part
            match = re.search(r'([ivxlcdm\d]+)', page_str, re.IGNORECASE)
            if match:
                page_str = match.group(1)
            else:
                return None

        # Try Arabic numeral first (most common)
        try:
            return int(page_str)
        except ValueError:
            pass

        # Try Roman numeral
        page_lower = page_str.lower()
        if config.is_roman_numeral(page_lower):
            return config.roman_to_int(page_lower)

        return None

    def load_toc_from_screenshots(self, image_paths: List[str]) -> List[TOCEntry]:
        """
        Load TOC from multiple screenshot files.

        Some CAFRs have multi-page table of contents. This method processes
        multiple screenshots in order, combines entries, removes duplicates,
        and returns a complete sorted TOC structure.

        Args:
            image_paths: List of paths to TOC screenshot files

        Returns:
            List of TOCEntry objects, sorted by page number with duplicates removed
        """
        logger.info(f"Loading TOC from {len(image_paths)} screenshot(s)")

        all_entries = []

        for i, image_path in enumerate(image_paths, start=1):
            logger.info(f"Processing screenshot {i}/{len(image_paths)}: {Path(image_path).name}")

            # Load entries from this screenshot
            entries = self.load_toc_from_screenshot(image_path)
            all_entries.extend(entries)

        logger.info(f"Total entries before deduplication: {len(all_entries)}")

        # Remove duplicates
        unique_entries = self._remove_duplicate_entries(all_entries)

        logger.info(f"Total entries after deduplication: {len(unique_entries)}")

        # Sort by page number (should already be sorted, but ensure it)
        if config.TOC_PARSING['sort_by_page']:
            unique_entries.sort(key=lambda e: e.page_number)

        return unique_entries

    def _remove_duplicate_entries(self, entries: List[TOCEntry]) -> List[TOCEntry]:
        """
        Remove duplicate TOC entries.

        Duplicates are identified by having the same section name and page number.

        Args:
            entries: List of TOC entries (may contain duplicates)

        Returns:
            List of unique TOC entries
        """
        seen = set()
        unique = []

        for entry in entries:
            # Create a key for duplicate detection
            key = (entry.section_name.lower().strip(), entry.page_number)

            if key not in seen:
                seen.add(key)
                unique.append(entry)
            else:
                logger.debug(f"Removing duplicate: {entry.section_name} (page {entry.page_number})")

        return unique

    def verify_toc_completeness(self) -> Dict[str, Any]:
        """
        Verify TOC completeness and detect potential issues.

        Checks for:
        - Gaps in page number sequence
        - Missing major sections
        - Minimum section count

        Returns:
            Dictionary with verification results and warnings
        """
        if not self.toc_entries:
            return {
                "is_complete": False,
                "warnings": ["No TOC entries loaded"],
                "errors": ["Cannot verify - no TOC entries"],
                "gaps": [],
                "main_section_count": 0
            }

        warnings = []
        errors = []
        gaps = []

        # Count main sections (level 1)
        main_sections = [e for e in self.toc_entries if e.level == 1]
        main_section_count = len(main_sections)

        # Check for minimum main sections
        if main_section_count < 3:
            warnings.append(f"Only {main_section_count} main section(s) found - typical CAFRs have 3+ "
                           "(Introductory, Financial, Statistical)")

        # Check for page number gaps
        page_numbers = sorted([e.page_number for e in self.toc_entries])

        for i in range(len(page_numbers) - 1):
            current = page_numbers[i]
            next_page = page_numbers[i + 1]
            gap_size = next_page - current

            # If gap is larger than 100 pages, it might indicate missing sections
            if gap_size > 100:
                gaps.append({
                    "after_page": current,
                    "before_page": next_page,
                    "gap_size": gap_size
                })
                warnings.append(f"Large gap: {gap_size} pages between page {current} and {next_page}")

        # Check for common CAFR sections
        section_names_lower = [e.section_name.lower() for e in self.toc_entries]

        expected_keywords = ["introductory", "financial", "statistical"]
        missing_keywords = []

        for keyword in expected_keywords:
            if not any(keyword in name for name in section_names_lower):
                missing_keywords.append(keyword)

        if missing_keywords:
            warnings.append(f"Common CAFR sections not found: {', '.join(missing_keywords)}")

        # Determine completeness
        is_complete = len(errors) == 0 and len(warnings) <= 1

        return {
            "is_complete": is_complete,
            "warnings": warnings,
            "errors": errors,
            "gaps": gaps,
            "main_section_count": main_section_count,
            "total_entries": len(self.toc_entries),
            "page_range": f"{page_numbers[0]}-{page_numbers[-1]}" if page_numbers else "N/A"
        }

    def print_toc(self):
        """
        Print TOC for user review before processing.

        Displays all TOC entries with hierarchy visualization.
        """
        if not self.toc_entries:
            print("No TOC entries loaded.")
            return

        print("=" * 80)
        print("TABLE OF CONTENTS - Review")
        print("=" * 80)
        print()

        print(f"{'Section Name':<55} {'Page':<8} {'Level'}")
        print("-" * 80)

        for entry in self.toc_entries:
            # Visual indentation based on level
            indent = "  " * (entry.level - 1)
            section_display = f"{indent}{entry.section_name}"

            # Truncate if too long
            if len(section_display) > 52:
                section_display = section_display[:49] + "..."

            print(f"{section_display:<55} {entry.page_number:<8} {entry.level}")

        print()
        print(f"Total entries: {len(self.toc_entries)}")

        # Show main section count
        main_sections = [e for e in self.toc_entries if e.level == 1]
        print(f"Main sections: {len(main_sections)}")

        # Show page range
        if self.toc_entries:
            page_numbers = [e.page_number for e in self.toc_entries]
            print(f"Page range: {min(page_numbers)}-{max(page_numbers)}")

        print("=" * 80)

    def map_page_to_section(self, page_number: int, toc_entries: List[TOCEntry] = None) -> Tuple[Optional[str], int, Optional[str]]:
        """
        Map a PDF page number to its TOC section.

        Logic:
        - A page belongs to a section if:
          * page_number >= section start page
          * AND page_number < next section start page
          * OR page_number >= section start and no next section (last section)

        - For hierarchical sections:
          * Returns the most specific (deepest) section
          * Stores parent section reference

        Args:
            page_number: Page number to map (document page number, not PDF sequential)
            toc_entries: List of TOC entries (uses self.toc_entries if not provided)

        Returns:
            Tuple of (section_name, section_level, parent_section_name)
            Returns (None, 0, None) if page not found in any section
        """
        if toc_entries is None:
            toc_entries = self.toc_entries

        if not toc_entries:
            return (None, 0, None)

        # Sort entries by page number (should already be sorted)
        sorted_entries = sorted(toc_entries, key=lambda e: e.page_number)

        # Find the section this page belongs to
        # Start from the end and work backwards to find the section that starts at or before this page
        matching_section = None
        next_section_page = None

        for i, entry in enumerate(sorted_entries):
            # Check if this page is at or after this section's start
            if page_number >= entry.page_number:
                # Check if there's a next section
                if i + 1 < len(sorted_entries):
                    next_section_page = sorted_entries[i + 1].page_number
                    # Page must be before the next section
                    if page_number < next_section_page:
                        matching_section = entry
                        # Keep looking for more specific (higher level) sections
                else:
                    # This is the last section, page is in it
                    matching_section = entry

        if not matching_section:
            return (None, 0, None)

        # Now find the most specific subsection (highest level number)
        # Look for subsections that start at or before this page
        most_specific_section = matching_section
        parent_section = None

        for entry in sorted_entries:
            # Only consider entries that start at or before our page
            if entry.page_number <= page_number:
                # Find next entry to determine end of this section
                next_entry_idx = sorted_entries.index(entry) + 1
                if next_entry_idx < len(sorted_entries):
                    next_entry_page = sorted_entries[next_entry_idx].page_number
                    if page_number >= next_entry_page:
                        continue  # Page is after this section

                # Check if this is a more specific section (higher level)
                if entry.level > most_specific_section.level:
                    # This is a subsection of our current section
                    parent_section = most_specific_section
                    most_specific_section = entry
                elif entry.level == 1 and entry.page_number <= page_number:
                    # Track the main section for parent reference
                    if most_specific_section.level > 1:
                        parent_section = entry

        # Determine parent section name
        parent_name = None
        if most_specific_section.level > 1:
            # Find the parent section (level - 1)
            for entry in reversed(sorted_entries):
                if (entry.level == most_specific_section.level - 1 and
                    entry.page_number <= most_specific_section.page_number):
                    parent_name = entry.section_name
                    break

        return (most_specific_section.section_name,
                most_specific_section.level,
                parent_name)

    def build_page_index(self, toc_entries: List[TOCEntry] = None) -> List[PageMetadata]:
        """
        Build complete page index for the PDF.

        Iterates through all PDF pages and creates PageMetadata for each:
        - Extracts footer page number
        - Extracts header text
        - Maps to TOC section
        - Handles edge cases (pages before sections, missing numbers)

        Args:
            toc_entries: List of TOC entries (uses self.toc_entries if not provided)

        Returns:
            List of PageMetadata objects for all pages
        """
        if toc_entries is None:
            toc_entries = self.toc_entries

        page_count = self.get_page_count()
        page_index = []

        logger.info(f"Building page index for {page_count} pages...")

        with pdfplumber.open(self.pdf_path) as pdf:
            for pdf_page_num in range(1, page_count + 1):
                # Progress indicator
                if pdf_page_num % 10 == 0 or pdf_page_num == 1 or pdf_page_num == page_count:
                    print(f"Processing page {pdf_page_num}/{page_count}...")

                page = pdf.pages[pdf_page_num - 1]  # pdfplumber uses 0-based indexing

                # Extract footer page number
                footer_page_num = self.read_footer_page_number(page)

                # Extract header text
                header_text = self.read_header_text(page)

                # Map to TOC section
                # Need to convert footer page number to int for section mapping
                section_name = None
                section_level = 0
                parent_section_name = None

                if footer_page_num:
                    # Convert footer page number to integer
                    page_num_int = self._convert_page_to_int(footer_page_num)
                    if page_num_int:
                        # Map using the document page number
                        section_name, section_level, parent_section_name = self.map_page_to_section(
                            page_num_int, toc_entries
                        )

                # Create PageMetadata
                metadata = PageMetadata(
                    pdf_page_num=pdf_page_num,
                    footer_page_num=footer_page_num,
                    section_name=section_name,
                    section_level=section_level,
                    header_text=header_text,
                    parent_section_name=parent_section_name,
                    png_file=None  # Will be populated during PNG conversion
                )

                page_index.append(metadata)

        # Store internally
        self.page_metadata = page_index

        logger.info(f"✓ Page index built: {len(page_index)} pages processed")

        # Summary stats
        pages_with_numbers = sum(1 for p in page_index if p.footer_page_num)
        pages_with_sections = sum(1 for p in page_index if p.section_name)
        pages_with_headers = sum(1 for p in page_index if p.header_text)

        logger.info(f"  Pages with footer numbers: {pages_with_numbers}/{len(page_index)}")
        logger.info(f"  Pages mapped to sections: {pages_with_sections}/{len(page_index)}")
        logger.info(f"  Pages with header text: {pages_with_headers}/{len(page_index)}")

        return page_index

    def _create_section_slug(self, section_name: Optional[str]) -> str:
        """
        Create a URL-friendly slug from section name.

        Args:
            section_name: Section name to convert

        Returns:
            Lowercase slug with underscores (e.g., "financial_section")
        """
        if not section_name:
            return "unsectioned"

        # Remove leading/trailing whitespace
        slug = section_name.strip()

        # Convert to lowercase
        slug = slug.lower()

        # Replace spaces and special characters with underscores
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '_', slug)

        # Remove leading/trailing underscores
        slug = slug.strip('_')

        return slug if slug else "unsectioned"

    def save_page_as_png(self, page_number: int, output_path: str, dpi: int = 300) -> str:
        """
        Convert a single PDF page to PNG.

        Args:
            page_number: PDF page number (1-based)
            output_path: Path where PNG should be saved
            dpi: DPI for PNG conversion (default 300)

        Returns:
            Path to saved PNG file
        """
        # Convert single page
        images = convert_from_path(
            self.pdf_path,
            dpi=dpi,
            first_page=page_number,
            last_page=page_number,
            thread_count=1
        )

        if not images:
            raise ValueError(f"Failed to convert page {page_number}")

        # Save the image
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        images[0].save(output_path, 'PNG')
        logger.debug(f"Saved page {page_number} to {output_path}")

        return str(output_path)

    def save_all_pages_as_png(self, dpi: int = 300, skip_existing: bool = False) -> List[str]:
        """
        Convert all PDF pages to PNG with section-based organization.

        Creates directory structure:
        output/
        ├── 01_introductory_section/
        │   ├── page_0001_introductory.png
        │   └── ...
        ├── 02_financial_section/
        │   └── ...

        Uses multiprocessing to convert pages in parallel (optimized for Threadripper).

        Args:
            dpi: DPI for PNG conversion (default 300)
            skip_existing: If True, skip pages that already have PNG files (default False)

        Returns:
            List of saved file paths
        """
        if not self.page_metadata:
            raise ValueError("Page index not built. Call build_page_index() first.")

        logger.info("=" * 60)
        logger.info("Converting PDF pages to PNG")
        logger.info("=" * 60)

        # Determine optimal worker count (8-16 for Threadripper)
        max_workers = min(16, max(8, cpu_count() // 2))
        logger.info(f"Using {max_workers} parallel workers")

        # Prepare conversion tasks
        conversion_tasks = []
        saved_files = []  # Initialize before loop
        section_counters = {}  # Track section numbers for folder naming

        # First pass: assign section numbers
        for metadata in self.page_metadata:
            if metadata.section_name and metadata.section_level == 1:
                if metadata.section_name not in section_counters:
                    section_counters[metadata.section_name] = len(section_counters) + 1

        # Second pass: create conversion tasks
        for metadata in self.page_metadata:
            # Determine section folder
            if metadata.section_name:
                # Find the main section (level 1) for this page
                main_section = metadata.section_name
                if metadata.section_level > 1 and metadata.parent_section_name:
                    # If this is a subsection, use the parent (main) section for folder
                    main_section = metadata.parent_section_name

                section_num = section_counters.get(main_section, 0)
                section_slug = self._create_section_slug(main_section)
                folder_name = f"{section_num:02d}_{section_slug}"
            else:
                folder_name = "00_unsectioned"

            # Create filename
            page_slug = self._create_section_slug(metadata.section_name)
            filename = f"page_{metadata.pdf_page_num:04d}_{page_slug}.png"

            # Full output path
            output_path = self.output_dir / folder_name / filename

            # Skip if file exists and skip_existing is True
            if skip_existing and output_path.exists():
                # Still track it as saved
                saved_files.append(str(output_path))
                continue

            conversion_tasks.append({
                'pdf_path': str(self.pdf_path),
                'page_number': metadata.pdf_page_num,
                'output_path': str(output_path),
                'dpi': dpi,
                'metadata_index': self.page_metadata.index(metadata)
            })

        # Report skipped files
        if skip_existing:
            skipped_count = len(self.page_metadata) - len(conversion_tasks)
            if skipped_count > 0:
                logger.info(f"Skipping {skipped_count} existing files")

        # Convert pages using multiprocessing
        if conversion_tasks:
            logger.info(f"Converting {len(conversion_tasks)} pages at {dpi} DPI...")
        else:
            logger.info("All pages already converted")
            return saved_files

        # Use multiprocessing pool
        with Pool(processes=max_workers) as pool:
            # Use tqdm for progress bar
            with tqdm(total=len(conversion_tasks), desc="Converting pages", unit="page") as pbar:
                for result in pool.imap(_convert_page_worker, conversion_tasks):
                    saved_files.append(result['output_path'])
                    # Update metadata with PNG file path
                    self.page_metadata[result['metadata_index']].png_file = result['output_path']
                    pbar.update(1)

        logger.info(f"✓ Converted {len(saved_files)} pages to PNG")

        # Summary by section
        sections_created = set()
        for task in conversion_tasks:
            folder = Path(task['output_path']).parent.name
            sections_created.add(folder)

        logger.info(f"  Created {len(sections_created)} section folders")

        return saved_files

    def save_section_as_png(self, section_name: str, dpi: int = 300, skip_existing: bool = False) -> List[str]:
        """
        Convert pages from a specific section to PNG.

        Useful for:
        - Testing with small subset
        - Re-exporting specific sections
        - Handling failed conversions

        Args:
            section_name: Name of section to export (must match TOC section name)
            dpi: DPI for PNG conversion (default 300)
            skip_existing: If True, skip pages that already have PNG files (default False)

        Returns:
            List of saved file paths
        """
        if not self.page_metadata:
            raise ValueError("Page index not built. Call build_page_index() first.")

        # Filter pages for this section
        # Match pages where section_name matches OR parent_section_name matches (for subsections)
        section_pages = [
            m for m in self.page_metadata
            if m.section_name == section_name or m.parent_section_name == section_name
        ]

        if not section_pages:
            logger.warning(f"No pages found for section: {section_name}")
            return []

        logger.info("=" * 60)
        logger.info(f"Converting section: {section_name}")
        logger.info("=" * 60)
        logger.info(f"Section contains {len(section_pages)} pages")

        # Temporarily replace page_metadata with filtered list
        original_metadata = self.page_metadata
        self.page_metadata = section_pages

        try:
            # Use existing save_all_pages_as_png with filtered metadata
            saved_files = self.save_all_pages_as_png(dpi=dpi, skip_existing=skip_existing)
        finally:
            # Restore original metadata
            self.page_metadata = original_metadata

        return saved_files

    def save_page_range_as_png(self, start_page: int, end_page: int, dpi: int = 300, skip_existing: bool = False) -> List[str]:
        """
        Convert a range of PDF pages to PNG.

        Useful for:
        - Testing with small subset
        - Re-exporting specific page ranges
        - Handling failed conversions

        Args:
            start_page: First PDF page number (1-based, inclusive)
            end_page: Last PDF page number (1-based, inclusive)
            dpi: DPI for PNG conversion (default 300)
            skip_existing: If True, skip pages that already have PNG files (default False)

        Returns:
            List of saved file paths
        """
        if not self.page_metadata:
            raise ValueError("Page index not built. Call build_page_index() first.")

        # Validate range
        if start_page < 1:
            raise ValueError("start_page must be >= 1")
        if end_page < start_page:
            raise ValueError("end_page must be >= start_page")

        # Filter pages in range
        range_pages = [
            m for m in self.page_metadata
            if start_page <= m.pdf_page_num <= end_page
        ]

        if not range_pages:
            logger.warning(f"No pages found in range {start_page}-{end_page}")
            return []

        logger.info("=" * 60)
        logger.info(f"Converting page range: {start_page}-{end_page}")
        logger.info("=" * 60)
        logger.info(f"Range contains {len(range_pages)} pages")

        # Temporarily replace page_metadata with filtered list
        original_metadata = self.page_metadata
        self.page_metadata = range_pages

        try:
            # Use existing save_all_pages_as_png with filtered metadata
            saved_files = self.save_all_pages_as_png(dpi=dpi, skip_existing=skip_existing)
        finally:
            # Restore original metadata
            self.page_metadata = original_metadata

        return saved_files

    def export_metadata(self, output_file: str = "cafr_metadata.json") -> str:
        """
        Export comprehensive metadata to JSON file.

        Creates a JSON file containing:
        - Source PDF information
        - TOC entries
        - Page metadata (all pages)
        - Processing statistics

        Args:
            output_file: Path to output JSON file (default: "cafr_metadata.json")

        Returns:
            Path to created JSON file

        Raises:
            ValueError: If page_metadata not built or other validation errors
        """
        if not self.page_metadata:
            raise ValueError("Page index not built. Call build_page_index() first.")

        logger.info("=" * 60)
        logger.info("Exporting metadata to JSON")
        logger.info("=" * 60)

        # Prepare output path
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = self.output_dir / output_path

        # Build metadata structure
        metadata = {
            "source_pdf": str(self.pdf_path),
            "total_pages": len(self.page_metadata),
            "processed_date": datetime.now().strftime("%Y-%m-%d"),
            "toc_entries": [],
            "pages": [],
            "statistics": {}
        }

        # Export TOC entries
        for entry in self.toc_entries:
            toc_dict = {
                "section_name": entry.section_name,
                "page_number": entry.page_number,
                "level": entry.level,
                "parent": entry.parent
            }
            metadata["toc_entries"].append(toc_dict)

        # Export page metadata
        for page in self.page_metadata:
            page_dict = {
                "pdf_page": page.pdf_page_num,
                "footer_page": page.footer_page_num,
                "section": page.section_name,
                "section_level": page.section_level,
                "header_text": page.header_text,
                "parent_section": page.parent_section_name,
                "png_file": page.png_file
            }
            metadata["pages"].append(page_dict)

        # Calculate statistics
        pages_with_numbers = sum(1 for p in self.page_metadata if p.footer_page_num)
        pages_without_numbers = len(self.page_metadata) - pages_with_numbers
        pages_with_sections = sum(1 for p in self.page_metadata if p.section_name)
        pages_without_sections = len(self.page_metadata) - pages_with_sections
        png_files_created = sum(1 for p in self.page_metadata if p.png_file)

        # Count sections by level
        main_sections = len([e for e in self.toc_entries if e.level == 1])
        subsections = len([e for e in self.toc_entries if e.level > 1])

        metadata["statistics"] = {
            "sections_count": len(self.toc_entries),
            "main_sections": main_sections,
            "subsections": subsections,
            "pages_with_numbers": pages_with_numbers,
            "pages_without_numbers": pages_without_numbers,
            "pages_with_sections": pages_with_sections,
            "pages_without_sections": pages_without_sections,
            "png_files_created": png_files_created
        }

        # Write JSON file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Metadata exported to: {output_path}")
        logger.info(f"  Total pages: {metadata['total_pages']}")
        logger.info(f"  TOC entries: {len(metadata['toc_entries'])}")
        logger.info(f"  PNG files: {png_files_created}")

        return str(output_path)

    def generate_report(self, output_file: str = "cafr_report.txt") -> str:
        """
        Generate human-readable text report.

        Creates a formatted text report containing:
        - PDF information and processing date
        - Table of Contents
        - Page mapping summary by section
        - Issues and warnings
        - Output files listing
        - Summary statistics

        Args:
            output_file: Path to output report file (default: "cafr_report.txt")

        Returns:
            Path to created report file

        Raises:
            ValueError: If page_metadata not built
        """
        if not self.page_metadata:
            raise ValueError("Page index not built. Call build_page_index() first.")

        logger.info("=" * 60)
        logger.info("Generating human-readable report")
        logger.info("=" * 60)

        # Prepare output path
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = self.output_dir / output_path

        # Build report content
        lines = []

        # Header
        lines.append("=" * 70)
        lines.append("CAFR PROCESSING REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"PDF: {self.pdf_path.name}")
        lines.append(f"Total Pages: {len(self.page_metadata)}")
        lines.append(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Table of Contents
        lines.append("TABLE OF CONTENTS")
        lines.append("-" * 70)

        for entry in self.toc_entries:
            # Indentation based on level
            indent = "  " * (entry.level - 1)
            section_display = f"{indent}{entry.section_name}"

            # Calculate dots to align page numbers
            dots_length = 50 - len(section_display)
            dots = "." * max(2, dots_length)

            lines.append(f"{section_display} {dots} {entry.page_number}")

        lines.append("")

        # Page Mapping Summary
        lines.append("PAGE MAPPING SUMMARY")
        lines.append("-" * 70)

        # Group pages by main section (level 1)
        main_sections = [e for e in self.toc_entries if e.level == 1]

        for i, section_entry in enumerate(main_sections):
            section_name = section_entry.section_name
            section_start = section_entry.page_number

            # Find end page (start of next section or last page)
            if i + 1 < len(main_sections):
                section_end = main_sections[i + 1].page_number - 1
            else:
                # Last section - find highest page number in this section
                section_pages = [
                    p for p in self.page_metadata
                    if p.section_name == section_name or p.parent_section_name == section_name
                ]
                if section_pages:
                    section_end = max(
                        p.pdf_page_num for p in section_pages
                        if p.footer_page_num  # Only count pages with numbers
                    ) if any(p.footer_page_num for p in section_pages) else section_start
                else:
                    section_end = section_start

            # Count pages and PNG files in this section
            section_pages = [
                p for p in self.page_metadata
                if p.section_name == section_name or p.parent_section_name == section_name
            ]

            page_count = len(section_pages)
            png_count = sum(1 for p in section_pages if p.png_file)

            # Status
            if png_count == page_count and page_count > 0:
                status = "✓ Complete"
            elif png_count > 0:
                status = f"⚠ Partial ({png_count}/{page_count})"
            else:
                status = "✗ No PNGs"

            lines.append(f"Section: {section_name}")
            lines.append(f"  Pages: {section_start}-{section_end} ({page_count} pages)")
            lines.append(f"  PNG Files: {png_count} created")
            lines.append(f"  Status: {status}")
            lines.append("")

        # Issues/Warnings
        lines.append("ISSUES/WARNINGS")
        lines.append("-" * 70)

        issues = []

        # Check for pages without page numbers
        pages_without_numbers = [p for p in self.page_metadata if not p.footer_page_num]
        if pages_without_numbers:
            # Group consecutive pages
            page_ranges = self._group_consecutive_pages([p.pdf_page_num for p in pages_without_numbers])
            for start, end in page_ranges:
                if start == end:
                    issues.append(f"- Page {start}: No page number detected")
                else:
                    issues.append(f"- Pages {start}-{end}: No page numbers detected")

        # Check for pages without sections
        pages_without_sections = [p for p in self.page_metadata if not p.section_name]
        if pages_without_sections:
            page_ranges = self._group_consecutive_pages([p.pdf_page_num for p in pages_without_sections])
            for start, end in page_ranges:
                if start == end:
                    issues.append(f"- Page {start}: Not mapped to any section")
                else:
                    issues.append(f"- Pages {start}-{end}: Not mapped to any section")

        # Check for very long headers (truncation warning)
        for page in self.page_metadata:
            if page.header_text and len(page.header_text) > 100:
                issues.append(f"- Page {page.pdf_page_num}: Header text very long ({len(page.header_text)} chars)")

        # Check for pages without PNG files
        pages_without_png = [p for p in self.page_metadata if not p.png_file]
        if pages_without_png and any(p.png_file for p in self.page_metadata):
            # Only warn if some PNGs were created
            page_ranges = self._group_consecutive_pages([p.pdf_page_num for p in pages_without_png])
            for start, end in page_ranges:
                if start == end:
                    issues.append(f"- Page {start}: PNG file not created")
                else:
                    issues.append(f"- Pages {start}-{end}: PNG files not created")

        if issues:
            for issue in issues:
                lines.append(issue)
        else:
            lines.append("- No issues detected")

        lines.append("")

        # Output Files
        lines.append("OUTPUT FILES")
        lines.append("-" * 70)

        # Check for metadata file
        metadata_file = self.output_dir / "cafr_metadata.json"
        if metadata_file.exists():
            lines.append(f"Metadata: {metadata_file.relative_to(self.output_dir.parent)}")
        else:
            lines.append(f"Metadata: Not yet created")

        # Report file (this file)
        lines.append(f"Report: {output_path.relative_to(self.output_dir.parent) if output_path.is_relative_to(self.output_dir.parent) else output_path}")

        # PNG files directory
        png_count = sum(1 for p in self.page_metadata if p.png_file)
        if png_count > 0:
            lines.append(f"PNG Files: {self.output_dir}/ ({png_count} files)")
        else:
            lines.append(f"PNG Files: Not yet created")

        lines.append("")

        # Summary Statistics
        lines.append("SUMMARY STATISTICS")
        lines.append("-" * 70)

        pages_with_numbers = sum(1 for p in self.page_metadata if p.footer_page_num)
        pages_with_sections = sum(1 for p in self.page_metadata if p.section_name)
        png_files_created = sum(1 for p in self.page_metadata if p.png_file)
        main_sections_count = len([e for e in self.toc_entries if e.level == 1])
        subsections_count = len([e for e in self.toc_entries if e.level > 1])

        lines.append(f"Total Pages: {len(self.page_metadata)}")
        lines.append(f"Pages with Numbers: {pages_with_numbers}")
        lines.append(f"Pages Mapped to Sections: {pages_with_sections}")
        lines.append(f"PNG Files Created: {png_files_created}")
        lines.append(f"TOC Entries: {len(self.toc_entries)}")
        lines.append(f"  Main Sections: {main_sections_count}")
        lines.append(f"  Subsections: {subsections_count}")

        lines.append("")
        lines.append("=" * 70)

        # Write report file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        logger.info(f"✓ Report generated: {output_path}")
        logger.info(f"  {len(lines)} lines")
        logger.info(f"  {len(issues)} issues/warnings")

        return str(output_path)

    def _group_consecutive_pages(self, page_numbers: List[int]) -> List[Tuple[int, int]]:
        """
        Group consecutive page numbers into ranges.

        Args:
            page_numbers: List of page numbers

        Returns:
            List of (start, end) tuples for consecutive ranges
        """
        if not page_numbers:
            return []

        # Sort page numbers
        sorted_pages = sorted(page_numbers)

        ranges = []
        start = sorted_pages[0]
        end = sorted_pages[0]

        for i in range(1, len(sorted_pages)):
            if sorted_pages[i] == end + 1:
                # Consecutive
                end = sorted_pages[i]
            else:
                # Gap - save current range and start new one
                ranges.append((start, end))
                start = sorted_pages[i]
                end = sorted_pages[i]

        # Save last range
        ranges.append((start, end))

        return ranges

    def process_cafr(
        self,
        toc_screenshots: List[str],
        dpi: int = 300,
        skip_png: bool = False,
        section: Optional[str] = None,
        verify_only: bool = False,
        auto_confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Process a complete CAFR PDF.

        Complete workflow:
        1. Load PDF and TOC from screenshot(s)
        2. Display TOC for user verification
        3. Ask for confirmation to proceed (unless auto_confirm=True)
        4. Build page index
        5. Save pages as PNG (unless skip_png=True)
        6. Export metadata JSON
        7. Generate human-readable report
        8. Print summary statistics

        Args:
            toc_screenshots: List of TOC screenshot paths
            dpi: DPI for PNG conversion (default 300)
            skip_png: If True, skip PNG conversion (default False)
            section: If provided, only process this section (default None = all)
            verify_only: If True, only verify TOC and exit (default False)
            auto_confirm: If True, skip user confirmation prompt (default False)

        Returns:
            Processing summary dictionary
        """
        logger.info("=" * 60)
        logger.info("CAFR PDF Processing Started")
        logger.info("=" * 60)

        # Step 1: Get page count
        page_count = self.get_page_count()
        logger.info(f"PDF: {self.pdf_path.name}")
        logger.info(f"Total pages: {page_count}")
        logger.info(f"Output directory: {self.output_dir}")

        # Step 2: Load TOC from screenshots
        logger.info("")
        logger.info("Loading TOC from screenshots...")
        self.toc_entries = self.load_toc_from_screenshots(toc_screenshots)
        logger.info(f"✓ Loaded {len(self.toc_entries)} TOC entries")

        # Step 3: Display TOC for review
        print()
        self.print_toc()

        # Verify TOC completeness
        verification = self.verify_toc_completeness()

        print()
        print("=" * 80)
        print("TOC Verification")
        print("=" * 80)

        if verification["is_complete"]:
            print("✓ TOC appears complete")
        else:
            print("⚠ TOC may be incomplete - please review")

        if verification["warnings"]:
            print("\nWarnings:")
            for warning in verification["warnings"]:
                print(f"  ⚠ {warning}")

        if verification["errors"]:
            print("\nErrors:")
            for error in verification["errors"]:
                print(f"  ✗ {error}")

        print("=" * 80)
        print()

        # If verify-only, stop here
        if verify_only:
            logger.info("Verify-only mode: Stopping after TOC verification")
            return {
                "pdf_file": str(self.pdf_path),
                "total_pages": page_count,
                "toc_entries": len(self.toc_entries),
                "status": "verified_only"
            }

        # Step 4: Ask for confirmation (unless auto_confirm)
        if not auto_confirm:
            print("Proceed with processing?")
            response = input("Enter 'yes' to continue, anything else to cancel: ").strip().lower()
            if response != 'yes':
                logger.info("Processing cancelled by user")
                return {
                    "pdf_file": str(self.pdf_path),
                    "total_pages": page_count,
                    "toc_entries": len(self.toc_entries),
                    "status": "cancelled"
                }
            print()

        # Step 5: Build page index
        logger.info("=" * 60)
        logger.info("Building page index...")
        logger.info("=" * 60)
        self.build_page_index()
        logger.info(f"✓ Page index built: {len(self.page_metadata)} pages")
        print()

        # Step 6: Save pages as PNG (unless skip_png)
        png_files_created = 0
        if not skip_png:
            logger.info("=" * 60)
            logger.info("Converting pages to PNG...")
            logger.info("=" * 60)

            if section:
                # Process only specific section
                logger.info(f"Processing section: {section}")
                png_files = self.save_section_as_png(section, dpi=dpi)
            else:
                # Process all pages
                png_files = self.save_all_pages_as_png(dpi=dpi)

            png_files_created = len(png_files)
            logger.info(f"✓ PNG conversion complete: {png_files_created} files created")
            print()
        else:
            logger.info("Skipping PNG conversion (--skip-png)")
            print()

        # Step 7: Export metadata JSON
        logger.info("=" * 60)
        logger.info("Exporting metadata...")
        logger.info("=" * 60)
        metadata_file = self.export_metadata()
        logger.info(f"✓ Metadata exported: {Path(metadata_file).name}")
        print()

        # Step 8: Generate human-readable report
        logger.info("=" * 60)
        logger.info("Generating report...")
        logger.info("=" * 60)
        report_file = self.generate_report()
        logger.info(f"✓ Report generated: {Path(report_file).name}")
        print()

        # Step 9: Print summary statistics
        pages_with_numbers = sum(1 for p in self.page_metadata if p.footer_page_num)
        pages_with_sections = sum(1 for p in self.page_metadata if p.section_name)
        main_sections = len([e for e in self.toc_entries if e.level == 1])

        print("=" * 80)
        print("PROCESSING SUMMARY")
        print("=" * 80)
        print(f"PDF: {self.pdf_path.name}")
        print(f"Total Pages: {page_count}")
        print(f"TOC Entries: {len(self.toc_entries)} ({main_sections} main sections)")
        print(f"Pages with Numbers: {pages_with_numbers}")
        print(f"Pages Mapped to Sections: {pages_with_sections}")
        print(f"PNG Files Created: {png_files_created}")
        print()
        print(f"Output Directory: {self.output_dir}")
        print(f"  Metadata: {Path(metadata_file).name}")
        print(f"  Report: {Path(report_file).name}")
        if png_files_created > 0:
            print(f"  PNG Files: {png_files_created} files in section directories")
        print("=" * 80)
        print()

        # Processing summary
        summary = {
            "pdf_file": str(self.pdf_path),
            "total_pages": page_count,
            "toc_entries": len(self.toc_entries),
            "pages_with_numbers": pages_with_numbers,
            "pages_with_sections": pages_with_sections,
            "png_files_created": png_files_created,
            "metadata_file": metadata_file,
            "report_file": report_file,
            "page_index": [
                {
                    "pdf_page_num": p.pdf_page_num,
                    "footer_page_num": p.footer_page_num,
                    "section_name": p.section_name,
                    "section_level": p.section_level,
                    "header_text": p.header_text,
                    "parent_section_name": p.parent_section_name,
                    "png_file": p.png_file
                }
                for p in self.page_metadata
            ],
            "processed_date": datetime.now().isoformat(),
            "status": "complete"
        }

        logger.info("✓ CAFR processing complete!")

        return summary

    def verify_processing(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify the completeness and quality of processed CAFR output.

        Performs comprehensive quality checks:
        1. PNG file count matches page count
        2. All sections have at least one page
        3. No gaps in page sequences
        4. File sizes reasonable (detect corrupted images)
        5. Metadata JSON is valid
        6. All TOC sections were found in PDF

        Args:
            output_dir: Directory to verify (default: self.output_dir)

        Returns:
            Verification report dictionary with status and issues
        """
        if output_dir is None:
            output_dir = self.output_dir
        else:
            output_dir = Path(output_dir)

        logger.info("=" * 60)
        logger.info("CAFR Processing Verification")
        logger.info("=" * 60)
        logger.info(f"Verifying: {output_dir}")
        logger.info("")

        issues = []
        warnings = []
        checks_passed = 0
        checks_total = 0

        # Check 1: Page metadata exists
        checks_total += 1
        if not self.page_metadata:
            issues.append("No page metadata found - run build_page_index() first")
            logger.error("✗ Page metadata missing")
        else:
            checks_passed += 1
            logger.info(f"✓ Page metadata loaded: {len(self.page_metadata)} pages")

        # Check 2: Metadata JSON exists and is valid
        checks_total += 1
        metadata_path = output_dir / "cafr_metadata.json"
        metadata_valid = False
        metadata_data = None

        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata_data = json.load(f)
                checks_passed += 1
                metadata_valid = True
                logger.info("✓ Metadata JSON exists and is valid")
            except json.JSONDecodeError as e:
                issues.append(f"Metadata JSON is corrupted: {e}")
                logger.error(f"✗ Metadata JSON is corrupted: {e}")
        else:
            warnings.append("Metadata JSON not found (may not have been exported yet)")
            logger.warning("⚠ Metadata JSON not found")

        # Check 3: PNG files vs page count
        checks_total += 1
        sections_dir = output_dir / "sections"
        png_files = []

        if sections_dir.exists():
            png_files = list(sections_dir.rglob("*.png"))
            expected_png_count = len(self.page_metadata)

            # Count pages that should have PNGs
            pages_with_pngs = sum(1 for p in self.page_metadata if p.png_file)

            if pages_with_pngs == 0:
                warnings.append("No PNG files created (processing may have used --skip-png)")
                logger.warning("⚠ No PNG files created")
            elif len(png_files) == pages_with_pngs:
                checks_passed += 1
                logger.info(f"✓ PNG file count matches: {len(png_files)} files")
            else:
                issues.append(f"PNG count mismatch: expected {pages_with_pngs}, found {len(png_files)}")
                logger.error(f"✗ PNG count mismatch: expected {pages_with_pngs}, found {len(png_files)}")
        else:
            warnings.append("Sections directory not found (processing may have used --skip-png)")
            logger.warning("⚠ Sections directory not found")

        # Check 4: All sections have at least one page
        checks_total += 1
        if self.toc_entries:
            sections_with_pages = set()
            for page in self.page_metadata:
                if page.section_name:
                    sections_with_pages.add(page.section_name)

            toc_sections = set(entry.section_name for entry in self.toc_entries if entry.level == 1)
            missing_sections = toc_sections - sections_with_pages

            if not missing_sections:
                checks_passed += 1
                logger.info(f"✓ All {len(toc_sections)} main sections found in page index")
            else:
                issues.append(f"Sections without pages: {', '.join(missing_sections)}")
                logger.error(f"✗ {len(missing_sections)} sections have no pages: {', '.join(list(missing_sections)[:3])}")
        else:
            warnings.append("No TOC entries loaded")
            logger.warning("⚠ No TOC entries to verify")

        # Check 5: Check for gaps in page sequences
        checks_total += 1
        page_numbers = sorted([p.footer_page_num for p in self.page_metadata if p.footer_page_num is not None])

        if page_numbers:
            gaps = []
            for i in range(len(page_numbers) - 1):
                if page_numbers[i+1] - page_numbers[i] > 1:
                    gaps.append((page_numbers[i], page_numbers[i+1]))

            if not gaps:
                checks_passed += 1
                logger.info(f"✓ No gaps in page number sequence ({len(page_numbers)} numbered pages)")
            else:
                warnings.append(f"Found {len(gaps)} gaps in page numbering")
                logger.warning(f"⚠ {len(gaps)} gaps in page numbering: {gaps[:3]}")
        else:
            warnings.append("No footer page numbers found in PDF")
            logger.warning("⚠ No footer page numbers found")

        # Check 6: Pages without page numbers
        checks_total += 1
        pages_without_numbers = [p for p in self.page_metadata if p.footer_page_num is None]

        if len(pages_without_numbers) == 0:
            checks_passed += 1
            logger.info("✓ All pages have footer page numbers")
        else:
            page_ranges = []
            if pages_without_numbers:
                start = pages_without_numbers[0].pdf_page_num
                end = pages_without_numbers[0].pdf_page_num
                for p in pages_without_numbers[1:]:
                    if p.pdf_page_num == end + 1:
                        end = p.pdf_page_num
                    else:
                        page_ranges.append(f"{start}-{end}" if start != end else str(start))
                        start = p.pdf_page_num
                        end = p.pdf_page_num
                page_ranges.append(f"{start}-{end}" if start != end else str(start))

            warnings.append(f"{len(pages_without_numbers)} pages without footer numbers (PDF pages: {', '.join(page_ranges)})")
            logger.warning(f"⚠ {len(pages_without_numbers)} pages without footer numbers")

        # Check 7: File sizes (detect corrupted or unusually small/large images)
        checks_total += 1
        if png_files:
            file_sizes = [f.stat().st_size for f in png_files]
            avg_size = sum(file_sizes) / len(file_sizes)
            min_size = min(file_sizes)
            max_size = max(file_sizes)

            # Flag files that are unusually small (< 10% of average) or large (> 10x average)
            suspicious_files = []
            for f in png_files:
                size = f.stat().st_size
                if size < avg_size * 0.1 or size > avg_size * 10:
                    suspicious_files.append((f.name, size))

            if not suspicious_files:
                checks_passed += 1
                logger.info(f"✓ All PNG file sizes reasonable (avg: {avg_size/1024/1024:.1f} MB)")
            else:
                warnings.append(f"{len(suspicious_files)} PNG files have unusual sizes")
                logger.warning(f"⚠ {len(suspicious_files)} PNG files have unusual sizes")
        else:
            # Skip this check if no PNGs
            pass

        # Check 8: Report file exists
        checks_total += 1
        report_path = output_dir / "cafr_report.txt"
        if report_path.exists():
            checks_passed += 1
            logger.info("✓ Report file exists")
        else:
            warnings.append("Report file not found (may not have been generated yet)")
            logger.warning("⚠ Report file not found")

        # Calculate total size
        total_size = 0
        if sections_dir.exists():
            for f in sections_dir.rglob("*"):
                if f.is_file():
                    total_size += f.stat().st_size

        # Generate verification report
        logger.info("")
        logger.info("=" * 60)
        logger.info("VERIFICATION REPORT")
        logger.info("=" * 60)
        logger.info(f"Checks Passed: {checks_passed}/{checks_total}")
        logger.info(f"Issues: {len(issues)}")
        logger.info(f"Warnings: {len(warnings)}")
        logger.info("")

        if issues:
            logger.info("ISSUES:")
            for issue in issues:
                logger.info(f"  ✗ {issue}")
            logger.info("")

        if warnings:
            logger.info("WARNINGS:")
            for warning in warnings:
                logger.info(f"  ⚠ {warning}")
            logger.info("")

        logger.info(f"Total pages: {len(self.page_metadata)}")
        logger.info(f"PNG files: {len(png_files)}")
        logger.info(f"Total size: {total_size / 1024 / 1024:.1f} MB")
        logger.info("=" * 60)

        verification_result = {
            "status": "passed" if len(issues) == 0 else "failed",
            "checks_passed": checks_passed,
            "checks_total": checks_total,
            "issues": issues,
            "warnings": warnings,
            "total_pages": len(self.page_metadata),
            "png_files": len(png_files),
            "total_size_mb": total_size / 1024 / 1024,
            "metadata_valid": metadata_valid
        }

        return verification_result

    def fix_issues(
        self,
        verification_result: Optional[Dict[str, Any]] = None,
        reprocess_failed_pages: bool = True,
        re_ocr_toc: bool = False,
        toc_screenshots: Optional[List[str]] = None,
        dpi: int = 300
    ) -> Dict[str, Any]:
        """
        Attempt to fix issues found during verification.

        Repair strategies:
        1. Re-process pages that failed PNG conversion
        2. Re-OCR TOC if sections are missing
        3. Suggest manual intervention if automated fixes fail

        Args:
            verification_result: Result from verify_processing() (optional - will run verification if not provided)
            reprocess_failed_pages: Attempt to re-generate missing PNG files
            re_ocr_toc: Re-run TOC OCR if sections are missing
            toc_screenshots: TOC screenshot paths (required if re_ocr_toc=True)
            dpi: DPI for PNG conversion

        Returns:
            Fix report dictionary with actions taken and results
        """
        logger.info("=" * 60)
        logger.info("CAFR Issue Repair")
        logger.info("=" * 60)
        logger.info("")

        # Run verification if not provided
        if verification_result is None:
            logger.info("Running verification first...")
            verification_result = self.verify_processing()
            print()

        issues_fixed = []
        issues_remaining = []
        manual_intervention_needed = []

        # If no issues, nothing to fix
        if verification_result["status"] == "passed" and not verification_result["issues"]:
            logger.info("✓ No issues found - nothing to fix!")
            return {
                "status": "no_issues",
                "issues_fixed": [],
                "issues_remaining": [],
                "manual_intervention_needed": []
            }

        # Fix 1: Re-process missing PNG files
        if reprocess_failed_pages:
            logger.info("Checking for missing PNG files...")

            # Find pages that should have PNGs but don't
            missing_pngs = []
            sections_dir = self.output_dir / "sections"

            for page in self.page_metadata:
                if page.png_file:
                    png_path = self.output_dir / page.png_file
                    if not png_path.exists():
                        missing_pngs.append(page)

            if missing_pngs:
                logger.info(f"Found {len(missing_pngs)} missing PNG files - attempting to regenerate...")

                try:
                    # Re-convert missing pages
                    for page in missing_pngs:
                        logger.info(f"  Re-processing PDF page {page.pdf_page_num}...")

                        # Determine section directory
                        if page.section_name:
                            section_slug = page.section_name.lower().replace(' ', '_').replace('/', '_')
                            section_dir = sections_dir / f"{page.section_level:02d}_{section_slug}"
                        else:
                            section_dir = sections_dir / "00_uncategorized"

                        section_dir.mkdir(parents=True, exist_ok=True)

                        # Convert page to PNG
                        images = convert_from_path(
                            str(self.pdf_path),
                            dpi=dpi,
                            first_page=page.pdf_page_num,
                            last_page=page.pdf_page_num,
                            thread_count=1
                        )

                        if images:
                            # Generate filename
                            if page.footer_page_num:
                                filename = f"page_{page.footer_page_num:04d}.png"
                            else:
                                filename = f"page_pdf{page.pdf_page_num:04d}.png"

                            output_path = section_dir / filename
                            images[0].save(output_path, "PNG")

                            # Update page metadata
                            page.png_file = str(output_path.relative_to(self.output_dir))

                    issues_fixed.append(f"Regenerated {len(missing_pngs)} missing PNG files")
                    logger.info(f"✓ Regenerated {len(missing_pngs)} PNG files")

                except Exception as e:
                    issues_remaining.append(f"Failed to regenerate PNG files: {e}")
                    logger.error(f"✗ Failed to regenerate PNG files: {e}")
            else:
                logger.info("✓ No missing PNG files found")

        # Fix 2: Re-OCR TOC if sections are missing
        if re_ocr_toc:
            if not toc_screenshots:
                manual_intervention_needed.append("Re-OCR requested but no TOC screenshots provided - use toc_screenshots parameter")
                logger.warning("⚠ Re-OCR requested but no TOC screenshots provided")
            else:
                logger.info("Re-running TOC OCR...")

                try:
                    old_entry_count = len(self.toc_entries)
                    self.toc_entries = self.load_toc_from_screenshots(toc_screenshots)
                    new_entry_count = len(self.toc_entries)

                    if new_entry_count > old_entry_count:
                        issues_fixed.append(f"Re-OCR found {new_entry_count - old_entry_count} additional TOC entries")
                        logger.info(f"✓ Re-OCR found {new_entry_count - old_entry_count} additional entries")

                        # Rebuild page index with new TOC
                        logger.info("Rebuilding page index with updated TOC...")
                        self.build_page_index()
                        logger.info("✓ Page index rebuilt")
                    else:
                        logger.info("⚠ Re-OCR did not find additional entries")
                        issues_remaining.append("Re-OCR did not improve TOC - may need better screenshots")

                except Exception as e:
                    issues_remaining.append(f"Failed to re-OCR TOC: {e}")
                    logger.error(f"✗ Failed to re-OCR TOC: {e}")

        # Analyze remaining issues and suggest manual intervention
        for issue in verification_result.get("issues", []):
            if "PNG count mismatch" in issue and not reprocess_failed_pages:
                manual_intervention_needed.append("PNG files missing - run fix_issues() with reprocess_failed_pages=True")
            elif "Sections without pages" in issue and not re_ocr_toc:
                manual_intervention_needed.append("Sections not mapped to pages - verify TOC screenshots are complete or run fix_issues() with re_ocr_toc=True")
            elif "Metadata JSON is corrupted" in issue:
                manual_intervention_needed.append("Metadata JSON is corrupted - re-run export_metadata()")
            elif issue not in [f for f in issues_fixed]:
                # Issue wasn't addressed by automated fixes
                if "Sections without pages" not in issue and "PNG count mismatch" not in issue:
                    issues_remaining.append(issue)

        # Summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("REPAIR SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Issues Fixed: {len(issues_fixed)}")
        logger.info(f"Issues Remaining: {len(issues_remaining)}")
        logger.info(f"Manual Intervention Needed: {len(manual_intervention_needed)}")
        logger.info("")

        if issues_fixed:
            logger.info("FIXED:")
            for fix in issues_fixed:
                logger.info(f"  ✓ {fix}")
            logger.info("")

        if issues_remaining:
            logger.info("REMAINING:")
            for issue in issues_remaining:
                logger.info(f"  ✗ {issue}")
            logger.info("")

        if manual_intervention_needed:
            logger.info("MANUAL INTERVENTION NEEDED:")
            for suggestion in manual_intervention_needed:
                logger.info(f"  ⚠ {suggestion}")
            logger.info("")

        logger.info("=" * 60)

        return {
            "status": "complete",
            "issues_fixed": issues_fixed,
            "issues_remaining": issues_remaining,
            "manual_intervention_needed": manual_intervention_needed
        }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='CAFR PDF Stripper - Municipal Financial Report Processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single CAFR
  %(prog)s --pdf vallejo_2024.pdf --toc toc.png --output vallejo_2024/

  # Process with multiple TOC screenshots
  %(prog)s --pdf report.pdf --toc toc1.png toc2.png --output output/

  # Specify DPI for PNG conversion
  %(prog)s --pdf report.pdf --toc toc.png --output output/ --dpi 300

  # Only generate metadata (skip PNG conversion)
  %(prog)s --pdf report.pdf --toc toc.png --output output/ --skip-png

  # Process only one section
  %(prog)s --pdf report.pdf --toc toc.png --output output/ --section "Financial Section"

  # Verify TOC only (no processing)
  %(prog)s --pdf report.pdf --toc toc.png --output output/ --verify-only
        """
    )

    parser.add_argument(
        '--pdf',
        required=True,
        help='Path to CAFR PDF file'
    )

    parser.add_argument(
        '--toc',
        nargs='+',
        required=True,
        help='Path(s) to TOC screenshot(s)'
    )

    parser.add_argument(
        '--output',
        required=True,
        help='Output directory for processed files'
    )

    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for PNG conversion (default: 300)'
    )

    parser.add_argument(
        '--skip-png',
        action='store_true',
        help='Only generate metadata and reports, skip PNG conversion'
    )

    parser.add_argument(
        '--section',
        type=str,
        default=None,
        help='Process only the specified section (e.g., "Financial Section")'
    )

    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only load and verify TOC, do not process'
    )

    parser.add_argument(
        '--yes',
        action='store_true',
        help='Auto-confirm processing (skip confirmation prompt)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Initialize stripper
        stripper = PDFStripper(args.pdf, args.output)

        # Process CAFR
        summary = stripper.process_cafr(
            toc_screenshots=args.toc,
            dpi=args.dpi,
            skip_png=args.skip_png,
            section=args.section,
            verify_only=args.verify_only,
            auto_confirm=args.yes
        )

        # Print completion message
        if summary["status"] == "complete":
            print("✓ Processing complete!")
        elif summary["status"] == "verified_only":
            print("✓ Verification complete!")
        elif summary["status"] == "cancelled":
            print("Processing cancelled by user")

    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.error(f"Error processing CAFR: {e}", exc_info=True)
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
