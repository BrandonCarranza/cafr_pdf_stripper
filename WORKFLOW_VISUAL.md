# IBCo PDF Stripper - Your Workflow

**Simplified for Single-City, Manual TOC Processing**

---

## 📸 Your Actual Workflow (Step-by-Step)

```
┌─────────────────────────────────────────────────────────┐
│                     STEP 1: PREPARE                     │
│                                                         │
│  You have: vallejo_cafr_2024.pdf (300 pages)          │
│                                                         │
│  1. Open PDF in viewer                                 │
│  2. Navigate to Table of Contents (usually pages 2-5)  │
│  3. Take screenshot(s) of TOC                          │
│  4. Save as: toc_vallejo_2024.png                     │
│                                                         │
│  Time: 2 minutes                                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    STEP 2: PROCESS                      │
│                                                         │
│  Run command:                                          │
│  $ python ibco_stripper.py \                          │
│      --pdf vallejo_cafr_2024.pdf \                    │
│      --toc toc_vallejo_2024.png \                     │
│      --output vallejo_2024/ \                         │
│      --dpi 300                                         │
│                                                         │
│  Tool does:                                            │
│  ✓ Loads your TOC screenshot                          │
│  ✓ OCR → extracts section names & pages              │
│  ✓ Shows you TOC for verification                     │
│  ✓ Reads all 300 pages                                │
│  ✓ Extracts page numbers from footers                 │
│  ✓ Maps pages to sections                             │
│  ✓ Converts pages to PNG files                        │
│  ✓ Organizes by section                               │
│  ✓ Generates metadata & report                        │
│                                                         │
│  Progress: [████████░░] 85% (255/300 pages)          │
│                                                         │
│  Time: 3-5 minutes                                     │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    STEP 3: REVIEW                       │
│                                                         │
│  Output created:                                       │
│                                                         │
│  vallejo_2024/                                        │
│  ├── sections/                                        │
│  │   ├── 01_introductory_section/                   │
│  │   │   ├── page_0001_introductory.png (300 DPI)  │
│  │   │   ├── page_0002_introductory.png            │
│  │   │   └── ... (24 pages)                        │
│  │   ├── 02_financial_section/                     │
│  │   │   ├── page_0025_financial.png              │
│  │   │   └── ... (175 pages)                      │
│  │   └── 03_statistical_section/                  │
│  │       └── ... (101 pages)                      │
│  ├── cafr_metadata.json (complete index)           │
│  └── cafr_report.txt (human-readable)              │
│                                                         │
│  Time: 1 minute to review                             │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    REPEAT FOR 15 YEARS                  │
│                                                         │
│  For each historical CAFR:                             │
│  1. Screenshot TOC → toc_2023.png                     │
│  2. Run processor → vallejo_2023/                     │
│  3. Review output                                      │
│                                                         │
│  Total for 15 CAFRs: ~90 minutes                      │
│  (6 minutes per CAFR including prep)                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 What Each File Contains

### Input: Your TOC Screenshot

```
toc_vallejo_2024.png
┌───────────────────────────────────┐
│  COMPREHENSIVE ANNUAL             │
│  FINANCIAL REPORT                 │
│                                   │
│  TABLE OF CONTENTS                │
│                                   │
│  Introductory Section........1    │
│    Letter of Transmittal.....3    │
│    GFOA Certificate..........12   │
│    Organizational Chart......15   │
│                                   │
│  Financial Section...........25   │
│    Independent Auditor's.....26   │
│    MD&A......................30   │
│    Basic Statements..........45   │
│                                   │
│  Statistical Section........200   │
└───────────────────────────────────┘
```

### Output: Metadata JSON

```json
{
  "source_pdf": "vallejo_cafr_2024.pdf",
  "city": "Vallejo",
  "state": "CA",
  "fiscal_year": 2024,
  "total_pages": 300,
  "processed_date": "2025-11-16 14:30:00",
  
  "toc_entries": [
    {
      "section": "Introductory Section",
      "start_page": 1,
      "level": 1,
      "page_count": 24
    },
    {
      "section": "Letter of Transmittal",
      "start_page": 3,
      "level": 2,
      "parent": "Introductory Section"
    }
  ],
  
  "pages": [
    {
      "pdf_page": 1,
      "footer_page": "i",
      "section": "Introductory Section",
      "header": "CITY OF VALLEJO",
      "png_file": "sections/01_introductory_section/page_0001.png"
    },
    {
      "pdf_page": 25,
      "footer_page": "1",
      "section": "Financial Section",
      "header": "FINANCIAL SECTION",
      "png_file": "sections/02_financial_section/page_0025.png"
    }
  ],
  
  "statistics": {
    "pages_processed": 300,
    "pages_with_numbers": 295,
    "pages_without_numbers": 5,
    "sections_found": 3,
    "png_files_created": 300,
    "total_size_mb": 850
  }
}
```

### Output: Human Report

```
=================================================
VALLEJO CAFR 2024 - PROCESSING REPORT
=================================================

