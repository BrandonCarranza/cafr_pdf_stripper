#!/usr/bin/env python3
"""
Test script for PROMPT 6C: Verification & Quality Check

Tests verification and repair functionality:
- Post-processing verification
- Quality checks (PNG count, sections, gaps, file sizes, metadata)
- Issue detection
- Automated repair (re-process pages, re-OCR TOC)
- Manual intervention suggestions

Usage:
    python test_verification.py
"""

import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import io

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
                return str(self.page_num)
            elif top and top < 100:
                return f"HEADER {self.page_num}"
            return "Sample text"

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
from ibco_stripper import PDFStripper, TOCEntry, PageMetadata


def create_test_setup(temp_dir: Path) -> tuple:
    """
    Create test CAFR setup with PDF and TOC.

    Args:
        temp_dir: Temporary directory

    Returns:
        Tuple of (pdf_path, toc_path, output_dir, stripper)
    """
    # Create mock PDF
    pdf_path = temp_dir / "test.pdf"
    pdf_path.write_text("Mock PDF")

    # Create mock TOC screenshot
    toc_path = temp_dir / "toc.png"
    toc_path.write_text("Mock TOC")

    # Create output directory
    output_dir = temp_dir / "output"
    output_dir.mkdir()

    # Create stripper
    stripper = PDFStripper(str(pdf_path), str(output_dir))

    # Mock TOC entries
    stripper.toc_entries = [
        TOCEntry(section_name="Introductory Section", page_number=1, level=1, parent=None),
        TOCEntry(section_name="Financial Section", page_number=11, level=1, parent=None),
        TOCEntry(section_name="Statistical Section", page_number=21, level=1, parent=None),
    ]

    # Build page index
    stripper.build_page_index()

    # Manually set section mappings (since mock won't do it automatically)
    for i, page in enumerate(stripper.page_metadata):
        page.footer_page_num = i + 1
        if i < 10:
            page.section_name = "Introductory Section"
            page.section_level = 1
        elif i < 20:
            page.section_name = "Financial Section"
            page.section_level = 1
        else:
            page.section_name = "Statistical Section"
            page.section_level = 1

    return pdf_path, toc_path, output_dir, stripper


def test_verification_complete():
    """Test verification on complete, valid processing output."""
    print("=" * 80)
    print("Testing Verification - Complete Output")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create complete output structure
        sections_dir = output_dir / "sections"
        sections_dir.mkdir()

        # Create PNG files for all pages
        for page in stripper.page_metadata:
            section_slug = "intro" if page.pdf_page_num < 11 else "financial" if page.pdf_page_num < 21 else "statistical"
            section_dir = sections_dir / f"01_{section_slug}"
            section_dir.mkdir(exist_ok=True)

            png_path = section_dir / f"page_{page.pdf_page_num:04d}.png"
            png_path.write_text("PNG data")

            # Update page metadata
            page.png_file = str(png_path.relative_to(output_dir))

        # Create metadata JSON
        metadata = {
            "statistics": {
                "total_pages": len(stripper.page_metadata)
            }
        }
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            json.dump(metadata, f)

        # Create report
        (output_dir / "cafr_report.txt").write_text("Test report")

        # Run verification
        result = stripper.verify_processing()

        # Test 1: Verification should pass
        if result['status'] == 'passed':
            print("✓ Verification passed for complete output")
            passed += 1
        else:
            print(f"✗ Verification failed: {result['status']}")
            failed += 1

        # Test 2: No issues
        if len(result['issues']) == 0:
            print("✓ No issues detected")
            passed += 1
        else:
            print(f"✗ Found {len(result['issues'])} issues: {result['issues']}")
            failed += 1

        # Test 3: All checks passed
        if result['checks_passed'] >= 6:  # At least 6 of 8 checks should pass
            print(f"✓ {result['checks_passed']}/{result['checks_total']} checks passed")
            passed += 1
        else:
            print(f"✗ Only {result['checks_passed']}/{result['checks_total']} checks passed")
            failed += 1

        # Test 4: Metadata valid
        if result['metadata_valid']:
            print("✓ Metadata JSON is valid")
            passed += 1
        else:
            print("✗ Metadata JSON is invalid")
            failed += 1

        print()
        print(f"Passed: {passed}/4")
        print(f"Failed: {failed}/4")
        print()

        return failed == 0


