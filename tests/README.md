# IBCo PDF Stripper - Test Suite

Comprehensive test suite for the CAFR PDF Stripper.

## Running Tests

### Run All Tests
```bash
python tests/run_all_tests.py
```

### Run with pytest (if available)
```bash
pytest tests/test_ibco_stripper.py -v
```

## Test Coverage

This comprehensive test suite covers the following functionality:

### 1. Footer Extraction (`TestFooterExtraction`)
- Roman numeral conversion (i, ii, iii → 1, 2, 3)
- For detailed tests: `test_pdf_reading.py`, `test_page_extraction.py`

### 2. TOC Parsing (`TestTOCParsing`)
- Loading TOC from screenshots
- Basic TOC structure validation
- For detailed tests: `test_toc_loading.py`, `test_toc_refinement.py`, `test_multiple_tocs.py`

### 3. Section Mapping (`TestSectionMapping`)
- Page index building
- Section assignment to pages
- For detailed tests: `test_section_mapper.py`, `test_page_index.py`

### 4. PNG Conversion (`TestPNGConversion`)
- Basic PNG generation
- Different DPI settings (150, 300 DPI)
- For detailed tests: `test_png_conversion.py`, `test_selective_export.py`

### 5. Metadata Export (`TestMetadataExport`)
- JSON export functionality
- JSON structure validation
- Metadata content verification
- For detailed tests: `test_metadata_export.py`, `test_report_generation.py`

## Complete Test Suite

The project includes 15+ comprehensive test files:

**Phase 1 - PDF Reading:**
- `test_structure.py` (PROMPT 1A)
- `test_pdf_reading.py` (PROMPT 1B)
- `test_page_extraction.py` (PROMPT 1C)

**Phase 2 - TOC Processing:**
- `test_toc_loading.py` (PROMPT 2A)
- `test_toc_refinement.py` (PROMPT 2B)
- `test_multiple_tocs.py` (PROMPT 2C)

**Phase 3 - Page Indexing:**
- `test_section_mapper.py` (PROMPT 3A)
- `test_page_index.py` (PROMPT 3B)

**Phase 4 - PNG Conversion:**
- `test_png_conversion.py` (PROMPT 4A)
- `test_selective_export.py` (PROMPT 4B)

**Phase 5 - Metadata & Reports:**
- `test_metadata_export.py` (PROMPT 5A)
- `test_report_generation.py` (PROMPT 5B)

**Phase 6 - Workflows:**
- `test_workflow.py` (PROMPT 6A)
- `test_batch_processing.py` (PROMPT 6B)
- `test_verification.py` (PROMPT 6C)

## Test Results

All 9 tests in the comprehensive suite pass:
- ✓ Footer Extraction (1 test)
- ✓ TOC Parsing (1 test)
- ✓ Section Mapping (2 tests)
- ✓ PNG Conversion (2 tests)
- ✓ Metadata Export (3 tests)

**Success Rate: 100%**

## Adding New Tests

To add new tests to the comprehensive suite:

1. Create a new test class in `tests/test_ibco_stripper.py`
2. Add test methods prefixed with `test_`
3. Update `tests/run_all_tests.py` to include the new class
4. Run the test suite to verify

Example:
```python
class TestNewFeature:
    """Test suite for new feature."""

    def test_basic_functionality(self):
        """Test basic functionality."""
        assert True  # Replace with actual test
```

## Dependencies

Tests use mocking to avoid requiring:
- pdfplumber
- pytesseract
- pdf2image
- PIL/Pillow
- tqdm

All tests run using only Python standard library plus the project code.
