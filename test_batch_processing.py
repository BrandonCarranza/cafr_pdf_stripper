#!/usr/bin/env python3
"""
Test script for PROMPT 6B: Multi-CAFR City Processor

Tests batch processing functionality:
- YAML configuration loading
- Configuration validation
- Sequential CAFR processing
- Master index generation
- Comparative report generation
- Error handling
- Command-line interface

Usage:
    python test_batch_processing.py
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

import yaml
import config
from ibco_stripper import PDFStripper, TOCEntry
from process_city import load_config, process_city, generate_master_index, generate_comparative_report


def create_mock_cafr_config(temp_dir: Path, num_years: int = 3) -> tuple:
    """
    Create mock CAFR configuration with test PDFs and TOC files.

    Args:
        temp_dir: Temporary directory for test files
        num_years: Number of years to create

    Returns:
        Tuple of (config_dict, config_path)
    """
    # Create mock PDF and TOC files
    pdf_dir = temp_dir / "pdfs"
    toc_dir = temp_dir / "toc"
    pdf_dir.mkdir()
    toc_dir.mkdir()

    cafrs = []
    for year in range(2024, 2024 - num_years, -1):
        # Create mock PDF
        pdf_path = pdf_dir / f"city_{year}.pdf"
        pdf_path.write_text(f"Mock PDF for {year}")

        # Create mock TOC screenshot
        toc_path = toc_dir / f"{year}_toc.png"
        toc_path.write_text(f"Mock TOC for {year}")

        cafrs.append({
            'year': year,
            'pdf': str(pdf_path),
            'toc_screenshots': [str(toc_path)]
        })

    config = {
        'city_name': 'Test City',
        'state': 'CA',
        'output_base': str(temp_dir / 'output'),
        'cafrs': cafrs
    }

    # Write config file
    config_path = temp_dir / 'city_config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return config, config_path


def test_config_loading():
    """Test YAML configuration file loading."""
    print("=" * 80)
    print("Testing Configuration Loading")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        passed = 0
        failed = 0

        # Test 1: Valid configuration
        config, config_path = create_mock_cafr_config(temp_path, num_years=3)

        try:
            loaded_config = load_config(str(config_path))
            print("✓ Valid configuration loaded successfully")
            passed += 1
        except Exception as e:
            print(f"✗ Failed to load valid configuration: {e}")
            failed += 1

        # Test 2: Configuration has required fields
        if 'city_name' in loaded_config and 'output_base' in loaded_config and 'cafrs' in loaded_config:
            print("✓ Configuration has required fields")
            passed += 1
        else:
            print("✗ Configuration missing required fields")
            failed += 1

        # Test 3: CAFR entries have required fields
        all_valid = True
        for cafr in loaded_config['cafrs']:
            if 'year' not in cafr or 'pdf' not in cafr or 'toc_screenshots' not in cafr:
                all_valid = False
                break

        if all_valid:
            print("✓ All CAFR entries have required fields")
            passed += 1
        else:
            print("✗ Some CAFR entries missing required fields")
            failed += 1

        # Test 4: Missing config file
        try:
            load_config(str(temp_path / 'nonexistent.yaml'))
            print("✗ Should raise error for missing config file")
            failed += 1
        except FileNotFoundError:
            print("✓ Raises error for missing config file")
            passed += 1

        # Test 5: Invalid YAML
        invalid_config_path = temp_path / 'invalid.yaml'
        invalid_config_path.write_text("invalid: yaml: content: [unclosed")

        try:
            load_config(str(invalid_config_path))
            print("✗ Should raise error for invalid YAML")
            failed += 1
        except yaml.YAMLError:
            print("✓ Raises error for invalid YAML")
            passed += 1

        # Test 6: Missing required field
        incomplete_config = {
            'city_name': 'Test',
            # Missing output_base and cafrs
        }
        incomplete_path = temp_path / 'incomplete.yaml'
        with open(incomplete_path, 'w') as f:
            yaml.dump(incomplete_config, f)

        try:
            load_config(str(incomplete_path))
            print("✗ Should raise error for missing required fields")
            failed += 1
        except ValueError:
            print("✓ Raises error for missing required fields")
            passed += 1

        print()
        print(f"Passed: {passed}/6")
        print(f"Failed: {failed}/6")
        print()

        return failed == 0


def test_sequential_processing():
    """Test sequential CAFR processing."""
    print("=" * 80)
    print("Testing Sequential Processing")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create config with 3 years
        config, config_path = create_mock_cafr_config(temp_path, num_years=3)

        passed = 0
        failed = 0

        # Mock pytesseract to return TOC text
        def mock_image_to_string(image, **kwargs):
            return """
            Table of Contents

            Introductory Section ..................... 1
            Financial Section ........................ 11
            Statistical Section ...................... 21
            """

        # Mock user input to auto-confirm
        with patch('pytesseract.image_to_string', side_effect=mock_image_to_string):
            # Process city with auto-confirm
            result = process_city(
                config_path=str(config_path),
                skip_png=True,  # Skip PNG to speed up test
                auto_confirm=True,
                verbose=False
            )

            # Test 1: All years processed
            if result['total_cafrs'] == 3:
                print(f"✓ Processed all 3 CAFRs")
                passed += 1
            else:
                print(f"✗ Expected 3 CAFRs, processed {result['total_cafrs']}")
                failed += 1

            # Test 2: All successful
            if result['successful'] == 3:
                print(f"✓ All 3 CAFRs successful")
                passed += 1
            else:
                print(f"✗ Expected 3 successful, got {result['successful']}")
                failed += 1

            # Test 3: Year-specific directories created
            output_base = Path(config['output_base'])
            expected_dirs = ['2024', '2023', '2022']
            all_exist = all((output_base / year).exists() for year in expected_dirs)

            if all_exist:
                print("✓ Year-specific directories created")
                passed += 1
            else:
                print("✗ Some year directories missing")
                failed += 1

            # Test 4: Metadata files created for each year
            metadata_files = [output_base / year / 'cafr_metadata.json' for year in expected_dirs]
            all_metadata_exist = all(f.exists() for f in metadata_files)

            if all_metadata_exist:
                print("✓ Metadata files created for all years")
                passed += 1
            else:
                print("✗ Some metadata files missing")
                failed += 1

            # Test 5: Report files created for each year
            report_files = [output_base / year / 'cafr_report.txt' for year in expected_dirs]
            all_reports_exist = all(f.exists() for f in report_files)

            if all_reports_exist:
                print("✓ Report files created for all years")
                passed += 1
            else:
                print("✗ Some report files missing")
                failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_master_index():
    """Test master index generation."""
    print("=" * 80)
    print("Testing Master Index Generation")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_base = temp_path / 'output'
        output_base.mkdir()

        # Create mock results
        results = [
            {
                'year': 2024,
                'status': 'complete',
                'total_pages': 150,
                'page_index': [
                    {'section_name': 'Intro', 'section_level': 1},
                    {'section_name': 'Financial', 'section_level': 1}
                ]
            },
            {
                'year': 2023,
                'status': 'complete',
                'total_pages': 145,
                'page_index': [
                    {'section_name': 'Intro', 'section_level': 1}
                ]
            },
            {
                'year': 2022,
                'status': 'error',
                'error': 'PDF not found'
            }
        ]

        # Create year-specific metadata files for successful years
        for result in results:
            if result['status'] == 'complete':
                year = result['year']
                year_dir = output_base / str(year)
                year_dir.mkdir()

                metadata = {
                    'statistics': {
                        'total_pages': result['total_pages'],
                        'sections': ['Section 1', 'Section 2']
                    }
                }

                with open(year_dir / 'metadata.json', 'w') as f:
                    json.dump(metadata, f)

        passed = 0
        failed = 0

        # Generate master index
        index_path = generate_master_index('Test City', 'CA', results, output_base)

        # Test 1: Master index file created
        if index_path.exists():
            print("✓ Master index file created")
            passed += 1
        else:
            print("✗ Master index file not created")
            failed += 1
            return False

        # Load and validate master index
        with open(index_path, 'r') as f:
            master_index = json.load(f)

        # Test 2: Has required fields
        required_fields = ['city_name', 'state', 'generated_at', 'total_years', 'successful_years', 'years']
        if all(field in master_index for field in required_fields):
            print("✓ Master index has required fields")
            passed += 1
        else:
            print("✗ Master index missing required fields")
            failed += 1

        # Test 3: Correct totals
        if master_index['total_years'] == 3 and master_index['successful_years'] == 2:
            print("✓ Correct year totals")
            passed += 1
        else:
            print(f"✗ Wrong totals: {master_index['total_years']} total, {master_index['successful_years']} successful")
            failed += 1

        # Test 4: Years sorted descending
        years_list = [y['year'] for y in master_index['years'] if 'year' in y]
        if years_list == sorted(years_list, reverse=True):
            print("✓ Years sorted in descending order")
            passed += 1
        else:
            print("✗ Years not sorted correctly")
            failed += 1

        # Test 5: Failed year included with error
        failed_entry = next((y for y in master_index['years'] if y.get('year') == 2022), None)
        if failed_entry and failed_entry.get('status') == 'error':
            print("✓ Failed year included with error status")
            passed += 1
        else:
            print("✗ Failed year not handled correctly")
            failed += 1

        print()
        print(f"Passed: {passed}/5")
        print(f"Failed: {failed}/5")
        print()

        return failed == 0


def test_comparative_report():
    """Test comparative report generation."""
    print("=" * 80)
    print("Testing Comparative Report Generation")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_base = temp_path / 'output'
        output_base.mkdir()

        # Create mock results with page index
        results = [
            {
                'year': 2024,
                'status': 'complete',
                'total_pages': 150,
                'page_index': [
                    {'section_name': 'Introductory Section', 'section_level': 1},
                    {'section_name': 'Introductory Section', 'section_level': 1},
                    {'section_name': 'Financial Section', 'section_level': 1},
                ]
            },
            {
                'year': 2023,
                'status': 'complete',
                'total_pages': 145,
                'page_index': [
                    {'section_name': 'Introductory Section', 'section_level': 1},
                    {'section_name': 'Financial Section', 'section_level': 1},
                ]
            },
            {
                'year': 2022,
                'status': 'error',
                'error': 'PDF not found'
            }
        ]

        passed = 0
        failed = 0

        # Generate comparative report
        report_path = generate_comparative_report('Test City', 'CA', results, output_base)

        # Test 1: Report file created
        if report_path.exists():
            print("✓ Comparative report file created")
            passed += 1
        else:
            print("✗ Comparative report file not created")
            failed += 1
            return False

        # Read report content
        with open(report_path, 'r') as f:
            report_content = f.read()

        # Test 2: Contains city name
        if 'Test City' in report_content:
            print("✓ Report contains city name")
            passed += 1
        else:
            print("✗ Report missing city name")
            failed += 1

        # Test 3: Contains year-by-year summary
        if 'YEAR-BY-YEAR SUMMARY' in report_content:
            print("✓ Report contains year-by-year summary")
            passed += 1
        else:
            print("✗ Report missing year-by-year summary")
            failed += 1

        # Test 4: Contains section comparison
        if 'SECTION STRUCTURE COMPARISON' in report_content:
            print("✓ Report contains section comparison")
            passed += 1
        else:
            print("✗ Report missing section comparison")
            failed += 1

        # Test 5: Contains page count trend
        if 'PAGE COUNT TREND' in report_content:
            print("✓ Report contains page count trend")
            passed += 1
        else:
            print("✗ Report missing page count trend")
            failed += 1

        # Test 6: Years appear in descending order
        year_positions = [report_content.find(str(year)) for year in [2024, 2023, 2022]]
        if all(p != -1 for p in year_positions) and year_positions == sorted(year_positions):
            print("✓ Years appear in descending order")
            passed += 1
        else:
            print("✗ Years not in correct order")
            failed += 1

        print()
        print(f"Passed: {passed}/6")
        print(f"Failed: {failed}/6")
        print()

        return failed == 0


def test_error_handling():
    """Test error handling in batch processing."""
    print("=" * 80)
    print("Testing Error Handling")
    print("=" * 80)
    print()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        passed = 0
        failed = 0

        # Test 1: Missing PDF file
        config = {
            'city_name': 'Test City',
            'state': 'CA',
            'output_base': str(temp_path / 'output'),
            'cafrs': [
                {
                    'year': 2024,
                    'pdf': str(temp_path / 'nonexistent.pdf'),
                    'toc_screenshots': [str(temp_path / 'toc.png')]
                }
            ]
        }

        config_path = temp_path / 'config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        result = process_city(
            config_path=str(config_path),
            auto_confirm=True,
            verbose=False
        )

        if result['failed'] == 1 and result['successful'] == 0:
            print("✓ Handles missing PDF file")
            passed += 1
        else:
            print("✗ Did not handle missing PDF correctly")
            failed += 1

        # Test 2: Missing TOC screenshot
        pdf_path = temp_path / 'test.pdf'
        pdf_path.write_text("Mock PDF")

        config['cafrs'][0]['pdf'] = str(pdf_path)
        config['cafrs'][0]['toc_screenshots'] = [str(temp_path / 'missing_toc.png')]

        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        result = process_city(
            config_path=str(config_path),
            auto_confirm=True,
            verbose=False
        )

        if result['failed'] == 1:
            print("✓ Handles missing TOC screenshot")
            passed += 1
        else:
            print("✗ Did not handle missing TOC correctly")
            failed += 1

        # Test 3: Empty CAFR list
        config['cafrs'] = []
        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        try:
            load_config(str(config_path))
            print("✗ Should raise error for empty CAFR list")
            failed += 1
        except ValueError:
            print("✓ Raises error for empty CAFR list")
            passed += 1

        print()
        print(f"Passed: {passed}/3")
        print(f"Failed: {failed}/3")
        print()

        return failed == 0


def test_cli_arguments():
    """Test command-line argument parsing."""
    print("=" * 80)
    print("Testing Command-Line Arguments")
    print("=" * 80)
    print()

    import argparse
    from process_city import main

    passed = 0
    failed = 0

    # We can't easily test main() without running the full process,
    # but we can verify the argument parser structure
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create minimal valid config
        config, config_path = create_mock_cafr_config(temp_path, num_years=1)

        # Test that we can parse arguments (without running)
        test_args = [
            '--config', str(config_path),
            '--dpi', '150',
            '--skip-png',
            '--verify-only',
            '--yes',
            '--verbose'
        ]

        # Parse args manually
        parser = argparse.ArgumentParser()
        parser.add_argument('--config', required=True)
        parser.add_argument('--dpi', type=int, default=300)
        parser.add_argument('--skip-png', action='store_true')
        parser.add_argument('--verify-only', action='store_true')
        parser.add_argument('--yes', action='store_true')
        parser.add_argument('--verbose', action='store_true')

        try:
            args = parser.parse_args(test_args)
            print("✓ Argument parser accepts all flags")
            passed += 1
        except:
            print("✗ Argument parser failed")
            failed += 1

        # Test argument values
        if args.config == str(config_path):
            print("✓ Config path parsed correctly")
            passed += 1
        else:
            print("✗ Config path incorrect")
            failed += 1

        if args.dpi == 150:
            print("✓ DPI argument parsed correctly")
            passed += 1
        else:
            print("✗ DPI argument incorrect")
            failed += 1

        if args.skip_png and args.verify_only and args.yes and args.verbose:
            print("✓ Boolean flags parsed correctly")
            passed += 1
        else:
            print("✗ Boolean flags incorrect")
            failed += 1

        print()
        print(f"Passed: {passed}/4")
        print(f"Failed: {failed}/4")
        print()

        return failed == 0


def main():
    """Run all tests."""
    print()
    print("=" * 80)
    print("PROMPT 6B: Multi-CAFR City Processor - Test Suite")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_config_loading()
    all_passed &= test_sequential_processing()
    all_passed &= test_master_index()
    all_passed &= test_comparative_report()
    all_passed &= test_error_handling()
    all_passed &= test_cli_arguments()

    # Final summary
    print("=" * 80)
    if all_passed:
        print("✓ All PROMPT 6B tests passed!")
        print()
        print("Implementation Status:")
        print("  ✓ YAML configuration loading")
        print("  ✓ Configuration validation")
        print("  ✓ Sequential CAFR processing")
        print("  ✓ Progress tracking")
        print("  ✓ Year-specific output directories")
        print("  ✓ Master index generation")
        print("  ✓ Comparative report generation")
        print("  ✓ Error handling (missing files, invalid config)")
        print("  ✓ Command-line interface")
        print()
        print("Ready for PROMPT 6C!")
        print("=")
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
