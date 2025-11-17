#!/usr/bin/env python3
"""
PROMPT 1C: Page Number Extraction Testing

Tests page number and header extraction on a real CAFR PDF:
- Iterates through all pages
- Extracts sequential page number (PDF order)
- Extracts footer page number (document pagination)
- Extracts header text
- Identifies format changes (Roman → Arabic)
- Reports missing page numbers

Usage:
    python test_page_extraction.py <path_to_cafr.pdf>
    python test_page_extraction.py sample_cafr.pdf
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

import pdfplumber

import config
from ibco_stripper import PDFStripper


class PageExtractionTester:
    """Tests page extraction functionality on real CAFR PDFs."""

    def __init__(self, pdf_path: str):
        """
        Initialize the tester.

        Args:
            pdf_path: Path to CAFR PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # We'll use PDFStripper's methods but don't need full initialization
        self.stripper = None

    def test_extraction(self) -> dict:
        """
        Test page extraction on all pages of the PDF.

        Returns:
            Dictionary with test results and statistics
        """
        print("=" * 80)
        print(f"CAFR Page Extraction Test: {self.pdf_path.name}")
        print("=" * 80)
        print()

        results = {
            'pdf_file': str(self.pdf_path),
            'total_pages': 0,
            'pages_with_numbers': 0,
            'pages_without_numbers': 0,
            'format_changes': [],
            'missing_pages': [],
            'page_data': []
        }

        # Create a temporary stripper for methods (won't use full init)
        # We need to access the extraction methods
        temp_stripper = type('TempStripper', (), {
            '_parse_page_number': lambda self, text: self._parse_impl(text)
        })()

        # Add the actual parsing implementation
        def parse_impl(text):
            import re
            text = text.strip()

            # Pattern 1: Just a number
            match = re.search(r'^\s*(\d+)\s*$', text)
            if match:
                return match.group(1)

            # Pattern 2: Roman numerals
            roman_pattern = r'^\s*([ivxlcdm]+)\s*$'
            match = re.search(roman_pattern, text, re.IGNORECASE)
            if match:
                roman = match.group(1).lower()
                if config.is_roman_numeral(roman):
                    return roman

            # Pattern 3: Number with separators
            match = re.search(r'[-~]\s*(\d+)\s*[-~]', text)
            if match:
                return match.group(1)

            # Pattern 4: Any number
            match = re.search(r'(\d+)', text)
            if match:
                return match.group(1)

            # Pattern 5: Any roman numeral
            match = re.search(r'\b([ivxlcdm]+)\b', text, re.IGNORECASE)
            if match:
                roman = match.group(1).lower()
                if config.is_roman_numeral(roman):
                    return roman

            return None

        temp_stripper._parse_impl = parse_impl

        # Open PDF and process pages
        with pdfplumber.open(self.pdf_path) as pdf:
            results['total_pages'] = len(pdf.pages)

            print(f"Processing {len(pdf.pages)} pages...")
            print()
            print(f"{'PDF Page':<10} {'Footer Page':<15} {'Header Text':<40} {'Notes'}")
            print("-" * 80)

            previous_format = None  # Track Roman vs Arabic format

            for i, page in enumerate(pdf.pages, start=1):
                # Extract footer page number
                footer_config = config.PDF_PROCESSING['footer_region']
                page_height = page.height
                footer_top = page_height * footer_config['top']
                footer_bbox = (0, footer_top, page.width, page_height)

                try:
                    footer_crop = page.crop(footer_bbox)
                    footer_text = footer_crop.extract_text()
                    footer_page_num = None
                    if footer_text:
                        footer_page_num = temp_stripper._parse_page_number(footer_text.strip())
                except:
                    footer_page_num = None

                # Extract header text
                header_config = config.PDF_PROCESSING['header_region']
                header_bottom = page_height * header_config['bottom']
                header_bbox = (0, 0, page.width, header_bottom)

                try:
                    header_crop = page.crop(header_bbox)
                    header_text = header_crop.extract_text()
                    if header_text:
                        header_text = ' '.join(header_text.split()).strip()
                        # Truncate if too long
                        if len(header_text) > 37:
                            header_text = header_text[:34] + "..."
                except:
                    header_text = None

                # Determine format (Roman or Arabic)
                current_format = None
                notes = []

                if footer_page_num:
                    results['pages_with_numbers'] += 1

                    # Check if Roman or Arabic
                    if config.is_roman_numeral(footer_page_num):
                        current_format = "roman"
                    elif footer_page_num.isdigit():
                        current_format = "arabic"

                    # Detect format change
                    if previous_format and current_format != previous_format:
                        notes.append(f"Format change: {previous_format} → {current_format}")
                        results['format_changes'].append({
                            'page': i,
                            'from_format': previous_format,
                            'to_format': current_format,
                            'footer_page': footer_page_num
                        })

                    previous_format = current_format
                else:
                    results['pages_without_numbers'] += 1
                    results['missing_pages'].append(i)
                    notes.append("⚠ No page number")

                # Store page data
                results['page_data'].append({
                    'pdf_page': i,
                    'footer_page': footer_page_num,
                    'header_text': header_text,
                    'format': current_format
                })

                # Print row
                footer_display = f'"{footer_page_num}"' if footer_page_num else "None"
                header_display = header_text if header_text else ""
                notes_display = " | ".join(notes) if notes else ""

                print(f"Page {i:<5} → {footer_display:<15} {header_display:<40} {notes_display}")

        print()
        return results

    def print_summary(self, results: dict):
        """
        Print summary statistics.

        Args:
            results: Test results dictionary
        """
        print("=" * 80)
        print("EXTRACTION SUMMARY")
        print("=" * 80)
        print()

        print(f"PDF File: {results['pdf_file']}")
        print(f"Total Pages: {results['total_pages']}")
        print(f"Pages with Numbers: {results['pages_with_numbers']}")
        print(f"Pages without Numbers: {results['pages_without_numbers']}")
        print()

        # Format changes
        if results['format_changes']:
            print("Format Changes Detected:")
            for change in results['format_changes']:
                print(f"  Page {change['page']:3} (PDF) → Page \"{change['footer_page']}\" (Footer): "
                      f"{change['from_format'].upper()} → {change['to_format'].upper()}")
            print()

        # Missing pages
        if results['missing_pages']:
            print(f"Pages without Page Numbers ({len(results['missing_pages'])} total):")
            # Group consecutive pages
            groups = []
            start = results['missing_pages'][0]
            end = start

            for page in results['missing_pages'][1:]:
                if page == end + 1:
                    end = page
                else:
                    groups.append((start, end))
                    start = page
                    end = page
            groups.append((start, end))

            for start, end in groups:
                if start == end:
                    print(f"  Page {start}")
                else:
                    print(f"  Pages {start}-{end}")
            print()

        # Verification status
        print("Verification Status:")
        coverage = (results['pages_with_numbers'] / results['total_pages']) * 100
        print(f"  Coverage: {coverage:.1f}% of pages have page numbers")

        if coverage >= 95:
            print("  ✓ Excellent coverage - extraction working well")
        elif coverage >= 85:
            print("  ✓ Good coverage - some pages missing numbers (expected for covers/dividers)")
        elif coverage >= 70:
            print("  ⚠ Fair coverage - consider adjusting footer region settings")
        else:
            print("  ✗ Poor coverage - footer region may need adjustment")

        print()
        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test page number and header extraction on CAFR PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with a CAFR PDF
  %(prog)s sample_cafr.pdf

  # Test with full path
  %(prog)s /path/to/vallejo_cafr_2024.pdf
        """
    )

    parser.add_argument(
        'pdf_file',
        help='Path to CAFR PDF file to test'
    )

    parser.add_argument(
        '--sample-only',
        action='store_true',
        help='Only show first 20 pages (for quick testing)'
    )

    args = parser.parse_args()

    try:
        # Run extraction test
        tester = PageExtractionTester(args.pdf_file)
        results = tester.test_extraction()
        tester.print_summary(results)

        print()
        print("✓ Page extraction test complete!")
        print()
        print("Next steps:")
        print("  - Review format changes (Roman → Arabic numbering)")
        print("  - Check if missing pages are expected (covers, dividers)")
        print("  - Ready for PROMPT 2A: TOC Screenshot Loading")
        print()

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print()
        print("Please provide a valid CAFR PDF file.", file=sys.stderr)
        print()
        print("If you don't have a sample CAFR PDF yet, you can:")
        print("  1. Download a CAFR from a municipal website")
        print("  2. Place it in the current directory")
        print("  3. Run: python test_page_extraction.py <filename.pdf>")
        return 1

    except Exception as e:
        print(f"Error during testing: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
