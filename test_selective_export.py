#!/usr/bin/env python3
"""
Test script for PROMPT 4B: Selective Page Export

Tests selective PNG export functionality:
- save_section_as_png() - Export specific section
- save_page_range_as_png() - Export page range
- skip_existing parameter - Resume capability
- Edge cases and error handling

Usage:
    python test_selective_export.py
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
from ibco_stripper import PDFStripper, TOCEntry, PageMetadata


def create_test_stripper(temp_path):
    """Create a test stripper with sample data."""
    stripper = PDFStripper.__new__(PDFStripper)
    stripper.pdf_path = Path("mock.pdf")
    stripper.output_dir = temp_path

    # Create mock TOC with 3 sections
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

    return stripper


def test_save_section():
    """Test exporting a specific section."""
    print("=" * 80)
    print("Testing Section Export")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export just the Introductory Section
        print("Exporting 'Introductory Section'...")
        print()
        saved_files = stripper.save_section_as_png("Introductory Section", dpi=300)
        print()

        passed = 0
        failed = 0

        # Test 1: Correct number of files (pages 1-10)
        if len(saved_files) == 10:
            print(f"✓ Exported {len(saved_files)} pages from section")
            passed += 1
        else:
            print(f"✗ Expected 10 files, got {len(saved_files)}")
            failed += 1

        # Test 2: All files exist
        all_exist = all(Path(f).exists() for f in saved_files)
        if all_exist:
            print("✓ All exported files exist")
            passed += 1
        else:
            print("✗ Some exported files missing")
            failed += 1

        # Test 3: Files are in correct directory
        all_in_intro = all("01_introductory_section" in f for f in saved_files)
        if all_in_intro:
            print("✓ All files in correct section directory")
            passed += 1
        else:
            print("✗ Files in wrong directory")
            failed += 1

        # Test 4: Correct page numbers (1-10)
        page_numbers = set()
        for f in saved_files:
            # Extract page number from filename (page_NNNN_...)
            filename = Path(f).name
            page_num = int(filename.split('_')[1])
            page_numbers.add(page_num)

        if page_numbers == set(range(1, 11)):
            print("✓ Correct page numbers exported (1-10)")
            passed += 1
        else:
            print(f"✗ Wrong page numbers: {sorted(page_numbers)}")
            failed += 1

        # Test 5: Original metadata unchanged
        if len(stripper.page_metadata) == 30:
            print("✓ Original page_metadata unchanged (30 pages)")
            passed += 1
        else:
            print(f"✗ page_metadata corrupted: {len(stripper.page_metadata)} pages")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_save_section_with_subsections():
    """Test exporting a section that includes subsections."""
    print("=" * 80)
    print("Testing Section Export with Subsections")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export Financial Section (should include both level 1 and level 2 pages)
        print("Exporting 'Financial Section' (includes subsections)...")
        print()
        saved_files = stripper.save_section_as_png("Financial Section", dpi=300)
        print()

        passed = 0
        failed = 0

        # Test 1: Should export pages 11-20 (Financial Section pages 11-14 + subsection pages 15-20)
        if len(saved_files) == 10:
            print(f"✓ Exported {len(saved_files)} pages (main + subsections)")
            passed += 1
        else:
            print(f"✗ Expected 10 files, got {len(saved_files)}")
            failed += 1

        # Test 2: Page numbers should be 11-20
        page_numbers = set()
        for f in saved_files:
            filename = Path(f).name
            page_num = int(filename.split('_')[1])
            page_numbers.add(page_num)

        if page_numbers == set(range(11, 21)):
            print("✓ Exported pages 11-20 (main section + subsections)")
            passed += 1
        else:
            print(f"✗ Wrong page numbers: {sorted(page_numbers)}")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_save_page_range():
    """Test exporting a page range."""
    print("=" * 80)
    print("Testing Page Range Export")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Export pages 5-15
        print("Exporting pages 5-15...")
        print()
        saved_files = stripper.save_page_range_as_png(5, 15, dpi=300)
        print()

        passed = 0
        failed = 0

        # Test 1: Correct number of files (11 pages: 5,6,7,8,9,10,11,12,13,14,15)
        if len(saved_files) == 11:
            print(f"✓ Exported {len(saved_files)} pages")
            passed += 1
        else:
            print(f"✗ Expected 11 files, got {len(saved_files)}")
            failed += 1

        # Test 2: All files exist
        all_exist = all(Path(f).exists() for f in saved_files)
        if all_exist:
            print("✓ All exported files exist")
            passed += 1
        else:
            print("✗ Some exported files missing")
            failed += 1

        # Test 3: Correct page numbers
        page_numbers = set()
        for f in saved_files:
            filename = Path(f).name
            page_num = int(filename.split('_')[1])
            page_numbers.add(page_num)

        if page_numbers == set(range(5, 16)):
            print("✓ Correct page numbers (5-15)")
            passed += 1
        else:
            print(f"✗ Wrong page numbers: {sorted(page_numbers)}")
            failed += 1

        # Test 4: Files span multiple sections
        # Pages 5-10 are Introductory, 11-15 are Financial
        intro_files = [f for f in saved_files if "01_introductory" in f]
        financial_files = [f for f in saved_files if "02_financial" in f]

        if len(intro_files) == 6 and len(financial_files) == 5:
            print("✓ Files correctly distributed across sections")
            print(f"  Introductory: {len(intro_files)} files")
            print(f"  Financial: {len(financial_files)} files")
            passed += 1
        else:
            print(f"✗ Wrong distribution: intro={len(intro_files)}, financial={len(financial_files)}")
            failed += 1

        print()
        print(f"Passed: {passed}/4")
        print(f"Failed: {failed}/4")
        print()

        return failed == 0


def test_skip_existing():
    """Test skip_existing parameter for resume capability."""
    print("=" * 80)
    print("Testing Skip Existing (Resume Capability)")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # First export: convert pages 1-10
        print("First export: Converting pages 1-10...")
        print()
        saved_files_1 = stripper.save_page_range_as_png(1, 10, dpi=300)
        print()

        # Verify all 10 files created
        if len(saved_files_1) != 10:
            print(f"✗ Setup failed: expected 10 files, got {len(saved_files_1)}")
            return False

        # Get timestamps of first 5 files
        first_5_files = saved_files_1[:5]
        original_mtimes = {f: Path(f).stat().st_mtime for f in first_5_files}

        # Wait a tiny bit to ensure different timestamps if files are recreated
        import time
        time.sleep(0.01)

        # Second export: convert pages 1-10 again WITHOUT skip_existing
        print("Second export: Re-converting pages 1-10 (skip_existing=False)...")
        print()
        saved_files_2 = stripper.save_page_range_as_png(1, 10, dpi=300, skip_existing=False)
        print()

        passed = 0
        failed = 0

        # Test 1: Files were recreated (different timestamps)
        new_mtimes = {f: Path(f).stat().st_mtime for f in first_5_files}
        files_recreated = any(new_mtimes[f] != original_mtimes[f] for f in first_5_files)

        if files_recreated:
            print("✓ Files recreated when skip_existing=False")
            passed += 1
        else:
            print("✗ Files not recreated (timestamps unchanged)")
            failed += 1

        # Update original timestamps
        original_mtimes = {f: Path(f).stat().st_mtime for f in first_5_files}
        time.sleep(0.01)

        # Third export: convert pages 1-10 WITH skip_existing
        print("Third export: Re-converting pages 1-10 (skip_existing=True)...")
        print()
        saved_files_3 = stripper.save_page_range_as_png(1, 10, dpi=300, skip_existing=True)
        print()

        # Test 2: Still returns 10 files
        if len(saved_files_3) == 10:
            print("✓ Returns all file paths even when skipping")
            passed += 1
        else:
            print(f"✗ Expected 10 files, got {len(saved_files_3)}")
            failed += 1

        # Test 3: Files were NOT recreated (same timestamps)
        new_mtimes = {f: Path(f).stat().st_mtime for f in first_5_files}
        files_skipped = all(new_mtimes[f] == original_mtimes[f] for f in first_5_files)

        if files_skipped:
            print("✓ Files skipped when skip_existing=True (timestamps unchanged)")
            passed += 1
        else:
            print("✗ Files were recreated even with skip_existing=True")
            failed += 1

        # Test 4: Partial conversion with skip_existing
        # Delete last 3 files, then re-export with skip_existing
        last_3_files = saved_files_3[-3:]
        for f in last_3_files:
            Path(f).unlink()

        print()
        print("Fourth export: Re-converting after deleting 3 files (skip_existing=True)...")
        print()
        saved_files_4 = stripper.save_page_range_as_png(1, 10, dpi=300, skip_existing=True)
        print()

        # Should still return 10 files
        if len(saved_files_4) == 10:
            print("✓ Returns all file paths")
            passed += 1
        else:
            print(f"✗ Expected 10 files, got {len(saved_files_4)}")
            failed += 1

        # Only the 3 deleted files should exist now
        deleted_files_exist = all(Path(f).exists() for f in last_3_files)
        if deleted_files_exist:
            print("✓ Missing files were recreated")
            passed += 1
        else:
            print("✗ Missing files not recreated")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_edge_cases():
    """Test edge cases and error handling."""
    print("=" * 80)
    print("Testing Edge Cases")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        passed = 0
        failed = 0

        # Test 1: Non-existent section
        print("Test 1: Non-existent section...")
        saved_files = stripper.save_section_as_png("Nonexistent Section", dpi=300)

        if len(saved_files) == 0:
            print("✓ Returns empty list for non-existent section")
            passed += 1
        else:
            print(f"✗ Should return empty list, got {len(saved_files)} files")
            failed += 1

        # Test 2: Invalid page range (start > end)
        print("Test 2: Invalid page range (start > end)...")
        try:
            stripper.save_page_range_as_png(20, 10)
            print("✗ Should raise ValueError for invalid range")
            failed += 1
        except ValueError as e:
            if "end_page must be >= start_page" in str(e):
                print("✓ Raises ValueError for invalid range")
                passed += 1
            else:
                print(f"✗ Wrong error message: {e}")
                failed += 1

        # Test 3: Invalid page range (start < 1)
        print("Test 3: Invalid page range (start < 1)...")
        try:
            stripper.save_page_range_as_png(0, 10)
            print("✗ Should raise ValueError for start_page < 1")
            failed += 1
        except ValueError as e:
            if "start_page must be >= 1" in str(e):
                print("✓ Raises ValueError for start_page < 1")
                passed += 1
            else:
                print(f"✗ Wrong error message: {e}")
                failed += 1

        # Test 4: Page range beyond document
        print("Test 4: Page range beyond document...")
        saved_files = stripper.save_page_range_as_png(25, 100, dpi=300)

        # Should export pages 25-30 (only pages that exist)
        if len(saved_files) == 6:
            print("✓ Exports only existing pages in range (25-30)")
            passed += 1
        else:
            print(f"✗ Expected 6 files, got {len(saved_files)}")
            failed += 1

        # Test 5: Empty page range
        print("Test 5: Empty page range (beyond document)...")
        saved_files = stripper.save_page_range_as_png(100, 200, dpi=300)

        if len(saved_files) == 0:
            print("✓ Returns empty list for out-of-bounds range")
            passed += 1
        else:
            print(f"✗ Should return empty list, got {len(saved_files)} files")
            failed += 1

        # Test 6: Error when page_metadata not built
        print("Test 6: Error when page_metadata not built...")
        stripper2 = PDFStripper.__new__(PDFStripper)
        stripper2.pdf_path = Path("mock.pdf")
        stripper2.output_dir = temp_path
        stripper2.page_metadata = []

        try:
            stripper2.save_section_as_png("Test Section")
            print("✗ Should raise ValueError when page_metadata empty")
            failed += 1
        except ValueError as e:
            if "Page index not built" in str(e):
                print("✓ Raises ValueError when page_metadata not built")
                passed += 1
            else:
                print(f"✗ Wrong error message: {e}")
                failed += 1

        print()
        print(f"Passed: {passed}/6")
        print(f"Failed: {failed}/6")
        print()

        return failed == 0


def main():
    """Run all tests."""
    print()
    print("=" * 80)
    print("PROMPT 4B: Selective Page Export - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_save_section()
    all_passed &= test_save_section_with_subsections()
    all_passed &= test_save_page_range()
    all_passed &= test_skip_existing()
    all_passed &= test_edge_cases()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 4B tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ save_section_as_png() - Export specific section")
        print("  ✓ save_page_range_as_png() - Export page range")
        print("  ✓ skip_existing parameter - Resume capability")
        print("  ✓ Section filtering - Includes main section + subsections")
        print("  ✓ Page range validation - Checks bounds")
        print("  ✓ Metadata preservation - Original metadata unchanged")
        print("  ✓ Edge cases - Non-existent sections, invalid ranges")
        print("  ✓ Resume capability - Skips existing files, recreates missing")
        print()
        print("Phase 4 complete! Ready for Phase 5!")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
