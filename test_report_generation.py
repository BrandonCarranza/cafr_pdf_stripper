#!/usr/bin/env python3
"""
Test script for PROMPT 5B: Human-Readable Report

Tests report generation functionality:
- generate_report() method
- Report formatting and structure
- TOC section formatting
- Page mapping summary
- Issues/warnings detection
- Output files listing
- Summary statistics

Usage:
    python test_report_generation.py
"""

import sys
import tempfile
from pathlib import Path

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
        if i <= 25:
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


def test_basic_report():
    """Test basic report generation."""
    print("=" * 80)
    print("Testing Basic Report Generation")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Generate report
        print("Generating report...")
        output_file = stripper.generate_report("test_report.txt")
        print()

        passed = 0
        failed = 0

        # Test 1: File was created
        if Path(output_file).exists():
            print(f"✓ Report file created: {Path(output_file).name}")
            passed += 1
        else:
            print("✗ Report file not created")
            failed += 1
            return False

        # Test 2: File has content
        with open(output_file, 'r') as f:
            content = f.read()

        if len(content) > 100:
            print(f"✓ Report has content ({len(content)} characters)")
            passed += 1
        else:
            print("✗ Report is too short")
            failed += 1

        # Test 3: Contains required sections
        required_sections = [
            "CAFR PROCESSING REPORT",
            "TABLE OF CONTENTS",
            "PAGE MAPPING SUMMARY",
            "ISSUES/WARNINGS",
            "OUTPUT FILES",
            "SUMMARY STATISTICS"
        ]

        missing_sections = [s for s in required_sections if s not in content]

        if not missing_sections:
            print(f"✓ All required sections present")
            passed += 1
        else:
            print(f"✗ Missing sections: {', '.join(missing_sections)}")
            failed += 1

        # Test 4: Contains PDF name
        if "sample_cafr.pdf" in content:
            print("✓ PDF name included")
            passed += 1
        else:
            print("✗ PDF name missing")
            failed += 1

        # Test 5: Contains total pages
        if "Total Pages: 30" in content:
            print("✓ Total pages count correct")
            passed += 1
        else:
            print("✗ Total pages count missing or incorrect")
            failed += 1

        # Test 6: Contains processed date
        if "Processed:" in content:
            print("✓ Processed date included")
            passed += 1
        else:
            print("✗ Processed date missing")
            failed += 1

        print()
        print(f"Passed: {passed}/6")
        print(f"Failed: {failed}/6")
        print()

        return failed == 0


def test_toc_formatting():
    """Test TOC section formatting."""
    print("=" * 80)
    print("Testing TOC Formatting")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Generate report
        output_file = stripper.generate_report("test_report.txt")

        with open(output_file, 'r') as f:
            lines = f.readlines()

        # Find TOC section
        toc_start = None
        for i, line in enumerate(lines):
            if "TABLE OF CONTENTS" in line:
                toc_start = i
                break

        passed = 0
        failed = 0

        # Test 1: TOC section found
        if toc_start is not None:
            print("✓ TOC section found")
            passed += 1
        else:
            print("✗ TOC section not found")
            failed += 1
            return False

        # Test 2: Contains section names
        toc_content = '\n'.join(lines[toc_start:toc_start+20])

        if "Introductory Section" in toc_content:
            print("✓ Contains Introductory Section")
            passed += 1
        else:
            print("✗ Missing Introductory Section")
            failed += 1

        # Test 3: Contains subsection with indentation
        if "  Letter of Transmittal" in toc_content:
            print("✓ Subsection indented correctly")
            passed += 1
        else:
            print("✗ Subsection indentation incorrect")
            failed += 1

        # Test 4: Contains page numbers with dots
        if "..." in toc_content or ".." in toc_content:
            print("✓ Page numbers aligned with dots")
            passed += 1
        else:
            print("✗ Missing dot alignment")
            failed += 1

        # Test 5: All TOC entries present
        if all(entry.section_name in toc_content for entry in stripper.toc_entries):
            print("✓ All TOC entries present")
            passed += 1
        else:
            print("✗ Some TOC entries missing")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_page_mapping_summary():
    """Test page mapping summary section."""
    print("=" * 80)
    print("Testing Page Mapping Summary")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Generate report
        output_file = stripper.generate_report("test_report.txt")

        with open(output_file, 'r') as f:
            content = f.read()

        passed = 0
        failed = 0

        # Test 1: Contains page mapping summary
        if "PAGE MAPPING SUMMARY" in content:
            print("✓ Page mapping summary section present")
            passed += 1
        else:
            print("✗ Page mapping summary missing")
            failed += 1

        # Test 2: Contains section page ranges
        if "Pages:" in content:
            print("✓ Contains page ranges")
            passed += 1
        else:
            print("✗ Page ranges missing")
            failed += 1

        # Test 3: Contains PNG file counts
        if "PNG Files:" in content:
            print("✓ Contains PNG file counts")
            passed += 1
        else:
            print("✗ PNG file counts missing")
            failed += 1

        # Test 4: Contains status indicators
        has_status = "✓ Complete" in content or "⚠ Partial" in content or "✗ No PNGs" in content
        if has_status:
            print("✓ Contains status indicators")
            passed += 1
        else:
            print("✗ Status indicators missing")
            failed += 1

        # Test 5: Lists all main sections
        main_sections = ["Introductory Section", "Financial Section", "Statistical Section"]
        all_present = all(section in content for section in main_sections)

        if all_present:
            print("✓ All main sections listed")
            passed += 1
        else:
            print("✗ Some main sections missing")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_issues_warnings():
    """Test issues/warnings detection."""
    print("=" * 80)
    print("Testing Issues/Warnings Detection")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Generate report
        output_file = stripper.generate_report("test_report.txt")

        with open(output_file, 'r') as f:
            content = f.read()

        passed = 0
        failed = 0

        # Test 1: Contains issues/warnings section
        if "ISSUES/WARNINGS" in content:
            print("✓ Issues/warnings section present")
            passed += 1
        else:
            print("✗ Issues/warnings section missing")
            failed += 1

        # Test 2: Detects pages without page numbers (pages 1-2)
        if "Pages 1-2: No page numbers detected" in content or "Page 1: No page number detected" in content:
            print("✓ Detects pages without page numbers")
            passed += 1
        else:
            print("✗ Failed to detect pages without numbers")
            failed += 1

        # Test 3: Detects pages without PNG files (pages 26-30)
        if "Pages 26-30: PNG files not created" in content or "Page 26: PNG file not created" in content:
            print("✓ Detects pages without PNG files")
            passed += 1
        else:
            print("✗ Failed to detect missing PNG files")
            failed += 1

        print()
        print(f"Passed: {passed}/3")
        print(f"Failed: {failed}/3")
        print()

        return failed == 0


