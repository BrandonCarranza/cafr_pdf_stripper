# Claude Code Prompt Sequence - IBCo PDF Stripper

**Build Target:** CAFR PDF Stripper with Manual TOC Screenshot Loading  
**System:** AMD Threadripper 3970X, Ubuntu 24.04, 256GB RAM, 12TB NVMe  
**Scale:** Single city, ~15 CAFRs per city, ~300 pages each  
**Workflow:** Manual TOC screenshots → Load into tool → Auto-process PDF

---

## 📋 Build Strategy

**Iterative Development in 6 Phases:**
1. Core PDF reader with page number extraction
2. TOC screenshot loader (OCR integration)
3. Page-to-section mapper
4. PNG page saver
5. Metadata generator
6. Single-city batch processor

**Total Estimated Prompts:** 12-15  
**Estimated Build Time:** 2-3 hours with Claude Code

---

## 🎯 PROMPT SEQUENCE

### PHASE 1: Foundation - PDF Reader & Page Numbers

#### PROMPT 1A: Project Setup
```
Create a Python project called "ibco_pdf_stripper" for processing municipal CAFR 
(Comprehensive Annual Financial Report) PDFs. 

Requirements:
- Python 3.12+
- Use pdfplumber for PDF processing
- Target system: AMD Threadripper 3970X with 256GB RAM
- Working directory: ~/workspace/ibco/

Project structure:
ibco_pdf_stripper/
├── ibco_stripper.py       # Main module
├── requirements.txt       # Dependencies
├── config.py             # Configuration
└── README.md             # Documentation

Dependencies needed:
- pdfplumber (PDF text extraction)
- pytesseract (OCR for TOC screenshots)
- Pillow (Image handling)
- pdf2image (PDF to PNG conversion)

Create the basic project structure with a stub main file and requirements.txt.
```

#### PROMPT 1B: Core PDF Reader
```
Build the core PDF reading functionality in ibco_stripper.py.

Create a class called PDFStripper with these methods:

1. __init__(pdf_path, output_dir)
   - Takes path to CAFR PDF file
   - Sets up output directory structure

2. read_footer_page_number(page) 
   - Extracts page number from bottom 10% of page
   - Returns integer page number or None
   - CAFR page numbers are typically centered in footer
   - Handle Roman numerals (i, ii, iii) and Arabic (1, 2, 3)

3. read_header_text(page)
   - Extracts text from top 10% of page
   - Returns header string
   - Headers usually contain section names or city name

4. get_page_count()
   - Returns total pages in PDF

Test with a sample PDF to verify page numbers are being read correctly.
Include detailed docstrings for each method.
```

#### PROMPT 1C: Page Number Extraction Testing
```
Create a test script that:

1. Opens a sample CAFR PDF
2. Iterates through all pages
3. For each page, extracts:
   - Sequential page number (PDF order)
   - Footer page number (document pagination)
   - Header text
4. Prints a summary showing any missing page numbers
5. Identifies pages where footer numbering changes format (Roman → Arabic)

Output format:
Page 5 (PDF) → Page "iii" (Footer) | Header: "Introductory Section"
Page 10 (PDF) → Page "1" (Footer) | Header: "Financial Section"

This will help verify our extraction is working before adding TOC functionality.
```

---

### PHASE 2: TOC Screenshot Processing

#### PROMPT 2A: TOC Screenshot Loader
```
Add TOC screenshot processing capability to PDFStripper class.

Create a new method: load_toc_from_screenshot(image_path)

This method should:
1. Load the TOC screenshot image using Pillow
2. Use pytesseract to OCR the image
3. Parse the OCR text to extract TOC entries

TOC format recognition:
- Look for patterns like:
  "Section Name .................. 15"
  "Section Name    15"
  "Management's Discussion and Analysis ... Page 25"

Return a list of TOCEntry objects with:
- section_name (string)
- page_number (integer)
- level (1=main section, 2=subsection, based on indentation)

Create a simple TOCEntry dataclass to hold this data.

Include error handling for poor OCR quality and suggest user verification.
```

