import threading
import time
from queue import Queue
from flask import Blueprint, jsonify
from llm import get_llm_service
from config import (
    args,
    GENERATE_BATCH_SIZE,
    AI_POSTS_QUEUE_SIZE,
    GENERATION_INTERVAL
)

# Create a Blueprint for generation routes
generate = Blueprint('generate', __name__)

# Initialize LLM service
llm_service = get_llm_service()
print("LLM service initialized")

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
            "subreddit": "ai",
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
                result = llm_service.exp_generate_text()
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

def start_background_generation():
    """Start the background generation thread."""
    generation_thread = threading.Thread(target=background_generation, daemon=True)
    generation_thread.start()
    return generation_thread

def get_ai_posts():
    """Get AI posts from the background generation queue."""
    ai_posts = []
    while not ai_posts_queue.empty() and len(ai_posts) < GENERATE_BATCH_SIZE:
        try:
            ai_post = ai_posts_queue.get_nowait()
            ai_posts.append(ai_post)
        except Queue.Empty:
            break
    return ai_posts

def generate_batch():
    """Generate a batch of AI posts (for testing)."""
    results = []
    for _ in range(GENERATE_BATCH_SIZE):
        result = llm_service.exp_generate_text()
        if "error" in result:
            return None
        results.append(result)
    return results

###########
# TESTING #
###########

@generate.route('/base')
def generate_base():
    try:
        results = generate_batch()
        if results is None:
            return jsonify({'error': 'Text generation failed'}), 500
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': 'Text generation failed', 'message': str(e)}), 500

@generate.route('/slop')
def generate_slop():
    # TODO: Implement slop generation
    return jsonify({'error': 'Not implemented yet'}), 501

@generate.route('/summarize')
def generate_summarize():
    try:
        result = llm_service.exp_generate_text()
        if "error" in result:
            return jsonify(result), 500
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': 'Text generation failed', 'message': str(e)}), 500

@generate.route('/finetuned')
def generate_finetuned():
    # TODO: Implement finetuned generation
    return jsonify({'error': 'Not implemented yet'}), 501 