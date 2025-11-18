#!/usr/bin/env python3
"""
IBCo CAFR PDF Stripper - Web Interface

Streamlit-based web interface for processing CAFR PDFs.
Provides three modes:
1. Single CAFR Processing
2. Batch Processing
3. Verification

Built for the IBCo (Independent Budget & Capital Operations) transparency initiative.
"""

import streamlit as st
import tempfile
import shutil
import json
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import sys
import os

# Import backend modules
from ibco_stripper import PDFStripper
from process_city import load_config, generate_master_index, generate_comparative_report

# Configure Streamlit page
st.set_page_config(
    page_title="IBCo CAFR Processor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'results' not in st.session_state:
    st.session_state.results = None
if 'output_dir' not in st.session_state:
    st.session_state.output_dir = None
if 'batch_results' not in st.session_state:
    st.session_state.batch_results = None


# ==============================================================================
# Helper Functions
# ==============================================================================

def save_uploaded_file(uploaded_file, target_dir: Path) -> Path:
    """
    Save uploaded file to temporary directory.

    Args:
        uploaded_file: Streamlit UploadedFile object
        target_dir: Directory to save file in

    Returns:
        Path to saved file
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / uploaded_file.name

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return file_path


def create_zip_from_directory(directory: Path, zip_name: str) -> io.BytesIO:
    """
    Create a ZIP file from a directory.

    Args:
        directory: Directory to zip
        zip_name: Name for the zip file

    Returns:
        BytesIO object containing the ZIP
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(directory.parent)
                zipf.write(file_path, arcname)

    zip_buffer.seek(0)
    return zip_buffer


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


# ==============================================================================
# Page 1: Single CAFR Processing
# ==============================================================================

def page_single_cafr():
    """Single CAFR processing page."""
    st.markdown('<p class="main-header">📄 Process Single CAFR</p>', unsafe_allow_html=True)

    st.markdown("""
    Process a single municipal CAFR PDF. This will:
    1. Load TOC from your screenshot(s)
    2. Extract page numbers from PDF footers
    3. Map pages to sections
    4. Convert pages to PNG files (optional)
    5. Generate metadata and reports
    """)

    # File upload section
    st.markdown('<p class="section-header">1. Upload Files</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        pdf_file = st.file_uploader(
            "Upload CAFR PDF",
            type=['pdf'],
            help="Select the municipal CAFR PDF file to process"
        )

    with col2:
        toc_files = st.file_uploader(
            "Upload TOC Screenshots (PNG/JPG)",
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="Upload screenshot(s) of the table of contents. Can upload multiple if TOC spans several pages."
        )

    # Processing options
    st.markdown('<p class="section-header">2. Processing Options</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        dpi = st.selectbox(
            "PNG Resolution (DPI)",
            options=[150, 300, 600],
            index=1,
            help="Higher DPI = better quality but larger files. 300 is recommended."
        )

    with col2:
        skip_png = st.checkbox(
            "Skip PNG Conversion",
            value=False,
            help="Only generate metadata and reports, skip PNG conversion (faster)"
        )

    with col3:
        verify_only = st.checkbox(
            "Verify TOC Only",
            value=False,
            help="Only load and verify TOC, don't process the full PDF"
        )

    # Advanced options (collapsible)
    with st.expander("Advanced Options"):
        section_filter = st.text_input(
            "Process Specific Section Only (optional)",
            value="",
            help="Enter section name to process only that section (e.g., 'Financial Section')"
        )

    # Process button
    st.markdown('<p class="section-header">3. Process CAFR</p>', unsafe_allow_html=True)

    if st.button("🚀 Process CAFR", type="primary", use_container_width=True):
        # Validate inputs
        if not pdf_file:
            st.error("❌ Please upload a PDF file")
            return

        if not toc_files:
            st.error("❌ Please upload at least one TOC screenshot")
            return

        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Save uploaded files
            with st.spinner("Saving uploaded files..."):
                pdf_path = save_uploaded_file(pdf_file, temp_path)

                toc_paths = []
                for toc_file in toc_files:
                    toc_path = save_uploaded_file(toc_file, temp_path / "toc")
                    toc_paths.append(str(toc_path))

            # Create output directory
            output_dir = temp_path / "output"
            output_dir.mkdir(parents=True, exist_ok=True)

            # Process CAFR
            try:
                # Initialize stripper
                with st.spinner("Initializing PDF processor..."):
                    stripper = PDFStripper(str(pdf_path), str(output_dir))

                # Capture stdout for progress messages
                progress_placeholder = st.empty()
                status_placeholder = st.empty()

                # Create progress bar
                progress_bar = st.progress(0)

                # Process with auto_confirm=True (no interactive prompts)
                with st.spinner("Processing CAFR..."):
                    # Update progress
                    progress_bar.progress(10)
                    status_placeholder.info("📖 Loading TOC from screenshots...")

                    section_param = section_filter if section_filter else None

                    results = stripper.process_cafr(
                        toc_screenshots=toc_paths,
                        dpi=dpi,
                        skip_png=skip_png,
                        section=section_param,
                        verify_only=verify_only,
                        auto_confirm=True  # No interactive prompts in web UI
                    )

                    progress_bar.progress(100)

                # Store results in session state
                st.session_state.processing_complete = True
                st.session_state.results = results
                st.session_state.output_dir = output_dir

                # Display results
                display_single_cafr_results(results, output_dir, pdf_file.name)

            except Exception as e:
                st.error(f"❌ Error processing CAFR: {str(e)}")
                st.exception(e)
                return

    # Display previous results if available
    elif st.session_state.processing_complete and st.session_state.results:
        st.info("📋 Showing results from previous processing")
        display_single_cafr_results(
            st.session_state.results,
            st.session_state.output_dir,
            "previous_cafr.pdf"
        )


def display_single_cafr_results(results: Dict[str, Any], output_dir: Path, pdf_name: str):
    """Display processing results for single CAFR."""
    st.markdown('<p class="section-header">4. Results</p>', unsafe_allow_html=True)

    status = results.get('status', 'unknown')

    if status == 'cancelled':
        st.warning("⚠️ Processing was cancelled")
        return

    if status == 'verified_only':
        st.success("✅ TOC verification complete")
        st.json(results)
        return

    if status == 'complete':
        st.success("✅ Processing complete!")

        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Pages", results.get('total_pages', 'N/A'))

        with col2:
            st.metric("TOC Entries", results.get('toc_entries', 'N/A'))

        with col3:
            sections = results.get('page_index', [])
            unique_sections = len(set(p.get('section_name') for p in sections if p.get('section_name')))
            st.metric("Sections", unique_sections)

        with col4:
            png_count = results.get('png_files_created', 0)
            st.metric("PNG Files", png_count)

        # Display detailed results
        with st.expander("📊 Detailed Statistics", expanded=True):
            st.json(results)

        # Download section
        st.markdown('<p class="section-header">5. Download Results</p>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        # Download metadata JSON
        with col1:
            metadata_file = output_dir / "cafr_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata_json = f.read()

                st.download_button(
                    label="📥 Download Metadata (JSON)",
                    data=metadata_json,
                    file_name="cafr_metadata.json",
                    mime="application/json"
                )

        # Download report TXT
        with col2:
            report_file = output_dir / "cafr_report.txt"
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report_txt = f.read()

                st.download_button(
                    label="📥 Download Report (TXT)",
                    data=report_txt,
                    file_name="cafr_report.txt",
                    mime="text/plain"
                )

        # Download all outputs as ZIP
        with col3:
            if st.button("📦 Prepare ZIP Download"):
                with st.spinner("Creating ZIP file..."):
                    zip_buffer = create_zip_from_directory(output_dir, "cafr_output")

                st.download_button(
                    label="📥 Download All Outputs (ZIP)",
                    data=zip_buffer,
                    file_name=f"cafr_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )

        # Display report preview
        if report_file.exists():
            with st.expander("📄 Report Preview"):
                with open(report_file, 'r') as f:
                    st.text(f.read())


# ==============================================================================
# Page 2: Batch Processing
# ==============================================================================

def page_batch_processing():
    """Batch processing page for multiple CAFRs."""
    st.markdown('<p class="main-header">📚 Batch Process Multiple CAFRs</p>', unsafe_allow_html=True)

    st.markdown("""
    Process multiple CAFRs at once using a YAML configuration file.
    This is ideal for processing multiple years for a single city.
    """)

    # Choose input method
    st.markdown('<p class="section-header">1. Configuration</p>', unsafe_allow_html=True)

    input_method = st.radio(
        "Choose configuration method:",
        options=["Upload YAML Config", "Build Config Manually"],
        horizontal=True
    )

    config_data = None
    config_path = None

    if input_method == "Upload YAML Config":
        st.markdown("**Upload YAML Configuration File**")

        config_file = st.file_uploader(
            "Upload YAML Config",
            type=['yaml', 'yml'],
            help="Upload a YAML configuration file with CAFR details"
        )

        if config_file:
            # Show config preview
            config_content = config_file.read().decode('utf-8')

            with st.expander("📄 Configuration Preview"):
                st.code(config_content, language='yaml')

            # Save config temporarily
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write(config_content)
                config_path = f.name

            try:
                config_data = load_config(config_path)
            except Exception as e:
                st.error(f"❌ Invalid configuration file: {str(e)}")
                return

    else:  # Build config manually
        st.markdown("**Build Configuration Manually**")

        col1, col2 = st.columns(2)

        with col1:
            city_name = st.text_input("City Name", value="Vallejo")
            state = st.text_input("State", value="CA")

        with col2:
            num_cafrs = st.number_input("Number of CAFRs", min_value=1, max_value=50, value=2)

        # Collect CAFR details
        cafrs = []

        for i in range(num_cafrs):
            st.markdown(f"**CAFR {i+1}**")

            col1, col2, col3 = st.columns(3)

            with col1:
                year = st.number_input(f"Year", min_value=1900, max_value=2100, value=2024-i, key=f"year_{i}")

            with col2:
                pdf = st.file_uploader(f"PDF File", type=['pdf'], key=f"pdf_{i}")

            with col3:
                toc = st.file_uploader(f"TOC Screenshot(s)", type=['png', 'jpg'], accept_multiple_files=True, key=f"toc_{i}")

            if pdf and toc:
                cafrs.append({
                    'year': year,
                    'pdf': pdf,
                    'toc_screenshots': toc
                })

            st.markdown("---")

        if cafrs:
            config_data = {
                'city_name': city_name,
                'state': state,
                'cafrs': cafrs
            }

    # Processing options
    if config_data:
        st.markdown('<p class="section-header">2. Processing Options</p>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            dpi = st.selectbox(
                "PNG Resolution (DPI)",
                options=[150, 300, 600],
                index=1
            )

        with col2:
            skip_png = st.checkbox("Skip PNG Conversion", value=False)

        # Process button
        st.markdown('<p class="section-header">3. Process Batch</p>', unsafe_allow_html=True)

        if st.button("🚀 Process All CAFRs", type="primary", use_container_width=True):
            process_batch(config_data, config_path, dpi, skip_png)

    # Display previous batch results if available
    if st.session_state.batch_results:
        st.info("📋 Showing results from previous batch processing")
        display_batch_results(st.session_state.batch_results)


def process_batch(config_data: Dict[str, Any], config_path: Optional[str], dpi: int, skip_png: bool):
    """Process batch of CAFRs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_base = temp_path / "output"
        output_base.mkdir(parents=True, exist_ok=True)

        city_name = config_data['city_name']
        state = config_data.get('state', '')
        cafrs = config_data['cafrs']

        st.info(f"Processing {len(cafrs)} CAFRs for {city_name}, {state}")

        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()

        results = []
        successful = 0
        failed = 0

        # Process each CAFR
        for i, cafr_config in enumerate(cafrs):
            year = cafr_config['year']

            progress_bar.progress((i) / len(cafrs))
            status_text.text(f"Processing {year} ({i+1}/{len(cafrs)})...")

            # Create year output directory
            year_output = output_base / str(year)
            year_output.mkdir(parents=True, exist_ok=True)

            try:
                # Handle file uploads if from manual config
                if isinstance(cafr_config.get('pdf'), st.runtime.uploaded_file_manager.UploadedFile):
                    pdf_path = save_uploaded_file(cafr_config['pdf'], temp_path / f"pdfs/{year}")

                    toc_paths = []
                    for toc_file in cafr_config['toc_screenshots']:
                        toc_path = save_uploaded_file(toc_file, temp_path / f"toc/{year}")
                        toc_paths.append(str(toc_path))
                else:
                    pdf_path = cafr_config['pdf']
                    toc_paths = cafr_config['toc_screenshots']

                # Process CAFR
                stripper = PDFStripper(str(pdf_path), str(year_output))

                summary = stripper.process_cafr(
                    toc_screenshots=toc_paths,
                    dpi=dpi,
                    skip_png=skip_png,
                    auto_confirm=True
                )

                summary['year'] = year
                results.append(summary)

                if summary['status'] == 'complete':
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                st.error(f"Error processing {year}: {str(e)}")
                results.append({
                    'year': year,
                    'status': 'error',
                    'error': str(e)
                })
                failed += 1

        progress_bar.progress(100)
        status_text.text("Generating master index and comparative report...")

        # Generate master index
        master_index_path = generate_master_index(city_name, state, results, output_base)

        # Generate comparative report
        comparative_report_path = generate_comparative_report(city_name, state, results, output_base)

        # Store results
        batch_summary = {
            'city_name': city_name,
            'state': state,
            'total_cafrs': len(cafrs),
            'successful': successful,
            'failed': failed,
            'results': results,
            'output_base': output_base,
            'master_index_path': master_index_path,
            'comparative_report_path': comparative_report_path
        }

        st.session_state.batch_results = batch_summary

        # Display results
        display_batch_results(batch_summary)


def display_batch_results(batch_summary: Dict[str, Any]):
    """Display batch processing results."""
    st.markdown('<p class="section-header">Results</p>', unsafe_allow_html=True)

    st.success(f"✅ Batch processing complete!")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("City", batch_summary['city_name'])

    with col2:
        st.metric("Total CAFRs", batch_summary['total_cafrs'])

    with col3:
        st.metric("Successful", batch_summary['successful'])

    with col4:
        st.metric("Failed", batch_summary['failed'])

    # Year-by-year results
    with st.expander("📊 Year-by-Year Results", expanded=True):
        for result in batch_summary['results']:
            year = result.get('year')
            status = result.get('status')

            if status == 'complete':
                st.success(f"✅ {year}: {result.get('total_pages', 'N/A')} pages processed")
            else:
                error = result.get('error', 'Unknown error')
                st.error(f"❌ {year}: {error}")

    # Download section
    st.markdown('<p class="section-header">Download Results</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    # Download master index
    with col1:
        master_index_path = batch_summary.get('master_index_path')
        if master_index_path and Path(master_index_path).exists():
            with open(master_index_path, 'r') as f:
                master_index_json = f.read()

            st.download_button(
                label="📥 Master Index (JSON)",
                data=master_index_json,
                file_name="master_index.json",
                mime="application/json"
            )

    # Download comparative report
    with col2:
        comparative_report_path = batch_summary.get('comparative_report_path')
        if comparative_report_path and Path(comparative_report_path).exists():
            with open(comparative_report_path, 'r') as f:
                comparative_report_txt = f.read()

            st.download_button(
                label="📥 Comparative Report (TXT)",
                data=comparative_report_txt,
                file_name="comparative_report.txt",
                mime="text/plain"
            )

    # Download all as ZIP
    with col3:
        if st.button("📦 Prepare Batch ZIP"):
            output_base = batch_summary.get('output_base')
            if output_base:
                with st.spinner("Creating ZIP file..."):
                    zip_buffer = create_zip_from_directory(Path(output_base), "batch_output")

                st.download_button(
                    label="📥 Download All (ZIP)",
                    data=zip_buffer,
                    file_name=f"batch_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip"
                )


# ==============================================================================
# Page 3: Verification
# ==============================================================================

def page_verification():
    """Verification page for checking processed outputs."""
    st.markdown('<p class="main-header">✅ Verify Processed Output</p>', unsafe_allow_html=True)

    st.markdown("""
    Verify the quality and completeness of already-processed CAFR outputs.
    Upload a previously processed output directory (as ZIP) to check for:
    - Missing pages
    - Incorrect section mappings
    - File integrity issues
    - Metadata completeness
    """)

    st.info("🔧 Verification functionality coming soon! For now, please use the CLI verification tools.")

    st.markdown("### Manual Verification Steps")

    st.code("""
# Using CLI for verification:

# 1. Check metadata completeness
python -c "import json; data = json.load(open('cafr_metadata.json')); print(f'Pages: {len(data[\"pages\"])}')"

# 2. Verify PNG files exist
find output/sections -name "*.png" | wc -l

# 3. Check for missing page numbers
grep -i "missing" cafr_report.txt

# 4. Validate JSON structure
python -m json.tool cafr_metadata.json > /dev/null && echo "Valid JSON"
    """, language='bash')


# ==============================================================================
# Main Application
# ==============================================================================

def main():
    """Main application entry point."""

    # Sidebar navigation
    st.sidebar.title("📊 IBCo CAFR Processor")
    st.sidebar.markdown("---")

    page = st.sidebar.radio(
        "Choose Mode:",
        options=["Single CAFR", "Batch Processing", "Verification"],
        index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    **IBCo CAFR PDF Stripper**

    Process municipal Comprehensive Annual Financial Reports (CAFRs) for the IBCo transparency initiative.

    **Features:**
    - TOC extraction from screenshots
    - Automated section mapping
    - High-quality PNG conversion
    - Complete metadata generation
    """)

    st.sidebar.markdown("### Quick Start")
    st.sidebar.markdown("""
    1. **Single CAFR:** Upload PDF + TOC screenshots
    2. **Batch:** Upload YAML config or build manually
    3. **Verify:** Check processed outputs
    """)

    st.sidebar.markdown("---")
    st.sidebar.markdown("Built for [IBCo](https://ibco-ca.us)")

    # Route to selected page
    if page == "Single CAFR":
        page_single_cafr()
    elif page == "Batch Processing":
        page_batch_processing()
    elif page == "Verification":
        page_verification()


if __name__ == "__main__":
    main()
