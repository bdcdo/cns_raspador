"""
Text Extraction Module

This module handles PDF text extraction from downloaded CNS resolution files
and combines the extracted text with the scraped metadata.
"""

import pdfplumber
import pandas as pd
import time
from datetime import datetime
import unicodedata
from pathlib import Path
import glob
import os


def install_pdfplumber():
    """Install pdfplumber if not available."""
    try:
        import pdfplumber
        print("pdfplumber already installed ✓")
        return True
    except ImportError:
        print("Installing pdfplumber...")
        import subprocess
        import sys
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber"])
            import pdfplumber
            print("pdfplumber installed successfully ✓")
            return True
        except Exception as e:
            print(f"Error installing pdfplumber: {e}")
            return False


def clean_filename_for_matching(title, max_length=100):
    """
    Clean title to create a valid filename for matching.
    
    Args:
        title (str): Original title
        max_length (int): Maximum filename length
        
    Returns:
        str: Clean filename
    """
    if not title:
        return "resolucao_sem_titulo"
    
    import string
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    clean_title = ''.join(c for c in title if c in valid_chars)
    
    # Remove double spaces and limit size
    clean_title = ' '.join(clean_title.split())
    if len(clean_title) > max_length:
        clean_title = clean_title[:max_length]
    
    return clean_title


def extract_text_from_pdf(pdf_path, max_pages=None):
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to PDF file
        max_pages (int): Maximum pages to process (None = all)
        
    Returns:
        str: Extracted text from PDF
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            
            # Process pages (limited if specified)
            pages_to_process = pdf.pages
            if max_pages:
                pages_to_process = pdf.pages[:max_pages]
            
            for page in pages_to_process:
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)
            
            # Join all text
            final_text = '\n'.join(full_text)
            
            # Clean text (remove excessive breaks, etc.)
            final_text = ' '.join(final_text.split())
            
            return final_text
            
    except Exception as e:
        return f"EXTRACTION_ERROR: {str(e)}"


def clean_extracted_text(text):
    """
    Clean and normalize extracted text from PDFs.
    
    Args:
        text (str): Raw extracted text
        
    Returns:
        str: Cleaned text
    """
    if not text or text.startswith("EXTRACTION_ERROR"):
        return text
    
    # Remove problematic special characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove excessive line breaks
    text = ' '.join(text.split())
    
    # Limit size if necessary (to not explode CSV)
    if len(text) > 50000:  # 50k chars max
        text = text[:50000] + "... [TEXT_TRUNCATED]"
    
    return text


def process_all_pdfs_to_text(pdf_folder="pdfs_cns_resolucoes", max_pages_per_pdf=None):
    """
    Process all PDFs in folder and extract their texts.
    
    Args:
        pdf_folder (str): Folder containing PDFs organized by year
        max_pages_per_pdf (int): Maximum pages per PDF (None = all)
        
    Returns:
        dict: {filename: extracted_text_info}
    """
    if not install_pdfplumber():
        return {}
        
    base_folder = Path(pdf_folder)
    
    if not base_folder.exists():
        print(f"Folder {pdf_folder} not found!")
        return {}
    
    # Find all PDFs
    all_pdfs = list(base_folder.glob('**/*.pdf'))
    print(f"Found {len(all_pdfs)} PDFs to process...")
    
    if not all_pdfs:
        print("No PDFs found!")
        return {}
    
    extracted_texts = {}
    successes = 0
    errors = 0
    
    print("Starting text extraction from PDFs...")
    print("=" * 60)
    
    for i, pdf_path in enumerate(all_pdfs, 1):
        try:
            # Filename (without extension) to use as key
            filename = pdf_path.stem
            year = pdf_path.parent.name
            
            print(f"{i}/{len(all_pdfs)} - Processing: {year}/{filename}")
            
            # Extract text
            text = extract_text_from_pdf(pdf_path, max_pages_per_pdf)
            clean_text = clean_extracted_text(text)
            
            # Unique key: year_filename
            key = f"{year}_{filename}"
            extracted_texts[key] = {
                'year': year,
                'filename': filename,
                'full_path': str(pdf_path),
                'text': clean_text,
                'text_size': len(clean_text),
                'has_error': clean_text.startswith("EXTRACTION_ERROR")
            }
            
            if clean_text.startswith("EXTRACTION_ERROR"):
                print(f"  ✗ Extraction error: {clean_text[:100]}...")
                errors += 1
            else:
                print(f"  ✓ Text extracted: {len(clean_text)} characters")
                successes += 1
            
            # Small pause to not overload
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(all_pdfs)} - Successes: {successes}, Errors: {errors}")
                time.sleep(0.1)
                
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            errors += 1
            
            # Still save error entry
            filename = pdf_path.stem
            year = pdf_path.parent.name
            key = f"{year}_{filename}"
            
            extracted_texts[key] = {
                'year': year,
                'filename': filename,
                'full_path': str(pdf_path),
                'text': f"EXTRACTION_ERROR: {str(e)}",
                'text_size': 0,
                'has_error': True
            }
    
    print("=" * 60)
    print(f"Extraction completed!")
    print(f"PDFs processed: {len(all_pdfs)}")
    print(f"Successes: {successes}")
    print(f"Errors: {errors}")
    print(f"Total texts collected: {len(extracted_texts)}")
    
    # Save intermediate result
    texts_filename = f'textos_pdfs_extraidos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # Convert to DataFrame to save
    text_data = []
    for key, info in extracted_texts.items():
        text_data.append({
            'key': key,
            'year': info['year'],
            'filename': info['filename'],
            'full_path': info['full_path'],
            'text_size': info['text_size'],
            'has_error': info['has_error'],
            'text': info['text']
        })
    
    df_texts = pd.DataFrame(text_data)
    df_texts.to_csv(texts_filename, index=False, encoding='utf-8')
    print(f"Texts saved to: {texts_filename}")
    
    return extracted_texts


