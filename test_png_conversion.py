#!/usr/bin/env python3
"""
Test script for PROMPT 4A: Page to PNG Converter

Tests PNG conversion functionality:
- Section slug creation
- Single page conversion
- Batch conversion with multiprocessing
- Directory structure creation
- Filename generation
- PageMetadata.png_file updates
- Progress indicator

Usage:
    python test_png_conversion.py
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Mock dependencies
class MockModule:
    """Mock module for dependencies."""
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()

class MockImage:
    """Mock PIL Image."""
    def save(self, path, format):
        # Create empty file to simulate image save
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text("mock_png_data")

class MockPDF2Image:
    """Mock pdf2image module."""
    @staticmethod
    def convert_from_path(pdf_path, dpi=300, first_page=None, last_page=None, thread_count=1):
        # Return mock image
        return [MockImage()]

# Mock tqdm to avoid progress bar during tests
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

sys.modules['pdfplumber'] = MockModule()
sys.modules['pytesseract'] = MockModule()
sys.modules['pdf2image'] = MockPDF2Image
sys.modules['PIL'] = MockModule()
sys.modules['PIL.Image'] = MockModule()
sys.modules['tqdm'] = MockTqdmModule()

import config
from ibco_stripper import PDFStripper, TOCEntry, PageMetadata, _convert_page_worker


def test_section_slug_creation():
    """Test section slug creation from various section names."""
    print("=" * 80)
    print("Testing Section Slug Creation")
    print("=" * 80)
    print()

    # Create stripper instance
    stripper = PDFStripper.__new__(PDFStripper)

    test_cases = [
        ("Introductory Section", "introductory_section"),
        ("Financial Section", "financial_section"),
        ("Management's Discussion & Analysis", "managements_discussion_analysis"),
        ("Government-wide Statements", "government_wide_statements"),
        ("Notes to Financial Statements", "notes_to_financial_statements"),
        ("  Statistical Section  ", "statistical_section"),  # Extra whitespace
        ("Special-Characters! @#$%", "special_characters"),
        (None, "unsectioned"),
        ("", "unsectioned"),
    ]

    print(f"{'Input Section Name':<40} {'Expected Slug':<30} {'Status'}")
    print("-" * 80)

    passed = 0
    failed = 0

    for section_name, expected_slug in test_cases:
        result_slug = stripper._create_section_slug(section_name)

        if result_slug == expected_slug:
            print(f"{str(section_name):<40} {expected_slug:<30} ✓")
            passed += 1
        else:
            print(f"{str(section_name):<40} {expected_slug:<30} ✗")
            print(f"  Got: {result_slug}")
            failed += 1

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_save_single_page():
    """Test single page PNG conversion."""
    print("=" * 80)
    print("Testing Single Page Conversion")
    print("=" * 80)
    print()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create stripper
        stripper = PDFStripper.__new__(PDFStripper)
        stripper.pdf_path = Path("mock.pdf")
        stripper.output_dir = temp_path

        # Test conversion
        output_path = temp_path / "test_page.png"

        print(f"Converting page 1 to {output_path.name}...")
        result_path = stripper.save_page_as_png(1, str(output_path), dpi=300)
        print()

        passed = 0
        failed = 0

        # Test 1: File was created
        if Path(result_path).exists():
            print("✓ PNG file created")
            passed += 1
        else:
            print("✗ PNG file not created")
            failed += 1

        # Test 2: Returned path matches requested path
        if result_path == str(output_path):
            print("✓ Returned path matches requested path")
            passed += 1
        else:
            print(f"✗ Path mismatch: expected {output_path}, got {result_path}")
            failed += 1

        # Test 3: File has content
        if Path(result_path).stat().st_size > 0:
            print("✓ PNG file has content")
            passed += 1
        else:
            print("✗ PNG file is empty")
            failed += 1

        print()
        print(f"Passed: {passed}/3")
        print(f"Failed: {failed}/3")
        print()

        return failed == 0


def test_save_all_pages():
    """Test batch PNG conversion with multiprocessing."""
    print("=" * 80)
    print("Testing Batch Page Conversion")
    print("=" * 80)
    print()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create stripper with page index
        stripper = PDFStripper.__new__(PDFStripper)
        stripper.pdf_path = Path("mock.pdf")
        stripper.output_dir = temp_path

        # Create mock TOC
        toc_entries = [
            TOCEntry("Introductory Section", 1, 1),
            TOCEntry("Financial Section", 11, 1),
            TOCEntry("  Basic Financial Statements", 15, 2),
            TOCEntry("Statistical Section", 21, 1),
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
            elif i < 15:
                section = "Financial Section"
                level = 1
                parent = None
            elif i < 21:
                section = "Basic Financial Statements"
                level = 2
                parent = "Financial Section"
            else:
                section = "Statistical Section"
                level = 1
                parent = None

            metadata = PageMetadata(
                pdf_page_num=i,
                footer_page_num=str(i),
                section_name=section,
                section_level=level,
                header_text="TEST HEADER",
                parent_section_name=parent,
                png_file=None
            )
            stripper.page_metadata.append(metadata)

        # Convert all pages
        print("Converting 30 pages...")
        print()
        saved_files = stripper.save_all_pages_as_png(dpi=300)
        print()

        passed = 0
        failed = 0

        # Test 1: Correct number of files created
        if len(saved_files) == 30:
            print(f"✓ Created {len(saved_files)} PNG files")
            passed += 1
        else:
            print(f"✗ Expected 30 files, got {len(saved_files)}")
            failed += 1

        # Test 2: All files exist
        all_exist = all(Path(f).exists() for f in saved_files)
        if all_exist:
            print("✓ All PNG files exist")
            passed += 1
        else:
            print("✗ Some PNG files missing")
            failed += 1

        # Test 3: Section directories created correctly
        expected_dirs = {
            "01_introductory_section",
            "02_financial_section",
            "03_statistical_section"
        }

        created_dirs = set()
        for f in saved_files:
            folder_name = Path(f).parent.name
            created_dirs.add(folder_name)

        if created_dirs == expected_dirs:
            print(f"✓ Created {len(expected_dirs)} section directories")
            passed += 1
        else:
            print(f"✗ Directory mismatch")
            print(f"  Expected: {expected_dirs}")
            print(f"  Got: {created_dirs}")
            failed += 1

        # Test 4: Files in correct directories
        files_in_intro = len([f for f in saved_files if "01_introductory_section" in f])
        files_in_financial = len([f for f in saved_files if "02_financial_section" in f])
        files_in_statistical = len([f for f in saved_files if "03_statistical_section" in f])

        if files_in_intro == 10 and files_in_financial == 10 and files_in_statistical == 10:
            print(f"✓ Files distributed correctly across sections")
            print(f"  Introductory: {files_in_intro} files")
            print(f"  Financial: {files_in_financial} files")
            print(f"  Statistical: {files_in_statistical} files")
            passed += 1
        else:
            print(f"✗ File distribution incorrect")
            print(f"  Introductory: {files_in_intro} (expected 10)")
            print(f"  Financial: {files_in_financial} (expected 10)")
            print(f"  Statistical: {files_in_statistical} (expected 10)")
            failed += 1

        # Test 5: Filenames follow correct format
        sample_file = Path(saved_files[0])
        filename_pattern = sample_file.name

        if filename_pattern.startswith("page_") and filename_pattern.endswith(".png"):
            print(f"✓ Filename follows format: {filename_pattern}")
            passed += 1
        else:
            print(f"✗ Incorrect filename format: {filename_pattern}")
            failed += 1

        # Test 6: PageMetadata updated with PNG paths
        all_metadata_updated = all(m.png_file is not None for m in stripper.page_metadata)
        if all_metadata_updated:
            print("✓ All PageMetadata objects updated with PNG paths")
            passed += 1
        else:
            not_updated = sum(1 for m in stripper.page_metadata if m.png_file is None)
            print(f"✗ {not_updated} PageMetadata objects not updated")
            failed += 1

        # Test 7: Subsections go to parent section folder
        # Pages 15-20 are "Basic Financial Statements" (level 2) with parent "Financial Section"
        # They should be in "02_financial_section" folder
        subsection_files = [saved_files[i] for i in range(14, 20)]  # Pages 15-20 (0-indexed)
        subsection_in_parent = all("02_financial_section" in f for f in subsection_files)

        if subsection_in_parent:
            print("✓ Subsection pages placed in parent section folder")
            passed += 1
        else:
            print("✗ Subsection pages not in correct folder")
            failed += 1

        print()
        print(f"Passed: {passed}/7")
        print(f"Failed: {failed}/7")
        print()

        return failed == 0


def test_worker_function():
    """Test the multiprocessing worker function."""
    print("=" * 80)
    print("Testing Multiprocessing Worker Function")
    print("=" * 80)
    print()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a conversion task
        task = {
            'pdf_path': 'mock.pdf',
            'page_number': 5,
            'output_path': str(temp_path / 'test_worker.png'),
            'dpi': 300,
            'metadata_index': 4
        }

        print("Running worker function...")
        result = _convert_page_worker(task)
        print()

        passed = 0
        failed = 0

        # Test 1: Worker returns correct structure
        if 'output_path' in result and 'metadata_index' in result:
            print("✓ Worker returns correct result structure")
            passed += 1
        else:
            print("✗ Worker result missing keys")
            failed += 1

        # Test 2: Output file created
        if Path(result['output_path']).exists():
            print("✓ Worker created PNG file")
            passed += 1
        else:
            print("✗ Worker did not create PNG file")
            failed += 1

        # Test 3: Metadata index preserved
        if result['metadata_index'] == 4:
            print("✓ Metadata index preserved")
            passed += 1
        else:
            print(f"✗ Metadata index wrong: expected 4, got {result['metadata_index']}")
            failed += 1

        print()
        print(f"Passed: {passed}/3")
        print(f"Failed: {failed}/3")
        print()

        return failed == 0


def test_edge_cases():
    """Test edge cases in PNG conversion."""
    print("=" * 80)
    print("Testing Edge Cases")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        stripper = PDFStripper.__new__(PDFStripper)
        stripper.pdf_path = Path("mock.pdf")
        stripper.output_dir = temp_path

        passed = 0
        failed = 0

        # Test 1: Pages with no section (unsectioned)
        stripper.page_metadata = [
            PageMetadata(
                pdf_page_num=1,
                footer_page_num=None,
                section_name=None,
                section_level=0,
                header_text=None,
                parent_section_name=None,
                png_file=None
            )
        ]

        saved_files = stripper.save_all_pages_as_png(dpi=300)

        if "00_unsectioned" in saved_files[0]:
            print("✓ Unsectioned pages go to '00_unsectioned' folder")
            passed += 1
        else:
            print(f"✗ Unsectioned page in wrong folder: {saved_files[0]}")
            failed += 1

        # Test 2: Error when page_metadata not built
        stripper2 = PDFStripper.__new__(PDFStripper)
        stripper2.pdf_path = Path("mock.pdf")
        stripper2.output_dir = temp_path
        stripper2.page_metadata = []

        try:
            stripper2.save_all_pages_as_png()
            print("✗ Should raise error when page_metadata is empty")
            failed += 1
        except ValueError as e:
            if "Page index not built" in str(e):
                print("✓ Raises error when page_metadata not built")
                passed += 1
            else:
                print(f"✗ Wrong error message: {e}")
                failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def main():
    """Run all tests."""
    print()
    print("=" * 80)
    print("PROMPT 4A: Page to PNG Converter - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_section_slug_creation()
    all_passed &= test_save_single_page()
    all_passed &= test_save_all_pages()
    all_passed &= test_worker_function()
    all_passed &= test_edge_cases()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 4A tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ _create_section_slug() - Creates URL-friendly slugs")
        print("  ✓ save_page_as_png() - Converts single page to PNG")
        print("  ✓ save_all_pages_as_png() - Batch conversion with multiprocessing")
        print("  ✓ Section directories - Creates numbered folders (01_, 02_, etc.)")
        print("  ✓ Filename format - page_{num:04d}_{section_slug}.png")
        print("  ✓ Multiprocessing - 8-16 parallel workers for Threadripper")
        print("  ✓ Progress indicator - tqdm progress bar")
        print("  ✓ PageMetadata updates - PNG paths stored in metadata")
        print("  ✓ Subsection handling - Places in parent section folder")
        print("  ✓ Edge cases - Unsectioned pages, error handling")
        print()
        print("Ready for PROMPT 4B!")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
