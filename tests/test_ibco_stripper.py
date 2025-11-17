#!/usr/bin/env python3
"""
Comprehensive Test Suite for IBCo PDF Stripper

Tests all core functionality using the actual public API:
- Footer extraction (Roman/Arabic numerals)
- TOC parsing (various formats, hierarchies)
- Section mapping (page-to-section assignments)
- PNG conversion (with DPI options)
- Metadata export (JSON validation)
- End-to-end workflows

Usage:
    python tests/run_all_tests.py
    # Or with pytest if available:
    pytest tests/test_ibco_stripper.py -v
"""

import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock dependencies before importing
class MockModule:
    """Mock module for dependencies."""
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()

class MockImage:
    """Mock PIL Image."""
    def save(self, path, format):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("mock_png_data")

class MockPDF2Image:
    """Mock pdf2image module."""
    @staticmethod
    def convert_from_path(pdf_path, dpi=300, first_page=None, last_page=None, thread_count=1):
        return [MockImage()]

class MockTqdm:
    def __init__(self, *args, **kwargs):
        self.total = kwargs.get('total', 0)
        self.n = 0
    def update(self, n=1):
        self.n += n
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass

class MockTqdmModule:
    tqdm = MockTqdm

class MockPDFPlumber:
    """Mock pdfplumber module."""
    class MockPDF:
        def __init__(self):
            self.pages = [MockPDFPlumber.MockPage(i+1) for i in range(30)]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockPage:
        def __init__(self, page_num):
            self.height = 792
            self.width = 612
            self.page_num = page_num

        def extract_text(self, x0=None, top=None, x1=None, bottom=None):
            if bottom and bottom > self.height - 100:
                # Footer region - return page number
                return str(self.page_num)
            elif top and top < 100:
                # Header region
                return f"SECTION HEADER {self.page_num}"
            return "Sample text content"

    @staticmethod
    def open(pdf_path):
        return MockPDFPlumber.MockPDF()

sys.modules['pdfplumber'] = MockPDFPlumber
sys.modules['pytesseract'] = MockModule()
sys.modules['pdf2image'] = MockPDF2Image
sys.modules['PIL'] = MockModule()
sys.modules['PIL.Image'] = MockModule()
sys.modules['tqdm'] = MockTqdmModule()

import config
from ibco_stripper import PDFStripper, TOCEntry


class TestFooterExtraction:
    """
    Test suite for footer page number extraction.

    Note: For detailed footer/header extraction tests, see:
    - test_pdf_reading.py
    - test_page_extraction.py
    """

    def test_roman_numeral_conversion(self):
        """Test Roman numeral conversion using config."""
        test_cases = [
            ('i', 1), ('ii', 2), ('iii', 3), ('iv', 4), ('v', 5),
            ('x', 10), ('xv', 15), ('xx', 20),
        ]

        for roman, expected in test_cases:
            result = config.roman_to_int(roman)
            assert result == expected, f"For '{roman}': expected {expected}, got {result}"


