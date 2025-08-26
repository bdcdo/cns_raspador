#!/usr/bin/env python3
"""
CNS Raspador - Main CLI Interface

Command line interface for scraping CNS (Conselho Nacional de Saúde) resolutions
from the Brazilian government website.

Usage:
    python main.py scrape                    # Scrape resolution data
    python main.py download [CSV_FILE]       # Download PDFs
    python main.py extract [CSV_FILE]        # Extract text from PDFs
    python main.py full [CSV_FILE]           # Full pipeline (scrape + download + extract)
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import main as scraper_main, download_all_pdfs
from src.text_extractor import main as extractor_main, create_complete_database_with_texts
import glob


def find_latest_csv(pattern="cns_resolucoes_*.csv", exclude_patterns=None):
    """Find the most recent CSV file matching pattern."""
    if exclude_patterns is None:
        exclude_patterns = ['teste', 'com_textos', 'temp']
    
    csv_files = glob.glob(pattern)
    csv_files = [f for f in csv_files if not any(excl in f for excl in exclude_patterns)]
    
    if not csv_files:
        return None
    
    return max(csv_files, key=os.path.getctime)


def cmd_scrape(args):
    """Execute scraping command."""
    print("🕷️ Starting CNS resolution scraping...")
    df_result = scraper_main()
    if df_result is not None:
        print("✅ Scraping completed successfully!")
        return True
    else:
        print("❌ Scraping failed!")
        return False


def cmd_download(args):
    """Execute PDF download command."""
    csv_file = args.csv_file
    
    if not csv_file:
        csv_file = find_latest_csv()
        if not csv_file:
            print("❌ No CSV file found! Run scraping first or specify a CSV file.")
            return False
        print(f"📁 Using latest CSV file: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    print(f"📥 Starting PDF download from: {csv_file}")
    result = download_all_pdfs(csv_file, skip_existing=True)
    
    if result and result['successes'] > 0:
        print("✅ PDF download completed successfully!")
        return True
    else:
        print("❌ PDF download failed!")
        return False


def cmd_extract(args):
    """Execute text extraction command."""
    csv_file = args.csv_file
    
    if not csv_file:
        csv_file = find_latest_csv()
        if not csv_file:
            print("❌ No CSV file found! Run scraping first or specify a CSV file.")
            return False
        print(f"📁 Using latest CSV file: {csv_file}")
    
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        return False
    
    print(f"📄 Starting text extraction from: {csv_file}")
    df_result = create_complete_database_with_texts(csv_file)
    
    if df_result is not None:
        print("✅ Text extraction completed successfully!")
        return True
    else:
        print("❌ Text extraction failed!")
        return False


def cmd_full(args):
    """Execute full pipeline."""
    print("🚀 Starting full CNS resolution processing pipeline...")
    print("=" * 60)
    
    # Step 1: Scraping
    print("📊 STEP 1: Scraping resolution data...")
    if not cmd_scrape(args):
        return False
    
    # Find the CSV file created by scraping
    csv_file = find_latest_csv()
    if not csv_file:
        print("❌ Could not find scraped CSV file!")
        return False
    
    # Step 2: Download PDFs
    print(f"\n📥 STEP 2: Downloading PDFs...")
    args.csv_file = csv_file  # Set CSV file for download
    if not cmd_download(args):
        return False
    
    # Step 3: Extract texts
    print(f"\n📄 STEP 3: Extracting texts from PDFs...")
    if not cmd_extract(args):
        return False
    
    print("\n🎉 Full pipeline completed successfully!")
    print("Your complete CNS resolution database is ready!")
    return True


def cmd_status(args):
    """Show current project status."""
    print("📊 CNS Raspador Project Status")
    print("=" * 40)
    
    # Check for CSV files
    csv_files = glob.glob("cns_resolucoes_*.csv")
    if csv_files:
        print(f"📄 CSV files found: {len(csv_files)}")
        latest = find_latest_csv()
        if latest:
            print(f"   Latest: {latest}")
    else:
        print("📄 No CSV files found")
    
    # Check for PDFs
    pdf_folder = Path("pdfs_cns_resolucoes")
    if pdf_folder.exists():
        total_pdfs = len(list(pdf_folder.glob("**/*.pdf")))
        print(f"📁 PDFs downloaded: {total_pdfs}")
        
        # Count by year
        year_folders = [f for f in pdf_folder.iterdir() if f.is_dir()]
        if year_folders:
            print("   Distribution by year:")
            for year_folder in sorted(year_folders):
                count = len(list(year_folder.glob("*.pdf")))
                print(f"     {year_folder.name}: {count} PDFs")
    else:
        print("📁 No PDF folder found")
    
    # Check for text extraction results
    text_files = glob.glob("cns_resolucoes_com_textos_*.csv")
    if text_files:
        print(f"📝 Text extraction files: {len(text_files)}")
        latest_text = max(text_files, key=os.path.getctime)
        print(f"   Latest: {latest_text}")
    else:
        print("📝 No text extraction files found")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="CNS Raspador - Brazilian National Health Council Resolution Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scrape command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape resolution data from CNS website')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download PDF files')
    download_parser.add_argument('csv_file', nargs='?', help='CSV file with resolution data (optional, uses latest if not specified)')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from downloaded PDFs')
    extract_parser.add_argument('csv_file', nargs='?', help='CSV file with resolution data (optional, uses latest if not specified)')
    
    # Full pipeline command
    full_parser = subparsers.add_parser('full', help='Run complete pipeline (scrape + download + extract)')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show project status')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = {
        'scrape': cmd_scrape,
        'download': cmd_download,
        'extract': cmd_extract,
        'full': cmd_full,
        'status': cmd_status
    }
    
    success = commands[args.command](args)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()