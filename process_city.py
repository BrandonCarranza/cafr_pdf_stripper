#!/usr/bin/env python3
"""
CAFR PDF Stripper - Multi-CAFR City Processor

Processes multiple years of CAFRs for a single city using a YAML configuration file.
Creates individual outputs for each year plus master index and comparative reports.

Usage:
    python process_city.py --config city_config.yaml
    python process_city.py --config city_config.yaml --skip-png
    python process_city.py --config city_config.yaml --verify-only
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

from ibco_stripper import PDFStripper


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    # Validate required fields
    required_fields = ['city_name', 'output_base', 'cafrs']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field in config: {field}")

    if not config['cafrs']:
        raise ValueError("Configuration must include at least one CAFR")

    # Validate each CAFR entry
    for i, cafr in enumerate(config['cafrs']):
        required_cafr_fields = ['year', 'pdf', 'toc_screenshots']
        for field in required_cafr_fields:
            if field not in cafr:
                raise ValueError(f"CAFR entry {i} missing required field: {field}")

    return config


def process_city(
    config_path: str,
    dpi: int = 300,
    skip_png: bool = False,
    verify_only: bool = False,
    auto_confirm: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Process all CAFRs for a city according to configuration.

    Args:
        config_path: Path to YAML configuration file
        dpi: DPI for PNG conversion
        skip_png: Skip PNG conversion (metadata only)
        verify_only: Only verify TOC, don't process
        auto_confirm: Skip confirmation prompts
        verbose: Enable verbose output

    Returns:
        Summary dictionary with processing results
    """
    # Load configuration
    print("=" * 80)
    print("CAFR Multi-Year City Processor")
    print("=" * 80)
    print()

    try:
        config = load_config(config_path)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

    city_name = config['city_name']
    state = config.get('state', '')
    output_base = Path(config['output_base'])
    cafrs = config['cafrs']

    print(f"City: {city_name}" + (f", {state}" if state else ""))
    print(f"Output Directory: {output_base}")
    print(f"CAFRs to Process: {len(cafrs)}")
    print()

    # Create output base directory
    output_base.mkdir(parents=True, exist_ok=True)

    # Track results for each CAFR
    results = []
    successful = 0
    failed = 0
    cancelled = 0

    # Process each CAFR sequentially
    for i, cafr_config in enumerate(cafrs, 1):
        year = cafr_config['year']
        pdf_path = cafr_config['pdf']
        toc_screenshots = cafr_config['toc_screenshots']

        print("=" * 80)
        print(f"Processing {city_name} CAFR {year} ({i}/{len(cafrs)})")
        print("=" * 80)
        print()

        # Create year-specific output directory
        year_output = output_base / str(year)
        year_output.mkdir(parents=True, exist_ok=True)

        # Verify PDF exists
        if not Path(pdf_path).exists():
            print(f"Error: PDF not found: {pdf_path}")
            print()
            results.append({
                'year': year,
                'status': 'error',
                'error': f'PDF not found: {pdf_path}'
            })
            failed += 1
            continue

        # Verify TOC screenshots exist
        missing_tocs = [toc for toc in toc_screenshots if not Path(toc).exists()]
        if missing_tocs:
            print(f"Error: TOC screenshots not found: {', '.join(missing_tocs)}")
            print()
            results.append({
                'year': year,
                'status': 'error',
                'error': f'TOC screenshots not found: {missing_tocs}'
            })
            failed += 1
            continue

        # Process this CAFR
        try:
            stripper = PDFStripper(pdf_path, str(year_output))

            summary = stripper.process_cafr(
                toc_screenshots=toc_screenshots,
                dpi=dpi,
                skip_png=skip_png,
                verify_only=verify_only,
                auto_confirm=auto_confirm
            )

            # Add year to summary
            summary['year'] = year
            results.append(summary)

            # Track outcome
            if summary['status'] == 'complete':
                successful += 1
            elif summary['status'] == 'cancelled':
                cancelled += 1
                if not auto_confirm:
                    # User cancelled - ask if they want to continue with remaining CAFRs
                    print()
                    response = input("Continue processing remaining CAFRs? [yes/no]: ").strip().lower()
                    if response != 'yes':
                        print("Batch processing cancelled by user.")
                        break
            else:
                failed += 1

            print()

        except Exception as e:
            print(f"Error processing {year} CAFR: {e}")
            if verbose:
                import traceback
                traceback.print_exc()
            print()
            results.append({
                'year': year,
                'status': 'error',
                'error': str(e)
            })
            failed += 1
            continue

    # Generate master index
    print("=" * 80)
    print("Generating Master Index")
    print("=" * 80)
    print()

    master_index = generate_master_index(city_name, state, results, output_base)

    # Generate comparative report
    print("=" * 80)
    print("Generating Comparative Report")
    print("=" * 80)
    print()

    comparative_report = generate_comparative_report(city_name, state, results, output_base)

    # Final summary
    print("=" * 80)
    print("Batch Processing Complete")
    print("=" * 80)
    print()
    print(f"City: {city_name}" + (f", {state}" if state else ""))
    print(f"Total CAFRs: {len(cafrs)}")
    print(f"Successfully Processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Cancelled: {cancelled}")
    print()
    print(f"Master Index: {master_index}")
    print(f"Comparative Report: {comparative_report}")
    print()

    return {
        'city_name': city_name,
        'state': state,
        'total_cafrs': len(cafrs),
        'successful': successful,
        'failed': failed,
        'cancelled': cancelled,
        'results': results,
        'master_index': str(master_index),
        'comparative_report': str(comparative_report)
    }


