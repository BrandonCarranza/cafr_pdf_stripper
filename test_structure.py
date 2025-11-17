#!/usr/bin/env python3
"""
Basic structure test for IBCo PDF Stripper.
Tests imports and basic functionality without requiring full dependencies.
"""

import sys
from pathlib import Path

# Mock the external dependencies for structure testing
class MockModule:
    def __getattr__(self, name):
        return MockModule()
    def __call__(self, *args, **kwargs):
        return MockModule()

# Mock imports
sys.modules['pdfplumber'] = MockModule()
sys.modules['pytesseract'] = MockModule()
sys.modules['pdf2image'] = MockModule()
sys.modules['tqdm'] = MockModule()

# Now we can import our modules
import config
from ibco_stripper import TOCEntry, PageMetadata

def test_configuration():
    """Test configuration module."""
    print("Testing configuration...")

    # Test config accessors
    assert isinstance(config.SYSTEM, dict)
    assert isinstance(config.PDF_PROCESSING, dict)
    assert config.SYSTEM['cpu_cores'] == 32
    print("  ✓ Configuration loaded successfully")

    # Test helper functions
    assert config.roman_to_int('iv') == 4
    assert config.roman_to_int('xii') == 12
    assert config.is_roman_numeral('iii') == True
    assert config.is_roman_numeral('abc') == False
    print("  ✓ Roman numeral conversion works")

    # Test get_config
    system_config = config.get_config('system')
    assert system_config == config.SYSTEM
    print("  ✓ Config accessor works")

def test_data_structures():
    """Test data structures."""
    print("\nTesting data structures...")

    # Test TOCEntry
    toc = TOCEntry(
        section_name="Financial Section",
        page_number=25,
        level=1
    )
    assert toc.section_name == "Financial Section"
    assert toc.page_number == 25
    print("  ✓ TOCEntry dataclass works")

    # Test PageMetadata
    page = PageMetadata(
        pdf_page_num=1,
        footer_page_num="i",
        section_name="Introductory Section",
        section_level=1,
        header_text="CITY OF VALLEJO"
    )
    assert page.pdf_page_num == 1
    assert page.footer_page_num == "i"
    print("  ✓ PageMetadata dataclass works")

def test_project_structure():
    """Test project file structure."""
    print("\nTesting project structure...")

    required_files = [
        'ibco_stripper.py',
        'config.py',
        'requirements.txt',
        'README.md',
        'CLAUDE_CODE_PROMPTS.md',
    ]

    for file in required_files:
        path = Path(file)
        assert path.exists(), f"Missing: {file}"
        print(f"  ✓ {file} exists")

def main():
    """Run all tests."""
    print("=" * 60)
    print("IBCo PDF Stripper - Structure Test")
    print("=" * 60)

    try:
        test_configuration()
        test_data_structures()
        test_project_structure()

        print("\n" + "=" * 60)
        print("✓ All structure tests passed!")
        print("=" * 60)
        print("\nProject structure is ready for PROMPT 1B")
        print("Next: Implement PDF reading and page number extraction")

        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
