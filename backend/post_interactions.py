import os
import json
from flask import Blueprint, jsonify, request, g
from config import args, PROMPTS, PROMPTS_FILE
from llm import get_llm_service
from stats import (
    increment_ai_post_count,
    increment_real_post_count,
    increment_liked_ai_post_count,
    increment_liked_real_post_count,
    increment_marked_as_ai,
    increment_dislike,
)
from auth import require_auth
from db import db_session
from db.models import Post, Interaction, HumorPost, AiGeneratedPost
import random
from sqlalchemy.exc import IntegrityError

# Create a Blueprint for post interactions
post_interactions = Blueprint('post_interactions', __name__)

llm_service = get_llm_service(args.model, 'base')

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
        from flask import g
        current_exp = getattr(g, 'current_experiment', None) or 'base'
        if current_exp == "summarize":
            summarize_preferences(post)

        # Persist interaction
        with db_session() as session:
            lookup_post_id = post.get('post_id')
            humor_id = post.get('humor_id')
            # Determine source and external id
            if isinstance(lookup_post_id, str) and lookup_post_id.startswith('ai-'):
                # Extract numeric id after ai-
                try:
                    ai_numeric_id = int(lookup_post_id.split('ai-')[-1])
                except Exception:
                    ai_numeric_id = None
                interaction = Interaction(
                    user_id=g.current_user_id,
                    ai_id=ai_numeric_id,
                    action='like'
                )
                session.add(interaction)
            elif humor_id is not None:
                hp = session.query(HumorPost).filter(HumorPost.id == humor_id).first()
                interaction = Interaction(
                    user_id=g.current_user_id,
                    humor_id=hp.id if hp else None,
                    action='like'
                )
                session.add(interaction)
            else:
                # Normal post flow; ensure Post exists and log by internal id
                db_post = session.query(Post).filter(
                    (Post.title == post.get('title'))
                ).first()
                if db_post is None:
                    db_post = Post(
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
            lookup_post_id = post.get('post_id')
            humor_id = post.get('humor_id')
            if isinstance(lookup_post_id, str) and lookup_post_id.startswith('ai-'):
                try:
                    ai_numeric_id = int(lookup_post_id.split('ai-')[-1])
                except Exception:
                    ai_numeric_id = None
                interaction = Interaction(
                    user_id=g.current_user_id,
                    ai_id=ai_numeric_id,
                    action='dislike'
                )
                session.add(interaction)
            elif humor_id is not None:
                hp = session.query(HumorPost).filter(HumorPost.id == humor_id).first()
                interaction = Interaction(
                    user_id=g.current_user_id,
                    humor_id=hp.id if hp else None,
                    action='dislike'
                )
                session.add(interaction)
            else:
                db_post = session.query(Post).filter(
                    (Post.title == post.get('title'))
                ).first()
                if db_post is None:
                    db_post = Post(
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
        # Update dislike counters by true post type
        increment_dislike(is_ai_post=bool(post.get('is_ai', False)))
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
            lookup_post_id = post.get('post_id')
            humor_id = post.get('humor_id')
            if isinstance(lookup_post_id, str) and lookup_post_id.startswith('ai-'):
                try:
                    ai_numeric_id = int(lookup_post_id.split('ai-')[-1])
                except Exception:
                    ai_numeric_id = None
                interaction = Interaction(
                    user_id=g.current_user_id,
                    ai_id=ai_numeric_id,
                    action='next'
                )
                session.add(interaction)
            elif humor_id is not None:
                hp = session.query(HumorPost).filter(HumorPost.id == humor_id).first()
                interaction = Interaction(
                    user_id=g.current_user_id,
                    humor_id=hp.id if hp else None,
                    action='next'
                )
                session.add(interaction)
            else:
                db_post = session.query(Post).filter(
                    (Post.title == post.get('title'))
                ).first()
                if db_post is None:
                    db_post = Post(
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



@post_interactions.route('/nextBatch', methods=['POST'])
@require_auth
def next_batch():
    try:
        data = request.get_json() or {}
        posts = data.get('posts', [])
        if not isinstance(posts, list):
            return jsonify({'error': 'Invalid data provided. Expected {"posts": [...]}'}), 400

        ai_count = 0
        real_count = 0
        with db_session() as session:
            for post in posts:
                if not isinstance(post, dict):
                    continue
                is_ai = bool(post.get('is_ai', False))
                ai_count += 1 if is_ai else 0
                real_count += 0 if is_ai else 1
                lookup_post_id = post.get('post_id')
                db_post = session.query(Post).filter(
                    (Post.title == post.get('title'))
                ).first()
                if isinstance(lookup_post_id, str) and lookup_post_id.startswith('ai-'):
                    try:
                        ai_numeric_id = int(lookup_post_id.split('ai-')[-1])
                    except Exception:
                        ai_numeric_id = None
                    try:
                        session.add(Interaction(
                            user_id=g.current_user_id,
                            ai_id=ai_numeric_id,
                            action='next'
                        ))
                        session.flush()
                    except IntegrityError:
                        session.rollback()
                        continue
                    continue
                if isinstance(lookup_post_id, str) and lookup_post_id.startswith('humor-'):
                    hp = session.query(HumorPost).filter(
                        (HumorPost.title == post.get('title')) & (HumorPost.subreddit == post.get('subreddit'))
                    ).first()
                    try:
                        session.add(Interaction(
                            user_id=g.current_user_id,
                            humor_id=hp.id if hp else None,
                            action='next'
                        ))
                        session.flush()
                    except IntegrityError:
                        session.rollback()
                        continue
                    continue
                if db_post is None:
                    db_post = Post(
                        title=post.get('title', ''),
                        self_text=post.get('self_text', ''),
                        subreddit=post.get('subreddit'),
                        over_18=str(post.get('over_18', 'false')).lower() == 'true',
                        link_flair_text=post.get('link_flair_text'),
                        is_ai=is_ai,
                        random_key=random.getrandbits(63),
                    )
                    session.add(db_post)
                    session.flush()
                try:
                    session.add(Interaction(
                        user_id=g.current_user_id,
                        post_id=db_post.id,
                        action='next'
                    ))
                    session.flush()
                except IntegrityError:
                    session.rollback()
                    # Ignore duplicate next for same user/post
                    continue

        # Stats are updated when the feed is served; do not double count here

        return jsonify({'message': 'Batch processed successfully', 'count': len(posts)})
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
        is_ai_judgment = data.get('isAI', False)

        # Persist a 'markedai' interaction
        with db_session() as session:
            lookup_post_id = post.get('post_id')
            humor_id = post.get('humor_id')
            is_ai_actual = False

            if isinstance(lookup_post_id, str) and lookup_post_id.startswith('ai-'):
                try:
                    ai_numeric_id = int(lookup_post_id.split('ai-')[-1])
                except Exception:
                    ai_numeric_id = None
                try:
                    session.add(Interaction(
                        user_id=g.current_user_id,
                        ai_id=ai_numeric_id,
                        action='markedai'
                    ))
                    session.flush()
                except IntegrityError:
                    session.rollback()
                is_ai_actual = True
            elif humor_id is not None:
                hp = session.query(HumorPost).filter(HumorPost.id == humor_id).first()
                try:
                    session.add(Interaction(
                        user_id=g.current_user_id,
                        humor_id=hp.id if hp else None,
                        action='markedai'
                    ))
                    session.flush()
                except IntegrityError:
                    session.rollback()
                is_ai_actual = False
            else:
                db_post = session.query(Post).filter(
                    (Post.title == post.get('title'))
                ).first()
                if db_post is None:
                    db_post = Post(
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
                try:
                    session.add(Interaction(
                        user_id=g.current_user_id,
                        post_id=db_post.id,
                        action='markedai'
                    ))
                    session.flush()
                except IntegrityError:
                    session.rollback()
                is_ai_actual = bool(db_post.is_ai)

        # Update experiment counters for marked-as-AI based on the actual post type, not the user's judgment
        increment_marked_as_ai(is_ai_post=is_ai_actual, amount=1)
        return jsonify({'message': 'AI judgment recorded successfully'})
            
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