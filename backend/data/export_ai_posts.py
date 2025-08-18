import argparse
import csv
from datetime import datetime
from typing import Optional
import os
import sys

# Ensure 'backend' package is importable when running this file directly
_HERE = os.path.dirname(__file__)
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from db import db_session  # type: ignore
from db.models import AiGeneratedPost  # type: ignore
from sqlalchemy import desc


def export_ai_posts(output_path: str, limit: Optional[int] = None, offset: int = 0):
    with db_session() as session:
        query = (
            session.query(AiGeneratedPost)
            .order_by(desc(AiGeneratedPost.generated_at))
            .offset(offset)
        )
        if limit is not None:
            query = query.limit(limit)
        rows = query.all()

    fieldnames = [
        'id', 'title', 'self_text', 'subreddit', 'model_name', 'prompt', 'generated_at'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                'id': r.id,
                'title': r.title,
                'self_text': r.self_text,
                'subreddit': r.subreddit or '',
                'model_name': r.model_name or '',
                'prompt': r.prompt or '',
                'generated_at': r.generated_at.isoformat() if isinstance(r.generated_at, datetime) else str(r.generated_at),
            })


def main():
    parser = argparse.ArgumentParser(description='Export AI generated posts to CSV')
    parser.add_argument('-o', '--output', default='ai_posts_export.csv', help='Output CSV file path')
    parser.add_argument('-n', '--limit', type=int, default=None, help='Max number of rows to export')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    args = parser.parse_args()

    export_ai_posts(args.output, args.limit, args.offset)
    print(f"Exported AI posts to {args.output}")


if __name__ == '__main__':
    main()


