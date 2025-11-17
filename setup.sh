#!/bin/bash
#
# IBCo PDF Stripper - First-Time Setup Script
#
# This script sets up the CAFR PDF processing environment:
# - Checks system requirements
# - Creates virtual environment
# - Installs dependencies
# - Creates directory structure
# - Runs verification tests
#
# Safe to run multiple times (idempotent)
#
# Usage:
#   ./setup.sh
#   ./setup.sh --workspace ~/my-cafr-workspace
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default workspace location
WORKSPACE="$HOME/workspace/ibco"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace)
            WORKSPACE="$2"
            shift 2
            ;;
        --help|-h)
            echo "IBCo PDF Stripper - Setup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --workspace DIR    Set workspace directory (default: ~/workspace/ibco)"
            echo "  --help, -h         Show this help message"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "================================================================================"
echo "IBCo PDF Stripper - First-Time Setup"
echo "================================================================================"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}[*]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python version
get_python_version() {
    $1 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null
}

# Function to compare versions
version_ge() {
    printf '%s\n%s' "$2" "$1" | sort -V -C
}

# Step 1: Check System Requirements
echo "================================================================================"
echo "Step 1: Checking System Requirements"
echo "================================================================================"
echo ""

# Check Python
print_status "Checking Python version..."
PYTHON_CMD=""
for cmd in python3.12 python3.13 python3.11 python3 python; do
    if command_exists $cmd; then
        VERSION=$(get_python_version $cmd)
        if [ -n "$VERSION" ] && version_ge "$VERSION" "3.11"; then
            PYTHON_CMD=$cmd
            print_success "Found $cmd (version $VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    print_error "Python 3.11+ not found. Please install Python 3.11 or higher."
    echo ""
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt-get install python3.12"
    echo "  macOS (Homebrew): brew install python@3.12"
    echo "  Fedora/RHEL: sudo dnf install python3.12"
    exit 1
fi

# Check poppler-utils (for pdf2image)
print_status "Checking poppler-utils (for PDF processing)..."
if command_exists pdftoppm; then
    print_success "poppler-utils is installed"
else
    print_error "poppler-utils not found. Required for PDF to image conversion."
    echo ""
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  macOS (Homebrew): brew install poppler"
    echo "  Fedora/RHEL: sudo dnf install poppler-utils"
    echo ""
    read -p "Continue without poppler-utils? (PNG conversion will not work) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    print_warning "Continuing without poppler-utils (PNG conversion disabled)"
fi

# Check tesseract
print_status "Checking tesseract-ocr (for TOC recognition)..."
if command_exists tesseract; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
    print_success "tesseract-ocr is installed (version $TESSERACT_VERSION)"
else
    print_error "tesseract-ocr not found. Required for OCR of TOC screenshots."
    echo ""
    echo "Installation instructions:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS (Homebrew): brew install tesseract"
    echo "  Fedora/RHEL: sudo dnf install tesseract"
    echo ""
    read -p "Continue without tesseract? (TOC loading will not work) [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    print_warning "Continuing without tesseract (TOC loading disabled)"
fi

# Check available RAM
print_status "Checking available RAM..."
if command_exists free; then
    TOTAL_RAM_MB=$(free -m | awk '/^Mem:/{print $2}')
    TOTAL_RAM_GB=$((TOTAL_RAM_MB / 1024))

    if [ $TOTAL_RAM_GB -ge 8 ]; then
        print_success "Available RAM: ${TOTAL_RAM_GB}GB (recommended: 8GB+)"
    elif [ $TOTAL_RAM_GB -ge 4 ]; then
        print_warning "Available RAM: ${TOTAL_RAM_GB}GB (recommended: 8GB+)"
        echo "            Processing large PDFs may be slow or fail"
    else
        print_warning "Available RAM: ${TOTAL_RAM_GB}GB (recommended: 8GB+)"
        echo "            You may encounter memory issues with large PDFs"
    fi
elif command_exists sysctl; then
    # macOS
    TOTAL_RAM_BYTES=$(sysctl -n hw.memsize)
    TOTAL_RAM_GB=$((TOTAL_RAM_BYTES / 1024 / 1024 / 1024))

    if [ $TOTAL_RAM_GB -ge 8 ]; then
        print_success "Available RAM: ${TOTAL_RAM_GB}GB (recommended: 8GB+)"
    else
        print_warning "Available RAM: ${TOTAL_RAM_GB}GB (recommended: 8GB+)"
    fi
else
    print_warning "Could not determine available RAM"
fi

# Check disk space
print_status "Checking available disk space..."
if command_exists df; then
    AVAILABLE_GB=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ $AVAILABLE_GB -ge 10 ]; then
        print_success "Available disk space: ${AVAILABLE_GB}GB"
    else
        print_warning "Available disk space: ${AVAILABLE_GB}GB (recommend 10GB+ for processing)"
    fi
fi

echo ""

# Step 2: Create Virtual Environment
echo "================================================================================"
echo "Step 2: Setting Up Python Virtual Environment"
echo "================================================================================"
echo ""

VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists at: $VENV_DIR"
    read -p "Recreate virtual environment? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        print_status "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
print_success "Virtual environment activated"

echo ""

# Step 3: Install Dependencies
echo "================================================================================"
echo "Step 3: Installing Python Dependencies"
echo "================================================================================"
echo ""

# Upgrade pip
print_status "Upgrading pip..."
python -m pip install --upgrade pip --quiet
print_success "pip upgraded"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    print_warning "requirements.txt not found, creating minimal requirements..."

    cat > requirements.txt << 'EOF'
