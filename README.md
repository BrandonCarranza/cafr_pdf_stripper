# CAFR PDF Stripper

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-Unlicense-green.svg)
![IBCo](https://img.shields.io/badge/IBCo-Transparency-orange.svg)

**Municipal Financial Report Processing for IBCo Transparency Initiative**

Converts 300-page municipal CAFR (Comprehensive Annual Financial Report) PDFs into organized, high-quality PNG files with intelligent section mapping and complete metadata generation.

---

## Overview & Purpose

### What It Does

Transforms municipal CAFR PDFs into organized, analyzed datasets in 5 automated steps:

1. **Load TOC Screenshot** - You screenshot the table of contents (simple, accurate)
2. **Extract Page Numbers** - Reads page numbers from PDF footers (handles Roman & Arabic)
3. **Map Sections** - Associates each page with its TOC section
4. **Convert to PNG** - High-quality 300 DPI PNG files, organized by section
5. **Generate Metadata** - Complete JSON index of every page

**Processing Time:** ~5 minutes for a 300-page CAFR

### Who It's For

Built for the **IBCo (Independent Budget & Capital Operations)** network to enable:

- **Municipal Financial Transparency** - Make CAFR data accessible and analyzable
- **Forensic Analysis** - Examine historical financial trends across years
- **Cited Evidence** - Generate verifiable references for accountability research
- **Historical Tracking** - Process 15+ years of CAFRs per city

**IBCo Network:**
- [ibco-ca.us](https://ibco-ca.us) - California transparency hub
- [vallejo.ibco-ca.us](https://vallejo.ibco-ca.us) - Vallejo financial data
- [stockton.ibco-ca.us](https://stockton.ibco-ca.us) - Stockton financial data

### Typical Use Case

Process 15 years of Vallejo CAFRs (2010-2024):
- **Input:** 15 PDF files (~300 pages each)
- **Processing:** Screenshot TOC (2 min) + Run processor (5 min) per CAFR
- **Output:** ~4,500 pages organized by section, ready for analysis
- **Total Time:** One afternoon (~90 minutes)

---

## Installation

### System Requirements

**Required:**
- **Python 3.11+** (Python 3.12 recommended)
- **poppler-utils** - For PDF to image conversion
- **tesseract-ocr** - For OCR of TOC screenshots

**Recommended:**
- **8GB RAM minimum** (16GB+ for large PDFs)
- **10GB free disk space** (for output files)
- **Multi-core CPU** (for parallel PNG conversion)

### Automated Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/BrandonCarranza/cafr_pdf_stripper.git
cd cafr_pdf_stripper

# Run automated setup
./setup.sh
```

The setup script will:
- ✅ Check system requirements
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Set up workspace directories (`~/workspace/ibco/`)
- ✅ Run verification tests
- ✅ Display usage instructions

### Manual Installation

**1. Install System Dependencies:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv poppler-utils tesseract-ocr

# macOS (Homebrew)
brew install python@3.12 poppler tesseract

# Fedora/RHEL
sudo dnf install python3.12 python3-virtualenv poppler-utils tesseract
```

**2. Create Virtual Environment:**

```bash
python3.12 -m venv venv
source venv/bin/activate
```

**3. Install Python Dependencies:**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. Create Workspace Directory:**

```bash
mkdir -p ~/workspace/ibco/{pdfs,toc_screenshots,output,config}
```

### Verification

```bash
# Quick check
python -c "import ibco_stripper; print('✓ Installation successful')"

# Run comprehensive test suite
python tests/run_all_tests.py

# Or use Makefile shortcuts
make test-quick
make test
```

**Troubleshooting installation issues?** See [INSTALL.md](INSTALL.md) for detailed troubleshooting and platform-specific notes.

### Web Interface (Optional)

**NEW:** Browser-based interface for easier processing!

```bash
# Install web interface dependencies
pip install -r requirements_web.txt

# Launch web UI
streamlit run web_ui.py

# Open browser to http://localhost:8501
```

**Features:**
- 📤 Drag-and-drop file uploads
- 📊 Real-time progress tracking
- 📥 One-click download results
- 🔄 Batch processing with visual feedback

See [WEB_UI_README.md](WEB_UI_README.md) for complete web interface documentation.

---

## Quick Start Guide

**Choose your interface:**
- **Web UI:** Easy drag-and-drop (see [WEB_UI_README.md](WEB_UI_README.md))
- **CLI:** Command-line for automation (instructions below)

### Step 1: Take TOC Screenshots

**Why manual screenshots?**
- CAFRs vary wildly in format between cities
- You verify accuracy before processing begins
- Only takes 2 minutes per CAFR
- Works with any TOC layout

**How to do it:**

1. Open your CAFR PDF in a PDF viewer
2. Navigate to the Table of Contents page(s)
3. Take a screenshot (entire screen or selection):
   - **macOS:** `Cmd+Shift+4` (drag to select)
   - **Windows:** `Win+Shift+S`
   - **Linux:** `Shift+PrtScn` or screenshot tool
4. Save as PNG: `vallejo_2024_toc.png`
5. If TOC spans multiple pages, take multiple screenshots

**Tip:** Include the full page - headers, footers, and all TOC entries. The OCR works better with complete context.

### Step 2: Run the Processor

**Activate environment:**
```bash
source venv/bin/activate
# Or use convenience script:
source activate_cafr.sh
```

**Process your CAFR:**
```bash
python ibco_stripper.py \
  --pdf ~/workspace/ibco/pdfs/vallejo_cafr_2024.pdf \
  --toc ~/workspace/ibco/toc_screenshots/vallejo_2024_toc.png \
  --output ~/workspace/ibco/output/vallejo_2024/ \
  --dpi 300
```

**Watch the progress:**
```
[*] Loading PDF: vallejo_cafr_2024.pdf
[*] Total pages: 300
[*] Processing TOC screenshot...
[✓] Found 3 sections
[*] Building page index...
[✓] Mapped 300 pages to sections
[*] Converting to PNG (300 DPI, 16 workers)...
100%|██████████████████| 300/300 [04:32<00:00, 1.10 pages/s]
[✓] Generated 300 PNG files
[*] Writing metadata...
[✓] Processing complete!
```

### Step 3: Review the Output

**Check the summary report:**
```bash
cat ~/workspace/ibco/output/vallejo_2024/cafr_report.txt
```

**Output:**
```
CAFR Processing Report
======================
PDF: vallejo_cafr_2024.pdf
Date: 2025-11-17
Total Pages: 300

Sections Found: 3
  1. Introductory Section (pages 1-24)
  2. Financial Section (pages 25-199)
  3. Statistical Section (pages 200-300)

PNG Files: 300 (at 300 DPI)
Output Size: 850 MB
```

**Browse the sections:**
```bash
ls ~/workspace/ibco/output/vallejo_2024/sections/
```

**Output:**
```
01_introductory_section/
02_financial_section/
03_statistical_section/
```

**Check metadata:**
```bash
cat ~/workspace/ibco/output/vallejo_2024/cafr_metadata.json | head -20
```

---

## Detailed Usage

### Command-Line Options

```bash
python ibco_stripper.py [OPTIONS]
```

**Required Arguments:**

| Option | Description | Example |
|--------|-------------|---------|
| `--pdf PATH` | Input CAFR PDF file | `--pdf vallejo_2024.pdf` |
| `--toc PATH` | TOC screenshot PNG file | `--toc toc_2024.png` |
| `--output DIR` | Output directory | `--output vallejo_2024/` |

**Optional Arguments:**

| Option | Default | Description | Example |
|--------|---------|-------------|---------|
| `--dpi N` | `300` | PNG resolution (150-600) | `--dpi 600` |
| `--workers N` | `16` | Parallel conversion workers | `--workers 8` |
| `--section NAME` | All | Process single section only | `--section "Financial Section"` |
| `--skip-png` | False | Generate metadata only (no PNGs) | `--skip-png` |
| `--resume` | False | Skip already-converted pages | `--resume` |
| `--verbose` | False | Show detailed progress | `--verbose` |

**Examples:**

```bash
# High-quality processing (600 DPI)
python ibco_stripper.py --pdf city.pdf --toc toc.png --output out/ --dpi 600

# Low-memory mode (fewer workers, lower DPI)
python ibco_stripper.py --pdf city.pdf --toc toc.png --output out/ --dpi 150 --workers 4

# Metadata only (no PNG conversion)
python ibco_stripper.py --pdf city.pdf --toc toc.png --output out/ --skip-png

# Process only Financial Section
python ibco_stripper.py --pdf city.pdf --toc toc.png --output out/ --section "Financial Section"

# Resume interrupted processing
python ibco_stripper.py --pdf city.pdf --toc toc.png --output out/ --resume
```

### Configuration File Format

For batch processing multiple years, create a YAML config file:

**File: `~/workspace/ibco/config/vallejo.yaml`**

```yaml
# City Configuration
city_name: "Vallejo"
state: "CA"
output_base: "../output/vallejo"

# Processing options (optional)
dpi: 300
workers: 16

# List of CAFRs to process
cafrs:
  - year: 2024
    pdf: "../pdfs/vallejo_cafr_2024.pdf"
    toc_screenshots:
      - "../toc_screenshots/vallejo_2024_toc_page1.png"
      - "../toc_screenshots/vallejo_2024_toc_page2.png"

  - year: 2023
    pdf: "../pdfs/vallejo_cafr_2023.pdf"
    toc_screenshots:
      - "../toc_screenshots/vallejo_2023_toc.png"

  - year: 2022
    pdf: "../pdfs/vallejo_cafr_2022.pdf"
    toc_screenshots:
      - "../toc_screenshots/vallejo_2022_toc.png"

  # Add more years as needed
```

**Run batch processing:**

```bash
python process_city.py --config ~/workspace/ibco/config/vallejo.yaml
```

**Output:**
```
Processing Vallejo CAFRs
========================
Years: 2024, 2023, 2022

[1/3] Processing 2024...
  ✓ 300 pages processed
[2/3] Processing 2023...
  ✓ 295 pages processed
[3/3] Processing 2022...
  ✓ 290 pages processed

Complete! Total: 885 pages
Output: ~/workspace/ibco/output/vallejo/
```

### Output Structure

```
~/workspace/ibco/output/vallejo_2024/
├── sections/
│   ├── 01_introductory_section/
│   │   ├── page_0001_introductory.png       # 300 DPI PNG
│   │   ├── page_0002_introductory.png
│   │   ├── page_0003_introductory.png
│   │   └── ... (24 pages total)
│   ├── 02_financial_section/
│   │   ├── page_0025_financial.png
│   │   ├── page_0026_financial.png
│   │   └── ... (175 pages total)
│   └── 03_statistical_section/
│       ├── page_0200_statistical.png
│       └── ... (101 pages total)
├── cafr_metadata.json                       # Complete page index
└── cafr_report.txt                          # Human-readable summary
```

**Metadata Structure (cafr_metadata.json):**

```json
{
  "source_pdf": "vallejo_cafr_2024.pdf",
  "total_pages": 300,
  "processed_date": "2025-11-17",
  "processing_options": {
    "dpi": 300,
    "workers": 16
  },
  "toc_entries": [
    {
      "section": "Introductory Section",
      "start_page": 1,
      "level": 1
    },
    {
      "section": "Letter of Transmittal",
      "start_page": 5,
      "level": 2
    },
    {
      "section": "Financial Section",
      "start_page": 25,
      "level": 1
    }
  ],
  "pages": [
    {
      "pdf_page": 1,
      "footer_page": "i",
      "section": "Introductory Section",
      "subsection": null,
      "png_file": "sections/01_introductory_section/page_0001_introductory.png"
    },
    {
      "pdf_page": 25,
      "footer_page": "1",
      "section": "Financial Section",
      "subsection": "Independent Auditor's Report",
      "png_file": "sections/02_financial_section/page_0025_financial.png"
    }
  ],
  "statistics": {
    "pages_processed": 300,
    "sections_found": 3,
    "subsections_found": 15,
    "png_files_created": 300,
    "total_size_mb": 850,
    "processing_time_seconds": 272
  }
}
```

---

## Troubleshooting

### Common Issues

**Problem: "Python 3.11+ not found"**

```bash
# Check installed version
python3 --version

# If too old, install newer version:
# Ubuntu/Debian
sudo apt-get install python3.12

# macOS
brew install python@3.12
```

**Problem: "pdftoppm not found" or pdf2image fails**

This means poppler-utils is not installed:

```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Verify installation
pdftoppm -v
```

**Problem: "tesseract not found" or TOC loading fails**

This means tesseract-ocr is not installed:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify installation
tesseract --version
```

**Problem: Memory errors during PNG conversion**

Reduce memory usage:

```bash
# Lower DPI (smaller files)
python ibco_stripper.py --pdf cafr.pdf --toc toc.png --output out/ --dpi 150

# Fewer parallel workers
python ibco_stripper.py --pdf cafr.pdf --toc toc.png --output out/ --workers 4

# Generate metadata only (no PNGs)
python ibco_stripper.py --pdf cafr.pdf --toc toc.png --output out/ --skip-png
```

**Problem: PNG conversion is very slow**

Speed up processing:

```bash
# Use more workers (if you have CPU cores available)
python ibco_stripper.py --pdf cafr.pdf --toc toc.png --output out/ --workers 32

# Lower DPI (faster conversion)
python ibco_stripper.py --pdf cafr.pdf --toc toc.png --output out/ --dpi 150
```

### OCR Quality Tips

**For best TOC recognition:**

1. **High-resolution screenshots**
   - Use native screen resolution (don't downscale)
   - Avoid compression artifacts
   - Save as PNG, not JPEG

2. **Clear text visibility**
   - Zoom PDF to 100% or higher before screenshot
   - Ensure TOC text is crisp and readable
   - Include full page context (not just cropped TOC)

3. **Good lighting/contrast**
   - White background, black text works best
   - Avoid dark mode PDFs (OCR struggles with white-on-black)

4. **Multiple TOC pages**
   - If TOC spans multiple pages, screenshot each page separately
   - Pass all screenshots: `--toc toc1.png toc2.png toc3.png`

**If OCR is still failing:**

```bash
# Check what tesseract sees
tesseract toc_screenshot.png stdout

# Should output something like:
# Introductory Section .......1
# Financial Section .......25
# Statistical Section .......200
```

If output is garbled, try:
- Re-take screenshot at higher zoom level
- Use PDF viewer's "print to PDF" feature for cleaner TOC
- Manually create a simple text file with TOC entries

### Performance Tuning

**For AMD Threadripper 3970X (32 cores, 256GB RAM):**

```bash
# Maximum quality and speed
python ibco_stripper.py \
  --pdf cafr.pdf \
  --toc toc.png \
  --output out/ \
  --dpi 600 \
  --workers 32
```

**For typical desktop (8 cores, 16GB RAM):**

```bash
# Balanced quality and speed
python ibco_stripper.py \
  --pdf cafr.pdf \
  --toc toc.png \
  --output out/ \
  --dpi 300 \
  --workers 8
```

**For laptop (4 cores, 8GB RAM):**

```bash
# Lower resource usage
python ibco_stripper.py \
  --pdf cafr.pdf \
  --toc toc.png \
  --output out/ \
  --dpi 150 \
  --workers 2
```

**Disk space estimates:**

| DPI | Avg Page Size | 300-Page CAFR |
|-----|---------------|---------------|
| 150 | ~500 KB | ~150 MB |
| 300 | ~2.5 MB | ~750 MB |
| 600 | ~10 MB | ~3 GB |

---

## Examples

### Example 1: Single CAFR Processing

**Scenario:** Process Vallejo's 2024 CAFR (300 pages)

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Screenshot the TOC (save as vallejo_2024_toc.png)
# Manually screenshot the table of contents pages

# 3. Run the processor
python ibco_stripper.py \
  --pdf ~/workspace/ibco/pdfs/vallejo_cafr_2024.pdf \
  --toc ~/workspace/ibco/toc_screenshots/vallejo_2024_toc.png \
  --output ~/workspace/ibco/output/vallejo_2024/ \
  --dpi 300

# 4. Verify output
cat ~/workspace/ibco/output/vallejo_2024/cafr_report.txt
ls ~/workspace/ibco/output/vallejo_2024/sections/

# 5. Check specific section
ls ~/workspace/ibco/output/vallejo_2024/sections/02_financial_section/ | head
```

**Expected output:**
```
sections/02_financial_section/
├── page_0025_financial.png
├── page_0026_financial.png
├── page_0027_financial.png
└── ... (175 PNG files total)
```

### Example 2: Multi-Year Batch Processing

**Scenario:** Process 5 years of Stockton CAFRs (2020-2024)

**1. Create config file:**

```bash
nano ~/workspace/ibco/config/stockton.yaml
```

**Content:**

```yaml
city_name: "Stockton"
state: "CA"
output_base: "../output/stockton"
dpi: 300
workers: 16

cafrs:
  - year: 2024
    pdf: "../pdfs/stockton_cafr_2024.pdf"
    toc_screenshots:
      - "../toc_screenshots/stockton_2024_toc.png"

  - year: 2023
    pdf: "../pdfs/stockton_cafr_2023.pdf"
    toc_screenshots:
      - "../toc_screenshots/stockton_2023_toc.png"

  - year: 2022
    pdf: "../pdfs/stockton_cafr_2022.pdf"
    toc_screenshots:
      - "../toc_screenshots/stockton_2022_toc.png"

  - year: 2021
    pdf: "../pdfs/stockton_cafr_2021.pdf"
    toc_screenshots:
      - "../toc_screenshots/stockton_2021_toc.png"

  - year: 2020
    pdf: "../pdfs/stockton_cafr_2020.pdf"
    toc_screenshots:
      - "../toc_screenshots/stockton_2020_toc.png"
```

**2. Run batch processor:**

```bash
python process_city.py --config ~/workspace/ibco/config/stockton.yaml
```

**3. Review results:**

```bash
ls ~/workspace/ibco/output/stockton/

# Output:
# 2024/
# 2023/
# 2022/
# 2021/
# 2020/
```

**Time estimate:** 5 years × 7 minutes = 35 minutes total

### Example 3: Selective Section Extraction

**Scenario:** Extract only the Financial Section from multiple CAFRs

**For quick analysis without processing all 300 pages:**

```bash
# Process only Financial Section from 2024 CAFR
python ibco_stripper.py \
  --pdf ~/workspace/ibco/pdfs/vallejo_cafr_2024.pdf \
  --toc ~/workspace/ibco/toc_screenshots/vallejo_2024_toc.png \
  --output ~/workspace/ibco/output/vallejo_2024_financial_only/ \
  --section "Financial Section" \
  --dpi 300

# Output: Only pages 25-199 (Financial Section)
```

**Process Financial Section from multiple years:**

```bash
#!/bin/bash
# extract_financial_sections.sh

YEARS="2020 2021 2022 2023 2024"

for YEAR in $YEARS; do
    echo "Processing $YEAR Financial Section..."
    python ibco_stripper.py \
        --pdf ~/workspace/ibco/pdfs/vallejo_cafr_${YEAR}.pdf \
        --toc ~/workspace/ibco/toc_screenshots/vallejo_${YEAR}_toc.png \
        --output ~/workspace/ibco/output/vallejo_${YEAR}_financial/ \
        --section "Financial Section" \
        --dpi 300
done

echo "Complete! Financial sections extracted for years: $YEARS"
```

**Time estimate:** 5 years × 2 minutes = 10 minutes (vs 35 minutes for full processing)

### Example 4: Metadata-Only Generation

**Scenario:** Build page index without PNG conversion (for quick catalog)

```bash
# Generate metadata only (fast, ~30 seconds)
python ibco_stripper.py \
  --pdf ~/workspace/ibco/pdfs/vallejo_cafr_2024.pdf \
  --toc ~/workspace/ibco/toc_screenshots/vallejo_2024_toc.png \
  --output ~/workspace/ibco/output/vallejo_2024_index/ \
  --skip-png

# Output:
# ✓ cafr_metadata.json (complete page index)
# ✓ cafr_report.txt (summary)
# ✗ No PNG files generated
```

**Use case:** Quickly catalog 50 years of CAFRs to understand structure before full processing.

---

## Advanced Topics

### Features

- ✅ **Manual TOC Screenshots** - More accurate than auto-extraction
- ✅ **Intelligent Page Mapping** - Links pages to sections automatically
- ✅ **Parallel Processing** - Optimized for multi-core systems (8-16 pages simultaneously)
- ✅ **Multiple Formats** - Handles Roman numerals (i, ii, iii) and Arabic (1, 2, 3)
- ✅ **Complete Metadata** - JSON index of every page with section context
- ✅ **Human-Readable Reports** - Text summaries for quick verification
- ✅ **Selective Export** - Process single sections or page ranges
- ✅ **Resume Capability** - Skip already-processed pages

### Architecture

**Workflow: Manual TOC (Simpler & More Reliable)**

Why manual TOC screenshots?
- CAFRs vary wildly in format between cities
- You verify accuracy before processing begins
- Only takes 2 minutes per CAFR
- Works with any TOC layout

Alternative: Auto-TOC extraction requires complex parsing rules and is error-prone for municipal documents.

**System Optimization**

Target Hardware: AMD Threadripper or similar multi-core systems
- Parallel PNG conversion (8-16 pages simultaneously)
- Memory caching for large PDFs
- Fast NVMe storage for output

Tested On:
- AMD Threadripper 3970X (32 cores, 256GB RAM)
- Ubuntu 24.04 LTS
- ~5 minutes for 300-page CAFR

Will Work On: Any system with Python 3.12+ and 8GB+ RAM (just slower)

### Testing

**Run comprehensive test suite:**

```bash
# All tests (9 test cases)
python tests/run_all_tests.py

# Or with pytest
pytest tests/test_ibco_stripper.py -v

# Quick verification
make test-quick

# Full test suite including all 15+ test files
make test
```

See [tests/README.md](tests/README.md) for test documentation.

---

## Building with Claude Code

This project is designed to be **built using Claude Code** with a structured prompt sequence:

1. Read [PROMPTS_QUICK_START.md](PROMPTS_QUICK_START.md) (10 min)
2. Follow [CLAUDE_CODE_PROMPTS.md](CLAUDE_CODE_PROMPTS.md) (2-3 hours)
3. Build in 4 sessions: Foundation → TOC → Pipeline → Complete

**Estimated Build Time:** 2-3 hours with Claude Code

See [WORKFLOW_VISUAL.md](WORKFLOW_VISUAL.md) for detailed workflow diagrams.

---

## Contributing

This project is part of the IBCo transparency initiative. Contributions welcome!

**Focus Areas:**
- Improving OCR accuracy for TOC screenshots
- Supporting additional CAFR formats
- Performance optimization
- Documentation improvements

**Process:**
1. Fork repository
2. Create feature branch
3. Submit pull request with clear description

---

## License

**Unlicense (Public Domain)**

This project is released to the public domain. Tools for transparency belong to everyone.

No permission needed. Use, modify, distribute freely for any purpose.

See [UNLICENSE](UNLICENSE) file for full text.

---

## Contact & Support

- **Issues:** [GitHub Issues](https://github.com/BrandonCarranza/cafr_pdf_stripper/issues)
- **Documentation:** See [INSTALL.md](INSTALL.md), [WORKFLOW_VISUAL.md](WORKFLOW_VISUAL.md)
- **IBCo Network:** [ibco-ca.us](https://ibco-ca.us)

---

## Acknowledgments

Built for the Independent Budget & Capital Operations (IBCo) transparency initiative to enable forensic analysis of municipal financial reports and promote government accountability through accessible data.

**Mission:** Make municipal financial data transparent, accessible, and analyzable for all citizens.
