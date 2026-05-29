#!/usr/bin/env python3
"""Update a session's status in session_queue.yaml. Idempotent, atomic write."""
import yaml, sys, os, shutil, argparse
from datetime import datetime, timezone

QUEUE = os.path.join(os.path.dirname(__file__), '..', 'session_queue.yaml')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('session_id')
    p.add_argument('--status', required=True,
                   choices=['pending','in_progress','complete','failed','blocked'])
    p.add_argument('--retry-count', type=int)
    args = p.parse_args()

    with open(QUEUE) as f:
        data = yaml.safe_load(f)

    found = False
    for session in data.get('sessions', []):
        if session['id'] == args.session_id:
            session['status'] = args.status
            session['updated_at'] = datetime.now(timezone.utc).isoformat()
            if args.retry_count is not None:
                session['retry_count'] = args.retry_count
            found = True
            break

    if not found:
        print(f"ERROR: session {args.session_id} not found", file=sys.stderr)
        sys.exit(1)

    tmp = QUEUE + '.tmp'
    with open(tmp, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    shutil.move(tmp, QUEUE)
    print(f"OK: {args.session_id} -> {args.status}")

if __name__ == '__main__':
    main()