def generate_master_index(
    city_name: str,
    state: str,
    results: List[Dict[str, Any]],
    output_base: Path
) -> Path:
    """
    Generate master index JSON combining all years.

    Args:
        city_name: Name of the city
        state: State abbreviation
        results: List of processing results for each year
        output_base: Base output directory

    Returns:
        Path to generated master index file
    """
    master_index = {
        'city_name': city_name,
        'state': state,
        'generated_at': datetime.now().isoformat(),
        'total_years': len(results),
        'successful_years': sum(1 for r in results if r.get('status') == 'complete'),
        'years': []
    }

    # Add data for each successfully processed year
    for result in results:
        year = result.get('year')
        if result.get('status') != 'complete':
            # Include failed/cancelled years with status
            master_index['years'].append({
                'year': year,
                'status': result.get('status'),
                'error': result.get('error')
            })
            continue

        # Load the year's metadata file
        year_metadata_path = output_base / str(year) / 'cafr_metadata.json'

        if year_metadata_path.exists():
            with open(year_metadata_path, 'r') as f:
                year_metadata = json.load(f)

            # Extract key info for master index
            year_entry = {
                'year': year,
                'status': 'completed',
                'total_pages': year_metadata.get('statistics', {}).get('total_pages'),
                'sections': year_metadata.get('statistics', {}).get('sections', []),
                'metadata_file': f"{year}/cafr_metadata.json",
                'report_file': f"{year}/cafr_report.txt",
                'output_directory': str(year)
            }

            master_index['years'].append(year_entry)
        else:
            # Metadata file missing
            master_index['years'].append({
                'year': year,
                'status': 'completed',
                'error': 'Metadata file not found'
            })

    # Sort years in descending order
    master_index['years'].sort(key=lambda x: x.get('year', 0), reverse=True)

    # Save master index
    index_path = output_base / 'master_index.json'
    with open(index_path, 'w') as f:
        json.dump(master_index, f, indent=2)

    print(f"Master index saved: {index_path}")
    print(f"  Total years: {master_index['total_years']}")
    print(f"  Successful: {master_index['successful_years']}")
    print()

    return index_path


