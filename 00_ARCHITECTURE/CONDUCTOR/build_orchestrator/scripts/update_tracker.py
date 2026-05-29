#!/usr/bin/env python3
"""Update state.json tracker — idempotent, atomic write via temp+rename."""
import json, sys, os, argparse, tempfile, shutil
from datetime import datetime, timezone

TRACKER = os.path.join(os.path.dirname(__file__), '..', 'tracker', 'state.json')

def load():
    with open(TRACKER) as f:
        return json.load(f)

def save(data):
    tmp = TRACKER + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    shutil.move(tmp, TRACKER)

def find_item(data, item_id):
    for track in data.get('tracks', []):
        for item in track.get('items', []):
            if item['id'] == item_id:
                return item
    return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--item', help='Item ID (e.g. G20, INF1, ACC1)')
    p.add_argument('--brief', help='Brief status')
    p.add_argument('--impl', help='Impl status')
    p.add_argument('--session', help='Session ID')
    p.add_argument('--branch', help='Branch name')
    p.add_argument('--merge-sha', help='Merge commit SHA')
    p.add_argument('--activity', help='Activity log message')
    p.add_argument('--workstream', help='Workstream-level status (complete/paused)')
    args = p.parse_args()

    data = load()
    now = datetime.now(timezone.utc).isoformat()

    if args.item:
        item = find_item(data, args.item)
        if item is None:
            print(f"WARN: item {args.item} not found in tracker", file=sys.stderr)
        else:
            if args.brief:
                item.setdefault('brief', {})['status'] = args.brief
            if args.impl:
                item.setdefault('impl', {})['status'] = args.impl
                if args.impl == 'in_progress':
                    item['impl']['started_at'] = now
                if args.impl in ('merged_main', 'deployed', 'verified'):
                    item['impl']['completed_at'] = now
            if args.session:
                item.setdefault('impl', {})['session_id'] = args.session
            if args.branch:
                item.setdefault('impl', {})['branch'] = args.branch
            if args.merge_sha:
                item.setdefault('impl', {})['merge_sha'] = args.merge_sha

    if args.activity:
        data.setdefault('activity', []).insert(0, {
            'time': now,
            'text': args.activity
        })
        data['activity'] = data['activity'][:100]  # keep last 100

    if args.workstream:
        data.setdefault('meta', {})['workstream_status'] = args.workstream
        data['meta']['last_updated'] = now[:10]

    data['meta']['last_updated'] = now[:10]
    save(data)
    print(f"OK: tracker updated — item={args.item or '-'} impl={args.impl or '-'} session={args.session or '-'}")

if __name__ == '__main__':
    main()
