import os
import json
from datetime import datetime
from typing import Dict, List

from flask import Blueprint, jsonify, request, send_from_directory
from sqlalchemy.sql import text

from db import db_session


datasets = Blueprint('datasets', __name__)


# Default categories used if none are configured yet
CATEGORIES_DEFAULT: List[str] = [
    'circlejerk',
    'jokes + puns',
    'gaming',
    'animals',
    'personal',
    'personal + gaming',
]


def _datasets_dir() -> str:
    # Absolute path to the project-level datasets directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'datasets'))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _category_file_path(category: str) -> str:
    return os.path.join(_datasets_dir(), f"{category}.json")


def _categories_file_path() -> str:
    return os.path.join(_datasets_dir(), "_categories.json")


def _read_categories() -> List[str]:
    path = _categories_file_path()
    if not os.path.exists(path):
        return list(CATEGORIES_DEFAULT)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                # Ensure all names are strings
                return [str(x) for x in data]
    except Exception:
        pass
    return list(CATEGORIES_DEFAULT)


def _write_categories(categories: List[str]) -> None:
    path = _categories_file_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)


def _read_category_items(category: str) -> List[Dict]:
    path = _category_file_path(category)
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _write_category_items(category: str, items: List[Dict]) -> None:
    path = _category_file_path(category)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


@datasets.route('/ui')
def datasets_ui():
    # Serve the static UI at /datasets/ui
    return send_from_directory(_datasets_dir(), 'index.html')


@datasets.route('/static/<path:filename>')
def datasets_static(filename: str):
    # Serve assets referenced by the UI
    return send_from_directory(_datasets_dir(), filename)


@datasets.route('/random')
def random_posts():
    try:
        limit = int(request.args.get('limit') or 10)
        if limit <= 0:
            limit = 10
    except Exception:
        limit = 10

    sql = text(
        """
        SELECT source, id, title, self_text, subreddit
        FROM (
            SELECT 'posts' AS source, p.id, p.title, p.self_text, p.subreddit
            FROM posts p
            UNION ALL
            SELECT 'humorposts' AS source, h.id, h.title, h.self_text, h.subreddit
            FROM humorposts h
        ) AS unioned
        ORDER BY RANDOM()
        LIMIT :limit
        """
    )

    with db_session() as session:
        rows = session.execute(sql, {"limit": limit}).mappings().all()

    posts = []
    for r in rows:
        posts.append({
            'source': r['source'],
            'id': r['id'],
            'title': r['title'],
            'self_text': r['self_text'],
            'subreddit': r['subreddit'],
        })

    return jsonify({
        'posts': posts,
        'count': len(posts)
    })


@datasets.route('/annotate', methods=['POST'])
def annotate():
    data = request.get_json(silent=True) or {}
    category = data.get('category')
    post = data.get('post') or {}

    cats = _read_categories()
    if category not in cats:
        return jsonify({
            'ok': False,
            'error': 'invalid_category',
            'allowed': cats,
        }), 400

    # Required post fields
    source = post.get('source')
    source_id = post.get('id')
    title = post.get('title')
    self_text = post.get('self_text')
    subreddit = post.get('subreddit')

    if not source or source not in ('posts', 'humorposts') or source_id is None:
        return jsonify({'ok': False, 'error': 'invalid_post'}), 400

    items = _read_category_items(category)
    # Dedupe by (source, id)
    exists = any((it.get('source') == source and it.get('id') == source_id) for it in items)
    if not exists:
        items.append({
            'source': source,
            'id': source_id,
            'title': title,
            'self_text': self_text,
            'subreddit': subreddit,
            'selected_at': datetime.utcnow().isoformat() + 'Z',
        })
        _write_category_items(category, items)

    return jsonify({'ok': True, 'added': not exists, 'count': len(items)})


@datasets.route('/stats')
def stats():
    counts: Dict[str, int] = {}
    cats = _read_categories()
    for cat in cats:
        items = _read_category_items(cat)
        counts[cat] = len(items)
    target = 500
    return jsonify({'counts': counts, 'target': target, 'categories': cats})


@datasets.route('/categories', methods=['GET', 'POST', 'DELETE'])
def categories():
    if request.method == 'GET':
        cats = _read_categories()
        return jsonify({'ok': True, 'categories': cats})

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'ok': False, 'error': 'invalid_name'}), 400
        cats = _read_categories()
        if name not in cats:
            cats.append(name)
            _write_categories(cats)
        return jsonify({'ok': True, 'added': name in cats, 'categories': cats})

    # DELETE
    name = (request.args.get('name') or '').strip()
    if not name:
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'ok': False, 'error': 'invalid_name'}), 400
    cats = _read_categories()
    if name in cats:
        cats = [c for c in cats if c != name]
        _write_categories(cats)
        removed = True
    else:
        removed = False
    return jsonify({'ok': True, 'removed': removed, 'categories': cats})