#### PROMPT 2B: TOC Parser Refinement
```
Improve the TOC parsing logic to handle real-world CAFR formats.

Common CAFR TOC patterns:
1. Numbered sections: "1. Introductory Section .......... 1"
2. Lettered sections: "A. Letter of Transmittal ......... 3"
3. Unnumbered sections: "Financial Section ................ 25"
4. Indented subsections (use spaces to determine level)
5. Page references with "Page": "Basic Financial Statements ..... Page 35"

Update parse_toc_text(ocr_text) to:
- Handle all these patterns with regex
- Determine hierarchy level from indentation (count leading spaces)
- Remove page dots/leaders
- Handle both Roman and Arabic numerals in page references
- Return structured TOCEntry list sorted by page number

Test with sample TOC text strings to verify parsing accuracy.
```

#### PROMPT 2C: Multiple TOC Screenshot Support
```
Extend load_toc_from_screenshot to handle multiple screenshot files.

Some CAFRs have multi-page TOCs. Create:

load_toc_from_screenshots(image_paths_list)
- Takes a list of image file paths
- Processes each screenshot in order
- Combines all TOC entries into single list
- Removes duplicates
- Sorts by page number
- Returns complete TOC structure

Add a method: verify_toc_completeness()
- Checks for gaps in page number sequence
- Warns if major sections are missing
- Suggests review if fewer than 3 main sections found

Include a print_toc() method for user review before processing.
```

---

### PHASE 3: Page-to-Section Mapping

#### PROMPT 3A: Section Mapper
```
Create the logic to map each PDF page to its TOC section.

Add method: map_page_to_section(page_number, toc_entries)

Logic:
1. Find the section where this page belongs
2. A page belongs to a section if:
   - Page number >= section start page
   - AND page number < next section start page
   - OR page number >= section start and no next section (last section)

3. Handle hierarchical sections:
   - If page is in a subsection, return the subsection name
   - Store parent section reference for context

Return: 
- section_name (string)
- section_level (integer)
- parent_section_name (string, or None)

Create a PageMetadata dataclass to store:
- pdf_page_num (sequential)
- footer_page_num (from document)
- section_name
- section_level
- header_text
- footer_text
```

#### PROMPT 3B: Build Complete Page Index
```
Add method: build_page_index(toc_entries)

This method should:
1. Iterate through all pages in PDF
2. For each page:
   - Extract page number from footer
   - Extract header text
   - Map to TOC section using previous logic
   - Create PageMetadata object
3. Return list of PageMetadata for all pages

Include progress indicator:
"Processing page 45/300..."

Handle edge cases:
- Pages before first section (cover, blank pages)
- Pages without detectable page numbers
- Pages between sections

Store the page index internally for later use.
```

---

### PHASE 4: PNG Page Extraction

#### PROMPT 4A: Page to PNG Converter
```
Add PNG export functionality using pdf2image.

Create method: save_page_as_png(page_number, output_path, dpi=300)

Implementation:
1. Use pdf2image.convert_from_path() to convert single page
2. Save as PNG with specified DPI (default 300 for quality)
3. Use meaningful filename: "page_{page_num:04d}_{section_slug}.png"
4. Return saved file path

Add method: save_all_pages_as_png(dpi=300)
1. Create subdirectory structure by section:
   output/
   ├── 01_introductory_section/
   │   ├── page_0001_introductory.png
   │   └── ...
   ├── 02_financial_section/
   │   └── ...
2. Save each page to appropriate section folder
3. Show progress bar or percentage
4. Return list of saved file paths

Optimize for Threadripper:
- Use multiprocessing to convert 8-16 pages in parallel
- Each process handles one page conversion
```

#### PROMPT 4B: Selective Page Export
```
Add method: save_section_as_png(section_name, dpi=300)

Allows exporting just one section's pages to PNG.

Steps:
1. Filter page index for pages in specified section
2. Create section-specific output directory
3. Convert only those pages to PNG
4. Use descriptive filenames

Also add: save_page_range_as_png(start_page, end_page, dpi=300)

Useful for:
- Testing with small subset
- Re-exporting specific sections
- Handling failed conversions

Include option to skip pages that already exist (resume capability).
```

---

### PHASE 5: Metadata & Reporting

