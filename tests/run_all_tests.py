#!/usr/bin/env python3
"""
Test runner for IBCo PDF Stripper test suite.

Runs all tests and provides summary.

Usage:
    python tests/run_all_tests.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_ibco_stripper import (
    TestFooterExtraction,
    TestTOCParsing,
    TestSectionMapping,
    TestPNGConversion,
    TestMetadataExport
)


def run_test_class(test_class, class_name):
    """Run all test methods in a test class."""
    print()
    print("=" * 80)
    print(f"{class_name}")
    print("=" * 80)
    print()

    instance = test_class()
    test_methods = [m for m in dir(instance) if m.startswith('test_')]

    passed = 0
    failed = 0
    errors = []

    for method_name in test_methods:
        try:
            method = getattr(instance, method_name)
            method()
            print(f"✓ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {method_name}: {e}")
            failed += 1
            errors.append((method_name, str(e)))
        except Exception as e:
            print(f"✗ {method_name}: ERROR: {e}")
            failed += 1
            errors.append((method_name, f"ERROR: {e}"))

    print()
    print(f"Passed: {passed}/{passed + failed}")
    print(f"Failed: {failed}/{passed + failed}")

    if errors:
        print()
        print("Failed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")

    return passed, failed


def main():
    """Run all test classes."""
    print()
    print("=" * 80)
    print("IBCo PDF Stripper - Comprehensive Test Suite")
    print("=" * 80)

    test_classes = [
        (TestFooterExtraction, "Footer Extraction Tests"),
        (TestTOCParsing, "TOC Parsing Tests"),
        (TestSectionMapping, "Section Mapping Tests"),
        (TestPNGConversion, "PNG Conversion Tests"),
        (TestMetadataExport, "Metadata Export Tests"),
    ]

    total_passed = 0
    total_failed = 0

    for test_class, class_name in test_classes:
        passed, failed = run_test_class(test_class, class_name)
        total_passed += passed
        total_failed += failed

    # Final summary
    print()
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print()
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    print(f"Success Rate: {total_passed}/{total_passed + total_failed} ({100 * total_passed / (total_passed + total_failed):.1f}%)")
    print()

    if total_failed == 0:
        print("✓ All tests passed!")
        print("=" * 80)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
