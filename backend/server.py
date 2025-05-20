from flask import Flask, jsonify
from flask_cors import CORS
import csv
import os
from transformers import pipeline
import torch

app = Flask(__name__)
CORS(app)

# Configuration
BATCH_SIZE = 3
CSV_FILE = os.path.join(os.path.dirname(__file__), 'archive', 'outputRS_2022-11.csv')

# Initialize the text generation pipeline
try:
    pipe = pipeline("text-generation", model="Qwen/Qwen3-0.6B", device=0 if torch.cuda.is_available() else -1)
except Exception as e:
    print(f"Error initializing pipeline: {e}")
    pipe = None

# Helper function to check if a post is valid
def is_valid_post(post):
    return (post.get('self_text') and 
            post['self_text'].strip() != '' and 
            post['self_text'] != '[deleted]' and
            post['self_text'] != '[removed]' and
            post.get('over_18') != 'true')

# Global variables for CSV reading
current_batch_index = 0
total_processed_rows = 0
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

@app.route('/generate')
def generate():
    try:
        if pipe is None:
            return jsonify({'error': 'Text generation model not initialized'}), 500
            
        messages = [{"role": "user", "content": "hi, how are you"}]
        result = pipe(messages, max_length=100, num_return_sequences=1, temperature=0.7)
        
        return jsonify({'generated_text': result[0]['generated_text']})
    except Exception as e:
        return jsonify({'error': 'Text generation failed', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True) 