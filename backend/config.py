import argparse
import os
import json

def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask server with optional background LLM generation')
    parser.add_argument('--background', action='store_true', help='Enable background LLM generation')
    parser.add_argument('--experiment', type=str, default='base', help='Experiment to run')
    parser.add_argument('--model', type=str, default='local', help='Choose from local, gpt-5, gpt-image')
    return parser.parse_args()

# Parse arguments once when the module is imported
args = parse_args()

# Server configuration
BATCH_SIZE = 10
CSV_FILE = os.path.join(os.path.dirname(__file__), 'posts.csv')
STATS_FILE = os.path.join(os.path.dirname(__file__), 'stats.json')  

# Generation configuration(
GENERATE_BATCH_SIZE = 3
AI_POSTS_QUEUE_SIZE = 5  # Maximum number of AI posts to store
GENERATION_INTERVAL = 5  # Seconds between generation attempts

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
    'GENERATE_BATCH_SIZE',
    'AI_POSTS_QUEUE_SIZE',
    'GENERATION_INTERVAL',
    'LOCAL_MODEL_NAME',
    'OPENAI_API_KEY',
    'OPENAI_MODEL_NAME',
    'DEFAULT_MAX_LENGTH',
    'DEFAULT_NUM_RETURN_SEQUENCES',
    'DEFAULT_TEMPERATURE',
    'PROMPTS',
    'PROMPTS_FILE'
] 