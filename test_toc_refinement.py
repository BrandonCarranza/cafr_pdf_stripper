#!/usr/bin/env python3
"""
Test script for PROMPT 2B: TOC Parser Refinement

Tests enhanced TOC parsing with:
- Roman numeral page references
- Multiple pattern formats
- Proper sorting by page number
- Hierarchy detection
- Edge case handling

Usage:
    python test_toc_refinement.py
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
from ibco_stripper import PDFStripper, TOCEntry


def test_roman_numeral_pages():
    """Test TOC entries with Roman numeral page numbers."""
    print("=" * 80)
    print("Testing Roman Numeral Page References")
    print("=" * 80)
    print()

    test_cases = [
        # (input_line, expected_section, expected_page_int, description)
        ("Introductory Section .................. i", "Introductory Section", 1, "Roman i = 1"),
        ("Table of Contents ..................... ii", "Table of Contents", 2, "Roman ii = 2"),
        ("Letter of Transmittal ................. iii", "Letter of Transmittal", 3, "Roman iii = 3"),
        ("GFOA Certificate ...................... iv", "GFOA Certificate", 4, "Roman iv = 4"),
        ("Organizational Chart .................. v", "Organizational Chart", 5, "Roman v = 5"),
        ("List of Officials ..................... vi", "List of Officials", 6, "Roman vi = 6"),
        ("Introduction .......................... x", "Introduction", 10, "Roman x = 10"),
        ("Summary ............................... xii", "Summary", 12, "Roman xii = 12"),
        ("Appendix A ............................ xv", "Appendix A", 15, "Roman xv = 15"),
    ]

    # Create temp stripper for testing
    stripper = PDFStripper.__new__(PDFStripper)

    passed = 0
    failed = 0

    print(f"{'Test Case':<40} {'Expected Page':<15} {'Got Page':<15} {'Status'}")
    print("-" * 80)

    for line, expected_section, expected_page, description in test_cases:
        entry = stripper._parse_toc_line(line)

        if entry and entry.section_name == expected_section and entry.page_number == expected_page:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
            if entry:
                print(f"{description:<40} {expected_page:<15} {entry.page_number:<15} {status}")
            else:
                print(f"{description:<40} {expected_page:<15} {'None':<15} {status}")
            continue

        print(f"{description:<40} {expected_page:<15} {entry.page_number:<15} {status}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_mixed_numbering():
    """Test TOC with mixed Roman and Arabic numerals."""
    print("=" * 80)
    print("Testing Mixed Roman/Arabic Numbering")
    print("=" * 80)
    print()

    # Simulates a real CAFR TOC with Roman → Arabic transition
    sample_toc = """
Introductory Section ......................... i
    Letter of Transmittal ..................... iii
    GFOA Certificate .......................... vi
    Organizational Chart ...................... viii

Financial Section ........................... 1
    Independent Auditor's Report .............. 2
    Management's Discussion and Analysis ...... 10
    Basic Financial Statements ................ 25

Statistical Section ......................... 150
    Financial Trends .......................... 151
    Revenue Capacity .......................... 165
