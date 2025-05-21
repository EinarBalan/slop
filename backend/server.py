from flask import Flask, jsonify
from flask_cors import CORS
import csv
import os
from llm import llm_service

app = Flask(__name__)
CORS(app)

# Configuration
BATCH_SIZE = 10
CSV_FILE = os.path.join(os.path.dirname(__file__), 'archive', 'outputRS_2022-11.csv')
GENERATE_BATCH_SIZE = 3

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

# TODO: make this work for more than one user
# TODO: create /feed endpoint that returns a batch with AI generated posts mixed in

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

prompt = """
Please generate a post for the subreddit r/ucla.
Your post should be relatively short and hopefully humorous. It can be about anything. 
Do not output any other text than the title and post.
Example outputs:

title: Cooked
self_text: Can’t wait for this shit ass quarter to end. My jealousy for semester students is unmatched and cannot be measured in a quantifiable manner right now.

title: don’t take people’s things 😭
self_text: i can’t believe i even have to say this omg. whoever took my water bottle please give it back it’s purple with lots of stickers
"""

@app.route('/generate')
def generate():
    try:
        results = []
        for _ in range(GENERATE_BATCH_SIZE):
            result = llm_service.generate_text(prompt)

            title = result["generated_text"][result["generated_text"].index('title: ') + 7: result["generated_text"].index('\nself_text:')]
            self_text = result["generated_text"][result["generated_text"].index('self_text:') + 11:]
            results.append({
                "title": title,
                "self_text": self_text,
                "subreddit": "ucla",
                "post_id": "0",
                "over_18": "false",
                "link_flair_text": "AI"
            })

            if "error" in result:
                return jsonify(result), 500
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': 'Text generation failed', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(port=3000, debug=True) 