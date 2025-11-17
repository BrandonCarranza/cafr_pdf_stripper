#!/usr/bin/env python3
"""
Test script for PROMPT 3A: Section Mapper

Tests page-to-section mapping functionality:
- Basic section mapping
- Hierarchical section mapping (subsections)
- Parent section detection
- Edge cases (pages before/after sections)
- Boundary pages

Usage:
    python test_section_mapper.py
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

sys.modules['pdfplumber'] = MockModule()
sys.modules['pytesseract'] = MockModule()
sys.modules['pdf2image'] = MockModule()
sys.modules['PIL'] = MockModule()
sys.modules['PIL.Image'] = MockModule()
sys.modules['tqdm'] = MockModule()

import config
from ibco_stripper import PDFStripper, TOCEntry, PageMetadata


def test_basic_section_mapping():
    """Test basic page to section mapping without hierarchy."""
    print("=" * 80)
    print("Testing Basic Section Mapping")
    print("=" * 80)
    print()

    # Create simple TOC with 3 main sections
    toc_entries = [
        TOCEntry("Introductory Section", 1, 1),
        TOCEntry("Financial Section", 25, 1),
        TOCEntry("Statistical Section", 150, 1),
    ]

    stripper = PDFStripper.__new__(PDFStripper)
    stripper.toc_entries = toc_entries

    # Test cases: (page_number, expected_section, expected_level)
    test_cases = [
        (1, "Introductory Section", 1, "First page of first section"),
        (10, "Introductory Section", 1, "Middle of first section"),
        (24, "Introductory Section", 1, "Last page of first section"),
        (25, "Financial Section", 1, "First page of second section"),
        (100, "Financial Section", 1, "Middle of second section"),
        (149, "Financial Section", 1, "Last page of second section"),
        (150, "Statistical Section", 1, "First page of last section"),
        (200, "Statistical Section", 1, "Middle of last section"),
        (300, "Statistical Section", 1, "End of last section"),
    ]

    print(f"{'Page':<8} {'Expected Section':<30} {'Got Section':<30} {'Status'}")
    print("-" * 80)

    passed = 0
    failed = 0

    for page, expected_section, expected_level, description in test_cases:
        section, level, parent = stripper.map_page_to_section(page)

        if section == expected_section and level == expected_level:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1

        print(f"{page:<8} {expected_section:<30} {section or 'None':<30} {status} {description}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_hierarchical_section_mapping():
    """Test section mapping with hierarchical sections (subsections)."""
    print("=" * 80)
    print("Testing Hierarchical Section Mapping")
    print("=" * 80)
    print()

    # Create TOC with hierarchy
    toc_entries = [
        TOCEntry("Introductory Section", 1, 1),
        TOCEntry("  Letter of Transmittal", 3, 2),
        TOCEntry("  GFOA Certificate", 12, 2),
        TOCEntry("Financial Section", 25, 1),
        TOCEntry("  Independent Auditor's Report", 26, 2),
        TOCEntry("  Basic Financial Statements", 45, 2),
        TOCEntry("    Government-wide Statements", 46, 3),
        TOCEntry("    Fund Statements", 50, 3),
        TOCEntry("  Notes to Statements", 76, 2),
        TOCEntry("Statistical Section", 150, 1),
    ]

    stripper = PDFStripper.__new__(PDFStripper)
    stripper.toc_entries = toc_entries

    # Test cases: (page, expected_section, expected_level, expected_parent)
    test_cases = [
        (1, "Introductory Section", 1, None, "Main section page 1"),
        (3, "  Letter of Transmittal", 2, "Introductory Section", "Subsection page 3"),
        (10, "  Letter of Transmittal", 2, "Introductory Section", "Middle of subsection"),
        (12, "  GFOA Certificate", 2, "Introductory Section", "Second subsection"),
        (20, "  GFOA Certificate", 2, "Introductory Section", "End of subsection"),
        (25, "Financial Section", 1, None, "Main section page 25"),
        (26, "  Independent Auditor's Report", 2, "Financial Section", "First subsection"),
        (46, "    Government-wide Statements", 3, "  Basic Financial Statements", "Sub-subsection level 3"),
        (48, "    Government-wide Statements", 3, "  Basic Financial Statements", "Middle of level 3"),
        (50, "    Fund Statements", 3, "  Basic Financial Statements", "Second level 3"),
        (70, "    Fund Statements", 3, "  Basic Financial Statements", "End of level 3"),
        (76, "  Notes to Statements", 2, "Financial Section", "Back to level 2"),
        (150, "Statistical Section", 1, None, "Main section page 150"),
    ]

    print(f"{'Page':<6} {'Expected Section':<35} {'Level':<6} {'Parent':<25} {'Status'}")
    print("-" * 80)

    passed = 0
    failed = 0

    for page, expected_section, expected_level, expected_parent, description in test_cases:
        section, level, parent = stripper.map_page_to_section(page)

        # Trim whitespace for comparison
        section = section.strip() if section else None
        expected_section = expected_section.strip()
        parent = parent.strip() if parent else None
        expected_parent = expected_parent.strip() if expected_parent else None

        if section == expected_section and level == expected_level and parent == expected_parent:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1
            print(f"{page:<6} {expected_section:<35} {expected_level:<6} {expected_parent or 'None':<25} {status}")
            print(f"       Got: section={section}, level={level}, parent={parent}")
            continue

        print(f"{page:<6} {expected_section:<35} {expected_level:<6} {expected_parent or 'None':<25} {status}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_edge_cases():
    """Test edge cases for section mapping."""
    print("=" * 80)
    print("Testing Edge Cases")
    print("=" * 80)
    print()

    # Create TOC
    toc_entries = [
        TOCEntry("Introductory Section", 10, 1),
        TOCEntry("Financial Section", 50, 1),
        TOCEntry("Statistical Section", 100, 1),
    ]

    stripper = PDFStripper.__new__(PDFStripper)
    stripper.toc_entries = toc_entries

    # Test cases
    test_cases = [
        (1, None, 0, "Page before first section"),
        (5, None, 0, "Page before first section (closer)"),
        (10, "Introductory Section", 1, "First page of first section"),
        (49, "Introductory Section", 1, "Last page before second section"),
        (50, "Financial Section", 1, "Boundary: first page of second section"),
        (200, "Statistical Section", 1, "Page beyond all sections"),
    ]

    print(f"{'Page':<6} {'Expected Result':<30} {'Got Result':<30} {'Status'}")
    print("-" * 80)

    passed = 0
    failed = 0

    for page, expected_section, expected_level, description in test_cases:
        section, level, parent = stripper.map_page_to_section(page)

        if section == expected_section and level == expected_level:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1

        result = f"{section} (L{level})" if section else "None"
        expected = f"{expected_section} (L{expected_level})" if expected_section else "None"

        print(f"{page:<6} {expected:<30} {result:<30} {status} {description}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_page_metadata_creation():
    """Test creating PageMetadata objects with section information."""
    print("=" * 80)
    print("Testing PageMetadata Creation")
    print("=" * 80)
    print()

    # Create TOC
    toc_entries = [
        TOCEntry("Financial Section", 1, 1),
        TOCEntry("  Basic Financial Statements", 25, 2),
    ]

    stripper = PDFStripper.__new__(PDFStripper)
    stripper.toc_entries = toc_entries

    # Test creating metadata for a page
    page_num = 30
    section, level, parent = stripper.map_page_to_section(page_num)

    metadata = PageMetadata(
        pdf_page_num=30,
        footer_page_num="6",
        section_name=section,
        section_level=level,
        header_text="FINANCIAL SECTION",
        parent_section_name=parent
    )

    print("Created PageMetadata:")
    print(f"  PDF Page: {metadata.pdf_page_num}")
    print(f"  Footer Page: {metadata.footer_page_num}")
    print(f"  Section: {metadata.section_name}")
    print(f"  Level: {metadata.section_level}")
    print(f"  Parent: {metadata.parent_section_name}")
    print(f"  Header: {metadata.header_text}")
    print()

    # Verify fields
    if (metadata.section_name == "  Basic Financial Statements" and
        metadata.section_level == 2 and
        metadata.parent_section_name == "Financial Section"):
        print("✓ PageMetadata created correctly with section mapping")
        print()
        return True
    else:
        print("✗ PageMetadata fields incorrect")
        print()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PROMPT 3A: Section Mapper - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run all tests
    all_passed &= test_basic_section_mapping()
    all_passed &= test_hierarchical_section_mapping()
    all_passed &= test_edge_cases()
    all_passed &= test_page_metadata_creation()

    # Summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 3A tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ map_page_to_section() - Maps pages to sections")
        print("  ✓ PageMetadata updated - Added parent_section_name field")
        print("  ✓ Hierarchical mapping - Handles subsections correctly")
        print("  ✓ Parent detection - Identifies parent sections")
        print("  ✓ Edge cases - Pages before/after sections handled")
        print()
        print("Ready for PROMPT 3B: Build Complete Page Index")
    else:
        print("✗ Some tests failed")
        return 1

    print("=" * 80)
    return 0


if __name__ == '__main__':
    sys.exit(main())
