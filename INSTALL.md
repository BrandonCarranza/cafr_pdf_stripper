# Installation Guide

## Quick Install (Recommended)

Run the automated setup script:

```bash
./setup.sh
```

This will:
- ✅ Check system requirements
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Set up workspace directories
- ✅ Run verification tests
- ✅ Display usage instructions

## Custom Workspace Location

```bash
./setup.sh --workspace /path/to/your/workspace
```

## System Requirements

### Required

- **Python 3.11+** (Python 3.12 recommended)
- **poppler-utils** - For PDF to image conversion
- **tesseract-ocr** - For OCR of TOC screenshots

### Recommended

- **8GB RAM minimum** (16GB+ for large PDFs)
- **10GB free disk space** (for output files)
- **Multi-core CPU** (for parallel PNG conversion)

## Manual Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv poppler-utils tesseract-ocr
```

**macOS (Homebrew):**
```bash
brew install python@3.12 poppler tesseract
```

**Fedora/RHEL:**
```bash
sudo dnf install python3.12 python3-virtualenv poppler-utils tesseract
```

### 2. Create Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create Workspace Directory

```bash
mkdir -p ~/workspace/ibco/{pdfs,toc_screenshots,output,config}
```

### 5. Verify Installation

```bash
python tests/run_all_tests.py
python -c "import ibco_stripper; print('OK')"
```

## Troubleshooting

### Python Version Issues

If you get "Python 3.11+ not found":
- Install Python 3.12 or higher
- Ensure it's in your PATH
- Try `python3.12` instead of `python3`

### poppler-utils Not Found

**Error:** `pdf2image` fails with "pdftoppm not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler

# Verify
pdftoppm -v
```

### tesseract Not Found

**Error:** `pytesseract` fails with "tesseract not found"

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Verify
tesseract --version
```

### Memory Issues

If processing fails with memory errors:
- Reduce DPI: Use `--dpi 150` instead of 300
- Process sections individually: Use `--section "Section Name"`
- Enable skip-png mode: Use `--skip-png` to generate only metadata
- Increase system RAM or swap space

### Permission Errors

If you get permission errors:
```bash
chmod +x setup.sh
chmod +x activate_cafr.sh
```

## Verifying Installation

### Quick Check

```bash
python -c "from ibco_stripper import PDFStripper; print('✓ Installation successful')"
```

### Run Test Suite

```bash
python tests/run_all_tests.py
```

### Test Individual Components

```bash
# Test PDF reading
python test_pdf_reading.py

# Test TOC loading
python test_toc_loading.py

# Test PNG conversion
python test_png_conversion.py

# Test full workflow
python test_workflow.py
```

## Uninstalling

To remove the installation:

```bash
# Remove virtual environment
rm -rf venv

# Remove workspace (CAUTION: This deletes your data!)
rm -rf ~/workspace/ibco

# Remove convenience scripts
rm -f activate_cafr.sh
```

## Next Steps

After installation:

1. **Read the README**: `cat README.md`
2. **View workflow**: `cat WORKFLOW_VISUAL.md`
3. **Activate environment**: `source venv/bin/activate`
4. **Process your first CAFR**: See README.md for examples

## Getting Help

- 📖 **Documentation**: See README.md and WORKFLOW_VISUAL.md
- 🧪 **Tests**: See tests/README.md
- 🐛 **Issues**: Check error messages and logs
- 💬 **Support**: Review CLAUDE_CODE_PROMPTS.md for implementation details

## Development Setup

For contributors:

```bash
# Clone repository
git clone <repository-url>
cd cafr_pdf_stripper

# Run setup
./setup.sh

# Run all tests
python tests/run_all_tests.py

# Install development dependencies (if needed)
pip install pytest pytest-cov black mypy
```

## System-Specific Notes

### AMD Threadripper 3970X (Target System)

This tool is optimized for:
- 32 cores / 64 threads
- 256GB RAM
- High-speed NVMe storage

For this system:
- Use maximum DPI (600) for best quality
- Enable parallel processing (default: 16 workers)
- Process multiple cities simultaneously

### Lower-Spec Systems

For systems with 8GB RAM or less:
- Use `--dpi 150` for smaller files
- Use `--skip-png` to generate only metadata
- Process one CAFR at a time
- Use `--section` to process sections individually

## Updating

To update to the latest version:

```bash
git pull origin main
pip install --upgrade -r requirements.txt
python tests/run_all_tests.py
```
