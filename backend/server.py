from flask import Flask, jsonify
from flask_cors import CORS
import csv
import os
import random
import json
from post_interactions import post_interactions
from generate import generate, start_background_generation, get_ai_posts
from config import args, BATCH_SIZE, CSV_FILE

app = Flask(__name__)
CORS(app)

# Register the blueprints
app.register_blueprint(post_interactions, url_prefix='/interactions')
app.register_blueprint(generate, url_prefix='/generate')

# Start background generation thread if enabled
if args.background:
    generation_thread = start_background_generation()
    print("Background LLM generation enabled")
else:
    print("Background LLM generation disabled")

# Helper function to check if a post is valid
def is_valid_post(post):
    return (post.get('self_text') and 
            post['self_text'].strip() != '' and 
            post['self_text'] != '[deleted]' and
            post['self_text'] != '[removed]' and
            post.get('over_18') != 'true')

# Global variables for CSV reading
current_batch_index = 0
total_processed_rows = 400 #! adjust starting point to see new posts
end_of_file = False

def read_csv_batch():
    global current_batch_index, total_processed_rows, end_of_file
    
    batch = []
    skipped_rows = 0
    
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Skip rows we've already processed
            for _ in range(total_processed_rows):
                next(reader, None)
            
            # Read the next batch
            for row in reader:
                total_processed_rows += 1
                
                if len(batch) >= BATCH_SIZE:
                    current_batch_index += 1
                    return {
                        'batch': batch,
                        'batchIndex': current_batch_index,
                        'skippedRows': skipped_rows,
                        'totalProcessedRows': total_processed_rows
                    }
                
                if is_valid_post(row):
                    batch.append(row)
                else:
                    skipped_rows += 1
            
            # If we get here, we've reached the end of the file
            end_of_file = True
            current_batch_index += 1
            return {
                'batch': batch,
                'batchIndex': current_batch_index,
                'skippedRows': skipped_rows,
                'totalProcessedRows': total_processed_rows,
                'endOfFile': True
            }
            
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

def reset_csv_reader():
    global current_batch_index, total_processed_rows, end_of_file
    current_batch_index = 0
    total_processed_rows = 0
    end_of_file = False

@app.route('/batch')
def get_batch():
    try:
        result = read_csv_batch()
        if result is None:
            return jsonify({'error': 'Failed to read batch'}), 500
            
        return jsonify({
            'posts': result['batch'],
            'count': len(result['batch']),
            'batchIndex': result['batchIndex'],
            'skippedInvalidPosts': result['skippedRows'],
            'totalProcessedRows': result['totalProcessedRows'],
            'endOfFile': result.get('endOfFile', False),
            'batchSize': BATCH_SIZE
        })
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/reset')
def reset():
    try:
        reset_csv_reader()
        return jsonify({'message': 'Parser reset to beginning of file'})
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@app.route('/feed')
def get_feed():
    try:
        # Get real posts
        result = read_csv_batch()
        if result is None:
            return jsonify({'error': 'Failed to read batch'}), 500
            
        posts = result['batch']
        
        # Add AI posts randomly throughout the batch if background generation is enabled
        ai_posts = []
        if args.background:
            ai_posts = get_ai_posts()
            
            # Insert AI posts at random positions
            for ai_post in ai_posts:
                insert_index = random.randint(0, len(posts))
                posts.insert(insert_index, ai_post)
            
        return jsonify({
            'posts': posts,
            'count': len(posts),
            'batchIndex': result['batchIndex'],
            'skippedInvalidPosts': result['skippedRows'],
            'totalProcessedRows': result['totalProcessedRows'],
            'endOfFile': result.get('endOfFile', False),
            'batchSize': BATCH_SIZE,
            'aiPostsCount': len(ai_posts),
        })
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True) 