def combine_csv_with_pdf_texts(csv_file, extracted_texts=None, pdf_folder="pdfs_cns_resolucoes"):
    """
    Combine CSV resolution data with PDF texts.
    
    Args:
        csv_file (str): Path to CSV with resolution data
        extracted_texts (dict): Dict with already extracted texts (or None to extract)
        pdf_folder (str): Folder with PDFs (if need to extract)
        
    Returns:
        DataFrame: DataFrame with new 'pdf_text' column
    """
    # Load resolution data
    if not os.path.exists(csv_file):
        print(f"CSV file not found: {csv_file}")
        return None
    
    df_resolutions = pd.read_csv(csv_file)
    print(f"Loaded CSV with {len(df_resolutions)} resolutions")
    
    # If texts not provided, extract now
    if extracted_texts is None:
        print("Texts not provided, extracting from PDFs...")
        extracted_texts = process_all_pdfs_to_text(pdf_folder)
    
    print(f"Available {len(extracted_texts)} PDF texts")
    
    # Add text columns
    df_resolutions['pdf_text'] = ''
    df_resolutions['pdf_text_size'] = 0
    df_resolutions['pdf_extraction_error'] = False
    
    # Counters for statistics
    matches_found = 0
    matches_not_found = 0
    
    print("Starting matching between CSV and PDF texts...")
    print("=" * 60)
    
    counter = 0
    for idx, row in df_resolutions.iterrows():
        counter += 1
        try:
            # Try different matching strategies
            original_title = row.get('titulo', '')
            year = row.get('ano', '')
            
            # Clean title to create filename
            expected_filename = clean_filename_for_matching(original_title)
            
            # Possible keys to search
            possible_keys = [
                f"{year}_{expected_filename}",  # Standard format
                f"{year}_{original_title}",     # Original title
                expected_filename,              # Just the name
                original_title                  # Just original title
            ]
            
            # Try to find text
            found_text = None
            used_key = None
            
            for possible_key in possible_keys:
                if possible_key in extracted_texts:
                    found_text = extracted_texts[possible_key]
                    used_key = possible_key
                    break
            
            # If not found, try partial matching (more flexible)
            if not found_text:
                for key, info in extracted_texts.items():
                    # Check if filename is contained in title or vice versa
                    if (expected_filename.lower() in key.lower() or 
                        key.lower() in expected_filename.lower() or
                        (info['year'] == str(year) and 
                         any(word in info['filename'].lower() 
                             for word in expected_filename.lower().split()[:3]))):
                        
                        found_text = info
                        used_key = key
                        break
            
            # Update DataFrame
            if found_text:
                df_resolutions.at[idx, 'pdf_text'] = found_text['text']
                df_resolutions.at[idx, 'pdf_text_size'] = found_text['text_size']
                df_resolutions.at[idx, 'pdf_extraction_error'] = found_text['has_error']
                matches_found += 1
                
                if counter % 50 == 0:  # Log every 50 records
                    print(f"  {counter}/{len(df_resolutions)} - Match: {used_key}")
            else:
                df_resolutions.at[idx, 'pdf_text'] = 'PDF_NOT_FOUND'
                df_resolutions.at[idx, 'pdf_text_size'] = 0
                df_resolutions.at[idx, 'pdf_extraction_error'] = True
                matches_not_found += 1
                
                if counter % 50 == 0:
                    print(f"  {counter}/{len(df_resolutions)} - Not found: {expected_filename}")
                
        except Exception as e:
            print(f"Error processing row {counter}: {e}")
            df_resolutions.at[idx, 'pdf_text'] = f'PROCESSING_ERROR: {str(e)}'
            df_resolutions.at[idx, 'pdf_text_size'] = 0
            df_resolutions.at[idx, 'pdf_extraction_error'] = True
            matches_not_found += 1
    
    print("=" * 60)
    print("MATCHING COMPLETED!")
    print(f"Total resolutions: {len(df_resolutions)}")
    print(f"Matches found: {matches_found}")
    print(f"Matches not found: {matches_not_found}")
    print(f"Success rate: {matches_found/len(df_resolutions)*100:.1f}%")
    
    # Text statistics
    texts_with_content = df_resolutions[
        (df_resolutions['pdf_text'] != 'PDF_NOT_FOUND') & 
        (~df_resolutions['pdf_text'].str.startswith('ERROR_')) &
        (df_resolutions['pdf_text_size'] > 0)
    ]
    
    if len(texts_with_content) > 0:
        print(f"\nExtracted text statistics:")
        print(f"Texts with content: {len(texts_with_content)}")
        print(f"Average size: {texts_with_content['pdf_text_size'].mean():.0f} characters")
        print(f"Min size: {texts_with_content['pdf_text_size'].min()}")
        print(f"Max size: {texts_with_content['pdf_text_size'].max()}")
    
    return df_resolutions


