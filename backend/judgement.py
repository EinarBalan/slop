import os
import json
import threading
from typing import List, Dict, Any, Tuple

from flask import Blueprint, jsonify, request, send_from_directory


judgement = Blueprint('judgement', __name__)


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _data_dir() -> str:
    path = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(path, exist_ok=True)
    return path


def _generated_root() -> str:
    # backend/data/generated/train_size_ablation
    path = os.path.join(_data_dir(), 'generated', 'train_size_ablation')
    return path


def _judgements_file_path() -> str:
    return os.path.join(_data_dir(), 'size_ablation_judgements.json')


# In-process lock to serialize read-modify-write cycles on the judgements file
_J_LOCK = threading.Lock()


def _read_json_file(path: str) -> Any:
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _write_json_file(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + '.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)


def _list_json_files() -> List[str]:
    base = _generated_root()
    files: List[str] = []
    if not os.path.exists(base):
        return files
    for root, _dirs, filenames in os.walk(base):
        for name in filenames:
            if name.endswith('.json'):
                full_path = os.path.join(root, name)
                # Return as a path relative to backend/data for clarity in the UI
                rel_to_data = os.path.relpath(full_path, _data_dir())
                files.append(rel_to_data)
    files.sort()
    return files


def _discover_options() -> List[Dict[str, str]]:
    options: List[Dict[str, str]] = []
    root = _generated_root()
    if not os.path.exists(root):
        return options
    for provider in sorted(os.listdir(root)):
        p_dir = os.path.join(root, provider)
        if not os.path.isdir(p_dir):
            continue
        for model in sorted(os.listdir(p_dir)):
            m_dir = os.path.join(p_dir, model)
            if not os.path.isdir(m_dir):
                continue
            for topic in sorted(os.listdir(m_dir)):
                t_dir = os.path.join(m_dir, topic)
                if not os.path.isdir(t_dir):
                    continue
                # ensure there are json files
                has_json = any(name.endswith('.json') for name in os.listdir(t_dir))
                if has_json:
                    options.append({'provider': provider, 'model': model, 'topic': topic})
    return options


def _iter_topic_files(provider: str, model: str, topic: str) -> List[str]:
    base = os.path.join(_generated_root(), provider, model, topic)
    paths: List[str] = []
    if not os.path.exists(base):
        return paths
    for name in os.listdir(base):
        if name.endswith('.json'):
            full = os.path.join(base, name)
            rel_to_data = os.path.relpath(full, _data_dir())
            paths.append(rel_to_data)
    paths.sort()
    return paths


@judgement.route('/judgement')
def serve_ui():
    # Serve the static UI at /judgement
    return send_from_directory(_data_dir(), 'judgement.html')


@judgement.route('/judgement/api/files')
def api_list_files():
    return jsonify({'ok': True, 'files': _list_json_files()})


@judgement.route('/judgement/api/file')
def api_get_file():
    path = (request.args.get('path') or '').strip()
    if not path:
        return jsonify({'ok': False, 'error': 'missing_path'}), 400
    # Only allow paths under data dir
    full_path = os.path.abspath(os.path.join(_data_dir(), path))
    if not full_path.startswith(_data_dir() + os.sep):
        return jsonify({'ok': False, 'error': 'invalid_path'}), 400
    if not os.path.exists(full_path):
        return jsonify({'ok': False, 'error': 'not_found'}), 404
    try:
        posts = _read_json_file(full_path) or []
        # Normalize to list of dicts
        if not isinstance(posts, list):
            posts = []
        # Attach index for stable identification on the client
        normalized: List[Dict[str, Any]] = []
        for idx, p in enumerate(posts):
            if isinstance(p, dict):
                normalized.append({
                    'index': idx,
                    'title': p.get('title') or '',
                    'self_text': p.get('self_text') or '',
                    'subreddit': p.get('subreddit') or '',
                })
        return jsonify({'ok': True, 'file_path': path, 'count': len(normalized), 'posts': normalized})
    except Exception as e:
        return jsonify({'ok': False, 'error': 'read_error', 'detail': str(e)}), 500


@judgement.route('/judgement/api/options')
def api_options():
    return jsonify({'ok': True, 'options': _discover_options()})


@judgement.route('/judgement/api/mixed')
def api_mixed():
    from random import shuffle

    provider = (request.args.get('provider') or '').strip()
    model = (request.args.get('model') or '').strip()
    topic = (request.args.get('topic') or '').strip()
    if not provider or not model or not topic:
        return jsonify({'ok': False, 'error': 'missing_params'}), 400

    # Load posts from all size files under the selection
    file_rels = _iter_topic_files(provider, model, topic)
    mixed: List[Dict[str, Any]] = []
    for rel in file_rels:
        full_path = os.path.join(_data_dir(), rel)
        items = _read_json_file(full_path)
        if not isinstance(items, list):
            continue
        for idx, p in enumerate(items):
            if not isinstance(p, dict):
                continue
            mixed.append({
                'title': p.get('title') or '',
                'self_text': p.get('self_text') or '',
                'subreddit': p.get('subreddit') or '',
                # Track the originating file for later percentage saving
                'file_path': rel,
                'local_index': idx,
            })
    shuffle(mixed)
    return jsonify({'ok': True, 'count': len(mixed), 'posts': mixed})


@judgement.route('/judgement/api/shown', methods=['POST'])
def api_shown_counts():
    data = request.get_json(silent=True) or {}
    file_counts = data.get('file_counts') or {}
    if not isinstance(file_counts, dict):
        return jsonify({'ok': False, 'error': 'invalid_payload'}), 400

    # Validate files exist under allowed root
    known = set(_list_json_files())
    entries: List[Dict[str, Any]] = []
    for file_path, delta in file_counts.items():
        if file_path not in known:
            # skip unknowns silently to be resilient
            continue
        try:
            d = int(delta)
        except Exception:
            continue
        if d <= 0:
            continue
        entries.append({'file_path': file_path, 'delta': d})

    if not entries:
        return jsonify({'ok': True, 'updated': 0})

    path = _judgements_file_path()
    with _J_LOCK:
        content = _read_json_file(path)
        if not isinstance(content, list):
            content = []

        # Index existing by file_path
        index: Dict[str, Dict[str, Any]] = {}
        for entry in content:
            if isinstance(entry, dict) and 'file_path' in entry:
                index[entry['file_path']] = entry

        updated = 0
        for e in entries:
            fp = e['file_path']
            delta = e['delta']
            if fp in index:
                rec = index[fp]
            else:
                rec = {'file_path': fp, 'adherence': 0, 'coherence': 0}
                content.append(rec)
                index[fp] = rec
            current = rec.get('shown_count') or 0
            try:
                current = int(current)
            except Exception:
                current = 0
            rec['shown_count'] = current + delta
            updated += 1

        _write_json_file(path, content)
    return jsonify({'ok': True, 'updated': updated})


@judgement.route('/judgement/api/update', methods=['POST'])
def api_update_summary():
    data = request.get_json(silent=True) or {}
    file_path = (data.get('file_path') or '').strip()
    # Support new count-based fields; fall back to adherence/coherence if provided
    adh_count = data.get('adh_count')
    coh_count = data.get('coh_count')
    if adh_count is None and 'adherence' in data:
        adh_count = data.get('adherence')
    if coh_count is None and 'coherence' in data:
        coh_count = data.get('coherence')

    if not file_path:
        return jsonify({'ok': False, 'error': 'missing_file_path'}), 400
    # Validate the path is one of the known files
    known = set(_list_json_files())
    if file_path not in known:
        return jsonify({'ok': False, 'error': 'unknown_file'}), 400

    try:
        a_val = int(adh_count)
        c_val = int(coh_count)
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid_counts'}), 400
    # Ensure non-negative
    if a_val < 0 or c_val < 0:
        return jsonify({'ok': False, 'error': 'invalid_counts'}), 400

    path = _judgements_file_path()
    with _J_LOCK:
        content = _read_json_file(path)
        if not isinstance(content, list):
            content = []

        # Update or insert (store counts)
        updated = False
        for entry in content:
            if isinstance(entry, dict) and entry.get('file_path') == file_path:
                entry['adherence'] = a_val
                entry['coherence'] = c_val
                updated = True
                break
        if not updated:
            content.append({
                'file_path': file_path,
                'adherence': a_val,
                'coherence': c_val,
            })

        _write_json_file(path, content)
    return jsonify({'ok': True})