Source: vallejo_cafr_2024.pdf
Total Pages: 300
Processed: November 16, 2025 at 2:30 PM
Processing Time: 4 minutes 23 seconds

TABLE OF CONTENTS
-------------------------------------------------
Introductory Section ..................... 1-24
  Letter of Transmittal .................. 3-11
  GFOA Certificate ....................... 12-14
  Organizational Chart ................... 15-24

Financial Section ........................ 25-199
  Independent Auditor's Report ........... 26-29
  Management's Discussion & Analysis ..... 30-44
  Basic Financial Statements ............. 45-75
  Notes to Financial Statements .......... 76-150
  Required Supplementary Information ..... 151-199

Statistical Section ...................... 200-300
  Financial Trends ....................... 201-220
  Revenue Capacity ....................... 221-240
  Debt Capacity .......................... 241-260
  Demographic Information ................ 261-280
  Operating Information .................. 281-300

PAGE PROCESSING SUMMARY
-------------------------------------------------
✓ 300 pages processed
✓ 300 PNG files created (300 DPI)
✓ 3 main sections found
✓ 8 subsections identified
⚠ 5 pages without page numbers (cover, dividers)

OUTPUT FILES
-------------------------------------------------
PNG Files: vallejo_2024/sections/
Metadata: vallejo_2024/cafr_metadata.json
Report: vallejo_2024/cafr_report.txt
Total Size: 850 MB

READY FOR ANALYSIS
-------------------------------------------------
All sections extracted and organized.
Pages are ready for transcription or analysis.
```

---

## 🔄 For 15 Historical CAFRs

```
Your Complete City Dataset:

/data/cafr/vallejo/
├── 2024/
│   ├── sections/ (300 pages)
│   ├── cafr_metadata.json
│   └── cafr_report.txt
├── 2023/
│   ├── sections/ (295 pages)
│   └── ...
├── 2022/
├── 2021/
├── 2020/
├── 2019/
├── 2018/
├── 2017/
├── 2016/
├── 2015/
├── 2014/
├── 2013/
├── 2012/
├── 2011/
└── 2010/

Total: ~4,500 pages across 15 years
Total Size: ~12 GB (at 300 DPI)
Processing Time: ~90 minutes (one afternoon)
```

---

## 🎛️ Optional: Batch Config

If you want to automate all 15 years:

```yaml
# vallejo_batch.yaml
city_name: "Vallejo"
state: "CA"
output_base: "/data/cafr/vallejo/"

cafrs:
  - year: 2024
    pdf: "pdfs/vallejo_cafr_2024.pdf"
    toc: "toc/vallejo_2024_toc.png"
  
  - year: 2023
    pdf: "pdfs/vallejo_cafr_2023.pdf"
    toc: "toc/vallejo_2023_toc.png"
  
  # ... all 15 years

processing:
  dpi: 300
  verify_before_processing: true
  sequential: true  # One at a time