#### PROMPT 5A: JSON Metadata Exporter
```
Create comprehensive metadata export functionality.

Add method: export_metadata(output_file="cafr_metadata.json")

JSON structure:
{
  "source_pdf": "filepath",
  "total_pages": 300,
  "processed_date": "2025-11-16",
  "toc_entries": [
    {
      "section_name": "Financial Section",
      "page_number": 25,
      "level": 1,
      "parent": null
    }
  ],
  "pages": [
    {
      "pdf_page": 1,
      "footer_page": "i",
      "section": "Introductory Section",
      "section_level": 1,
      "header_text": "CITY OF VALLEJO",
      "png_file": "01_introductory/page_0001.png"
    }
  ],
  "statistics": {
    "sections_count": 3,
    "pages_with_numbers": 295,
    "pages_without_numbers": 5,
    "png_files_created": 300
  }
}

Include comprehensive error checking and validation.
```

#### PROMPT 5B: Human-Readable Report
```
Create method: generate_report(output_file="cafr_report.txt")

Generate a formatted text report:

=====================================
CAFR PROCESSING REPORT
=====================================

PDF: vallejo_cafr_2024.pdf
Total Pages: 300
Processed: 2025-11-16 14:30:00

TABLE OF CONTENTS
-------------------------------------
Introductory Section .............. 1
  Letter of Transmittal ........... 3
  Organization Chart .............. 15
Financial Section ................. 25
  MD&A .............................. 30
  Basic Financial Statements ...... 45
Statistical Section ............... 200

PAGE MAPPING SUMMARY
-------------------------------------
Section: Introductory Section
  Pages: 1-24 (24 pages)
  PNG Files: 24 created
  Status: ✓ Complete

Section: Financial Section
  Pages: 25-199 (175 pages)
  PNG Files: 175 created
  Status: ✓ Complete

ISSUES/WARNINGS
-------------------------------------
- Pages 5-7: No page numbers detected
- Page 156: Header text truncated

OUTPUT FILES
-------------------------------------
Metadata: output/cafr_metadata.json
Report: output/cafr_report.txt
PNG Files: output/sections/

Include summary statistics and any warnings/errors encountered.
```

---

### PHASE 6: Single-City Workflow

#### PROMPT 6A: Single CAFR Processor
```
Create the main processing workflow for a single CAFR.

Add method: process_cafr(pdf_path, toc_screenshots, output_dir)

Complete workflow:
1. Load PDF
2. Load TOC from screenshot(s)
3. Display TOC for user verification
4. Ask for confirmation to proceed
5. Build page index
6. Save all pages as PNG (with progress)
7. Export metadata JSON
8. Generate human-readable report
9. Print summary statistics

Include command-line interface:
python ibco_stripper.py \
  --pdf vallejo_cafr_2024.pdf \
  --toc toc_page1.png toc_page2.png \
  --output vallejo_output/ \
  --dpi 300

Add optional flags:
  --skip-png (only generate metadata)
  --section "Financial Section" (process only one section)
  --verify-only (show TOC, don't process)
```

#### PROMPT 6B: Multi-CAFR City Processor
```
Create a batch processor for one city's historical CAFRs.

Add script: process_city.py

Takes a configuration file:
city_config.yaml:
  city_name: "Vallejo"
  state: "CA"
  output_base: "/data/cafr/vallejo/"
  
  cafrs:
    - year: 2024
      pdf: "pdfs/vallejo_2024.pdf"
      toc_screenshots: ["toc/2024_toc.png"]
    
    - year: 2023
      pdf: "pdfs/vallejo_2023.pdf"
      toc_screenshots: ["toc/2023_toc.png"]
    
    # ... (up to 15 years)

Processing:
1. Load configuration
2. For each CAFR:
   - Process as standalone
   - Create year-specific output directory
   - Generate year-specific metadata
3. Create master index of all years
4. Generate comparative report across years

Progress tracking:
"Processing Vallejo CAFR 2024 (3/15)..."

Run sequentially (not parallel) since:
- Only one city at a time
- User can monitor each CAFR individually
- Easier debugging if issues arise
```

#### PROMPT 6C: Verification & Quality Check
```
Add post-processing verification functionality.

Create method: verify_processing(output_dir)

Checks:
1. PNG file count matches page count
2. All sections have at least one page
3. No gaps in page sequences
4. File sizes reasonable (detect corrupted images)
5. Metadata JSON is valid
6. All TOC sections were found in PDF

Generate verification report:
VERIFICATION REPORT
===================
✓ 300 pages processed
✓ 300 PNG files created
✓ All sections found
✓ No missing pages
⚠ 3 pages without page numbers (pages 5-7)
✓ Metadata JSON valid
✓ Total size: 850 MB

Create method: fix_issues()
- Attempt to re-process failed pages
- Re-OCR TOC if sections missing
- Suggest manual intervention if needed
```

