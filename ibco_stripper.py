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
    png_file: Optional[str] = None


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

    def process_cafr(self, toc_screenshots: List[str], dpi: int = 300) -> Dict[str, Any]:
        """
        Process a complete CAFR PDF.

        Args:
            toc_screenshots: List of TOC screenshot paths
            dpi: DPI for PNG conversion (default 300)

        Returns:
            Processing summary
        """
        logger.info("=" * 60)
        logger.info("CAFR PDF Processing Started")
        logger.info("=" * 60)

        # Get page count
        page_count = self.get_page_count()
        logger.info(f"PDF contains {page_count} pages")

        # Load TOC from multiple screenshots
        logger.info("Loading TOC from screenshots...")
        self.toc_entries = self.load_toc_from_screenshots(toc_screenshots)

        logger.info(f"Loaded {len(self.toc_entries)} TOC entries")

        # Print TOC for review
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

        # Processing summary
        summary = {
            "pdf_file": str(self.pdf_path),
            "total_pages": page_count,
            "toc_entries": len(self.toc_entries),
            "processed_date": datetime.now().isoformat(),
            "status": "initialized"
        }

        logger.info("=" * 60)
        logger.info("CAFR PDF Processing Summary")
        logger.info("=" * 60)
        logger.info(json.dumps(summary, indent=2))

        return summary


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
        '--verify-only',
        action='store_true',
        help='Only load and verify TOC, do not process'
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
        summary = stripper.process_cafr(args.toc, dpi=args.dpi)

        print("\nProcessing complete!")
        print(f"Output directory: {args.output}")

    except Exception as e:
        logger.error(f"Error processing CAFR: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
