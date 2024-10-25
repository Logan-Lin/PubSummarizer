import argparse
import os
import re
import time
import yaml
from tqdm import tqdm

from pdf_parser import parse_and_clean_pdf, clean_text
from pdf_scraper import download_pdf, scrape_openreview
from sql import Database, Paper
from summarizer import summarize_text


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Process academic papers from conferences.')
    parser.add_argument('-c', '--config', type=str, default='config.yaml', help='Path to the configuration file')
    args = parser.parse_args()

    # Load configuration
    with open(args.config, 'r') as config_file:
        config = yaml.safe_load(config_file)
    
    # Extract parameters from config
    platform = config['scraping']['platform']
    conference = config['scraping']['conference']
    year = config['scraping']['year']
    track = config['scraping']['track']
    submission_type = config['scraping']['submission_type']
    output_dir = config['paths']['output_dir']
    db_path = config['paths']['db_path']
    
    # Initialize database
    db = Database(db_path)
    db.create_tables()
    
    # Scrape PDF URLs based on platform
    if platform.lower() == 'openreview':
        papers = scrape_openreview(conference, year, track, submission_type)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process each paper
    for title, url in tqdm(papers, desc="Processing papers"):
        # Preprocess the title to create a valid ID
        processed_id = clean_text(title)  # Remove non-ASCII characters
        processed_title = processed_id
        processed_id = f'{processed_id.replace(" ", "_")}_{conference}_{year}_{track}_{submission_type}_{platform}'

        # Check if the paper already exists in the database
        existing_papers = db.get_papers(filters={'id': processed_id})
        if existing_papers and existing_papers[0].summary:
            print(f"Skipping {title}, already processed.")
            continue
        
        # Download PDF
        pdf_path = download_pdf(f'{processed_id}.pdf', url, output_dir)
        if not pdf_path:
            print(f"Failed to download {title}.")
            continue
        
        # Parse and clean PDF
        content = parse_and_clean_pdf(pdf_path)
        if config['summarization']['content_cap']:
            content = content[:config['summarization']['content_cap']]

        # Summarize the content.
        provider = config['summarization']['provider']
        model_name = config['summarization']['model_name']
        summary = summarize_text(config['summarization']['prefix'], config['summarization']['suffix'], 
                                 content, provider, model_name, **config['summarization']['param'])
        
        # Create a new Paper entry
        paper_entry = Paper(
            id=processed_id,
            title=processed_title,
            conference=conference,
            year=year,
            track=track,
            submission_type=submission_type,
            platform=platform,
            pdf_url=url,
            pdf_path=pdf_path,
            content=content,
            summary=summary
        )
        
        # Add entry to the database
        db.add_entry(paper_entry)
        
        # Delay to avoid overwhelming the server
        time.sleep(config['scraping']['delay'])

    print("All papers processed.")


if __name__ == "__main__":
    main()