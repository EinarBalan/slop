import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask server with optional background LLM generation')
    parser.add_argument('--background', action='store_true', help='Enable background LLM generation')
    parser.add_argument('--experiment', type=str, default='base', help='Experiment to run')
    return parser.parse_args()

# Parse arguments once when the module is imported
args = parse_args()

# Server configuration
BATCH_SIZE = 10
CSV_FILE = os.path.join(os.path.dirname(__file__), 'archive', 'outputRS_2022-11.csv')

# Generation configuration
GENERATE_BATCH_SIZE = 3
AI_POSTS_QUEUE_SIZE = 10  # Maximum number of AI posts to store
GENERATION_INTERVAL = 5  # Seconds between generation attempts

# LLM configuration
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
DEFAULT_MAX_LENGTH = 1024
DEFAULT_NUM_RETURN_SEQUENCES = 1
DEFAULT_TEMPERATURE = 0.7

# LLM prompts
BASE_PROMPT = """
Please generate a post for the subreddit r/ucla.
Your post should be relatively short and preferably humorous. It can be about anything. Do not output any other text than the title and post. Make sure to stick to the format exactly.
Example outputs:

title: Cooked
self_text: Can't wait for this shit ass quarter to end. My jealousy for semester students is unmatched and cannot be measured in a quantifiable manner right now.

title: don't take people's things 😭
self_text: i can't believe i even have to say this omg. whoever took my water bottle please give it back it's purple with lots of stickers

title: Dinner in Westwood
self_text: My daughter has 2 day freshman orientation in July. Looking for recommendations for dinner on a Friday night we will be staying in Westwood that night. We will prefer not to drive. Thank you. We like all types of food. Just want her to get familiar with what's close to campus.
"""

SUMMARIZE_PROMPT = """
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
self_text: My daughter has 2 day freshman orientation in July. Looking for recommendations for dinner on a Friday night we will be staying in Westwood that night. We will prefer not to drive. Thank you. We like all types of food. Just want her to get familiar with what's close to campus.

Based on the previous summary and this new post, please generate a new summary of the user's interests.
"""

# Export the args object and constants so they can be imported by other modules
__all__ = [
    'args', 
    'BATCH_SIZE', 
    'CSV_FILE',
    'GENERATE_BATCH_SIZE',
    'AI_POSTS_QUEUE_SIZE',
    'GENERATION_INTERVAL',
    'MODEL_NAME',
    'DEFAULT_MAX_LENGTH',
    'DEFAULT_NUM_RETURN_SEQUENCES',
    'DEFAULT_TEMPERATURE',
    'BASE_PROMPT',
    'SUMMARIZE_PROMPT'
] 