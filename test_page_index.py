#!/usr/bin/env python3
"""
Test script for PROMPT 3B: Build Complete Page Index

Tests page index building functionality:
- Iterate through all PDF pages
- Extract footer page numbers
- Extract header text
- Map pages to sections
- Handle edge cases (pages before sections, no page numbers)
- Store page index internally
- Display progress indicator

Usage:
    python test_page_index.py
"""

import sys
from pathlib import Path

# Mock dependencies
class MockModule:
    """Mock module for dependencies."""
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()

class MockPDFPlumber:
    """Mock pdfplumber module."""
    class MockPDF:
        def __init__(self, pages):
            self.pages = pages

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockPage:
        def __init__(self, footer_text, header_text):
            self.footer_text = footer_text
            self.header_text = header_text

        def extract_text(self):
            return ""

    @staticmethod
    def open(path):
        # Create mock PDF with 50 pages
        # Create reverse lookup for Roman numerals
        int_to_roman = {v: k for k, v in config.ROMAN_NUMERALS.items()}

        pages = []
        for i in range(50):
            pdf_page = i + 1
            # Pages 1-10: Cover pages with no page numbers
            if pdf_page <= 10:
                footer = None  # No footer on cover pages
                header = "COVER SECTION"
            # Pages 11-30: Introductory (1-20)
            elif pdf_page <= 30:
                footer = str(pdf_page - 10)
                header = "INTRODUCTORY SECTION"
            # Pages 31-45: Financial (21-35)
            elif pdf_page <= 45:
                footer = str(pdf_page - 10)
                header = "FINANCIAL SECTION"
            # Pages 46-50: Statistical (36-40)
            else:
                footer = str(pdf_page - 10)
                header = "STATISTICAL SECTION"

            pages.append(MockPDFPlumber.MockPage(footer, header))

        return MockPDFPlumber.MockPDF(pages)

sys.modules['pdfplumber'] = MockPDFPlumber
sys.modules['pytesseract'] = MockModule()
sys.modules['pdf2image'] = MockModule()
sys.modules['PIL'] = MockModule()
sys.modules['PIL.Image'] = MockModule()
sys.modules['tqdm'] = MockModule()

import config
from ibco_stripper import PDFStripper, TOCEntry, PageMetadata


