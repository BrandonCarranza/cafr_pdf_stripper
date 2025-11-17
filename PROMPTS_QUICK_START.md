# Claude Code Prompts - Quick Reference

**Your Actual Workflow:** Manual TOC Screenshots → Single-City Processing  
**Scale:** 1 city, ~15 CAFRs, ~300 pages each  
**Build Time:** 2-3 hours with Claude Code

---

## 🎯 Your Build Path

### Option A: Claude Code Terminal (Recommended)
```bash
# Start Claude Code in your workspace
cd ~/workspace/ibco
claude code

# Then copy/paste prompts from CLAUDE_CODE_PROMPTS.md
# Build incrementally, test as you go
```

### Option B: Claude Code Web
1. Go to claude.ai
2. Start new chat
3. Copy/paste each prompt
4. Save code to your workspace
5. Test locally, iterate as needed

---

## 📋 16 Prompts in 4 Sessions

### SESSION 1: Foundation (1 hour)
**Prompts:** 1A, 1B, 1C  
**Builds:** Core PDF reader, page number extraction  
**Test:** Extract page numbers from sample CAFR  

```
Copy PROMPT 1A → Claude Code → Review code → Test
Copy PROMPT 1B → Claude Code → Review code → Test  
Copy PROMPT 1C → Claude Code → Run test → Verify output
```

**You should have:** Basic PDF reader that extracts page numbers

---

### SESSION 2: TOC Processing (45 min)
**Prompts:** 2A, 2B, 2C  
**Builds:** Screenshot OCR, TOC parsing, multi-screenshot support  
**Test:** Load your TOC screenshots, verify parsing  

```
Screenshot your CAFR table of contents first!
Save as: toc_page1.png, toc_page2.png (if multi-page)

Copy PROMPT 2A → Build OCR loader
Copy PROMPT 2B → Improve parsing patterns
Copy PROMPT 2C → Add multi-screenshot support

Test with YOUR actual TOC screenshots!
```

**You should have:** Tool that reads your TOC screenshots correctly

---

### SESSION 3: Processing Pipeline (1 hour)
**Prompts:** 3A, 3B, 4A, 4B  
**Builds:** Section mapping, PNG export, parallel processing  
**Test:** Process one section of CAFR to PNG  

```
Copy PROMPT 3A → Build section mapper
Copy PROMPT 3B → Create page index
Copy PROMPT 4A → Add PNG export
Copy PROMPT 4B → Add selective export

Test: Process just "Financial Section" to verify workflow
```

**You should have:** Working pipeline that saves pages as PNG

---

### SESSION 4: Complete & Polish (30 min)
**Prompts:** 5A, 5B, 6A, 6B, 6C, 7A, 7B  
**Builds:** Metadata, reports, batch processing, optimization  
**Test:** Full CAFR processing  

```
Copy PROMPT 5A → JSON metadata export
Copy PROMPT 5B → Human-readable report
Copy PROMPT 6A → Main processing workflow
Copy PROMPT 6B → City batch processor
Copy PROMPT 6C → Verification

Skip 7A if you don't need formal tests
Use 7B to optimize for your Threadripper
```

**You should have:** Complete, production-ready tool

---

## 🚀 Quick Start After Build

```bash
# Your actual workflow:

# 1. Screenshot TOC from CAFR
# Save as: toc_vallejo_2024.png

# 2. Run processor
python ibco_stripper.py \
  --pdf vallejo_cafr_2024.pdf \
  --toc toc_vallejo_2024.png \
  --output vallejo_2024/ \
  --dpi 300

# 3. Check results
cat vallejo_2024/cafr_report.txt
ls vallejo_2024/sections/

# Done! ~3-5 minutes for 300 pages
```

---

## 💡 Pro Tips for Claude Code

### Make Prompts Work Better:

**❌ Don't say:**
> "Build a PDF processor"

**✅ Do say:**
> "Build a PDF processor for 300-page municipal CAFR documents. 
> I'll manually screenshot the table of contents and load it.
> Extract page numbers from footers and save pages as PNG files
> organized by section."

### If Claude Code Output Isn't Perfect:

**Follow-up prompts:**
```
"That's close, but the page number extraction isn't working for 
Roman numerals. Can you modify the regex pattern to handle 
i, ii, iii, iv, etc.?"

"The TOC parser is getting confused by extra spaces. Can you 
make it more flexible with whitespace handling?"

"Perfect! Now add a progress bar so I can see the processing 
status for 300 pages."
```

### Testing Each Step:

After each prompt, test with real data:
```bash
# Test page extraction
python test_extraction.py vallejo_2024.pdf

# Test TOC loading  
python test_toc.py toc_screenshot.png

# Test full pipeline
python ibco_stripper.py --verify-only
```