---

### PHASE 7: Testing & Refinement

#### PROMPT 7A: Create Test Suite
```
Create comprehensive tests for the IBCo PDF Stripper.

Create tests/test_ibco_stripper.py:

Test cases:
1. test_footer_extraction()
   - Test with sample PDF pages
   - Verify Roman numeral conversion
   - Test Arabic numerals
   - Test missing page numbers

2. test_toc_parsing()
   - Test various TOC formats
   - Test multi-level hierarchies
   - Test edge cases (missing dots, weird spacing)

3. test_section_mapping()
   - Verify pages map to correct sections
   - Test boundary pages (last page of section)
   - Test pages before first section

4. test_png_conversion()
   - Convert sample page
   - Verify file exists and has content
   - Test different DPI settings

5. test_metadata_export()
   - Generate metadata
   - Validate JSON structure
   - Verify all required fields present

Use pytest framework. Include sample test data files.
```

#### PROMPT 7B: Performance Optimization
```
Optimize for Threadripper 3970X performance.

Current bottlenecks to address:
1. PNG conversion (CPU intensive)
2. OCR processing (if TOC quality poor)
3. Large PDF loading (memory)

Optimizations:

1. Parallel PNG Conversion:
   - Use multiprocessing.Pool
   - Convert 8-16 pages simultaneously
   - Monitor memory usage (each process ~2GB)
   - Target: 4 cores per page = 16 pages parallel

2. Smart Caching:
   - Cache page images in memory (we have 256GB)
   - Cache TOC structure
   - Cache page index after first build

3. Progress Optimization:
   - Use tqdm for progress bars
   - Show estimated time remaining
   - Display throughput (pages/minute)

Test with full 300-page CAFR:
- Target: <5 minutes for full processing
- Target: <30 seconds for metadata-only
- Target: <2 minutes for single section

Benchmark and report actual times.
```

---

## 🎯 USAGE PROMPTS (After Build)

### PROMPT 8: First-Time Setup
```
Create a setup script (setup.sh) that:

1. Checks system requirements:
   - Python 3.12+
   - poppler-utils (for pdf2image)
   - tesseract-ocr
   - Available RAM (recommend 8GB minimum)

2. Creates virtual environment
3. Installs dependencies from requirements.txt
4. Creates default directory structure:
   ~/workspace/ibco/
   ├── pdfs/          (input PDFs)
   ├── toc_screenshots/ (TOC images)
   ├── output/        (processed results)
   └── config/        (YAML configs)

5. Runs verification test with sample data
6. Prints usage instructions

Make it idempotent (safe to run multiple times).
```

### PROMPT 9: Documentation
```
Create comprehensive README.md with:

1. Overview & Purpose
   - What it does
   - Who it's for (IBCo municipal fiscal transparency)
   - Typical use case

2. Installation
   - System requirements
   - Setup instructions
   - Verification steps

3. Quick Start Guide
   - Step 1: Take TOC screenshots
   - Step 2: Run processor
   - Step 3: Review output
   - Example commands

4. Detailed Usage
   - Command-line options
   - Configuration file format
   - Output structure explanation

5. Troubleshooting
   - Common issues
   - OCR quality tips
   - Performance tuning

6. Examples
   - Single CAFR processing
   - Multi-year city processing
   - Selective section extraction

Keep it concise but complete. Include actual command examples.
```

---

## 📊 PROMPT EXECUTION STRATEGY

### For Claude Code Terminal:

**Session 1: Foundation (Prompts 1A-1C)**
```bash
claude code session start ibco-foundation
# Execute prompts 1A, 1B, 1C
# Test with sample PDF
claude code session save
```

**Session 2: TOC Processing (Prompts 2A-2C)**
```bash
claude code session start ibco-toc
# Execute prompts 2A, 2B, 2C  
# Test with TOC screenshot
claude code session save
```

**Session 3: Mapping & Export (Prompts 3A-4B)**
```bash
claude code session start ibco-export
# Execute prompts 3A, 3B, 4A, 4B
# Test full pipeline
claude code session save
```

