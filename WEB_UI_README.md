# IBCo CAFR PDF Stripper - Web Interface

**Browser-Based Interface for Processing CAFR PDFs**

This web interface provides an easy-to-use, browser-based frontend for the IBCo CAFR PDF Stripper, built with Streamlit.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Running the Web Interface](#running-the-web-interface)
4. [Features](#features)
5. [User Guide](#user-guide)
6. [Troubleshooting](#troubleshooting)
7. [Comparison: Web UI vs CLI](#comparison-web-ui-vs-cli)

---

## Quick Start

```bash
# 1. Install web dependencies (in addition to base dependencies)
pip install -r requirements_web.txt

# 2. Launch web interface
streamlit run web_ui.py

# 3. Open browser to http://localhost:8501
```

---

## Installation

### Prerequisites

Ensure you have already installed the base IBCo CAFR PDF Stripper:

```bash
# If not already installed, run setup first
./setup.sh

# Or manually install base dependencies
pip install -r requirements.txt
```

### Install Web Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install additional web dependencies
pip install -r requirements_web.txt
```

**What gets installed:**
- `streamlit` - Web framework for the UI
- `pyyaml` - YAML configuration file support

**Total additional size:** ~50 MB

---

## Running the Web Interface

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Launch Streamlit
streamlit run web_ui.py
```

**Expected output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.100:8501
```

### Custom Port

```bash
# Run on custom port
streamlit run web_ui.py --server.port 8080

# Disable auto-open browser
streamlit run web_ui.py --server.headless true
```

### Production Deployment

For production deployment (NOT recommended for single user, but available):

```bash
# Run with production settings
streamlit run web_ui.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true \
  --browser.gatherUsageStats false
```

**Security Note:** The web interface is designed for local, single-user use. For multi-user deployments, add authentication and consider running behind a reverse proxy.

---

## Features

### Page 1: Single CAFR Processing

Process one CAFR at a time with a simple upload interface.

**Capabilities:**
- Upload PDF file (any size)
- Upload multiple TOC screenshots
- Adjust DPI settings (150, 300, 600)
- Skip PNG conversion (metadata only)
- Verify TOC only (no processing)
- Filter by specific section
- Real-time progress tracking
- Download metadata JSON
- Download report TXT
- Download all outputs as ZIP

**Workflow:**
1. Upload CAFR PDF
2. Upload TOC screenshot(s)
3. Configure options (DPI, skip PNG, etc.)
4. Click "Process CAFR"
5. View results and download outputs

### Page 2: Batch Processing

Process multiple CAFRs for a single city.

**Two Input Methods:**

**Method 1: Upload YAML Config**
- Upload existing YAML configuration file
- Preview config before processing
- Process all years automatically

**Method 2: Build Config Manually**
- Enter city name and state
- Specify number of CAFRs
- Upload PDF + TOC for each year
- Auto-generate configuration

**Capabilities:**
- Process 1-50 CAFRs in sequence
- Generate master index (JSON)
- Generate comparative report (TXT)
- Year-by-year progress tracking
- Download individual year outputs
- Download batch ZIP with all years

**Workflow:**
1. Upload YAML config OR build manually
2. Configure batch options
3. Click "Process All CAFRs"
4. Monitor per-CAFR progress
5. Download master index and comparative report

### Page 3: Verification

**Status:** Coming soon

Will provide:
- Upload processed output ZIP
- Verify metadata completeness
- Check for missing pages
- Validate file integrity
- Suggest corrections

**Current Workaround:** Use CLI verification tools (see page for examples)

---

## User Guide

### Processing Your First CAFR

**Step 1: Prepare Your Files**

Before opening the web interface, prepare:

1. **CAFR PDF file** - The municipal report you want to process
   - File size: Typically 10-100 MB
   - Pages: Usually 200-400 pages
   - Example: `vallejo_cafr_2024.pdf`

2. **TOC screenshot(s)** - Screenshot of the table of contents
   - Format: PNG or JPG
   - Size: Full screen recommended
   - Multiple files OK if TOC spans multiple pages
   - Example: `vallejo_2024_toc.png`

**How to take TOC screenshots:**
- Open PDF in your PDF viewer
- Navigate to Table of Contents (usually pages ii-v)
- Take screenshot:
  - **macOS:** `Cmd+Shift+4` (drag to select)
  - **Windows:** `Win+Shift+S`
  - **Linux:** `Shift+PrtScn`
- Save as PNG

**Step 2: Launch Web Interface**

```bash
source venv/bin/activate
streamlit run web_ui.py
```

Browser will open to http://localhost:8501

**Step 3: Upload Files**

1. Click "Browse files" under "Upload CAFR PDF"
2. Select your PDF file
3. Click "Browse files" under "Upload TOC Screenshots"
4. Select your TOC screenshot(s)

**Step 4: Configure Options**

- **DPI:** 300 recommended (balance of quality and size)
  - 150 DPI: Faster, smaller files (~150 MB for 300 pages)
  - 300 DPI: Standard quality (~750 MB for 300 pages)
  - 600 DPI: High quality, large files (~3 GB for 300 pages)

- **Skip PNG Conversion:** Check to generate only metadata (fast, ~30 seconds)

- **Verify TOC Only:** Check to just preview TOC without processing

**Step 5: Process**

1. Click "🚀 Process CAFR" button
2. Wait for progress bar to complete (~5 minutes for 300-page PDF at 300 DPI)
3. View results summary

**Step 6: Download Results**

Three download options:

1. **Metadata (JSON)** - Complete page index and statistics
2. **Report (TXT)** - Human-readable processing summary
3. **All Outputs (ZIP)** - Complete output including all PNG files

---

### Batch Processing Multiple Years

**Scenario:** Process 5 years of Vallejo CAFRs (2020-2024)

**Option A: Using YAML Config**

1. Create `vallejo_batch.yaml`:

```yaml
city_name: "Vallejo"
state: "CA"
output_base: "../output/vallejo"

cafrs:
  - year: 2024
    pdf: "../pdfs/vallejo_cafr_2024.pdf"
    toc_screenshots:
      - "../toc_screenshots/vallejo_2024_toc.png"

  - year: 2023
    pdf: "../pdfs/vallejo_cafr_2023.pdf"
    toc_screenshots:
      - "../toc_screenshots/vallejo_2023_toc.png"

  - year: 2022
    pdf: "../pdfs/vallejo_cafr_2022.pdf"
    toc_screenshots:
      - "../toc_screenshots/vallejo_2022_toc.png"

  # ... additional years
```

2. Navigate to "Batch Processing" page
3. Select "Upload YAML Config"
4. Upload `vallejo_batch.yaml`
5. Configure options (DPI, skip PNG)
6. Click "🚀 Process All CAFRs"

**Option B: Building Config Manually**

1. Navigate to "Batch Processing" page
2. Select "Build Config Manually"
3. Enter city name: "Vallejo"
4. Enter state: "CA"
5. Set number of CAFRs: 5
6. For each CAFR:
   - Enter year (2024, 2023, 2022, 2021, 2020)
   - Upload PDF file
   - Upload TOC screenshot(s)
7. Configure options
8. Click "🚀 Process All CAFRs"

**Results:**

After processing completes, you'll get:

- **Master Index (JSON)** - Combined metadata for all years
- **Comparative Report (TXT)** - Year-by-year comparison
- **Individual year outputs** - Separate directories for each year
- **Batch ZIP** - All outputs packaged together

---

## Troubleshooting

### Web Interface Won't Start

**Problem:** `streamlit: command not found`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Install web dependencies
pip install -r requirements_web.txt
```

---

**Problem:** `ModuleNotFoundError: No module named 'ibco_stripper'`

**Solution:**
```bash
# Run from the project root directory
cd ~/cafr_pdf_stripper
streamlit run web_ui.py
```

---

### Upload Fails

**Problem:** File upload stuck at 0% or fails

**Solution:**
```bash
# Increase max upload size (default: 200 MB)
streamlit run web_ui.py --server.maxUploadSize 500
```

Or create `.streamlit/config.toml`:

```toml
[server]
maxUploadSize = 500
```

---

**Problem:** "File too large" error

**Solution:**
- Check PDF file size (should be < 200 MB by default)
- Increase max upload size (see above)
- Or use CLI for very large files

---

### Processing Errors

**Problem:** "Error processing CAFR: PDF file not found"

**Solution:**
- Files are temporarily stored - should be automatic
- Try refreshing the page and re-uploading
- Check browser console for errors

---

**Problem:** Processing hangs or takes too long

**Solution:**
- Lower DPI setting (try 150 instead of 300)
- Enable "Skip PNG Conversion" for metadata only
- Use CLI for very large PDFs (500+ pages)

---

**Problem:** Out of memory error

**Solution:**
```bash
# Close other applications
# Or use CLI with --workers flag to reduce parallelism
python ibco_stripper.py --pdf cafr.pdf --toc toc.png --output out/ --workers 4
```

---

### Download Issues

**Problem:** ZIP download fails or is incomplete

**Solution:**
- Smaller batches - process fewer years at once
- Download individual files instead of ZIP
- Check available disk space
- Use CLI for very large batches

---

## Comparison: Web UI vs CLI

| Feature | Web UI | CLI |
|---------|--------|-----|
| **Ease of Use** | ✅ Very easy, no commands | ⚠️ Requires command knowledge |
| **File Upload** | ✅ Drag-and-drop | ⚠️ Manual file paths |
| **Progress Tracking** | ✅ Visual progress bar | ⚠️ Text output only |
| **Download Results** | ✅ One-click download | ⚠️ Manual file copying |
| **Batch Processing** | ✅ Upload or build config | ✅ YAML config required |
| **Large Files (>500 pages)** | ⚠️ May struggle | ✅ Better performance |
| **Automation** | ❌ Manual uploads | ✅ Scriptable |
| **Resource Usage** | ⚠️ Higher (web server overhead) | ✅ Lower |
| **Multi-User** | ❌ Single user only | N/A |
| **Remote Access** | ✅ Can be configured | ❌ Local only |

**Recommendation:**
- **Web UI:** Best for occasional use, single CAFRs, visual feedback
- **CLI:** Best for automation, large batches, scripting, lower resource usage

**Both interfaces use the same backend** - choose based on your preference!

---

## Advanced Configuration

### Streamlit Configuration

Create `.streamlit/config.toml` in project root:

```toml
[server]
port = 8501
maxUploadSize = 500
enableXsrfProtection = true
enableCORS = false

[browser]
gatherUsageStats = false
serverAddress = "localhost"
serverPort = 8501

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Custom Styling

Modify the CSS in `web_ui.py`:

```python
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;  /* Change this color */
    }
</style>
""", unsafe_allow_html=True)
```

---

## Security Considerations

**⚠️ Important: This web interface is designed for local, single-user use.**

**Do NOT expose to the internet without:**
1. Adding authentication (e.g., HTTP basic auth via reverse proxy)
2. Using HTTPS (SSL/TLS)
3. Restricting file upload sizes
4. Sanitizing file inputs
5. Rate limiting

**For production deployment, consider:**
- nginx reverse proxy with authentication
- SSL certificate (Let's Encrypt)
- Firewall rules
- User access controls

---

## Support

**Issues with web interface?**

1. Check this README first
2. Check [INSTALL.md](INSTALL.md) for base installation issues
3. Check [README.md](README.md) for general usage
4. Submit issue: https://github.com/BrandonCarranza/cafr_pdf_stripper/issues

**Questions about CAFR processing?**

See [DEMO.md](DEMO.md) for workflow examples and [README.md](README.md) for detailed documentation.

---

## License

Same as main project: **Unlicense (Public Domain)**

This web interface is part of the IBCo CAFR PDF Stripper and is released to the public domain.

---

**Built for transparency. Made with Streamlit and Claude Code.**

*IBCo - Making municipal financial data accessible to all citizens.*