"""

    stripper = PDFStripper.__new__(PDFStripper)
    entries = stripper._parse_toc_text(sample_toc)

    print(f"Parsed {len(entries)} TOC entries:")
    print()
    print(f"{'Section Name':<50} {'Page (int)':<12} {'Level'}")
    print("-" * 80)

    for entry in entries:
        indent = "  " * (entry.level - 1)
        print(f"{indent}{entry.section_name:<{50-len(indent)}} {entry.page_number:<12} {entry.level}")

    print()

    # Verify sorting
    is_sorted = all(entries[i].page_number <= entries[i+1].page_number
                    for i in range(len(entries)-1))

    if is_sorted:
        print("✓ Entries are properly sorted by page number")
        print(f"  First entry: page {entries[0].page_number} ({entries[0].section_name})")
        print(f"  Last entry: page {entries[-1].page_number} ({entries[-1].section_name})")
    else:
        print("✗ Entries are NOT sorted correctly")
        for i in range(len(entries)-1):
            if entries[i].page_number > entries[i+1].page_number:
                print(f"  Error: page {entries[i].page_number} comes before page {entries[i+1].page_number}")

    print()

    return is_sorted and len(entries) == 11


def test_enhanced_patterns():
    """Test enhanced pattern matching for edge cases."""
    print("=" * 80)
    print("Testing Enhanced Pattern Matching")
    print("=" * 80)
    print()

    test_cases = [
        # (input_line, should_parse, description)
        ("1. Introductory Section .......... 1", True, "Numbered section with dots"),
        ("A. Letter of Transmittal ......... 3", True, "Lettered section with dots"),
        ("Financial Section   25", True, "Multiple spaces (no dots)"),
        ("Statistical Section Page 150", True, "With 'Page' prefix"),
        ("Basic Financial Statements Page iv", True, "Page + Roman numeral"),
        ("Notes to Statements .... iii", True, "Dots + Roman numeral"),
        ("Appendix A     xii", True, "Spaces + Roman numeral"),
        ("Management Discussion & Analysis 30", True, "Ampersand in name"),
        ("CAFR", False, "Header only (no page)"),
        ("TABLE OF CONTENTS", False, "Header only"),
        ("", False, "Empty line"),
    ]

    stripper = PDFStripper.__new__(PDFStripper)

    passed = 0
    failed = 0

    print(f"{'Test Case':<50} {'Should Parse':<15} {'Result':<15} {'Status'}")
    print("-" * 80)

    for line, should_parse, description in test_cases:
        entry = stripper._parse_toc_line(line)
        parsed = entry is not None

        if parsed == should_parse:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        result = "Parsed" if parsed else "Not parsed"
        expected = "Yes" if should_parse else "No"

        print(f"{description:<50} {expected:<15} {result:<15} {status}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def test_page_conversion():
    """Test the _convert_page_to_int helper method."""
    print("=" * 80)
    print("Testing Page String to Integer Conversion")
    print("=" * 80)
    print()

    test_cases = [
        # (input, expected_output, description)
        ("1", 1, "Arabic numeral 1"),
        ("25", 25, "Arabic numeral 25"),
        ("200", 200, "Arabic numeral 200"),
        ("i", 1, "Roman numeral i"),
        ("iii", 3, "Roman numeral iii"),
        ("iv", 4, "Roman numeral iv"),
        ("x", 10, "Roman numeral x"),
        ("xii", 12, "Roman numeral xii"),
        ("Page 25", 25, "Page prefix with Arabic"),
        ("Page iii", 3, "Page prefix with Roman"),
        ("page 30", 30, "Lowercase 'page'"),
        ("abc", None, "Invalid string"),
        ("", None, "Empty string"),
    ]

    stripper = PDFStripper.__new__(PDFStripper)

    passed = 0
    failed = 0

    print(f"{'Input':<20} {'Expected':<12} {'Got':<12} {'Status'}")
    print("-" * 60)

    for input_str, expected, description in test_cases:
        result = stripper._convert_page_to_int(input_str)

        if result == expected:
            status = "✓"
            passed += 1
        else:
            status = "✗"
            failed += 1

        print(f"'{input_str}':<19 {str(expected):<12} {str(result):<12} {status} {description}")

    print()
    print(f"Passed: {passed}/{len(test_cases)}")
    print(f"Failed: {failed}/{len(test_cases)}")
    print()

    return failed == 0


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PROMPT 2B: TOC Parser Refinement - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run all tests
    all_passed &= test_page_conversion()
    all_passed &= test_roman_numeral_pages()
    all_passed &= test_mixed_numbering()
    all_passed &= test_enhanced_patterns()

    # Summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 2B tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ Roman numeral page reference support")
        print("  ✓ Enhanced pattern matching (8 patterns)")
        print("  ✓ Page string to integer conversion")
        print("  ✓ Automatic sorting by page number")
        print("  ✓ Mixed Roman/Arabic numbering support")
        print("  ✓ Edge case handling")
        print()
        print("Ready for PROMPT 2C: Multiple TOC Screenshot Support")
    else:
        print("✗ Some tests failed")
        return 1

    print("=" * 80)
    return 0


if __name__ == '__main__':
    sys.exit(main())