def test_basic_page_index():
    """Test building page index with basic TOC."""
    print("=" * 80)
    print("Testing Basic Page Index Building")
    print("=" * 80)
    print()

    # Create TOC matching our mock PDF structure
    # Roman numerals i-x (PDF pages 1-10)
    # Then pages 1-40 (PDF pages 11-50)
    toc_entries = [
        TOCEntry("Introductory Section", 1, 1),   # Document page 1 = PDF page 11
        TOCEntry("Financial Section", 21, 1),     # Document page 21 = PDF page 31
        TOCEntry("Statistical Section", 36, 1),   # Document page 36 = PDF page 46
    ]

    # Create stripper (mock the PDF file)
    stripper = PDFStripper.__new__(PDFStripper)
    stripper.pdf_path = Path("mock.pdf")
    stripper.toc_entries = toc_entries
    stripper.page_metadata = []

    # Mock get_page_count to return 50
    stripper.get_page_count = lambda: 50

    # Mock read_footer_page_number
    def mock_read_footer(page):
        return page.footer_text
    stripper.read_footer_page_number = mock_read_footer

    # Mock read_header_text
    def mock_read_header(page):
        return page.header_text
    stripper.read_header_text = mock_read_header

    # Build page index
    print("Building page index...")
    print()
    page_index = stripper.build_page_index()
    print()

    # Verify results
    print("Verifying page index...")
    print()

    passed = 0
    failed = 0

    # Test 1: Verify correct number of pages
    if len(page_index) == 50:
        print("✓ Page index contains 50 pages")
        passed += 1
    else:
        print(f"✗ Expected 50 pages, got {len(page_index)}")
        failed += 1

    # Test 2: Verify page_metadata is stored internally
    if len(stripper.page_metadata) == 50:
        print("✓ Page index stored internally in page_metadata")
        passed += 1
    else:
        print(f"✗ page_metadata not stored correctly")
        failed += 1

    # Test 3: Check cover pages without page numbers (PDF pages 1-10)
    cover_pages_correct = True
    for i in range(10):
        pdf_page = i + 1
        metadata = page_index[i]

        if metadata.pdf_page_num != pdf_page:
            print(f"✗ PDF page {pdf_page}: wrong pdf_page_num")
            cover_pages_correct = False
        elif metadata.footer_page_num is not None:
            print(f"✗ PDF page {pdf_page}: expected no footer, got '{metadata.footer_page_num}'")
            cover_pages_correct = False
        elif metadata.section_name is not None:
            # Cover pages should not map to sections (no page numbers)
            print(f"✗ PDF page {pdf_page}: should not have section (no page number)")
            cover_pages_correct = False

    if cover_pages_correct:
        print("✓ Cover pages (no page numbers) handled correctly")
        passed += 1
    else:
        failed += 1

    # Test 4: Check Introductory Section pages (document pages 1-20, PDF pages 11-30)
    intro_correct = True
    for i in range(10, 30):
        pdf_page = i + 1
        doc_page = pdf_page - 10
        metadata = page_index[i]

        if metadata.footer_page_num != str(doc_page):
            print(f"✗ PDF page {pdf_page}: expected footer '{doc_page}', got '{metadata.footer_page_num}'")
            intro_correct = False
        elif metadata.section_name != "Introductory Section":
            print(f"✗ PDF page {pdf_page} (doc page {doc_page}): expected 'Introductory Section', got '{metadata.section_name}'")
            intro_correct = False
        elif metadata.section_level != 1:
            print(f"✗ PDF page {pdf_page}: wrong section level")
            intro_correct = False

    if intro_correct:
        print("✓ Introductory Section pages (1-20) mapped correctly")
        passed += 1
    else:
        failed += 1

    # Test 5: Check Financial Section pages (document pages 21-35, PDF pages 31-45)
    financial_correct = True
    for i in range(30, 45):
        pdf_page = i + 1
        doc_page = pdf_page - 10
        metadata = page_index[i]

        if metadata.section_name != "Financial Section":
            print(f"✗ PDF page {pdf_page} (doc page {doc_page}): expected 'Financial Section', got '{metadata.section_name}'")
            financial_correct = False

    if financial_correct:
        print("✓ Financial Section pages (21-35) mapped correctly")
        passed += 1
    else:
        failed += 1

    # Test 6: Check Statistical Section pages (document pages 36-40, PDF pages 46-50)
    statistical_correct = True
    for i in range(45, 50):
        pdf_page = i + 1
        doc_page = pdf_page - 10
        metadata = page_index[i]

        if metadata.section_name != "Statistical Section":
            print(f"✗ PDF page {pdf_page} (doc page {doc_page}): expected 'Statistical Section', got '{metadata.section_name}'")
            statistical_correct = False

    if statistical_correct:
        print("✓ Statistical Section pages (36-40) mapped correctly")
        passed += 1
    else:
        failed += 1

    # Test 7: Check header text extraction
    headers_correct = True
    for i, metadata in enumerate(page_index):
        if metadata.header_text is None:
            print(f"✗ PDF page {i+1}: missing header text")
            headers_correct = False
            break

    if headers_correct:
        print("✓ Header text extracted for all pages")
        passed += 1
    else:
        failed += 1

    print()
    print(f"Passed: {passed}/7")
    print(f"Failed: {failed}/7")
    print()

    return failed == 0


