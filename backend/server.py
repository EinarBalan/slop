from flask import Flask, jsonify
from flask_cors import CORS
import csv
import os
from llm import llm_service
import threading
import time
import random
from queue import Queue
import json

app = Flask(__name__)
CORS(app)

# Configuration
BATCH_SIZE = 10
CSV_FILE = os.path.join(os.path.dirname(__file__), 'archive', 'outputRS_2022-11.csv')
GENERATE_BATCH_SIZE = 3
AI_POSTS_QUEUE_SIZE = 10  # Maximum number of AI posts to store
GENERATION_INTERVAL = 5  # Seconds between generation attempts

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

# TODO: create /feed endpoint that returns a batch with AI generated posts mixed in
# TODO: different endpoints for different experiments

# Queue to store AI generated posts
ai_posts_queue = Queue(maxsize=AI_POSTS_QUEUE_SIZE)

def parse_ai_post(generated_text):
    """Parse the generated text into a post format."""
    try:
        title_start = generated_text.find('title: ') + 7
        title_end = generated_text.find('\nself_text:')
        self_text_start = title_end + 11
        
        title = generated_text[title_start:title_end].strip()
        self_text = generated_text[self_text_start:].strip()
        
        return {
            "title": title,
            "self_text": self_text,
            "subreddit": "ucla",
            "post_id": "0",
            "over_18": "false",
            "link_flair_text": "AI"
        }
    except Exception as e:
        print(f"Error parsing AI post: {e}")
        return None

def background_generation():
    """Background task to continuously generate posts."""
    while True:
        try:
            if not ai_posts_queue.full():
                result = llm_service.generate_text(base_prompt)
                if "error" not in result:
                    post = parse_ai_post(result["generated_text"])
                    if post:
                        try:
                            ai_posts_queue.put_nowait(post)
                        except Queue.Full:
                            pass  # Queue is full, skip this post
            time.sleep(GENERATION_INTERVAL)
        except Exception as e:
            print(f"Error in background generation: {e}")
            time.sleep(GENERATION_INTERVAL)

# Start background generation thread
generation_thread = threading.Thread(target=background_generation, daemon=True)
generation_thread.start()

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
        
        # Add AI posts randomly throughout the batch
        ai_posts = []
        while not ai_posts_queue.empty() and len(ai_posts) < BATCH_SIZE // 3:  # Add up to 1/3 AI posts
            try:
                ai_post = ai_posts_queue.get_nowait()
                ai_posts.append(ai_post)
            except Queue.Empty:
                break
                
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
            'aiPostsCount': len(ai_posts)
        })
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

base_prompt = """
Please generate a post for the subreddit r/ucla.
Your post should be relatively short and preferably humorous. It can be about anything. Do not output any other text than the title and post. Make sure to stick to the format exactly.
Example outputs:

title: Cooked
self_text: Can’t wait for this shit ass quarter to end. My jealousy for semester students is unmatched and cannot be measured in a quantifiable manner right now.

title: don’t take people’s things 😭
self_text: i can’t believe i even have to say this omg. whoever took my water bottle please give it back it’s purple with lots of stickers

title: Dinner in Westwood
self_text: My daughter has 2 day freshman orientation in July. Looking for recommendations for dinner on a Friday night we will be staying in Westwood that night. We will prefer not to drive. Thank you. We like all types of food. Just want her to get familiar with what’s close to campus.
"""

summarize_prompt = """
The following is a summary of the current user's interests based on posts they have liked in the past: 'Based on the posts the user has liked, it appears that their interests include:

* Complaints about UCLA's academic quarter system and the stress associated with it
* Concern for personal property (specifically water bottles)
* Food and dining options near the UCLA campus
* Parental or family-related concerns (as evidenced by liking a post about freshman orientation)

The user seems to be a student at UCLA, possibly an undergraduate, who is frustrated with the academic demands of
the quarter system and is looking for ways to navigate the campus community. They also appear to be concerned with
maintaining a sense of normalcy in their life despite the challenges of university life.'

Here is a new post that the user has liked:

title: Dinner in Westwood
self_text: My daughter has 2 day freshman orientation in July. Looking for recommendations for dinner on a Friday night we will be staying in Westwood that night. We will prefer not to drive. Thank you. We like all types of food. Just want her to get familiar with what’s close to campus.

Based on the previous summary and this new post, please generate a new summary of the user's interests.
"""

@app.route('/generate/base')
def generate_base():
    try:
        results = []
        for _ in range(GENERATE_BATCH_SIZE):
            result = llm_service.generate_text(base_prompt)
            results.append(result)
            # title = result["generated_text"][result["generated_text"].index('title: ') + 7: result["generated_text"].index('\nself_text:')]
            # self_text = result["generated_text"][result["generated_text"].index('self_text:') + 11:]
            # results.append({
            #     "title": title,
            #     "self_text": self_text,
            #     "subreddit": "ucla",
            #     "post_id": "0",
            #     "over_18": "false",
            #     "link_flair_text": "AI"
            # })

            if "error" in result:
                return jsonify(result), 500
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': 'Text generation failed', 'message': str(e)}), 500

@app.route('/generate/slop')
def generate_slop():
    pass

@app.route('/generate/summarize')
def generate_summarize():
    pass

@app.route('/generate/finetuned')
def generate_finetuned():
    pass

if __name__ == '__main__':
    app.run(port=3000, debug=True) 