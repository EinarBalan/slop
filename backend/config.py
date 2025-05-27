import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Run the Flask server with optional background LLM generation')
    parser.add_argument('--background', action='store_true', help='Enable background LLM generation')
    parser.add_argument('--experiment', type=str, default='base', help='Experiment to run')
    return parser.parse_args()

# Parse arguments once when the module is imported
args = parse_args()

# Export the args object so it can be imported by other modules
__all__ = ['args'] 