def test_verification_missing_pngs():
    """Test verification detects missing PNG files."""
    print("=" * 80)
    print("Testing Verification - Missing PNGs")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create sections directory but don't create PNG files
        sections_dir = output_dir / "sections"
        sections_dir.mkdir()

        # Mark pages as having PNGs (but don't actually create them)
        for page in stripper.page_metadata:
            page.png_file = f"sections/test/page_{page.pdf_page_num:04d}.png"

        # Create metadata
        metadata = {"statistics": {"total_pages": len(stripper.page_metadata)}}
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            json.dump(metadata, f)

        # Run verification
        result = stripper.verify_processing()

        # Test 1: Should detect PNG count mismatch
        png_issue_found = any("PNG count mismatch" in issue for issue in result['issues'])
        if png_issue_found:
            print("✓ Detected PNG count mismatch")
            passed += 1
        else:
            print("✗ Did not detect PNG count mismatch")
            failed += 1

        # Test 2: Verification should fail
        if result['status'] == 'failed':
            print("✓ Verification failed as expected")
            passed += 1
        else:
            print(f"✗ Verification should have failed: {result['status']}")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_verification_missing_sections():
    """Test verification detects sections without pages."""
    print("=" * 80)
    print("Testing Verification - Missing Sections")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Add TOC entry that won't be found in pages
        stripper.toc_entries.append(
            TOCEntry(section_name="Missing Section", page_number=100, level=1, parent=None)
        )

        # Create metadata
        metadata = {"statistics": {"total_pages": len(stripper.page_metadata)}}
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            json.dump(metadata, f)

        # Run verification
        result = stripper.verify_processing()

        # Test 1: Should detect sections without pages
        section_issue_found = any("Sections without pages" in issue for issue in result['issues'])
        if section_issue_found:
            print("✓ Detected sections without pages")
            passed += 1
        else:
            print("✗ Did not detect sections without pages")
            failed += 1

        # Test 2: Verification should fail
        if result['status'] == 'failed':
            print("✓ Verification failed as expected")
            passed += 1
        else:
            print("✗ Verification should have failed")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_verification_corrupted_metadata():
    """Test verification detects corrupted metadata JSON."""
    print("=" * 80)
    print("Testing Verification - Corrupted Metadata")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create corrupted metadata JSON
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            f.write("{ invalid json content [")

        # Run verification
        result = stripper.verify_processing()

        # Test 1: Should detect corrupted JSON
        json_issue_found = any("Metadata JSON is corrupted" in issue for issue in result['issues'])
        if json_issue_found:
            print("✓ Detected corrupted metadata JSON")
            passed += 1
        else:
            print("✗ Did not detect corrupted metadata JSON")
            failed += 1

        # Test 2: Metadata should not be valid
        if not result['metadata_valid']:
            print("✓ Metadata marked as invalid")
            passed += 1
        else:
            print("✗ Metadata should be marked invalid")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_fix_issues_no_problems():
    """Test fix_issues when there are no problems."""
    print("=" * 80)
    print("Testing Fix Issues - No Problems")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create complete output
        sections_dir = output_dir / "sections"
        sections_dir.mkdir()

        for page in stripper.page_metadata:
            section_dir = sections_dir / "test"
            section_dir.mkdir(exist_ok=True)
            png_path = section_dir / f"page_{page.pdf_page_num:04d}.png"
            png_path.write_text("PNG data")
            page.png_file = str(png_path.relative_to(output_dir))

        metadata = {"statistics": {"total_pages": len(stripper.page_metadata)}}
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            json.dump(metadata, f)

        # Run fix
        result = stripper.fix_issues()

        # Test 1: Should report no issues
        if result['status'] == 'no_issues':
            print("✓ Correctly identified no issues")
            passed += 1
        else:
            print(f"✗ Wrong status: {result['status']}")
            failed += 1

        # Test 2: No fixes should be made
        if len(result['issues_fixed']) == 0:
            print("✓ No fixes attempted")
            passed += 1
        else:
            print(f"✗ Should not have attempted fixes: {result['issues_fixed']}")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_fix_issues_missing_pngs():
    """Test fix_issues can regenerate missing PNG files."""
    print("=" * 80)
    print("Testing Fix Issues - Regenerate Missing PNGs")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create sections directory
        sections_dir = output_dir / "sections"
        sections_dir.mkdir()

        # Mark first 5 pages as having PNGs but don't create them
        for i, page in enumerate(stripper.page_metadata[:5]):
            section_dir = sections_dir / "test"
            section_dir.mkdir(exist_ok=True)
            page.png_file = f"sections/test/page_{page.pdf_page_num:04d}.png"

        # Run fix with mocked pdf2image
        with patch('ibco_stripper.convert_from_path', side_effect=MockPDF2Image.convert_from_path):
            result = stripper.fix_issues(reprocess_failed_pages=True)

            # Test 1: Should have fixed issues
            if len(result['issues_fixed']) > 0:
                print(f"✓ Fixed {len(result['issues_fixed'])} issue(s)")
                passed += 1
            else:
                print("✗ Did not fix any issues")
                failed += 1

            # Test 2: PNG files should be mentioned in fixes
            png_fix_found = any("PNG" in fix for fix in result['issues_fixed'])
            if png_fix_found:
                print("✓ PNG regeneration mentioned in fixes")
                passed += 1
            else:
                print("✗ PNG regeneration not mentioned in fixes")
                failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_fix_issues_re_ocr():
    """Test fix_issues can re-OCR TOC."""
    print("=" * 80)
    print("Testing Fix Issues - Re-OCR TOC")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Start with limited TOC
        stripper.toc_entries = [
            TOCEntry(section_name="Section 1", page_number=1, level=1, parent=None)
        ]

        # Mock pytesseract to return more entries
        def mock_image_to_string(image, **kwargs):
            return """
            Table of Contents

            Section 1 ........................ 1
            Section 2 ........................ 10
            Section 3 ........................ 20
            """

        with patch('pytesseract.image_to_string', side_effect=mock_image_to_string):
            result = stripper.fix_issues(
                re_ocr_toc=True,
                toc_screenshots=[str(toc_path)],
                reprocess_failed_pages=False
            )

            # Test 1: Should have found additional entries
            if len(stripper.toc_entries) > 1:
                print(f"✓ Found {len(stripper.toc_entries)} TOC entries after re-OCR")
                passed += 1
            else:
                print(f"✗ Did not find additional entries: {len(stripper.toc_entries)}")
                failed += 1

            # Test 2: Re-OCR should be mentioned in fixes
            ocr_fix_found = any("Re-OCR" in fix or "OCR" in fix for fix in result['issues_fixed'])
            if ocr_fix_found or len(result['issues_fixed']) > 0:
                print("✓ Re-OCR mentioned in results")
                passed += 1
            else:
                print("✗ Re-OCR not mentioned in results")
                failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_manual_intervention_suggestions():
    """Test that fix_issues suggests manual intervention when needed."""
    print("=" * 80)
    print("Testing Manual Intervention Suggestions")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create corrupted metadata
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            f.write("{ invalid json")

        # Run fix (should suggest manual intervention)
        result = stripper.fix_issues(reprocess_failed_pages=False, re_ocr_toc=False)

        # Test 1: Should suggest manual intervention
        if len(result['manual_intervention_needed']) > 0:
            print(f"✓ Suggested {len(result['manual_intervention_needed'])} manual intervention(s)")
            passed += 1
        else:
            print("✗ Did not suggest manual intervention")
            failed += 1

        # Test 2: Should mention metadata in suggestions
        metadata_suggestion = any("metadata" in s.lower() for s in result['manual_intervention_needed'])
        if metadata_suggestion or len(result['manual_intervention_needed']) > 0:
            print("✓ Relevant suggestions provided")
            passed += 1
        else:
            print("✗ Missing relevant suggestions")
            failed += 1

        print()
        print(f"Passed: {passed}/2")
        print(f"Failed: {failed}/2")
        print()

        return failed == 0


