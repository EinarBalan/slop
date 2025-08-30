from flask import Flask, jsonify
from flask_cors import CORS
from post_interactions import post_interactions
from generate import generate, start_background_generation
from config import args
from auth import auth
from feed import feed
from experiments import experiments
from db.seed import seed_if_empty, clear_served_posts

app = Flask(__name__)
CORS(app)

# Initialize database (idempotent) at startup
try:
    seed_if_empty()
    clear_served_posts()
except Exception as e:
    print(f"Database init failed: {e}")

# Register the blueprints
app.register_blueprint(post_interactions, url_prefix='/interactions')
app.register_blueprint(generate, url_prefix='/generate')
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(feed)
app.register_blueprint(experiments, url_prefix='/experiments')

# Start background generation thread if enabled
if args.background:
    generation_thread = start_background_generation()
    print("Background LLM generation enabled")
else:
    print("Background LLM generation disabled")

if __name__ == '__main__':
    app.run(port=3000, debug=True) 
    