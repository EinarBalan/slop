import json
from config import STATS_FILE, args
import os

AI_POST_COUNT = 0
LIKED_AI_POST_COUNT = 0
REAL_POST_COUNT = 0
LIKED_REAL_POST_COUNT = 0

def increment_ai_post_count():
    global AI_POST_COUNT
    AI_POST_COUNT += 1
    report_stats()

def increment_liked_ai_post_count():
    global LIKED_AI_POST_COUNT
    LIKED_AI_POST_COUNT += 1
    report_stats()

def increment_real_post_count():
    global REAL_POST_COUNT
    REAL_POST_COUNT += 1
    report_stats()

def increment_liked_real_post_count():
    global LIKED_REAL_POST_COUNT
    LIKED_REAL_POST_COUNT += 1
    report_stats()

def report_stats():
    """
    Output stats to stats.json
    """
    # Get the directory and filename from STATS_FILE
    stats_dir = os.path.dirname(STATS_FILE)
    stats_filename = os.path.basename(STATS_FILE)
    # Construct new filename with experiment name
    experiment_stats_file = os.path.join(stats_dir, f"{args.experiment}-{stats_filename}")
    
    with open(experiment_stats_file, 'w') as f:
        json.dump({
            'ai_post_count': AI_POST_COUNT,
            'liked_ai_post_count': LIKED_AI_POST_COUNT,
            'ai_like_rate': LIKED_AI_POST_COUNT / AI_POST_COUNT if AI_POST_COUNT > 0 else 0,
            'real_post_count': REAL_POST_COUNT,
            'liked_real_post_count': LIKED_REAL_POST_COUNT,
            'real_like_rate': LIKED_REAL_POST_COUNT / REAL_POST_COUNT if REAL_POST_COUNT > 0 else 0,
            'experiment': args.experiment
        }, f)