**Session 4: Finalization (Prompts 5A-7B)**
```bash
claude code session start ibco-final
# Execute remaining prompts
# Full integration test
claude code session save
```

### For Claude Code Web:

1. **Copy prompt to chat**
2. **Claude Code builds the component**
3. **Review and test**
4. **Iterate if needed**
5. **Move to next prompt**

Save each component as you go. Build incrementally.

---

## 🔧 CUSTOMIZATION PROMPTS

### If OCR Quality is Poor:
```
Add interactive TOC entry mode:

When OCR confidence is low, prompt user:
"OCR detected these TOC entries. Please verify or edit:

1. Introductory Section .... 1
2. Finantial Section ....... 25  (Did you mean 'Financial'?)
3. [Unable to read] ........ 50

Enter 'y' to accept, 'e' to edit, 'r' to re-OCR"

Allow inline editing of section names and page numbers.
Save corrected TOC for future reference.
```

### If PDF Has Unusual Format:
```
Add custom parsing rules configuration:

Create parsing_rules.yaml:
  footer_region: 
    top: 0.90
    bottom: 1.0
  
  header_region:
    top: 0.0
    bottom: 0.10
  
  page_number_patterns:
    - regex: "Page (\d+)"
    - regex: "(\d+)"
    - regex: "([ivxlcdm]+)"  # Roman numerals

Allow user to adjust regions and patterns without code changes.
```

---

## ✅ SUCCESS CRITERIA

After completing all prompts, you should have:

- [ ] Single CAFR processes in <5 minutes
- [ ] 300 PNG files created with proper naming
- [ ] JSON metadata with complete page index
- [ ] Human-readable report generated
- [ ] TOC screenshot loading works reliably
- [ ] Page numbers extracted correctly (95%+ accuracy)
- [ ] Sections mapped correctly
- [ ] Multi-CAFR batch processing works
- [ ] All outputs in organized directory structure
- [ ] Documentation complete

---

## 🚀 QUICK START EXAMPLE

Once built, your workflow will be:

```bash
# Step 1: Take TOC screenshots
# Open PDF, screenshot pages with table of contents
# Save as toc_page1.png, toc_page2.png

# Step 2: Process CAFR
python ibco_stripper.py \
  --pdf vallejo_2024.pdf \
  --toc toc_page1.png toc_page2.png \
  --output vallejo_2024_output \
  --dpi 300

# Step 3: Review output
cat vallejo_2024_output/cafr_report.txt
ls vallejo_2024_output/sections/

# Processing time: ~3-5 minutes for 300 pages
```

---

## 📝 NOTES FOR CLAUDE CODE

**When executing these prompts:**

1. **Be Specific About Context**: Mention this is for municipal CAFR processing
2. **Request Testing**: Ask Claude Code to test each component
3. **Iterate**: If something doesn't work, provide feedback and ask for revision
4. **Save Incrementally**: Don't try to build everything at once
5. **Use Real Data**: Test with actual CAFR screenshots when possible

**Sample Iteration Pattern:**
```
"That worked well, but the page number extraction is missing numbers 
in the footer. Can you adjust the footer region from bottom 10% to 
bottom 15% and re-test?"
```

**Troubleshooting Tip:**
If Claude Code output isn't quite right, try:
```
"The previous implementation had [specific issue]. Can you refactor 
the [method name] to handle [specific case]? Here's an example of 
the actual data format: [paste example]"
```

---

## 🎯 FINAL PROMPT (After All Built)

```
Now that the IBCo PDF Stripper is complete, create a demonstration:

1. Process a sample CAFR (or use test data)
2. Generate all outputs
3. Create a visual guide showing:
   - Input: PDF + TOC screenshots
   - Process: Steps and progress
   - Output: PNG files, metadata, report
4. Document the complete workflow
5. List any limitations or known issues
6. Suggest future enhancements

Create a DEMO.md file with screenshots (if possible) or 
detailed descriptions of what the user will see at each step.
```

---

**Total Prompt Count:** 16 prompts  
**Estimated Build Time:** 2-3 hours  
**Result:** Production-ready CAFR PDF stripper for single-city processing

**Ready to start? Begin with PROMPT 1A!**