```

Run with:
```bash
python process_city.py vallejo_batch.yaml
```

This processes all 15 automatically while you grab coffee!

---

## 📊 Performance Expectations

### On Your Threadripper 3970X:

**Single CAFR (300 pages):**
- TOC OCR: 2-5 seconds
- Page reading: 30 seconds
- PNG conversion: 3 minutes (parallel)
- Metadata generation: 5 seconds
- **Total: ~4 minutes**

**15 CAFRs (4,500 pages):**
- Setup (screenshots): 30 minutes
- Processing: 60 minutes
- Verification: 15 minutes
- **Total: ~2 hours**

**What's Using Your Threadripper:**
- PNG conversion: 8-16 pages in parallel
- OCR if TOC is multi-page
- Everything else is I/O-bound (fast NVMe helps)

---

## 🎯 Compare: What You Built vs Original

### Original Code (that I made):
- ✅ Auto-TOC extraction from PDF
- ✅ Batch processing for multiple cities
- ✅ Complex parallelization
- ✅ Advanced features you don't need

### Your Optimized Version (via Claude Code):
- ✅ Manual TOC screenshots (more accurate!)
- ✅ Single-city focus (simpler)
- ✅ Sequential processing (easier to monitor)
- ✅ Just the features you need

**Result:** Simpler, more reliable, easier to verify!

---

## 💡 Why Manual TOC Screenshots Are Better

**Auto-extraction challenges:**
- TOC formats vary wildly between cities
- PDF text extraction can be unreliable
- Complex parsing rules needed
- Hard to debug when it fails

**Manual screenshots advantages:**
- ✓ You verify it's correct before processing
- ✓ Works with any TOC format
- ✓ OCR is simple and reliable
- ✓ Easy to re-do if needed
- ✓ Only takes 2 minutes per CAFR

**For 15 CAFRs:** 30 minutes of screenshots vs hours debugging auto-extraction!

---

## 🚀 After Building with Claude Code

Your actual commands will be:

```bash
# One-time setup
cd ~/workspace/ibco
python setup.py  # Creates directories, installs deps

# For each CAFR:
# 1. Screenshot TOC
# 2. Run:
python ibco_stripper.py \
  --pdf vallejo_cafr_2024.pdf \
  --toc toc_2024.png \
  --output vallejo_2024/

# 3. Verify:
cat vallejo_2024/cafr_report.txt
ls -lh vallejo_2024/sections/

# Done! Move to next year.
```

---

## 📈 What You'll Have

After processing all 15 Vallejo CAFRs:

**Data:**
- 4,500 high-quality PNG pages (300 DPI)
- Complete metadata for every page
- Organized by year and section
- Ready for transcription/analysis

**Use Cases:**
- Search across all years
- Track trends over time
- Compare sections year-over-year
- Feed to OCR for full text extraction
- Publish on IBCo transparency portal

**Storage:**
- ~850 MB per CAFR × 15 = ~12 GB
- Easily fits on your 4TB Samsung 990 PRO
- Fast access from NVMe

---

## ✅ Success Checklist

After building with Claude Code prompts, you should be able to:

- [ ] Load your TOC screenshot and see parsed sections
- [ ] Process a single CAFR in ~5 minutes
- [ ] Get 300 PNG files organized by section
- [ ] Have complete JSON metadata for every page
- [ ] Read a human-friendly report
- [ ] Process 15 CAFRs in one afternoon
- [ ] Verify every step completed successfully
- [ ] Re-run if needed without issues

**If all checked:** You're production-ready! 🎉

---

**Ready to start building?**

1. Read [CLAUDE_CODE_PROMPTS.md](CLAUDE_CODE_PROMPTS.md) - Full prompt sequence
2. Read [PROMPTS_QUICK_START.md](PROMPTS_QUICK_START.md) - How to use prompts
3. Open Claude Code (terminal or web)
4. Copy PROMPT 1A
5. Start building!

**Estimated time:** One afternoon to build, one afternoon to process Vallejo!