def test_no_issues():
    """Test report when there are no issues."""
    print("=" * 80)
    print("Testing No Issues Scenario")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = PDFStripper.__new__(PDFStripper)
        stripper.pdf_path = Path("/path/to/perfect_cafr.pdf")
        stripper.output_dir = temp_path

        # Create perfect TOC
        stripper.toc_entries = [
            TOCEntry("Introductory Section", 1, 1, None),
        ]

        # Create perfect pages (all have numbers, sections, and PNGs)
        stripper.page_metadata = []
        for i in range(1, 11):
            metadata = PageMetadata(
                pdf_page_num=i,
                footer_page_num=str(i),
                section_name="Introductory Section",
                section_level=1,
                header_text=f"HEADER {i}",
                parent_section_name=None,
                png_file=f"output/{i:04d}.png"
            )
            stripper.page_metadata.append(metadata)

        # Generate report
        output_file = stripper.generate_report("test_report.txt")

        with open(output_file, 'r') as f:
            content = f.read()

        passed = 0
        failed = 0

        # Test 1: Contains "No issues detected"
        if "No issues detected" in content:
            print("✓ Shows 'No issues detected'")
            passed += 1
        else:
            print("✗ Missing 'No issues detected' message")
            failed += 1

        print()
        print(f"Passed: {passed}/1")
        print(f"Failed: {failed}/1")
        print()

        return failed == 0


def test_output_files_section():
    """Test output files section."""
    print("=" * 80)
    print("Testing Output Files Section")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Create a metadata file
        metadata_file = temp_path / "cafr_metadata.json"
        metadata_file.write_text('{"test": "data"}')

        # Generate report
        output_file = stripper.generate_report("test_report.txt")

        with open(output_file, 'r') as f:
            content = f.read()

        passed = 0
        failed = 0

        # Test 1: Contains OUTPUT FILES section
        if "OUTPUT FILES" in content:
            print("✓ Output files section present")
            passed += 1
        else:
            print("✗ Output files section missing")
            failed += 1

        # Test 2: Lists metadata file
        if "Metadata:" in content:
            print("✓ Metadata file listed")
            passed += 1
        else:
            print("✗ Metadata file not listed")
            failed += 1

        # Test 3: Lists report file
        if "Report:" in content:
            print("✓ Report file listed")
            passed += 1
        else:
            print("✗ Report file not listed")
            failed += 1

        # Test 4: Lists PNG files with count
        if "PNG Files:" in content and "25 files" in content:
            print("✓ PNG files listed with count")
            passed += 1
        else:
            print("✗ PNG files listing incorrect")
            failed += 1

        print()
        print(f"Passed: {passed}/4")
        print(f"Failed: {failed}/4")
        print()

        return failed == 0