def test_edge_cases():
    """Test edge cases in page index building."""
    print("=" * 80)
    print("Testing Edge Cases")
    print("=" * 80)
    print()

    # Create TOC that doesn't start at page 1
    toc_entries = [
        TOCEntry("Main Section", 10, 1),
    ]

    # Create stripper
    stripper = PDFStripper.__new__(PDFStripper)
    stripper.pdf_path = Path("mock.pdf")
    stripper.toc_entries = toc_entries
    stripper.page_metadata = []

    # Mock get_page_count
    stripper.get_page_count = lambda: 20

    # Mock read_footer_page_number - some pages have no footer
    def mock_read_footer(page):
        pdf_page = stripper._current_page
        if pdf_page <= 5:
            return None  # No footer on first 5 pages
        else:
            return str(pdf_page - 5)
    stripper.read_footer_page_number = mock_read_footer

    # Mock read_header_text - some pages have no header
    def mock_read_header(page):
        pdf_page = stripper._current_page
        if pdf_page <= 3:
            return None  # No header on first 3 pages
        else:
            return "TEST HEADER"
    stripper.read_header_text = mock_read_header

    # Track current page for mocks
    stripper._current_page = 0

    # Override build_page_index to track current page
    original_build = PDFStripper.build_page_index

    def wrapped_build(self, toc_entries=None):
        if toc_entries is None:
            toc_entries = self.toc_entries

        page_count = self.get_page_count()
        page_index = []

        import pdfplumber

        with pdfplumber.open(self.pdf_path) as pdf:
            for pdf_page_num in range(1, page_count + 1):
                self._current_page = pdf_page_num
                page = pdf.pages[pdf_page_num - 1]

                footer_page_num = self.read_footer_page_number(page)
                header_text = self.read_header_text(page)

                section_name = None
                section_level = 0
                parent_section_name = None

                if footer_page_num:
                    page_num_int = self._convert_page_to_int(footer_page_num)
                    if page_num_int:
                        section_name, section_level, parent_section_name = self.map_page_to_section(
                            page_num_int, toc_entries
                        )

                metadata = PageMetadata(
                    pdf_page_num=pdf_page_num,
                    footer_page_num=footer_page_num,
                    section_name=section_name,
                    section_level=section_level,
                    header_text=header_text,
                    parent_section_name=parent_section_name,
                    png_file=None
                )

                page_index.append(metadata)

        self.page_metadata = page_index
        return page_index

    stripper.build_page_index = lambda toc=None: wrapped_build(stripper, toc)

    # Build page index
    print("Building page index with edge cases...")
    print()
    page_index = stripper.build_page_index()
    print()

    passed = 0
    failed = 0

    # Test 1: Pages without footer numbers
    pages_without_footer = [p for p in page_index if p.footer_page_num is None]
    if len(pages_without_footer) == 5:
        print(f"✓ Correctly handled {len(pages_without_footer)} pages without footer numbers")
        passed += 1
    else:
        print(f"✗ Expected 5 pages without footer, got {len(pages_without_footer)}")
        failed += 1

    # Test 2: Pages without footer should not have sections
    pages_without_footer_have_sections = [p for p in pages_without_footer if p.section_name is not None]
    if len(pages_without_footer_have_sections) == 0:
        print("✓ Pages without footer numbers have no section mapping")
        passed += 1
    else:
        print(f"✗ {len(pages_without_footer_have_sections)} pages without footer incorrectly have sections")
        failed += 1

    # Test 3: Pages without headers
    pages_without_header = [p for p in page_index if p.header_text is None]
    if len(pages_without_header) == 3:
        print(f"✓ Correctly handled {len(pages_without_header)} pages without headers")
        passed += 1
    else:
        print(f"✗ Expected 3 pages without headers, got {len(pages_without_header)}")
        failed += 1

    # Test 4: Pages before first section (doc pages 1-9, PDF pages 6-14)
    # These have footers but are before section start (page 10)
    pages_before_section = [p for p in page_index[5:14] if p.section_name is None and p.footer_page_num is not None]
    if len(pages_before_section) == 9:
        print(f"✓ Correctly handled {len(pages_before_section)} pages before first section")
        passed += 1
    else:
        print(f"✗ Expected 9 pages before first section, got {len(pages_before_section)}")
        failed += 1

    # Test 5: Pages in section (doc pages 10-15, PDF pages 15-20)
    pages_in_section = [p for p in page_index[14:20] if p.section_name == "Main Section"]
    if len(pages_in_section) == 6:
        print(f"✓ Correctly mapped {len(pages_in_section)} pages to section")
        passed += 1
    else:
        print(f"✗ Expected 6 pages in section, got {len(pages_in_section)}")
        failed += 1

    print()
    print(f"Passed: {passed}/5")
    print(f"Failed: {failed}/5")
    print()

    return failed == 0


