#!/usr/bin/env python3
"""
Test script for PROMPT 5A: JSON Metadata Exporter

Tests metadata export functionality:
- export_metadata() method
- JSON structure validation
- TOC entries export
- Page metadata export
- Statistics calculation
- Error handling and validation

Usage:
    python test_metadata_export.py
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Mock dependencies
class MockModule:
    """Mock module for dependencies."""
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()

sys.modules['pdfplumber'] = MockModule()
sys.modules['pytesseract'] = MockModule()
sys.modules['pdf2image'] = MockModule()
sys.modules['PIL'] = MockModule()
sys.modules['PIL.Image'] = MockModule()
sys.modules['tqdm'] = MockModule()

import config
from ibco_stripper import PDFStripper, TOCEntry, PageMetadata


def create_test_stripper(temp_path):
    """Create a test stripper with sample data."""
    stripper = PDFStripper.__new__(PDFStripper)
    stripper.pdf_path = Path("/path/to/sample_cafr.pdf")
    stripper.output_dir = temp_path

    # Create mock TOC with 3 main sections and subsections
    toc_entries = [
        TOCEntry("Introductory Section", 1, 1, None),
        TOCEntry("Letter of Transmittal", 3, 2, "Introductory Section"),
        TOCEntry("Financial Section", 11, 1, None),
        TOCEntry("Basic Financial Statements", 15, 2, "Financial Section"),
        TOCEntry("Government-wide Statements", 17, 3, "Basic Financial Statements"),
        TOCEntry("Statistical Section", 21, 1, None),
    ]

    stripper.toc_entries = toc_entries

    # Create mock page metadata (30 pages)
    stripper.page_metadata = []
    for i in range(1, 31):
        # Map pages to sections
        if i < 11:
            section = "Introductory Section"
            level = 1
            parent = None
            footer = str(i) if i > 2 else None  # First 2 pages no footer
        elif i < 15:
            section = "Financial Section"
            level = 1
            parent = None
            footer = str(i)
        elif i < 21:
            section = "Basic Financial Statements"
            level = 2
            parent = "Financial Section"
            footer = str(i)
        else:
            section = "Statistical Section"
            level = 1
            parent = None
            footer = str(i)

        # Simulate some PNG files created
        if i <= 20:
            png_file = f"output/{i:04d}.png"
        else:
            png_file = None

        metadata = PageMetadata(
            pdf_page_num=i,
            footer_page_num=footer,
            section_name=section,
            section_level=level,
            header_text=f"HEADER {i}",
            parent_section_name=parent,
            png_file=png_file
        )
        stripper.page_metadata.append(metadata)

    return stripper


def test_basic_export():
    """Test basic metadata export."""
    print("=" * 80)
    print("Testing Basic Metadata Export")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export metadata
        print("Exporting metadata...")
        output_file = stripper.export_metadata("test_metadata.json")
        print()

        passed = 0
        failed = 0

        # Test 1: File was created
        if Path(output_file).exists():
            print(f"✓ Metadata file created: {Path(output_file).name}")
            passed += 1
        else:
            print("✗ Metadata file not created")
            failed += 1
            return False

        # Test 2: File is valid JSON
        try:
            with open(output_file, 'r') as f:
                metadata = json.load(f)
            print("✓ File contains valid JSON")
            passed += 1
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}")
            failed += 1
            return False

        # Test 3: Required top-level keys present
        required_keys = ["source_pdf", "total_pages", "processed_date", "toc_entries", "pages", "statistics"]
        missing_keys = [k for k in required_keys if k not in metadata]

        if not missing_keys:
            print(f"✓ All required keys present: {', '.join(required_keys)}")
            passed += 1
        else:
            print(f"✗ Missing keys: {', '.join(missing_keys)}")
            failed += 1

        # Test 4: Source PDF path is correct
        if metadata["source_pdf"] == "/path/to/sample_cafr.pdf":
            print("✓ Source PDF path correct")
            passed += 1
        else:
            print(f"✗ Wrong source PDF: {metadata['source_pdf']}")
            failed += 1

        # Test 5: Total pages is correct
        if metadata["total_pages"] == 30:
            print("✓ Total pages correct (30)")
            passed += 1
        else:
            print(f"✗ Wrong total pages: {metadata['total_pages']}")
            failed += 1

        # Test 6: Processed date is valid format
        try:
            datetime.strptime(metadata["processed_date"], "%Y-%m-%d")
            print(f"✓ Processed date valid: {metadata['processed_date']}")
            passed += 1
        except ValueError:
            print(f"✗ Invalid date format: {metadata['processed_date']}")
            failed += 1

        print()
        print(f"Passed: {passed}/6")
        print(f"Failed: {failed}/6")
        print()

        return failed == 0


def test_toc_export():
    """Test TOC entries export."""
    print("=" * 80)
    print("Testing TOC Entries Export")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export metadata
        output_file = stripper.export_metadata("test_metadata.json")

        with open(output_file, 'r') as f:
            metadata = json.load(f)

        passed = 0
        failed = 0

        # Test 1: Correct number of TOC entries
        if len(metadata["toc_entries"]) == 6:
            print(f"✓ Exported {len(metadata['toc_entries'])} TOC entries")
            passed += 1
        else:
            print(f"✗ Expected 6 TOC entries, got {len(metadata['toc_entries'])}")
            failed += 1

        # Test 2: TOC entry structure
        if metadata["toc_entries"]:
            first_entry = metadata["toc_entries"][0]
            required_fields = ["section_name", "page_number", "level", "parent"]
            missing_fields = [f for f in required_fields if f not in first_entry]

            if not missing_fields:
                print(f"✓ TOC entries have required fields")
                passed += 1
            else:
                print(f"✗ Missing fields in TOC entries: {', '.join(missing_fields)}")
                failed += 1

        # Test 3: Specific TOC entry values
        first_entry = metadata["toc_entries"][0]
        if (first_entry["section_name"] == "Introductory Section" and
            first_entry["page_number"] == 1 and
            first_entry["level"] == 1 and
            first_entry["parent"] is None):
            print("✓ First TOC entry values correct")
            passed += 1
        else:
            print(f"✗ First TOC entry values incorrect")
            print(f"  Got: {first_entry}")
            failed += 1

        # Test 4: Subsection with parent
        subsection = metadata["toc_entries"][1]  # Letter of Transmittal
        if (subsection["section_name"] == "Letter of Transmittal" and
            subsection["level"] == 2 and
            subsection["parent"] == "Introductory Section"):
            print("✓ Subsection with parent correct")
            passed += 1
        else:
            print(f"✗ Subsection values incorrect")
            print(f"  Got: {subsection}")
            failed += 1

        # Test 5: Level 3 subsection
        level3 = metadata["toc_entries"][4]  # Government-wide Statements
        if (level3["section_name"] == "Government-wide Statements" and
            level3["level"] == 3):
            print("✓ Level 3 subsection correct")
            passed += 1
        else:
            print(f"✗ Level 3 subsection incorrect")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_pages_export():
    """Test page metadata export."""
    print("=" * 80)
    print("Testing Page Metadata Export")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export metadata
        output_file = stripper.export_metadata("test_metadata.json")

        with open(output_file, 'r') as f:
            metadata = json.load(f)

        passed = 0
        failed = 0

        # Test 1: Correct number of pages
        if len(metadata["pages"]) == 30:
            print(f"✓ Exported {len(metadata['pages'])} pages")
            passed += 1
        else:
            print(f"✗ Expected 30 pages, got {len(metadata['pages'])}")
            failed += 1

        # Test 2: Page entry structure
        if metadata["pages"]:
            first_page = metadata["pages"][0]
            required_fields = ["pdf_page", "footer_page", "section", "section_level",
                             "header_text", "parent_section", "png_file"]
            missing_fields = [f for f in required_fields if f not in first_page]

            if not missing_fields:
                print(f"✓ Page entries have required fields")
                passed += 1
            else:
                print(f"✗ Missing fields in page entries: {', '.join(missing_fields)}")
                failed += 1

        # Test 3: First page values
        first_page = metadata["pages"][0]
        if (first_page["pdf_page"] == 1 and
            first_page["section"] == "Introductory Section" and
            first_page["section_level"] == 1):
            print("✓ First page values correct")
            passed += 1
        else:
            print(f"✗ First page values incorrect")
            print(f"  Got: {first_page}")
            failed += 1

        # Test 4: Page without footer (page 1)
        if first_page["footer_page"] is None:
            print("✓ Page without footer handled correctly (null)")
            passed += 1
        else:
            print(f"✗ Expected null footer, got: {first_page['footer_page']}")
            failed += 1

        # Test 5: Page with footer (page 3)
        page_3 = metadata["pages"][2]
        if page_3["footer_page"] == "3":
            print("✓ Page with footer correct")
            passed += 1
        else:
            print(f"✗ Expected footer '3', got: {page_3['footer_page']}")
            failed += 1

        # Test 6: Page with PNG file (page 5)
        page_5 = metadata["pages"][4]
        if page_5["png_file"] and "0005.png" in page_5["png_file"]:
            print("✓ PNG file path included")
            passed += 1
        else:
            print(f"✗ PNG file path missing or incorrect: {page_5['png_file']}")
            failed += 1

        # Test 7: Page without PNG file (page 25)
        page_25 = metadata["pages"][24]
        if page_25["png_file"] is None:
            print("✓ Page without PNG file handled correctly (null)")
            passed += 1
        else:
            print(f"✗ Expected null PNG file, got: {page_25['png_file']}")
            failed += 1

        # Test 8: Subsection page with parent (page 17)
        page_17 = metadata["pages"][16]
        if (page_17["section"] == "Basic Financial Statements" and
            page_17["parent_section"] == "Financial Section"):
            print("✓ Subsection page with parent correct")
            passed += 1
        else:
            print(f"✗ Subsection page incorrect: {page_17}")
            failed += 1

        print()
        print(f"Passed: {passed}/8")
        print(f"Failed: {failed}/8")
        print()

        return failed == 0


def test_statistics():
    """Test statistics calculation."""
    print("=" * 80)
    print("Testing Statistics Calculation")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export metadata
        output_file = stripper.export_metadata("test_metadata.json")

        with open(output_file, 'r') as f:
            metadata = json.load(f)

        stats = metadata["statistics"]

        passed = 0
        failed = 0

        # Test 1: Statistics object exists
        if stats:
            print("✓ Statistics object present")
            passed += 1
        else:
            print("✗ Statistics object missing")
            failed += 1
            return False

        # Test 2: Sections count (6 total)
        if stats["sections_count"] == 6:
            print(f"✓ Sections count correct: {stats['sections_count']}")
            passed += 1
        else:
            print(f"✗ Wrong sections count: {stats['sections_count']}")
            failed += 1

        # Test 3: Main sections (3: Intro, Financial, Statistical)
        if stats["main_sections"] == 3:
            print(f"✓ Main sections correct: {stats['main_sections']}")
            passed += 1
        else:
            print(f"✗ Wrong main sections: {stats['main_sections']}")
            failed += 1

        # Test 4: Subsections (3: Letter, Basic, Gov-wide)
        if stats["subsections"] == 3:
            print(f"✓ Subsections correct: {stats['subsections']}")
            passed += 1
        else:
            print(f"✗ Wrong subsections: {stats['subsections']}")
            failed += 1

        # Test 5: Pages with numbers (28, pages 3-30)
        if stats["pages_with_numbers"] == 28:
            print(f"✓ Pages with numbers: {stats['pages_with_numbers']}")
            passed += 1
        else:
            print(f"✗ Wrong pages with numbers: {stats['pages_with_numbers']}")
            failed += 1

        # Test 6: Pages without numbers (2, pages 1-2)
        if stats["pages_without_numbers"] == 2:
            print(f"✓ Pages without numbers: {stats['pages_without_numbers']}")
            passed += 1
        else:
            print(f"✗ Wrong pages without numbers: {stats['pages_without_numbers']}")
            failed += 1

        # Test 7: Pages with sections (all 30)
        if stats["pages_with_sections"] == 30:
            print(f"✓ Pages with sections: {stats['pages_with_sections']}")
            passed += 1
        else:
            print(f"✗ Wrong pages with sections: {stats['pages_with_sections']}")
            failed += 1

        # Test 8: Pages without sections (0)
        if stats["pages_without_sections"] == 0:
            print(f"✓ Pages without sections: {stats['pages_without_sections']}")
            passed += 1
        else:
            print(f"✗ Wrong pages without sections: {stats['pages_without_sections']}")
            failed += 1

        # Test 9: PNG files created (20)
        if stats["png_files_created"] == 20:
            print(f"✓ PNG files created: {stats['png_files_created']}")
            passed += 1
        else:
            print(f"✗ Wrong PNG files count: {stats['png_files_created']}")
            failed += 1

        print()
        print(f"Passed: {passed}/9")
        print(f"Failed: {failed}/9")
        print()

        return failed == 0


def test_error_handling():
    """Test error handling and validation."""
    print("=" * 80)
    print("Testing Error Handling")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        passed = 0
        failed = 0

        # Test 1: Error when page_metadata not built
        print("Test 1: Error when page_metadata not built...")
        stripper = PDFStripper.__new__(PDFStripper)
        stripper.pdf_path = Path("mock.pdf")
        stripper.output_dir = temp_path
        stripper.toc_entries = []
        stripper.page_metadata = []

        try:
            stripper.export_metadata()
            print("✗ Should raise ValueError when page_metadata empty")
            failed += 1
        except ValueError as e:
            if "Page index not built" in str(e):
                print("✓ Raises ValueError when page_metadata not built")
                passed += 1
            else:
                print(f"✗ Wrong error message: {e}")
                failed += 1

        # Test 2: Creates parent directory if needed
        print("Test 2: Creates parent directory if needed...")
        stripper = create_test_stripper(temp_path)
        nested_path = "nested/dir/metadata.json"
        output_file = stripper.export_metadata(nested_path)

        if Path(output_file).exists():
            print("✓ Created nested directories")
            passed += 1
        else:
            print("✗ Failed to create nested directories")
            failed += 1

        # Test 3: Handles absolute paths
        print("Test 3: Handles absolute paths...")
        absolute_path = temp_path / "absolute_metadata.json"
        output_file = stripper.export_metadata(str(absolute_path))

        if Path(output_file).exists() and Path(output_file) == absolute_path:
            print("✓ Handles absolute paths correctly")
            passed += 1
        else:
            print("✗ Failed to handle absolute path")
            failed += 1

        # Test 4: Handles relative paths
        print("Test 4: Handles relative paths...")
        output_file = stripper.export_metadata("relative_metadata.json")

        if Path(output_file).exists() and "relative_metadata.json" in output_file:
            print("✓ Handles relative paths correctly")
            passed += 1
        else:
            print("✗ Failed to handle relative path")
            failed += 1

        # Test 5: Overwrites existing file
        print("Test 5: Overwrites existing file...")
        first_output = stripper.export_metadata("overwrite_test.json")

        # Modify a value in memory
        stripper.page_metadata[0].footer_page_num = "MODIFIED"

        second_output = stripper.export_metadata("overwrite_test.json")

        with open(second_output, 'r') as f:
            metadata = json.load(f)

        if metadata["pages"][0]["footer_page"] == "MODIFIED":
            print("✓ Overwrites existing file with new data")
            passed += 1
        else:
            print("✗ Failed to overwrite existing file")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_json_format():
    """Test JSON formatting and encoding."""
    print("=" * 80)
    print("Testing JSON Format and Encoding")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Add some unicode characters to test encoding
        stripper.page_metadata[0].header_text = "CITY OF VALLEJO – CAFR"
        stripper.toc_entries[0].section_name = "Introducción"

        # Export metadata
        output_file = stripper.export_metadata("test_metadata.json")

        passed = 0
        failed = 0

        # Test 1: File is UTF-8 encoded
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print("✓ File is UTF-8 encoded")
            passed += 1
        except UnicodeDecodeError:
            print("✗ File encoding error")
            failed += 1

        # Test 2: JSON is properly indented
        with open(output_file, 'r') as f:
            lines = f.readlines()

        # Check for indentation
        indented_lines = [l for l in lines if l.startswith('  ')]
        if len(indented_lines) > 10:  # Should have many indented lines
            print("✓ JSON is properly indented")
            passed += 1
        else:
            print("✗ JSON not indented")
            failed += 1

        # Test 3: Unicode characters preserved
        with open(output_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        if "–" in metadata["pages"][0]["header_text"]:
            print("✓ Unicode characters preserved (en-dash)")
            passed += 1
        else:
            print("✗ Unicode characters not preserved")
            failed += 1

        if "ó" in metadata["toc_entries"][0]["section_name"]:
            print("✓ Unicode characters preserved (accented char)")
            passed += 1
        else:
            print("✗ Unicode characters not preserved")
            failed += 1

        # Test 5: File size is reasonable
        file_size = Path(output_file).stat().st_size
        if file_size > 100 and file_size < 100000:  # Between 100 bytes and 100KB
            print(f"✓ File size reasonable: {file_size} bytes")
            passed += 1
        else:
            print(f"✗ File size unusual: {file_size} bytes")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def main():
    """Run all tests."""
    print()
    print("=" * 80)
    print("PROMPT 5A: JSON Metadata Exporter - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_basic_export()
    all_passed &= test_toc_export()
    all_passed &= test_pages_export()
    all_passed &= test_statistics()
    all_passed &= test_error_handling()
    all_passed &= test_json_format()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 5A tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ export_metadata() - Exports comprehensive metadata to JSON")
        print("  ✓ JSON structure - Includes source_pdf, total_pages, processed_date")
        print("  ✓ TOC export - All TOC entries with section_name, page, level, parent")
        print("  ✓ Page export - All pages with complete metadata")
        print("  ✓ Statistics - Comprehensive stats (sections, pages, PNG files)")
        print("  ✓ Error handling - Validates page_metadata, handles paths")
        print("  ✓ JSON formatting - Proper indentation, UTF-8 encoding")
        print("  ✓ Unicode support - Preserves special characters")
        print()
        print("Ready for PROMPT 5B!")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
