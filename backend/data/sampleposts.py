import argparse
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Any

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
        "users",
        "interactions",
        "served_posts",
        "experiments",
    }
    if table not in allowed_tables:
        raise ValueError(
            f"Invalid --table '{table}'. Allowed: {', '.join(sorted(allowed_tables))}"
        )
    return table


def fetch_sample(engine: Engine, table: str, limit: int) -> list[dict[str, Any]]:
    # Use ORDER BY random() which is supported on Postgres
    sql = text(f"SELECT * FROM {table} ORDER BY random() LIMIT :limit")
    with engine.connect() as conn:
        result = conn.execute(sql, {"limit": limit})
        rows = [dict(row._mapping) for row in result]
    return rows


def main() -> None:
    args = parse_args()
    if args.limit <= 0:
        print("--limit must be > 0", file=sys.stderr)
        sys.exit(2)

    engine = get_engine()
    table = validate_table_name(engine, args.table)
    rows = fetch_sample(engine, table, args.limit)
    dump_rows_as_json(rows, args.out)


if __name__ == "__main__":
    main()


