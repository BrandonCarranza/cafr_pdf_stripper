# Getting Sample CAFR PDFs for Testing

## Quick Sources for Sample CAFRs

### Option 1: California Cities (Recommended for Testing)

**Vallejo, CA:**
- Website: https://www.cityofvallejo.net/
- Search for: "Comprehensive Annual Financial Report" or "CAFR"
- Navigate to: Government → Finance → Financial Reports
- Download most recent fiscal year

**Stockton, CA:**
- Website: https://www.stocktonca.gov/
- Finance Department → Financial Reports
- Look for CAFR PDFs (typically 200-300 pages)

**Sacramento, CA:**
- Website: https://www.cityofsacramento.gov/
- Finance → Reports and Documents → CAFR

### Option 2: Government Finance Officers Association (GFOA)

**GFOA Award Winners:**
- Website: https://www.gfoa.org/coa
- Browse award-winning CAFRs from municipalities
- High-quality, well-formatted examples

### Option 3: Municipal Websites

Most California cities publish CAFRs online:
1. Google: `"[City Name] CA" CAFR filetype:pdf`
2. Look for Finance or Controller department
3. Download most recent year

## What to Look For in a Good Test CAFR

✓ **Size:** 200-400 pages (typical)
✓ **Structure:** Clear Table of Contents
✓ **Sections:** Introductory, Financial, Statistical
✓ **Page Numbers:** Roman numerals (i, ii, iii) transitioning to Arabic (1, 2, 3)
✓ **Headers:** Section names in page headers

## After Downloading

1. **Place PDF in project directory:**
   ```bash
   # Save as descriptive name
   cp ~/Downloads/vallejo_cafr_2024.pdf /home/user/cafr_pdf_stripper/
   ```

2. **Screenshot the Table of Contents:**
   - Open PDF in viewer
   - Navigate to TOC (usually pages 2-5)
   - Take screenshot(s)
   - Save as: `toc_vallejo_2024.png`

3. **Test page extraction:**
   ```bash
   python test_page_extraction.py vallejo_cafr_2024.pdf
   ```

## Example Output

You should see output like:
```
PDF Page   Footer Page     Header Text                              Notes
--------------------------------------------------------------------------------
Page 1    → "i"            CITY OF VALLEJO
Page 2    → "ii"           CITY OF VALLEJO
Page 5    → "v"            INTRODUCTORY SECTION
Page 25   → "1"            FINANCIAL SECTION                        Format change: roman → arabic
Page 26   → "2"            FINANCIAL SECTION
```

## File Size Notes

- CAFRs are typically 5-50 MB
- They are in `.gitignore` (won't be committed to git)
- Store locally for testing only
- Don't commit PDFs to the repository

## Recommended Test CAFR

For IBCo's California focus, **Vallejo** or **Stockton** CAFRs are ideal:
- Both cities have fiscal challenges (ideal for transparency work)
- Well-formatted PDFs
- Clear section structure
- Available online for free
- 250-350 pages (good test size)

## Quick Command

```bash
# After downloading a CAFR to your Downloads folder:
cd /home/user/cafr_pdf_stripper
cp ~/Downloads/name_of_cafr.pdf ./sample_cafr.pdf
python test_page_extraction.py sample_cafr.pdf
```

## Need Help?

If you can't find a CAFR:
1. Contact the city's Finance Department
2. Check the city's website under:
   - Finance → Reports
   - Controller → Financial Reports
   - Budget → Annual Reports
3. Look for "ACFR" (Annual Comprehensive Financial Report) - same as CAFR
