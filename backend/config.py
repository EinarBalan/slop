import argparse
import os
import json
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask server with optional background LLM generation')
    parser.add_argument('--background', action='store_true', help='Enable background LLM generation')
    parser.add_argument('--experiment', type=str, default='base', help='Experiment to run')
    parser.add_argument('--model', type=str, default='local', help='Choose from local, gpt-5, gpt-image')
    parser.add_argument('--archive', action='store_true',
                        help='Serve AI posts from archive instead of generating new ones. '
                             'If enabled, the chosen --model/--experiment will not be honored for AI posts.')
    return parser.parse_args()

# Parse arguments once when the module is imported
args = parse_args()

# Server configuration
BATCH_SIZE = 10
STATS_FILE = os.path.join(os.path.dirname(__file__), 'stats.json')  

# Database configuration
DB_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, 'app.sqlite3')
CSV_FILE = os.path.join(DB_DIR, 'posts.csv')

# Auth configuration
SECRET_KEY = os.getenv("SECRET_KEY", "yea-secret")
DEV_AUTH_NO_PASSWORD = os.getenv("DEV_AUTH_NO_PASSWORD", "true").lower() in ("1", "true", "yes")

# Generation configuration(
GENERATE_BATCH_SIZE = 3
AI_POSTS_QUEUE_SIZE = 5  # Maximum number of AI posts to store
GENERATION_INTERVAL = 5  # Seconds between generation attempts
AI_POSTS_RATIO = 0.4    # Fraction of AI posts in the feed (0.0 - 1.0)

# local LLM configuration
LOCAL_MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
DEFAULT_MAX_LENGTH = 1024
DEFAULT_NUM_RETURN_SEQUENCES = 1
DEFAULT_TEMPERATURE = 0.7

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = "gpt-5"

# Load prompts from JSON file
PROMPTS_FILE = os.path.join(os.path.dirname(__file__), 'prompts.json')
with open(PROMPTS_FILE, 'r') as f:
    PROMPTS = json.load(f)

# Export the args object and constants so they can be imported by other modules
__all__ = [
    'args', 
    'BATCH_SIZE', 
    'CSV_FILE',
    'DB_FILE',
    'DB_DIR',
    'SECRET_KEY',
    'DEV_AUTH_NO_PASSWORD',
    'GENERATE_BATCH_SIZE',
    'AI_POSTS_QUEUE_SIZE',
    'GENERATION_INTERVAL',
    'AI_POSTS_RATIO',
    'LOCAL_MODEL_NAME',
    'OPENAI_API_KEY',
    'OPENAI_MODEL_NAME',
    'DEFAULT_MAX_LENGTH',
    'DEFAULT_NUM_RETURN_SEQUENCES',
    'DEFAULT_TEMPERATURE',
    'PROMPTS',
    'PROMPTS_FILE'
] 