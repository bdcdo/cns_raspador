"""
CNS Raspador - Conselho Nacional de Saúde Resolution Scraper

A complete toolkit for scraping, downloading and extracting text from
Brazilian National Health Council (CNS) resolutions.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .scraper import (
    generate_page_urls,
    extract_article_data,
    collect_page_data,
    collect_all_data,
    download_all_pdfs,
    main as scraper_main
)

from .text_extractor import (
    extract_text_from_pdf,
    process_all_pdfs_to_text,
    combine_csv_with_pdf_texts,
    create_complete_database_with_texts,
    main as extractor_main
)

__all__ = [
    'generate_page_urls',
    'extract_article_data',
    'collect_page_data',
    'collect_all_data',
    'download_all_pdfs',
    'scraper_main',
    'extract_text_from_pdf',
    'process_all_pdfs_to_text',
    'combine_csv_with_pdf_texts',
    'create_complete_database_with_texts',
    'extractor_main'
]