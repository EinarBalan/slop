import csv
import os
from pathlib import Path

# Banned keywords to filter out
BANNED_KEYWORDS = ["sex", "selfharm", "thread", "meta", "[deleted]", "[removed]"]

def is_valid_post(post):
    # Check if post has required fields and isn't deleted/removed/NSFW
    if not (post.get('self_text') and 
            post['self_text'].strip() != '' and 
            post.get('over_18') != 'true'):
        return False
    
    # Check for banned keywords in all text fields
    for value in post.values():
        if isinstance(value, str):
            text = value.lower()
            if any(keyword in text for keyword in BANNED_KEYWORDS):
                return False
    
    return True

def process_csv_files():
    archive_dir = Path('archive')
    output_file = 'posts.csv'
    
    # Get all CSV files in the archive directory
    csv_files = sorted(archive_dir.glob('*.csv'))
    
    if not csv_files:
        print("No CSV files found in archive directory")
        return
    
    # Get fieldnames from first file
    with open(csv_files[0], 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
    
    # Process all files
    total_posts = 0
    filtered_posts = 0
    
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for csv_file in csv_files:
            print(f"Processing {csv_file.name}...")
            
            with open(csv_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                for post in reader:
                    total_posts += 1
                    if is_valid_post(post):
                        writer.writerow(post)
                        filtered_posts += 1
                    
                    # Print progress every 100,000 posts
                    if total_posts % 100000 == 0:
                        print(f"Processed {total_posts:,} posts, kept {filtered_posts:,} posts")
    
    print(f"\nProcessing complete!")
    print(f"Total posts processed: {total_posts:,}")
    print(f"Posts kept after filtering: {filtered_posts:,}")
    print(f"Posts filtered out: {total_posts - filtered_posts:,}")
    print(f"Output saved to: {output_file}")

if __name__ == '__main__':
    process_csv_files() 