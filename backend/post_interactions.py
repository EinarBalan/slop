import os
import json
from flask import Blueprint, jsonify, request, g
from config import args, PROMPTS, PROMPTS_FILE
from llm import get_llm_service
from stats import increment_ai_post_count, increment_real_post_count, increment_liked_ai_post_count, increment_liked_real_post_count
from auth import require_auth
from db import db_session
from db.models import Post, Interaction
import random

# Create a Blueprint for post interactions
post_interactions = Blueprint('post_interactions', __name__)

llm_service = get_llm_service(args.model, args.experiment)

# File paths for storing different types of interactions
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
LIKED_POSTS_FILE = os.path.join(DATA_DIR, 'postsLiked.json')
DISLIKED_POSTS_FILE = os.path.join(DATA_DIR, 'postsDisliked.json')
AI_JUDGED_POSTS_FILE = os.path.join(DATA_DIR, 'postsAIJudged.json')

def load_posts(file_path):
    """Load posts from a JSON file."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Error loading posts from {file_path}: {e}")
        return []

def save_posts(posts, file_path):
    """Save posts to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(posts, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving posts to {file_path}: {e}")
        return False

def summarize_preferences(post):
    """Update preference summary based on the post."""
    
    # load existing summary
    summary = PROMPTS["summary"]
    prompt = PROMPTS["summarize"]

    # remove everything following "previous summary:"
    prompt = prompt.split("previous summary:")[0]

    # update summary with new post
    formatted_summarize_prompt = f"""
    {prompt}
    previous summary: {summary}
    new post: {post}
    """
    # generate new summary
    new_summary = llm_service.generate_text(formatted_summarize_prompt)
    
    # save new summary
    PROMPTS["summary"] = new_summary
    PROMPTS["summarize"] = formatted_summarize_prompt

    # write to prompts.json
    with open(PROMPTS_FILE, 'w') as f:
        json.dump(PROMPTS, f, indent=2)
    

@post_interactions.route('/like', methods=['POST'])
@require_auth
def like_post():
    try:
        post = request.get_json()
        if not post:
            return jsonify({'error': 'No post data provided'}), 400

        # summarize preferences if experiment is "summarize"
        if args.experiment == "summarize":
            summarize_preferences(post)

        # Persist interaction
        with db_session() as session:
            db_post = session.query(Post).filter(
                (Post.post_id == post.get('post_id')) | (Post.title == post.get('title'))
            ).first()
            if db_post is None:
                db_post = Post(
                    post_id=post.get('post_id'),
                    title=post.get('title', ''),
                    self_text=post.get('self_text', ''),
                    subreddit=post.get('subreddit'),
                    over_18=str(post.get('over_18', 'false')).lower() == 'true',
                    link_flair_text=post.get('link_flair_text'),
                    is_ai=bool(post.get('is_ai', False)),
                    random_key=random.getrandbits(63),
                )
                session.add(db_post)
                session.flush()
            interaction = Interaction(
                user_id=g.current_user_id,
                post_id=db_post.id,
                action='like'
            )
            session.add(interaction)
        if post.get('is_ai', False):
            increment_liked_ai_post_count()
        else:
            increment_liked_real_post_count()

        return jsonify({
            'message': 'Post liked successfully'
        })
    
            
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@post_interactions.route('/dislike', methods=['POST'])
@require_auth
def dislike_post():
    try:
        post = request.get_json()
        if not post:
            return jsonify({'error': 'No post data provided'}), 400
        with db_session() as session:
            db_post = session.query(Post).filter(
                (Post.post_id == post.get('post_id')) | (Post.title == post.get('title'))
            ).first()
            if db_post is None:
                db_post = Post(
                    post_id=post.get('post_id'),
                    title=post.get('title', ''),
                    self_text=post.get('self_text', ''),
                    subreddit=post.get('subreddit'),
                    over_18=str(post.get('over_18', 'false')).lower() == 'true',
                    link_flair_text=post.get('link_flair_text'),
                    is_ai=bool(post.get('is_ai', False)),
                    random_key=random.getrandbits(63),
                )
                session.add(db_post)
                session.flush()
            interaction = Interaction(
                user_id=g.current_user_id,
                post_id=db_post.id,
                action='dislike'
            )
            session.add(interaction)
        return jsonify({'message': 'Post disliked successfully'})
            
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@post_interactions.route('/next', methods=['POST'])
@require_auth
def next_post():
    try:
        post = request.get_json()
        if not post:
            return jsonify({'error': 'No post data provided'}), 400
        
        if post.get('is_ai', False):
            increment_ai_post_count()
        else:
            increment_real_post_count()

        with db_session() as session:
            db_post = session.query(Post).filter(
                (Post.post_id == post.get('post_id')) | (Post.title == post.get('title'))
            ).first()
            if db_post is None:
                db_post = Post(
                    post_id=post.get('post_id'),
                    title=post.get('title', ''),
                    self_text=post.get('self_text', ''),
                    subreddit=post.get('subreddit'),
                    over_18=str(post.get('over_18', 'false')).lower() == 'true',
                    link_flair_text=post.get('link_flair_text'),
                    is_ai=bool(post.get('is_ai', False)),
                    random_key=random.getrandbits(63),
                )
                session.add(db_post)
                session.flush()
            interaction = Interaction(
                user_id=g.current_user_id,
                post_id=db_post.id,
                action='next'
            )
            session.add(interaction)
        return jsonify({'message': 'Post processed successfully', 'post': post})
    
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500



@post_interactions.route('/judgeAI', methods=['POST'])
@require_auth
def judge_ai_post():
    try:
        data = request.get_json()
        if not data or 'post' not in data or 'isAI' not in data:
            return jsonify({'error': 'Invalid data provided. Need post and isAI fields'}), 400

        post = data['post']
        is_ai = data.get('isAI', False)

        # Load existing AI judged posts
        judged_posts = load_posts(AI_JUDGED_POSTS_FILE)
        
        # Add new judgment to the list
        judged_posts.append({
            'post': post,
            'isAI': is_ai,
            'timestamp': data.get('timestamp', None)  # Optional timestamp
        })
        
        # Save updated list
        if save_posts(judged_posts, AI_JUDGED_POSTS_FILE):
            return jsonify({
                'message': 'AI judgment recorded successfully',
                'totalJudgedPosts': len(judged_posts)
            })
        else:
            return jsonify({'error': 'Failed to save AI judgment'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@post_interactions.route('/reset', methods=['POST'])
def reset_all():
    try:
        # List of all interaction files to reset
        files_to_reset = [
            LIKED_POSTS_FILE,
            DISLIKED_POSTS_FILE,
            AI_JUDGED_POSTS_FILE
        ]
        
        # Reset each file
        for file_path in files_to_reset:
            try:
                with open(file_path, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                print(f"Error resetting {file_path}: {e}")
                return jsonify({
                    'error': f'Failed to reset {os.path.basename(file_path)}',
                    'message': str(e)
                }), 500
        
        return jsonify({
            'message': 'All interaction data has been reset successfully',
            'resetFiles': [os.path.basename(f) for f in files_to_reset]
        })
            
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500 