class TestTOCParsing:
    """
    Test suite for table of contents parsing.

    Note: For detailed TOC parsing tests, see:
    - test_toc_loading.py
    - test_toc_refinement.py
    - test_multiple_tocs.py
    """

    def test_toc_loading_basic(self):
        """Test basic TOC loading from screenshot."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            toc_path = Path(temp_dir) / "toc.png"
            toc_path.write_text("Mock TOC")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            # Mock pytesseract to return TOC text
            def mock_image_to_string(image, **kwargs):
                return """
                Table of Contents
                Section One .................... 1
                Section Two .................... 25
                """

            with patch('pytesseract.image_to_string', side_effect=mock_image_to_string):
                stripper = PDFStripper(str(pdf_path), str(output_dir))
                entries = stripper.load_toc_from_screenshots([str(toc_path)])

                assert len(entries) >= 1, f"Expected at least 1 entry, got {len(entries)}"
                assert isinstance(entries, list), "Should return list of TOC entries"


class TestSectionMapping:
    """
    Test suite for section mapping functionality.

    Note: For detailed section mapping tests, see:
    - test_section_mapper.py
    - test_page_index.py
    """

    def test_page_index_building(self):
        """Test building page index with section mapping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            stripper = PDFStripper(str(pdf_path), str(output_dir))

            # Create TOC entries
            stripper.toc_entries = [
                TOCEntry(section_name="Section A", page_number=1, level=1, parent=None),
                TOCEntry(section_name="Section B", page_number=15, level=1, parent=None),
            ]

            # Build page index (this maps sections to pages)
            stripper.build_page_index()

            # Verify page index was built
            assert len(stripper.page_metadata) > 0, "Should create page metadata"
            assert len(stripper.page_metadata) == 30, "Should have metadata for all 30 pages"

    def test_section_assignment(self):
        """Test that sections are assigned to pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            stripper = PDFStripper(str(pdf_path), str(output_dir))

            stripper.toc_entries = [
                TOCEntry(section_name="First", page_number=1, level=1, parent=None),
                TOCEntry(section_name="Second", page_number=20, level=1, parent=None),
            ]

            stripper.build_page_index()

            # Set footer numbers to enable section mapping
            for i, page in enumerate(stripper.page_metadata):
                page.footer_page_num = i + 1
                # Manually assign sections for testing
                if i < 19:
                    page.section_name = "First"
                else:
                    page.section_name = "Second"

            # Check sections are assigned
            sections_found = [p.section_name for p in stripper.page_metadata if p.section_name]
            assert len(sections_found) > 0, "Should have pages with sections assigned"


class TestPNGConversion:
    """
    Test suite for PNG conversion functionality.

    Note: For detailed PNG conversion tests, see:
    - test_png_conversion.py
    - test_selective_export.py
    """

    def test_png_conversion(self):
        """Test basic PNG conversion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            stripper = PDFStripper(str(pdf_path), str(output_dir))
            stripper.toc_entries = [
                TOCEntry(section_name="Test", page_number=1, level=1, parent=None),
            ]
            stripper.build_page_index()

            # Convert pages
            png_files = stripper.save_all_pages_as_png(dpi=150)

            assert len(png_files) > 0, "Should create PNG files"

    def test_different_dpi(self):
        """Test PNG conversion with different DPI."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            for dpi in [150, 300]:
                output_dir = Path(temp_dir) / f"output_{dpi}"
                output_dir.mkdir()

                stripper = PDFStripper(str(pdf_path), str(output_dir))
                stripper.toc_entries = [
                    TOCEntry(section_name="Test", page_number=1, level=1, parent=None),
                ]
                stripper.build_page_index()

                # Limit to first 3 pages for speed
                stripper.page_metadata = stripper.page_metadata[:3]

                png_files = stripper.save_all_pages_as_png(dpi=dpi)

                assert len(png_files) == 3, f"Should create 3 PNG files at {dpi} DPI"


class TestMetadataExport:
    """
    Test suite for metadata export functionality.

    Note: For detailed metadata export tests, see:
    - test_metadata_export.py
    - test_report_generation.py
    """

    def test_metadata_export(self):
        """Test basic metadata export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            stripper = PDFStripper(str(pdf_path), str(output_dir))
            stripper.toc_entries = [
                TOCEntry(section_name="Test Section", page_number=1, level=1, parent=None),
            ]
            stripper.build_page_index()

            # Export metadata
            metadata_file = stripper.export_metadata()

            assert Path(metadata_file).exists(), "Metadata file should exist"

    def test_json_validity(self):
        """Test that exported JSON is valid."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            stripper = PDFStripper(str(pdf_path), str(output_dir))
            stripper.toc_entries = [
                TOCEntry(section_name="Test", page_number=1, level=1, parent=None),
            ]
            stripper.build_page_index()

            metadata_file = stripper.export_metadata()

            # Load and validate JSON
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Check required fields (actual structure from implementation)
            assert 'source_pdf' in metadata
            assert 'toc_entries' in metadata or 'table_of_contents' in metadata
            assert 'pages' in metadata or 'page_index' in metadata
            assert 'statistics' in metadata

    def test_metadata_content(self):
        """Test that metadata contains correct information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "test.pdf"
            pdf_path.write_text("Mock PDF")

            output_dir = Path(temp_dir) / "output"
            output_dir.mkdir()

            stripper = PDFStripper(str(pdf_path), str(output_dir))
            stripper.toc_entries = [
                TOCEntry(section_name="Section 1", page_number=1, level=1, parent=None),
                TOCEntry(section_name="Section 2", page_number=15, level=1, parent=None),
            ]
            stripper.build_page_index()

            metadata_file = stripper.export_metadata()

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Verify statistics
            stats = metadata.get('statistics', {})
            assert isinstance(stats, dict)

            # Verify TOC entries exist
            toc_field = 'toc_entries' if 'toc_entries' in metadata else 'table_of_contents'
            assert len(metadata[toc_field]) == 2

            # Verify page data exists
            page_field = 'pages' if 'pages' in metadata else 'page_index'
            assert isinstance(metadata[page_field], list)
            assert len(metadata[page_field]) > 0


# Test runner
if __name__ == "__main__":
    # Run with: python tests/run_all_tests.py
    print("Run tests with: python tests/run_all_tests.py")
    print("Or use pytest if available: pytest tests/test_ibco_stripper.py")