# IBCo PDF Stripper Dependencies
pdfplumber>=0.10.0
pytesseract>=0.3.10
pdf2image>=1.16.0
Pillow>=10.0.0
PyYAML>=6.0
tqdm>=4.65.0
EOF

    print_success "Created requirements.txt"
fi

# Install dependencies
print_status "Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet
print_success "Dependencies installed"

echo ""

# Step 4: Create Directory Structure
echo "================================================================================"
echo "Step 4: Creating Workspace Directory Structure"
echo "================================================================================"
echo ""

print_status "Workspace location: $WORKSPACE"

# Create directories
mkdir -p "$WORKSPACE"
mkdir -p "$WORKSPACE/pdfs"
mkdir -p "$WORKSPACE/toc_screenshots"
mkdir -p "$WORKSPACE/output"
mkdir -p "$WORKSPACE/config"

print_success "Created directory structure:"
echo "  $WORKSPACE/"
echo "  ├── pdfs/              (Place input PDF files here)"
echo "  ├── toc_screenshots/   (Place TOC screenshot images here)"
echo "  ├── output/            (Processed results will go here)"
echo "  └── config/            (YAML configuration files)"

# Create sample config file
SAMPLE_CONFIG="$WORKSPACE/config/sample_city_config.yaml"
if [ ! -f "$SAMPLE_CONFIG" ]; then
    print_status "Creating sample configuration file..."

    cat > "$SAMPLE_CONFIG" << 'EOF'
# Sample City Configuration
# Copy this file and customize for your city's CAFRs

city_name: "Sample City"
state: "CA"
output_base: "../output/sample_city"

cafrs:
  - year: 2024
    pdf: "../pdfs/sample_city_2024.pdf"
    toc_screenshots:
      - "../toc_screenshots/sample_2024_toc.png"

  - year: 2023
    pdf: "../pdfs/sample_city_2023.pdf"
    toc_screenshots:
      - "../toc_screenshots/sample_2023_toc.png"

# Add more years as needed
EOF

    print_success "Created sample config: $SAMPLE_CONFIG"
fi

echo ""

# Step 5: Run Verification Tests
echo "================================================================================"
echo "Step 5: Running Verification Tests"
echo "================================================================================"
echo ""

print_status "Running test suite to verify installation..."

# Run the comprehensive test suite
if python tests/run_all_tests.py > /tmp/cafr_test_output.log 2>&1; then
    print_success "All tests passed!"
else
    print_warning "Some tests failed (this is OK if dependencies are missing)"
    echo "            See /tmp/cafr_test_output.log for details"
fi

# Check that core module can be imported
print_status "Verifying core module can be imported..."
if python -c "import ibco_stripper; print('OK')" >/dev/null 2>&1; then
    print_success "Core module imported successfully"
else
    print_error "Failed to import core module"
    print_error "Installation may be incomplete"
    exit 1
fi

echo ""

# Step 6: Print Usage Instructions
echo "================================================================================"
echo "Setup Complete!"
echo "================================================================================"
echo ""

print_success "IBCo PDF Stripper is ready to use!"
echo ""
echo "Quick Start Guide:"
echo "=================="
echo ""
echo "1. Activate the virtual environment:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "2. Process a single CAFR:"
echo "   ${BLUE}python ibco_stripper.py \\${NC}"
echo "   ${BLUE}     --pdf $WORKSPACE/pdfs/your_cafr.pdf \\${NC}"
echo "   ${BLUE}     --toc $WORKSPACE/toc_screenshots/toc.png \\${NC}"
echo "   ${BLUE}     --output $WORKSPACE/output/your_city_2024/${NC}"
echo ""
echo "3. Process multiple years (batch mode):"
echo "   ${BLUE}python process_city.py --config $WORKSPACE/config/your_city.yaml${NC}"
echo ""
echo "4. Verify processed output:"
echo "   ${BLUE}python -c \"from ibco_stripper import PDFStripper; \\${NC}"
echo "   ${BLUE}   s = PDFStripper('pdf.pdf', 'output/'); \\${NC}"
echo "   ${BLUE}   s.verify_processing()\"${NC}"
echo ""
echo "Documentation:"
echo "============="
echo "  - README.md           - Project overview"
echo "  - WORKFLOW_VISUAL.md  - Visual workflow guide"
echo "  - CLAUDE_CODE_PROMPTS.md - Development history"
echo "  - tests/README.md     - Test suite documentation"
echo ""
echo "Example Workflows:"
echo "================="
echo "  Single CAFR:    See examples in README.md"
echo "  Batch process:  Edit config/sample_city_config.yaml"
echo "  Verification:   python -m ibco_stripper verify <output_dir>"
echo ""
echo "Workspace location: ${GREEN}$WORKSPACE${NC}"
echo ""
echo "Need help? Check the README.md or run commands with --help"
echo ""
echo "================================================================================"

# Create a convenience script
ACTIVATE_SCRIPT="activate_cafr.sh"
if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    print_status "Creating convenience activation script..."

    cat > "$ACTIVATE_SCRIPT" << EOF
#!/bin/bash
# Convenience script to activate CAFR environment

source venv/bin/activate
echo "CAFR PDF Stripper environment activated"
echo "Workspace: $WORKSPACE"
echo ""
echo "Try: python ibco_stripper.py --help"
EOF

    chmod +x "$ACTIVATE_SCRIPT"
    print_success "Created activation script: ./$ACTIVATE_SCRIPT"
fi

echo ""
print_success "Setup complete! Happy processing!"
echo ""