def generate_comparative_report(
    city_name: str,
    state: str,
    results: List[Dict[str, Any]],
    output_base: Path
) -> Path:
    """
    Generate comparative text report across all years.

    Args:
        city_name: Name of the city
        state: State abbreviation
        results: List of processing results for each year
        output_base: Base output directory

    Returns:
        Path to generated comparative report file
    """
    report_lines = []

    # Header
    report_lines.append("=" * 80)
    report_lines.append(f"CAFR Comparative Report: {city_name}" + (f", {state}" if state else ""))
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"Total Years: {len(results)}")
    report_lines.append("")

    # Summary table
    report_lines.append("-" * 80)
    report_lines.append("YEAR-BY-YEAR SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append("")
    report_lines.append(f"{'Year':<10} {'Status':<15} {'Pages':<10} {'Sections':<10}")
    report_lines.append("-" * 80)

    # Sort results by year (descending)
    sorted_results = sorted(results, key=lambda x: x.get('year', 0), reverse=True)

    for result in sorted_results:
        year = result.get('year', 'N/A')
        status = result.get('status', 'unknown')

        if status == 'complete':
            pages = result.get('total_pages', 'N/A')

            # Count unique sections
            page_index = result.get('page_index', [])
            sections = set()
            for page in page_index:
                section = page.get('section_name')
                if section:
                    sections.add(section)
            section_count = len(sections)

            report_lines.append(f"{year:<10} {status:<15} {pages:<10} {section_count:<10}")
        else:
            error = result.get('error', 'N/A')
            report_lines.append(f"{year:<10} {status:<15} {error}")

    report_lines.append("")

    # Section comparison
    report_lines.append("-" * 80)
    report_lines.append("SECTION STRUCTURE COMPARISON")
    report_lines.append("-" * 80)
    report_lines.append("")

    # Collect all sections across years
    sections_by_year = {}
    for result in sorted_results:
        if result.get('status') != 'complete':
            continue

        year = result.get('year')
        page_index = result.get('page_index', [])

        # Get unique level-1 sections in order
        sections = []
        seen = set()
        for page in page_index:
            section = page.get('section_name')
            level = page.get('section_level', 0)
            if section and level == 1 and section not in seen:
                sections.append(section)
                seen.add(section)

        sections_by_year[year] = sections

    # Display sections for each year
    for year in sorted(sections_by_year.keys(), reverse=True):
        report_lines.append(f"{year}:")
        for i, section in enumerate(sections_by_year[year], 1):
            report_lines.append(f"  {i}. {section}")
        report_lines.append("")

    # Page count trend
    report_lines.append("-" * 80)
    report_lines.append("PAGE COUNT TREND")
    report_lines.append("-" * 80)
    report_lines.append("")

    completed_results = [r for r in sorted_results if r.get('status') == 'complete']

    if completed_results:
        for result in completed_results:
            year = result.get('year')
            pages = result.get('total_pages', 0)
            report_lines.append(f"{year}: {pages} pages")

        # Calculate average
        avg_pages = sum(r.get('total_pages', 0) for r in completed_results) / len(completed_results)
        report_lines.append("")
        report_lines.append(f"Average: {avg_pages:.1f} pages")
    else:
        report_lines.append("No completed CAFRs to compare")

    report_lines.append("")

    # Processing summary
    report_lines.append("-" * 80)
    report_lines.append("PROCESSING SUMMARY")
    report_lines.append("-" * 80)
    report_lines.append("")

    successful = sum(1 for r in results if r.get('status') == 'completed')
    failed = sum(1 for r in results if r.get('status') == 'error')
    cancelled = sum(1 for r in results if r.get('status') == 'cancelled')

    report_lines.append(f"Total CAFRs: {len(results)}")
    report_lines.append(f"Successfully Processed: {successful}")
    report_lines.append(f"Failed: {failed}")
    report_lines.append(f"Cancelled: {cancelled}")
    report_lines.append("")

    # Footer
    report_lines.append("=" * 80)
    report_lines.append("END OF COMPARATIVE REPORT")
    report_lines.append("=" * 80)

    # Save report
    report_path = output_base / 'comparative_report.txt'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"Comparative report saved: {report_path}")
    print()

    return report_path


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='CAFR Multi-CAFR City Processor - Process multiple years for one city',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all CAFRs in config
  %(prog)s --config city_config.yaml

  # Skip PNG conversion (metadata and reports only)
  %(prog)s --config city_config.yaml --skip-png

  # Verify TOC for all years (no processing)
  %(prog)s --config city_config.yaml --verify-only

  # Auto-confirm all prompts (for automation)
  %(prog)s --config city_config.yaml --yes

Configuration file format (YAML):
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
        """
    )

    parser.add_argument('--config', required=True, help='Path to YAML configuration file')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for PNG conversion (default: 300)')
    parser.add_argument('--skip-png', action='store_true', help='Only generate metadata and reports, skip PNG conversion')
    parser.add_argument('--verify-only', action='store_true', help='Only load and verify TOC for all years, do not process')
    parser.add_argument('--yes', action='store_true', help='Auto-confirm processing (skip confirmation prompts)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Process city
    try:
        result = process_city(
            config_path=args.config,
            dpi=args.dpi,
            skip_png=args.skip_png,
            verify_only=args.verify_only,
            auto_confirm=args.yes,
            verbose=args.verbose
        )

        # Exit with success if at least one CAFR processed successfully
        if result.get('successful', 0) > 0:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