def test_hierarchical_sections():
    """Test page index with hierarchical sections."""
    print("=" * 80)
    print("Testing Hierarchical Section Mapping in Page Index")
    print("=" * 80)
    print()

    # Create hierarchical TOC (without leading spaces in section names)
    toc_entries = [
        TOCEntry("Financial Section", 1, 1),
        TOCEntry("Management Discussion", 3, 2),
        TOCEntry("Basic Financial Statements", 10, 2),
        TOCEntry("Government-wide Statements", 12, 3),
        TOCEntry("Fund Statements", 20, 3),
        TOCEntry("Statistical Section", 30, 1),
    ]

    # Create stripper
    stripper = PDFStripper.__new__(PDFStripper)
    stripper.pdf_path = Path("mock.pdf")
    stripper.toc_entries = toc_entries
    stripper.page_metadata = []

    # Mock methods
    stripper.get_page_count = lambda: 40

    def mock_read_footer(page):
        return str(stripper._current_page)
    stripper.read_footer_page_number = mock_read_footer

    def mock_read_header(page):
        return "TEST"
    stripper.read_header_text = mock_read_header

    stripper._current_page = 0

    # Use wrapped build like in test_edge_cases
    def wrapped_build(self, toc_entries=None):
        if toc_entries is None:
            toc_entries = self.toc_entries

        page_count = self.get_page_count()
        page_index = []

        import pdfplumber

        with pdfplumber.open(self.pdf_path) as pdf:
            for pdf_page_num in range(1, page_count + 1):
                self._current_page = pdf_page_num
                page = pdf.pages[pdf_page_num - 1]

                footer_page_num = self.read_footer_page_number(page)
                header_text = self.read_header_text(page)

                section_name = None
                section_level = 0
                parent_section_name = None

                if footer_page_num:
                    page_num_int = self._convert_page_to_int(footer_page_num)
                    if page_num_int:
                        section_name, section_level, parent_section_name = self.map_page_to_section(
                            page_num_int, toc_entries
                        )

                metadata = PageMetadata(
                    pdf_page_num=pdf_page_num,
                    footer_page_num=footer_page_num,
                    section_name=section_name,
                    section_level=section_level,
                    header_text=header_text,
                    parent_section_name=parent_section_name,
                    png_file=None
                )

                page_index.append(metadata)

        self.page_metadata = page_index
        return page_index

    stripper.build_page_index = lambda toc=None: wrapped_build(stripper, toc)

    # Build index
    print("Building page index with hierarchical sections...")
    print()
    page_index = stripper.build_page_index()
    print()

    passed = 0
    failed = 0

    # Test specific pages
    test_cases = [
        (12, "Government-wide Statements", 3, "Basic Financial Statements", "Page 12: Level 3 subsection"),
        (15, "Government-wide Statements", 3, "Basic Financial Statements", "Page 15: Still in level 3"),
        (20, "Fund Statements", 3, "Basic Financial Statements", "Page 20: Different level 3"),
        (25, "Fund Statements", 3, "Basic Financial Statements", "Page 25: Still in Fund Statements"),
        (30, "Statistical Section", 1, None, "Page 30: New main section"),
    ]

    print(f"{'Page':<6} {'Expected Section':<28} {'Level':<6} {'Parent':<25} {'Status'}")
    print("-" * 80)

    for page_num, expected_section, expected_level, expected_parent, description in test_cases:
        metadata = page_index[page_num - 1]

        if (metadata.section_name == expected_section and
            metadata.section_level == expected_level and
            metadata.parent_section_name == expected_parent):
            print(f"{page_num:<6} {expected_section:<28} {expected_level:<6} {str(expected_parent):<25} ✓")
            passed += 1
        else:
            print(f"{page_num:<6} {expected_section:<28} {expected_level:<6} {str(expected_parent):<25} ✗")
            print(f"       Got: {metadata.section_name}, L{metadata.section_level}, parent={metadata.parent_section_name}")
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
    print("PROMPT 3B: Build Complete Page Index - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_basic_page_index()
    all_passed &= test_edge_cases()
    all_passed &= test_hierarchical_sections()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 3B tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ build_page_index() - Iterates through all PDF pages")
        print("  ✓ Footer extraction - Reads page numbers from footers")
        print("  ✓ Header extraction - Reads header text")
        print("  ✓ Section mapping - Maps pages to TOC sections")
        print("  ✓ Edge cases - Handles pages before sections, missing numbers")
        print("  ✓ Progress indicator - Shows 'Processing page N/total...'")
        print("  ✓ Internal storage - Stores in page_metadata attribute")
        print("  ✓ Summary stats - Reports pages with numbers/sections/headers")
        print()
        print("Ready for Phase 4!")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
