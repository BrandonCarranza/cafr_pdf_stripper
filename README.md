# CAFR PDF Stripper

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-Unlicense-green.svg)
![IBCo](https://img.shields.io/badge/IBCo-Transparency-orange.svg)

**Municipal Financial Report Processing for IBCo Transparency Initiative**

Converts 300-page municipal CAFR (Comprehensive Annual Financial Report) PDFs into organized, high-quality PNG files with intelligent section mapping and complete metadata generation.

---

## 📚 Documentation

- **[Build Guide](CLAUDE_CODE_PROMPTS.md)** - Complete 16-prompt sequence for building with Claude Code
- **[Quick Start](PROMPTS_QUICK_START.md)** - Fast reference and session breakdown
- **[Workflow Guide](WORKFLOW_VISUAL.md)** - Visual step-by-step workflow

**New to this project?** Start with [PROMPTS_QUICK_START.md](PROMPTS_QUICK_START.md)

---

## What It Does

Transforms municipal CAFR PDFs into organized, analyzed datasets:

1. **Load TOC Screenshot** - You screenshot the table of contents (simple, accurate)
2. **Extract Page Numbers** - Reads page numbers from PDF footers (handles Roman & Arabic)
3. **Map Sections** - Associates each page with its TOC section
4. **Convert to PNG** - High-quality 300 DPI PNG files, organized by section
5. **Generate Metadata** - Complete JSON index of every page

**Processing Time:** ~5 minutes for a 300-page CAFR

---

## Quick Start

### Installation

**Automated Setup (Recommended):**
```bash
./setup.sh
```

This automated script will:
- ✅ Check system requirements (Python 3.11+, poppler-utils, tesseract-ocr)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up workspace directories
- ✅ Run verification tests

**Manual Installation:**

See [INSTALL.md](INSTALL.md) for detailed installation instructions, troubleshooting, and manual setup steps.

**Quick Verification:**
```bash
make test-quick
# or
python -c "import ibco_stripper; print('✓ Installation successful')"
```

### Usage
```bash
# 1. Screenshot your CAFR's table of contents
# Save as: toc_screenshot.png

# 2. Process the CAFR
python ibco_stripper.py \
  --pdf vallejo_cafr_2024.pdf \
  --toc toc_screenshot.png \
  --output vallejo_2024/ \
  --dpi 300

# 3. Review results
cat vallejo_2024/cafr_report.txt
ls vallejo_2024/sections/
```

---

## Output Structure

```
vallejo_2024/
├── sections/
│   ├── 01_introductory_section/
│   │   ├── page_0001_introductory.png (300 DPI)
│   │   ├── page_0002_introductory.png
│   │   └── ... (24 pages)
│   ├── 02_financial_section/
│   │   ├── page_0025_financial.png
│   │   └── ... (175 pages)
│   └── 03_statistical_section/
│       └── ... (101 pages)
├── cafr_metadata.json       # Complete page index with sections
└── cafr_report.txt          # Human-readable processing summary
```

### Example Metadata (cafr_metadata.json)
```json
{
  "source_pdf": "vallejo_cafr_2024.pdf",
  "total_pages": 300,
  "processed_date": "2025-11-17",
  "toc_entries": [
    {
      "section": "Financial Section",
      "start_page": 25,
      "level": 1
    }
  ],
  "pages": [
    {
      "pdf_page": 25,
      "footer_page": "1",
      "section": "Financial Section",
      "png_file": "sections/02_financial_section/page_0025.png"
    }
  ],
  "statistics": {
    "pages_processed": 300,
    "sections_found": 3,
    "png_files_created": 300
  }
}
```

---

## Use Case: IBCo Transparency Initiative

Built for the **IBCo (Independent Budget & Capital Operations)** network to enable:

- **Municipal Financial Transparency** - Make CAFR data accessible and analyzable
- **Forensic Analysis** - Examine historical financial trends across years
- **Cited Evidence** - Generate verifiable references for accountability research
- **Historical Tracking** - Process 15+ years of CAFRs per city

### IBCo Network
- [ibco-ca.us](https://ibco-ca.us) - California transparency hub
- [vallejo.ibco-ca.us](https://vallejo.ibco-ca.us) - Vallejo financial data
- [stockton.ibco-ca.us](https://stockton.ibco-ca.us) - Stockton financial data

---

## Features

- ✅ **Manual TOC Screenshots** - More accurate than auto-extraction
- ✅ **Intelligent Page Mapping** - Links pages to sections automatically
- ✅ **Parallel Processing** - Optimized for multi-core systems (8-16 pages simultaneously)
- ✅ **Multiple Formats** - Handles Roman numerals (i, ii, iii) and Arabic (1, 2, 3)
- ✅ **Complete Metadata** - JSON index of every page with section context
- ✅ **Human-Readable Reports** - Text summaries for quick verification
- ✅ **Selective Export** - Process single sections or page ranges
- ✅ **Resume Capability** - Skip already-processed pages

---

## Architecture

### Workflow: Manual TOC (Simpler & More Reliable)

**Why manual TOC screenshots?**
- CAFRs vary wildly in format between cities
- You verify accuracy before processing begins
- Only takes 2 minutes per CAFR
- Works with any TOC layout

**Alternative:** Auto-TOC extraction requires complex parsing rules and is error-prone for municipal documents.

### System Optimization

**Target Hardware:** AMD Threadripper or similar multi-core systems
- Parallel PNG conversion (8-16 pages simultaneously)
- Memory caching for large PDFs
- Fast NVMe storage for output

**Tested On:**
- AMD Threadripper 3970X (32 cores, 256GB RAM)
- Ubuntu 24.04 LTS
- ~5 minutes for 300-page CAFR

**Will Work On:** Any system with Python 3.12+ and 8GB+ RAM (just slower)

---

## Building with Claude Code

This project is designed to be **built using Claude Code** with a structured prompt sequence:

1. Read [PROMPTS_QUICK_START.md](PROMPTS_QUICK_START.md) (10 min)
2. Follow [CLAUDE_CODE_PROMPTS.md](CLAUDE_CODE_PROMPTS.md) (2-3 hours)
3. Build in 4 sessions: Foundation → TOC → Pipeline → Complete

**Estimated Build Time:** 2-3 hours with Claude Code
**Estimated Processing Time:** 90 minutes for 15 historical CAFRs

See [WORKFLOW_VISUAL.md](WORKFLOW_VISUAL.md) for detailed workflow diagrams.

---

## Example: Processing 15 Years of Vallejo CAFRs

```bash
# For each year (2010-2024):
# 1. Screenshot TOC (2 min)
# 2. Run processor (5 min)
# 3. Verify output (1 min)

# Result:
/data/cafr/vallejo/
├── 2024/ (300 pages, 850MB)
├── 2023/ (295 pages, 830MB)
├── 2022/
└── ... (15 years total)

# Total: ~4,500 pages, ~12GB, ready for analysis
# Time: One afternoon (~90 minutes)
```

---

## Requirements

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils tesseract-ocr

# macOS
brew install poppler tesseract

# Fedora/RHEL
sudo dnf install poppler-utils tesseract
```

### Python Dependencies
See [requirements.txt](requirements.txt) for full list:
- `pdfplumber` - PDF text extraction
- `pytesseract` - OCR for TOC screenshots
- `Pillow` - Image processing
- `pdf2image` - PDF to PNG conversion
- `tqdm` - Progress bars

---

## Project Status

**Current State:** Planning & Documentation Phase

This repository contains:
- ✅ Complete build documentation
- ✅ 16-prompt sequence for Claude Code
- ✅ Workflow guides and examples
- ⏳ Source code (to be built with Claude Code prompts)

**Next Steps:**
1. Use Claude Code to build the tool following [CLAUDE_CODE_PROMPTS.md](CLAUDE_CODE_PROMPTS.md)
2. Test with Vallejo CAFR dataset
3. Expand to additional California municipalities

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
- **IBCo Network:** [ibco-ca.us](https://ibco-ca.us)
- **Project Context:** See [CLAUDE_CODE_PROMPTS.md](CLAUDE_CODE_PROMPTS.md) for full background

---

## Acknowledgments

Built for the Independent Budget & Capital Operations (IBCo) transparency initiative to enable forensic analysis of municipal financial reports and promote government accountability through accessible data.

**Mission:** Make municipal financial data transparent, accessible, and analyzable for all citizens.
