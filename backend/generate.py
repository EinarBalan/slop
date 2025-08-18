import threading
import time
from queue import Queue, Empty, Full
from flask import Blueprint, jsonify, request, Response
from llm import get_llm_service
from config import (
    args,
    GENERATE_BATCH_SIZE,
    AI_POSTS_QUEUE_SIZE,
    GENERATION_INTERVAL
)
from db import db_session
from db.models import AiGeneratedPost
from auth import require_auth
from sqlalchemy import desc
import csv
import io

# Create a Blueprint for generation routes
generate = Blueprint('generate', __name__)

# Initialize LLM service

llm_service = get_llm_service(args.model, args.experiment)
print("LLM service initialized")

# Queue to store AI generated posts
ai_posts_queue = Queue(maxsize=AI_POSTS_QUEUE_SIZE)

def parse_ai_post(generated_text):
    """Parse the generated text into a post format."""
    try:
        title_start = generated_text.find('title: ') + 7
        title_end = generated_text.find('\nself_text:')
        self_text_start = title_end + 11
        subreddit_start = generated_text.find('\nsubreddit: ') + 11
        
        title = generated_text[title_start:title_end].strip()
        self_text = generated_text[self_text_start:subreddit_start-11].strip()
        subreddit = generated_text[subreddit_start:].strip()
        
        # Remove 'r/' prefix if present
        if subreddit.startswith('r/'):
            subreddit = subreddit[2:]
        
        return {
            "title": title,
            "self_text": self_text,
            "subreddit": subreddit,
            "post_id": "0",
            "over_18": "false",
            "link_flair_text": "AI",
            "is_ai": True
        }
    except Exception as e:
        print(f"Error parsing AI post: {e}")
        return None

def background_generation():
    """Background task to continuously generate posts."""
    while True:
        try:
            if not ai_posts_queue.full():
                if args.archive:
                    # Pull recent archived AI posts to buffer the queue
                    try:
                        with db_session() as session:
                            rows = (
                                session.query(AiGeneratedPost)
                                .order_by(desc(AiGeneratedPost.generated_at))
                                .limit(GENERATE_BATCH_SIZE)
                                .all()
                            )
                        for r in rows:
                            post = {
                                "title": r.title,
                                "self_text": r.self_text,
                                "subreddit": r.subreddit,
                                "post_id": "0",
                                "over_18": "false",
                                "link_flair_text": "AI",
                                "is_ai": True,
                            }
                            try:
                                ai_posts_queue.put_nowait(post)
                            except Full:
                                break
                    except Exception as e:
                        print(f"Failed to fetch archived AI posts: {e}")
                else:
                    result = llm_service.exp_generate_text()
                    if "error" not in result:
                        post = parse_ai_post(result["generated_text"])
                        if post:
                            # Persist to archive table
                            try:
                                with db_session() as session:
                                    session.add(AiGeneratedPost(
                                        title=post.get("title", ""),
                                        self_text=post.get("self_text", ""),
                                        subreddit=post.get("subreddit"),
                                        model_name=f"{args.model}",
                                        prompt=None,
                                    ))
                            except Exception as e:
                                print(f"Failed to persist AI post: {e}")

                            # Enqueue for serving
                            try:
                                ai_posts_queue.put_nowait(post)
                            except Full:
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
        except Empty:
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


@generate.route('/ai_posts', methods=['GET'])
@require_auth
def list_ai_posts():
    try:
        limit = int(request.args.get('limit') or 50)
        offset = int(request.args.get('offset') or 0)
        fmt = (request.args.get('format') or 'json').lower()

        with db_session() as session:
            q = (
                session.query(AiGeneratedPost)
                .order_by(desc(AiGeneratedPost.generated_at))
                .offset(offset)
                .limit(min(limit, 500))
            )
            rows = q.all()

        data = [
            {
                'id': r.id,
                'title': r.title,
                'self_text': r.self_text,
                'subreddit': r.subreddit,
                'model_name': r.model_name,
                'prompt': r.prompt,
                'generated_at': r.generated_at.isoformat(),
            }
            for r in rows
        ]

        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(data[0].keys()) if data else ['id','title','self_text','subreddit','model_name','prompt','generated_at'])
            writer.writeheader()
            for row in data:
                writer.writerow(row)
            csv_bytes = output.getvalue()
            return Response(csv_bytes, mimetype='text/csv', headers={
                'Content-Disposition': 'attachment; filename="ai_posts.csv"'
            })

        return jsonify({'items': data, 'count': len(data), 'offset': offset, 'limit': limit})
    except Exception as e:
        return jsonify({'error': 'Failed to list AI posts', 'message': str(e)}), 500