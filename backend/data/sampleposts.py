import argparse
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sample N rows from a database table and output as JSON",
    )
    parser.add_argument(
        "--table",
        required=True,
        help="Table to read from (e.g., posts, humorposts, ai_generated_posts)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=10,
        help="Number of rows to fetch (default: 10)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="-",
        help="Output file path (default: - for stdout)",
    )
    parser.add_argument(
        "--subreddit",
        action="append",
        default=[],
        help=(
            "Restrict to specific subreddit(s). "
            "Pass multiple times or comma-separated (exact match)."
        ),
    )
    return parser.parse_args()


def get_engine() -> Engine:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is required. Set it to your external database (e.g., postgresql+psycopg://user:pass@host:5432/slop)"
        )
    return create_engine(database_url, pool_pre_ping=True)


def json_safe(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def dump_rows_as_json(rows: list[dict[str, Any]], out_path: str) -> None:
    data = [
        {k: json_safe(v) for k, v in row.items()}
        for row in rows
    ]
    if out_path == "-":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def validate_table_name(engine: Engine, table: str) -> str:
    # Restrict to known tables to avoid SQL injection through identifiers.
    # Extend this whitelist as your schema evolves.
    allowed_tables = {
        "posts",
        "humorposts",
        "ai_generated_posts",
    }
    if table not in allowed_tables:
        raise ValueError(
            f"Invalid --table '{table}'. Allowed: {', '.join(sorted(allowed_tables))}"
        )
    return table


def fetch_sample(engine: Engine, table: str, limit: int, subreddits: Optional[list[str]] = None) -> list[dict[str, Any]]:
    # Use ORDER BY random() which is supported on Postgres
    params: dict[str, Any] = {"limit": limit}

    # Build optional subreddit filter
    sub_filter = ""
    if subreddits:
        placeholders = ", ".join([f":sub_{i}" for i in range(len(subreddits))])
        sub_filter = f" AND subreddit IN ({placeholders})"
        for i, name in enumerate(subreddits):
            params[f"sub_{i}"] = name

    if table == "humorposts":
        sql = text(
            f"SELECT * FROM {table} "
            "WHERE self_text != '' AND image_url IS NULL "
            "AND (subreddit IS NULL OR subreddit NOT ILIKE '%joke%')"
            f"{sub_filter} ORDER BY random() LIMIT :limit"
        )
    else:
        where_clause = f"WHERE true{sub_filter}" if sub_filter else ""
        sql = text(f"SELECT * FROM {table} {where_clause} ORDER BY random() LIMIT :limit")
    with engine.connect() as conn:
        result = conn.execute(sql, params)
        rows = [dict(row._mapping) for row in result]
    return rows


def main() -> None:
    args = parse_args()
    if args.limit <= 0:
        print("--limit must be > 0", file=sys.stderr)
        sys.exit(2)

    engine = get_engine()
    table = validate_table_name(engine, args.table)
    # Normalize subreddit inputs (support repeated flags and comma-separated values)
    subs: list[str] = []
    for item in (args.subreddit or []):
        subs.extend([s.strip() for s in item.split(',') if s.strip()])
    subs = list(dict.fromkeys(subs))  # de-duplicate, preserve order

    rows = fetch_sample(engine, table, args.limit, subreddits=subs or None)
    dump_rows_as_json(rows, args.out)


if __name__ == "__main__":
    main()