---

## 🎯 Your Specific Needs

### What You Said:
- ✅ Manual TOC screenshots (not auto-extraction)
- ✅ Read page numbers from PDF footers
- ✅ Save pages according to TOC structure
- ✅ ~300 pages per CAFR
- ✅ ~15 CAFRs per city
- ✅ Single city at a time

### What This Means:

**SKIP these sections:**
- Auto-TOC extraction from PDF (use screenshots instead)
- Multi-city parallel processing (do one city at a time)
- Complex batch scheduling (manual workflow is fine)

**FOCUS on these:**
- Excellent OCR of your TOC screenshots
- Reliable page number extraction
- Clean directory structure by section
- Good progress indicators
- Easy to re-run if needed

---

## 📊 Expected Results

After completing all prompts:

**Input:**
- `vallejo_cafr_2024.pdf` (300 pages)
- `toc_page1.png` (your screenshot)

**Output:**
```
vallejo_2024/
├── sections/
│   ├── 01_introductory_section/
│   │   ├── page_0001_introductory.png
│   │   ├── page_0002_introductory.png
│   │   └── ...
│   ├── 02_financial_section/
│   │   ├── page_0025_financial.png
│   │   └── ...
│   └── 03_statistical_section/
│       └── ...
├── cafr_metadata.json
└── cafr_report.txt
```

**Processing Time:**
- TOC screenshot loading: 5 seconds
- Page extraction: 3-5 minutes (300 pages)
- Total: ~5 minutes per CAFR

**For 15 CAFRs:**
- Total time: ~75 minutes (1.25 hours)
- One at a time, easily monitored

---

## 🔧 Customization Examples

### If Your TOC Format is Unusual:

```
"My CAFR TOC uses this format:
Section I - Introductory Material ........... Page 1
Section II - Financial Data ................. Page 25

Can you adjust the TOC parsing pattern to handle this?"
```

### If Page Numbers Are in Weird Locations:

```
"The page numbers in my CAFR are in the top-right corner, not 
the bottom center. Can you modify the footer extraction to look 
in the top 10% of the page instead?"
```

### If You Want Different Output:

```
"Instead of organizing by section folders, can you save all 
PNGs in one folder but name them like:
vallejo_2024_p0001_introductory.png
vallejo_2024_p0025_financial.png"
```

---

## ⚠️ Common Issues & Solutions

### Issue: OCR Not Reading TOC Accurately

**Solution:**
```
"The OCR is making mistakes on my TOC screenshot. Can you:
1. Add pre-processing to enhance image contrast
2. Let me manually review/edit the parsed TOC
3. Show OCR confidence scores so I know what to check"
```

### Issue: Page Numbers Not Detected

**Solution:**
```
"Page numbers aren't being found on some pages. Can you:
1. Try looking in different regions (top, bottom, sides)
2. Add a fallback that looks for ANY numbers on the page
3. Report which pages failed and let me manually enter them"
```

### Issue: Processing Too Slow

**Solution:**
```
"Processing 300 pages takes 10 minutes. Can you optimize by:
1. Using multiprocessing to convert 8 pages at once
2. Caching the PDF pages in memory (I have 256GB RAM)
3. Using lower quality PNG if file size is too big"
```

---

## 🎯 Next Steps

1. **Read CLAUDE_CODE_PROMPTS.md** - Full prompt sequence
2. **Start with SESSION 1** - Build foundation
3. **Test each component** - Use your real CAFR data
4. **Iterate as needed** - Refine based on your specific PDFs
5. **Move to SESSION 2-4** - Complete the build

**Estimated Time:**
- Reading prompts: 15 minutes
- Building tool: 2-3 hours
- Testing with real CAFR: 30 minutes
- Processing 15 CAFRs: 1.5 hours

**Total: One afternoon to build, one afternoon to process your city!**

---

## 📝 Notes

**You Don't Need:**
- Complex parallel processing (one CAFR at a time is fine)
- Auto-TOC extraction (you'll screenshot it)
- Multi-city batch (only doing one city)
- GPU acceleration (Threadripper CPU is plenty)

**You DO Need:**
- Good TOC screenshot OCR
- Reliable page number extraction  
- Clean output organization
- Progress visibility
- Easy to verify results

**Your Threadripper is Overkill:**
For 15 CAFRs of 300 pages each, even a modest system would work fine.
But since you have it, use it for fast PNG conversion (8-16 pages parallel).

---

**Ready to build?**

→ Open `CLAUDE_CODE_PROMPTS.md`  
→ Copy PROMPT 1A  
→ Paste into Claude Code  
→ Let's go! 🚀
