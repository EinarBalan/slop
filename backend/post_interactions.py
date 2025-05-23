import os
import json
from flask import Blueprint, jsonify, request

# Create a Blueprint for post interactions
post_interactions = Blueprint('post_interactions', __name__)

# File paths for storing different types of interactions
LIKED_POSTS_FILE = os.path.join(os.path.dirname(__file__), 'postsLiked.json')
DISLIKED_POSTS_FILE = os.path.join(os.path.dirname(__file__), 'postsDisliked.json')
AI_JUDGED_POSTS_FILE = os.path.join(os.path.dirname(__file__), 'postsAIJudged.json')

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

@post_interactions.route('/like', methods=['POST'])
def like_post():
    try:
        post = request.get_json()
        if not post:
            return jsonify({'error': 'No post data provided'}), 400

        # Load existing liked posts
        liked_posts = load_posts(LIKED_POSTS_FILE)
        
        # Add new post to the list
        liked_posts.append(post)
        
        # Save updated list
        if save_posts(liked_posts, LIKED_POSTS_FILE):
            return jsonify({
                'message': 'Post liked successfully',
                'totalLikedPosts': len(liked_posts)
            })
        else:
            return jsonify({'error': 'Failed to save liked post'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@post_interactions.route('/dislike', methods=['POST'])
def dislike_post():
    try:
        post = request.get_json()
        if not post:
            return jsonify({'error': 'No post data provided'}), 400

        # Load existing disliked posts
        disliked_posts = load_posts(DISLIKED_POSTS_FILE)
        
        # Add new post to the list
        disliked_posts.append(post)
        
        # Save updated list
        if save_posts(disliked_posts, DISLIKED_POSTS_FILE):
            return jsonify({
                'message': 'Post disliked successfully',
                'totalDislikedPosts': len(disliked_posts)
            })
        else:
            return jsonify({'error': 'Failed to save disliked post'}), 500
            
    except Exception as e:
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

@post_interactions.route('/judgeAI', methods=['POST'])
def judge_ai_post():
    try:
        data = request.get_json()
        if not data or 'post' not in data or 'isAI' not in data:
            return jsonify({'error': 'Invalid data provided. Need post and isAI fields'}), 400

        post = data['post']
        is_ai = data['isAI']

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