def test_summary_statistics():
    """Test summary statistics section."""
    print("=" * 80)
    print("Testing Summary Statistics")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        stripper = create_test_stripper(temp_path)

        # Generate report
        output_file = stripper.generate_report("test_report.txt")

        with open(output_file, 'r') as f:
            content = f.read()

        passed = 0
        failed = 0

        # Test 1: Contains SUMMARY STATISTICS section
        if "SUMMARY STATISTICS" in content:
            print("✓ Summary statistics section present")
            passed += 1
        else:
            print("✗ Summary statistics section missing")
            failed += 1

        # Test 2: Contains total pages
        if "Total Pages: 30" in content:
            print("✓ Total pages statistic correct")
            passed += 1
        else:
            print("✗ Total pages statistic incorrect")
            failed += 1

        # Test 3: Contains pages with numbers (28, pages 3-30)
        if "Pages with Numbers: 28" in content:
            print("✓ Pages with numbers statistic correct")
            passed += 1
        else:
            print("✗ Pages with numbers statistic incorrect")
            failed += 1

        # Test 4: Contains PNG files count (25)
        if "PNG Files Created: 25" in content:
            print("✓ PNG files statistic correct")
            passed += 1
        else:
            print("✗ PNG files statistic incorrect")
            failed += 1

        # Test 5: Contains TOC entries (5)
        if "TOC Entries: 5" in content:
            print("✓ TOC entries statistic correct")
            passed += 1
        else:
            print("✗ TOC entries statistic incorrect")
            failed += 1

        # Test 6: Contains main sections count (3)
        if "Main Sections: 3" in content:
            print("✓ Main sections statistic correct")
            passed += 1
        else:
            print("✗ Main sections statistic incorrect")
            failed += 1

        # Test 7: Contains subsections count (2)
        if "Subsections: 2" in content:
            print("✓ Subsections statistic correct")
            passed += 1
        else:
            print("✗ Subsections statistic incorrect")
            failed += 1

        print()
        print(f"Passed: {passed}/7")
        print(f"Failed: {failed}/7")
        print()

        return failed == 0


def test_error_handling():
    """Test error handling."""
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
            stripper.generate_report()
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
        nested_path = "nested/dir/report.txt"
        output_file = stripper.generate_report(nested_path)

        if Path(output_file).exists():
            print("✓ Created nested directories")
            passed += 1
        else:
            print("✗ Failed to create nested directories")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_group_consecutive_pages():
    """Test _group_consecutive_pages helper method."""
    print("=" * 80)
    print("Testing Group Consecutive Pages Helper")
    print("=" * 80)
    print()

    stripper = PDFStripper.__new__(PDFStripper)

    passed = 0
    failed = 0

    # Test 1: Single page
    result = stripper._group_consecutive_pages([5])
    if result == [(5, 5)]:
        print("✓ Single page: [(5, 5)]")
        passed += 1
    else:
        print(f"✗ Single page failed: {result}")
        failed += 1

    # Test 2: Consecutive pages
    result = stripper._group_consecutive_pages([1, 2, 3, 4, 5])
    if result == [(1, 5)]:
        print("✓ Consecutive pages: [(1, 5)]")
        passed += 1
    else:
        print(f"✗ Consecutive pages failed: {result}")
        failed += 1

    # Test 3: Multiple ranges
    result = stripper._group_consecutive_pages([1, 2, 3, 10, 11, 20])
    if result == [(1, 3), (10, 11), (20, 20)]:
        print("✓ Multiple ranges: [(1, 3), (10, 11), (20, 20)]")
        passed += 1
    else:
        print(f"✗ Multiple ranges failed: {result}")
        failed += 1

    # Test 4: Unsorted input
    result = stripper._group_consecutive_pages([5, 1, 3, 2, 4])
    if result == [(1, 5)]:
        print("✓ Unsorted input: [(1, 5)]")
        passed += 1
    else:
        print(f"✗ Unsorted input failed: {result}")
        failed += 1

    # Test 5: Empty list
    result = stripper._group_consecutive_pages([])
    if result == []:
        print("✓ Empty list: []")
        passed += 1
    else:
        print(f"✗ Empty list failed: {result}")
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
    print("PROMPT 5B: Human-Readable Report - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_basic_report()
    all_passed &= test_toc_formatting()
    all_passed &= test_page_mapping_summary()
    all_passed &= test_issues_warnings()
    all_passed &= test_no_issues()
    all_passed &= test_output_files_section()
    all_passed &= test_summary_statistics()
    all_passed &= test_error_handling()
    all_passed &= test_group_consecutive_pages()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 5B tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ generate_report() - Creates formatted text report")
        print("  ✓ Header section - PDF info and processing timestamp")
        print("  ✓ TOC section - Formatted with indentation and alignment")
        print("  ✓ Page mapping - Summary by section with status indicators")
        print("  ✓ Issues/warnings - Detects missing numbers, sections, PNGs")
        print("  ✓ Output files - Lists metadata, report, PNG files")
        print("  ✓ Summary stats - Comprehensive statistics")
        print("  ✓ Helper methods - Group consecutive pages")
        print("  ✓ Error handling - Validates page_metadata")
        print()
        print("Phase 5 complete! Ready for Phase 6!")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