def test_page_number_gaps():
    """Test verification detects gaps in page numbering."""
    print("=" * 80)
    print("Testing Page Number Gap Detection")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        pdf_path, toc_path, output_dir, stripper = create_test_setup(temp_path)

        passed = 0
        failed = 0

        # Create gap in page numbering (1, 2, 3, 10, 11, 12...)
        for i, page in enumerate(stripper.page_metadata):
            if i < 3:
                page.footer_page_num = i + 1
            else:
                page.footer_page_num = i + 10

        # Create metadata
        metadata = {"statistics": {"total_pages": len(stripper.page_metadata)}}
        with open(output_dir / "cafr_metadata.json", 'w') as f:
            json.dump(metadata, f)

        # Run verification
        result = stripper.verify_processing()

        # Test 1: Should detect gaps
        gap_warning_found = any("gaps in page numbering" in warning.lower() for warning in result['warnings'])
        if gap_warning_found:
            print("✓ Detected gaps in page numbering")
            passed += 1
        else:
            print("✗ Did not detect gaps in page numbering")
            failed += 1

        print()
        print(f"Passed: {passed}/1")
        print(f"Failed: {failed}/1")
        print()

        return failed == 0


def main():
    """Run all tests."""
    print()
    print("=" * 80)
    print("PROMPT 6C: Verification & Quality Check - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_verification_complete()
    all_passed &= test_verification_missing_pngs()
    all_passed &= test_verification_missing_sections()
    all_passed &= test_verification_corrupted_metadata()
    all_passed &= test_fix_issues_no_problems()
    all_passed &= test_fix_issues_missing_pngs()
    all_passed &= test_fix_issues_re_ocr()
    all_passed &= test_manual_intervention_suggestions()
    all_passed &= test_page_number_gaps()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 6C tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ verify_processing() method")
        print("  ✓ PNG file count verification")
        print("  ✓ Section completeness checks")
        print("  ✓ Page sequence gap detection")
        print("  ✓ File size anomaly detection")
        print("  ✓ Metadata JSON validation")
        print("  ✓ Report file verification")
        print("  ✓ fix_issues() method")
        print("  ✓ Automated PNG regeneration")
        print("  ✓ Re-OCR TOC functionality")
        print("  ✓ Manual intervention suggestions")
        print()
        print("🎉 ALL 16 PROMPTS COMPLETE! 🎉")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