def create_complete_database_with_texts(csv_file=None, pdf_folder="pdfs_cns_resolucoes", max_pages_per_pdf=None):
    """
    Main function that creates complete database with PDF texts.
    
    Args:
        csv_file (str): Base CSV file (or None to use most recent)
        pdf_folder (str): Folder with PDFs
        max_pages_per_pdf (int): Page limit per PDF
        
    Returns:
        DataFrame: Complete database with texts
    """
    # Find CSV file if not specified
    if csv_file is None:
        csv_files = glob.glob('cns_resolucoes_*.csv')
        csv_files = [f for f in csv_files if 'teste' not in f and 'com_textos' not in f]
        
        if not csv_files:
            print("No CSV resolution files found!")
            print("Run first the resolution data collection script.")
            return None
        
        csv_file = max(csv_files, key=os.path.getctime)
        print(f"Using CSV file: {csv_file}")
    
    print("=" * 60)
    print("CREATING COMPLETE DATABASE WITH PDF TEXTS")
    print("=" * 60)
    
    # Step 1: Extract texts from PDFs
    print("\n🔍 STEP 1: Extracting texts from PDFs...")
    extraction_start = datetime.now()
    extracted_texts = process_all_pdfs_to_text(pdf_folder, max_pages_per_pdf)
    extraction_end = datetime.now()
    
    if not extracted_texts:
        print("❌ No texts extracted. Check if PDFs exist.")
        return None
    
    print(f"✅ Extraction completed in {extraction_end - extraction_start}")
    
    # Step 2: Combine with CSV data
    print("\n🔗 STEP 2: Combining texts with resolution data...")
    combination_start = datetime.now()
    df_complete = combine_csv_with_pdf_texts(csv_file, extracted_texts, pdf_folder)
    combination_end = datetime.now()
    
    if df_complete is None:
        print("❌ Error in data combination.")
        return None
    
    print(f"✅ Combination completed in {combination_end - combination_start}")
    
    # Step 3: Save final result
    print("\n💾 STEP 3: Saving complete database...")
    final_filename = f'cns_resolucoes_com_textos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    df_complete.to_csv(final_filename, index=False, encoding='utf-8')
    
    # Final report
    total_time = datetime.now() - extraction_start
    
    print("=" * 60)
    print("🎉 COMPLETE DATABASE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📁 File saved: {final_filename}")
    print(f"⏱️ Total time: {total_time}")
    print(f"📊 Total resolutions: {len(df_complete)}")
    
    # Text statistics
    valid_texts = df_complete[
        (df_complete['pdf_text'] != 'PDF_NOT_FOUND') &
        (~df_complete['pdf_text'].str.startswith('ERROR_')) &
        (df_complete['pdf_text_size'] > 0)
    ]
    
    print(f"✅ Resolutions with extracted text: {len(valid_texts)} ({len(valid_texts)/len(df_complete)*100:.1f}%)")
    
    if len(valid_texts) > 0:
        print(f"📝 Text statistics:")
        print(f"   • Average size: {valid_texts['pdf_text_size'].mean():.0f} characters")
        print(f"   • Largest text: {valid_texts['pdf_text_size'].max()} characters")
        print(f"   • Smallest text: {valid_texts['pdf_text_size'].min()} characters")
    
    # Check available columns
    print(f"📋 Available columns: {list(df_complete.columns)}")
    
    return df_complete


def main():
    """Main execution function."""
    print("Starting PDF text extraction process...")
    df_result = create_complete_database_with_texts()
    
    if df_result is not None:
        print("\n🎉 Process completed successfully!")
        return df_result
    else:
        print("\n❌ Process failed. Check logs for details.")
        return None


if __name__ == "__main__":
    main()