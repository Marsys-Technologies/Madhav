#!/usr/bin/env python3
"""Read-only owner dashboard. Runtime uses only the Python standard library."""
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit
from urllib.request import urlopen

UTC = timezone.utc
ROOT = Path(__file__).resolve().parent
STATUSES = {'done', 'not_applicable', 'running', 'review', 'ready', 'waiting', 'blocked', 'parked', 'unknown'}
GROUPS = {'done': 'done', 'not_applicable': 'done', 'running': 'in_progress',
          'review': 'in_progress', 'ready': 'ready', 'waiting': 'waiting',
          'blocked': 'stuck', 'parked': 'stuck', 'unknown': 'waiting'}
LABELS = {'done': 'Done', 'not_applicable': 'Not needed', 'running': 'In progress',
          'review': 'Being checked', 'ready': 'Ready to start', 'waiting': 'Waiting on earlier work',
          'blocked': 'Stuck', 'parked': 'Set aside', 'unknown': 'Not yet measured'}
# (I) INTERPRETATION: presentation-only summaries of the tracker titles; never used for counts.
TITLES = dict(line.split('|', 1) for line in '''B-0|Check the campaign specifications
B-4|Record the campaign opening and coordination
B-1a|Preserve the tracker and earlier campaign work
B-1b|Improve work assignment and completion checks
B-1c|Independently test the campaign controls
B-5|Complete the handover from the earlier campaign
B-6|Check that the operations service is ready
B-1p|Prepare the launch changes for review
B-1v|Independently review the launch changes
B-1|Integrate the accepted launch changes
B-2|Install and check the campaign controls
B-3b|Check the practice environments and required tests
B-3|Accept the worker environments
B-7|Approve launch with the first worker
B-8|Observe the first accepted work before adding workers
B-6r|Keep the operations service safely up to date
B-CLAIM-RECOVERY|Preserve ownership when interrupted work resumes
B-K-INBOX|Make workers read current directions before resuming
B-DEPLOY-DIAG|Investigate and verify a failed deployment
B-DB-BASELINE|Prepare each worker's practice data
KV3-B-OPS-CONTRACT|Agree and test the shared operations contract
K0a-0|Prove the campaign tests actually run
K0a-1a|Standardise names and calculation conventions
K0a-1b|Make repeated operations safe
K0a-1c|Share event categories and safe resumption
K0a-1|Complete the shared foundations
K0a-2|Repair references used by the timing system
K0a-4|Carry one assertion through the whole system and test it
K0-SV|Agree calculation and certification contracts with Suvarṇa
K1-1a|Build the shared period and timing foundations
K1-1b|Add named period methods and their conditions
K2-1a|Connect promises, relationships and event categories
K2-1b|Represent cancellations and exceptions explicitly
K2-2|Resolve relationships before matching rules
K1-2|Present periods with their conditions and promises
K7-1b|Connect every view to the shared service
K7-2|Correct stale counts and label contextual periods
K7-3|Show evidence quality and distinguish missing findings
K7-4|Connect the comparison method to priorities
KA-2|Register rules with their prerequisites and sources
KA-3a|Represent transit obstructions over time
KA-3b|Qualify disputed methods and disclose coverage
KA-4|Build calendar and auspicious-time services
KA-4b|Show cited cancellations within their allowed scope
K3-1|Rebuild obstruction findings on test examples
K3-2|Connect obstruction findings to verified real records
K4-1|Share measurement preparation and comparison experiments
K4-2b|Remove superseded convergence calculations safely
K4-3|Attach canonical claims without double counting
K5-G1a|Connect suppression inputs and pin timing correctly
K5-G1b|Test insight thresholds and freeze the baseline
VC-1|Freeze the evaluation rules before results exist
VC-2|Run the three evaluation comparisons
K5-2|Test the compact representation against the numerical contract
K5-2b|Adopt the compact representation while preserving earlier data
K5-3|Specify and implement the replacement model
K6-4|Present monthly event measures with units
K6-5a|Test the issued-forecast lifecycle contract
K6-5|Record immutable forecasts only when delivered
K8-R26|Reconcile certification checks with the live rules
K8-REG|Make the registry describe actual readers and writers
K9-1|Rehearse a complete Kāla build
K9-4a|Run the protected production rebuild
K9-4b|Verify and publish the rebuilt results
K9-5|Rehearse certification across the Kāla assets
K9-6|Verify all seven live views after publication
KR-1|Remove replaced code after its successor is published
KR-2|Retire duplicate writers after redirecting their reader
K0a-3|Record candidate builds and publication evidence
K7-1a|Register the seven shared views
KA-1e|Build the transit calculation engine
KA-1w|Connect transit calculations to storage and views
K4-2aw|Build and qualify the convergence writer
K4-2a|Build the convergence foundations
K6-123|Build the three timing and life-period views
K9-23|Build publication, verification and rollback operations
K-CERT|Expose the evidence tier required for certification
K-CERT-2|Register and verify the citation-resolution writer
K-AVADHI-C|Resolve or explicitly rescope a failing period check
KV3-SCHEMA-1|Add the evidence-tier storage needed for certification
J-0|Accept the inherited work and ownership inventory
J-0m|Turn inherited work into individually checkable tasks
J-1a|Prepare the small-test operations
J-2a|Run the first small test
J-2b|Check and remove the first small test
J-2c|Run the second small test
J-2d|Check and remove the second small test
J-3a|Prepare the measuring build
J-3b|Prepare independent measurement checks
J-3c|Run the measuring build
J-3d|Read back, report and remove the measuring build
J-4a|Resolve final-build decisions and period prerequisites
J-4p|Use the chart's verified settled period build
J-4b|Apply and verify protected changes
J-4c|Integrate the final rules and their independent checks
J-4d|Build and qualify a final-rules candidate
J-4e|Start the full-century build
J-4f|Observe and verify the completed full build
J-5q|Evaluate the built generation against every required check
J-5s|Independently verify and seal the new generation
J-6a|Serve sealed results and refuse test-only results
J-6m|Prepare and verify the publication authority change
J-6r|Rehearse reader switchover and rollback
J-6|Switch to the accepted generation
J-6l|Verify the live switchover and observe stability
J-7a|Retire the legacy transit writer
J-7|Evaluate Sudarśana as an additional judge method
J-7b|Record the forecast layer's reading contract
J-8a|Resolve remaining earlier work and archive its records
J-8|Complete the earlier campaign's close report
J-0a|Inventory open inherited changes
J-0b|Inventory earlier tasks, decisions and holds
J-0c|Assign evidence-backed dispositions and landing stages
J-0d|Map shared-file ownership and required waits
J-GOCHARA-TIMEOUT|Adjust the measured build time limit and verify it
L0-M|Extract cited auspicious-time cancellation rules
L0-K|Admit the KP source material into the served corpus
L0-K-RUNNER|Repair and test the source-ingestion runner
V-K0a|Review the shared foundations
V-K12|Review periods and promises
V-K7|Review the seven owner-facing views
V-KA|Review adapters and services
V-K3|Review obstruction findings on examples
V-K3b|Review obstruction findings on real records
V-K4|Review convergence
V-VC|Review the value evaluation against the frozen rules
V-K5|Review the forecasting work
V-K6|Review the timing and forecast records
V-J6|Review sealing, switchover and rollback evidence
V-K9|Review the complete rebuilt layer
D-R5|Decide asset naming and storage
D-R6|Decide how comparisons feed priorities
D-R8|Decide how disputed methods are qualified
D-R9|Decide the conditions for retaining the century-build hold
D-R11|Decide ownership of issued-forecast records
D-KR|Decide retirement of duplicate writers
D-VC|Decide the value-checkpoint outcome
D-COMPACT|Decide whether to admit the compact representation
D-G2|Decide whether to open the replacement-model work
D-TEARDOWN|Decide whether small-test cleanup is authorised
D-G9|Decide the supported forecast horizon
D-CLOUD|Authorise the full-century candidate build
D-FLIP|Authorise switching to the verified generation
D-T2|Decide admission of additional judge methods
D-GOCHARA-TIMEOUT|Decide the measured build time limit
D-RETIRE-B-K-INBOX|Decide retirement of the earlier worker-inbox task
D-RETIRE-B-CLAIM-RECOVERY|Decide retirement of the earlier ownership-recovery task
JOIN-ALL|Check all retained results, gaps and deferred work
C-1|Complete the close report
C-2|Validate and record the campaign close
C-3|Stop workers and release their resources
C-4|Independently accept final closure and shutdown'''.splitlines())
TRACK_TEXT = {
    'B': ('Launch preparation', 'Checks and setup needed before the campaign can launch.'),
    'CTRL': ('Campaign controls', 'Owner-directed improvements to the controls, with independent review.'),
    'K': ('Kāla timing engine', 'Build and verify the timing engine in the agreed order.'),
    'J': ('Transit judgment', 'Complete inherited transit work through the verified generation change.'),
    'L': ('Source material', 'Extract and admit the source material needed by the timing work.'),
    'V': ('Independent reviews', 'Review each completed batch before it can be accepted.'),
    'N': ('Decisions', 'Resolve the reserved questions under the agreed evidence checks.'),
    'C': ('Project closure', 'Check retained results, report gaps and complete shutdown.'),
}


def parse_time(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.astimezone(UTC) if dt.tzinfo else None
    except ValueError:
        return None


def plain_text(value, limit=220):
    """Remove file references and expand common jargon without inventing a reason."""
    text = str(value or '')
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'(?:[\w.~@+-]+/)+[\w./@+-]+|\b[\w.-]+\.(?:py|jsonl?|md|ts|sql|sh|yaml|yml|html|plist)\b',
                  'the supporting record', text, flags=re.I)
    for old, new in [('PR', 'change'), ('CI', 'automated checks'), ('DB', 'data store'),
                     ('exact-head', 'exact version'), ('readback', 'verification'),
                     ('precheck', 'preliminary checks'), ('guarded completion', 'checked completion'),
                     ('detector matched', 'The required check matched'),
                     ('checked completion pending', 'completion awaits confirmation'),
                     ('commits', 'code changes'), ('squash', 'integrated version'),
                     ('BLOCKING', 'blocking'), ('ACCEPTED', 'accepted'), ('READY', 'ready')]:
        text = re.sub(r'\b' + re.escape(old) + r'\b', new, text)
    text = re.sub(r'\b(?:L[0-5]|G\d+)\b', 'the relevant layer', text)
    text = re.sub(r'\b[a-z]+_[a-z0-9_]+\b', 'the relevant component', text)
    text = re.sub(r'\b[0-9a-f]{9,64}\b', 'a recorded version', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Sentence boundaries come after removing dotted filenames.
    text = re.split(r'(?<=[.!?])\s+', text, maxsplit=1)[0]
    if len(text) > limit:
        text = text[:limit].rsplit(' ', 1)[0].rstrip(' ,;:') + '…'
    return text


# Deferred items (the tracker's `deferred` row flag: out of this campaign by ruling, not finished) are their own bucket: never
# counted as done, never "stuck", never in attention. Only the set-aside statuses fold in; a failed or conflicting one stays visible.
DEFERRED_QUIET = {'blocked', 'parked', 'unknown'}


def is_deferred(item):
    return item.get('deferred') is True and item['status'] in DEFERRED_QUIET


def present_item(item):
    status = item['status']
    deferred = is_deferred(item)
    return {'id': item['id'], 'title': TITLES.get(item['id']) or plain_text(item['title'], 130),
            'status': status, 'status_label': 'Deferred' if deferred else LABELS[status],
            'group': 'deferred' if deferred else GROUPS[status],
            'owner': plain_text(item.get('owner'), 80), 'detail': plain_text(item.get('detail')),
            'since': item.get('started_at') or item.get('updated_at'),
            'updated_at': item.get('updated_at'), 'depends_on': item.get('depends_on', [])}


def engine_status(health):
    if health.get('emergency_hold') is True:
        return 'emergency hold'
    if health.get('hold') is True or health.get('paused') is True:
        return 'paused'
    age = health.get('engine_tick_age_s')
    if health.get('hold') is False and isinstance(age, (int, float)) and 0 <= age < 10:
        return 'running'
    return None


def validate_state(state):
    if not isinstance(state, dict) or not parse_time(state.get('generated_at')):
        raise ValueError('Missing tracker observation time')
    if not isinstance(state.get('tracks'), list) or not isinstance(state.get('health'), dict):
        raise ValueError('Incomplete tracker state')
    seen = set()
    for track in state['tracks']:
        if (not isinstance(track, dict) or not isinstance(track.get('items'), list)
                or not all(isinstance(track.get(k), str) for k in ('id', 'title', 'plain'))):
            raise ValueError('Incomplete workstream')
        for item in track['items']:
            if (not isinstance(item, dict)
                    or not all(isinstance(item.get(k), str) for k in ('id', 'title', 'status'))
                    or item['status'] not in STATUSES or item['id'] in seen):
                raise ValueError('Unrecognised or duplicate item')
            seen.add(item['id'])
    if not isinstance(state.get('native_queue'), list):
        raise ValueError('Owner decision queue unavailable')
    for decision in state['native_queue']:
        if not isinstance(decision, dict) or not all(isinstance(decision.get(k), str) for k in ('id', 'title')):
            raise ValueError('Incomplete owner decision')


def wave_group(item):
    # J-W4-* joins are included by the same J- prefix rule (D-21).
    return 'wave4' if item['id'].startswith('J-') else 'rest'


def closure_class(item):
    if item['id'].startswith('V-'):
        return 'verdict'
    if item['id'].startswith('J-0'):
        return 'planning'
    # (I) INTERPRETATION: only tracker-declared code earns capability credit.
    # Untyped joins, decisions and registration records conservatively count as planning.
    return 'capability' if item.get('completion_kind') == 'code' else 'planning'


SCOPE_CHANGE = {'at': '2026-10-14T19:04:00+00:00', 'before': 152, 'after': 213,
                'label': 'Scope grew: 152 → 213 items · 14 Oct 19:04 UTC'}


def compute_summary(state, first_done, now, first_complete=None, effort=None, scope_changes=()):
    validate_state(state)
    items = [present_item(i) for t in state['tracks'] for i in t['items']]
    counts = {s: sum(i['status'] == s for i in items) for s in STATUSES}
    raw_items = {i['id']: i for t in state['tracks'] for i in t['items']}
    completed = counts['done'] + counts['not_applicable']
    progress_lines = []
    for key, label in (('wave4', 'Wave 4 · Gochara 5.0'), ('rest', 'Everything else'), ('total', 'Total')):
        rows = [i for i in items if key == 'total' or wave_group(i) == key]
        progress_lines.append({'id': key, 'label': label, 'complete': sum(i['group'] == 'done' for i in rows),
                               'total': len(rows)})
    metrics = {'total': len(items), 'done': counts['done'], 'not_applicable': counts['not_applicable'],
               'complete': completed, 'percent': round(completed * 100 / len(items), 1) if items else None,
               'in_progress': counts['running'] + counts['review'], 'ready': counts['ready'],
               'waiting': sum(i['status'] in ('waiting', 'unknown') and i['group'] != 'deferred' for i in items),
               'stuck': sum(i['group'] == 'stuck' for i in items),
               'deferred': sum(i['group'] == 'deferred' for i in items),
               'completed_24h': None, 'completed_7d': None, 'pace_per_day': None, 'projected_finish': None}
    metrics.update(closures_24h=None, closures_7d=None,
                   agent_hours_24h=effort['agent_hours_24h'] if effort is not None else None,
                   agent_hours_7d=effort['agent_hours_7d'] if effort is not None else None,
                   agent_hours_per_closure_24h=None, agent_hours_per_closure_7d=None)
    tracks = []
    for track in state['tracks']:
        rows = [present_item(i) for i in track['items']]
        grouped = {g: sum(i['group'] == g for i in rows)
                   for g in ('done', 'in_progress', 'ready', 'waiting', 'stuck', 'deferred')}
        title, plain = TRACK_TEXT.get(track['id'], (plain_text(track['title']), plain_text(track['plain'])))
        tracks.append({'id': track['id'], 'title': title, 'plain': plain, 'total': len(rows),
                       'counts': grouped, 'items': rows,
                       'next': [i for i in rows if i['status'] in ('running', 'review', 'ready')][:2]})
    history, recent = None, None
    if first_done is not None:
        dated = [(i, first_done[i['id']]) for i in items
                 if i['status'] == 'done' and i['id'] in first_done and first_done[i['id']] <= now]
        dated.sort(key=lambda row: row[1], reverse=True)
        for window, delta in (('24h', timedelta(hours=24)), ('7d', timedelta(days=7))):
            closed = [i for i, dt in dated if now - delta <= dt <= now]
            metrics['completed_' + window] = len(closed)
            metrics['closures_' + window] = {
                kind: sum(closure_class(raw_items[i['id']]) == kind for i in closed)
                for kind in ('capability', 'verdict', 'planning')}
            hours = metrics['agent_hours_' + window]
            if hours is not None and closed:
                metrics['agent_hours_per_closure_' + window] = hours / len(closed)
        pace = metrics['completed_7d'] / 7
        metrics['pace_per_day'] = pace
        remaining = len(items) - completed
        if pace > 0:
            metrics['projected_finish'] = (now + timedelta(days=math.ceil(remaining / pace))).date().isoformat()
        complete_dates = first_complete if first_complete is not None else first_done
        dated_complete = [(i, complete_dates[i['id']]) for i in items
                          if i['group'] == 'done' and i['id'] in complete_dates and complete_dates[i['id']] <= now]
        changes = [dict(c) for c in (SCOPE_CHANGE, *scope_changes) if parse_time(c['at']) <= now]
        changes.sort(key=lambda c: parse_time(c['at']))
        start = min((dt for _, dt in dated_complete), default=now)
        if changes:
            start = min(start, parse_time(changes[0]['at']))
        day = datetime.combine(start.date() - timedelta(days=1), datetime.min.time(), UTC)
        # Day-end observations plus exact scope-change instants, with an explicit current observation.
        instants = {now}
        while day.date() <= now.date():
            instants.add(min(day + timedelta(days=1, microseconds=-1), now))
            day += timedelta(days=1)
        instants.update(parse_time(c['at']) for c in changes)
        series = []
        for at in sorted(instants):
            wave4 = sum(wave_group(i) == 'wave4' and dt <= at for i, dt in dated_complete)
            rest = sum(wave_group(i) == 'rest' and dt <= at for i, dt in dated_complete)
            # Historical scope is only known where the amendment or observed changes establish it.
            scope = changes[0]['before'] if changes else None
            for change in changes:
                if parse_time(change['at']) <= at:
                    scope = change['after']
            if at == now:
                scope = len(items)
            series.append({'date': at.date().isoformat(), 'at': at.isoformat(),
                           'done': sum(dt <= at for _, dt in dated), 'complete': wave4 + rest,
                           'wave4': wave4, 'rest': rest, 'total': scope})
        history = {'series': series, 'undated_done': counts['done'] - len(dated), 'dated_done': len(dated),
                   'undated_complete': completed - len(dated_complete), 'dated_complete': len(dated_complete),
                   'timezone': 'UTC', 'not_applicable': counts['not_applicable'], 'scope_changes': changes}
        recent = [{**i, 'completed_at': dt.isoformat()} for i, dt in dated[:20]]
    return {'observed_at': state['generated_at'], 'metrics': metrics, 'progress_lines': progress_lines, 'tracks': tracks, 'history': history,
            'working_items': [i for i in items if i['status'] in ('running', 'review')],
            'up_next': [i for i in items if i['status'] == 'ready'],
            'attention': [i for i in items if i['status'] in ('blocked', 'parked') and i['group'] != 'deferred'],
            'deferred': [i for i in items if i['group'] == 'deferred'],
            'owner_decisions': [{'id': d['id'], 'title': TITLES.get(d['id']) or plain_text(d['title']),
                                 'detail': plain_text(d.get('recommendation')), 'status': d.get('status')}
                                for d in state['native_queue']],
            'milestones': [i for i in items if i['id'].startswith('V-')]
                          + sorted([i for i in items if i['id'] in ('C-1', 'C-2', 'C-3', 'C-4')], key=lambda i: i['id']),
            'recently_completed': recent, 'engine_status': engine_status(state['health'])}


class EventHistory:
    """Keep first done/complete timestamps and a byte offset; no disk cache or full-log retention."""
    def __init__(self, path):
        self.path = Path(path)
        self.identity = None
        self.offset = 0
        self.first_done = {}
        self.first_complete = {}

    def read(self):
        with self.path.open('rb') as stream:
            stat = os.fstat(stream.fileno())
            identity = (stat.st_dev, stat.st_ino)
            if identity != self.identity or stat.st_size < self.offset:
                self.identity, self.offset, self.first_done, self.first_complete = identity, 0, {}, {}
            stream.seek(self.offset)
            while True:
                position = stream.tell()
                line = stream.readline()
                if not line or not line.endswith(b'\n'):
                    break  # Retry an unfinished append next time.
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError('Invalid event record')
                    if event.get('kind') == 'item' and event.get('state') in ('done', 'not_applicable'):
                        dt, item = parse_time(event.get('ts')), event.get('item')
                        if not dt or not isinstance(item, str):
                            raise ValueError('Invalid completion record')
                        self.first_complete[item] = min(dt, self.first_complete.get(item, dt))
                        if event['state'] == 'done':
                            self.first_done[item] = min(dt, self.first_done.get(item, dt))
                except (ValueError, UnicodeError) as exc:
                    self.offset = position
                    raise ValueError('Completion history contains an unreadable record') from exc
                self.offset = stream.tell()
        return dict(self.first_done)


def process_rows(processes):
    rows = {}
    for line in processes.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
        try:
            args = shlex.split(parts[1])
        except ValueError:
            continue
        if args:
            exe = Path(args[0]).name
            engine = 'Codex' if exe == 'codex' and 'exec' in args[1:] else 'Claude' if exe == 'claude' else None
            rows[int(parts[0])] = (engine, args)
    return rows


def job_start(name):
    match = re.match(r'[XJ]-(\d{8}T\d{6}Z)', name)
    return datetime.strptime(match[1], '%Y%m%dT%H%M%SZ').replace(tzinfo=UTC) if match else None


def job_effort(directory, now):
    """(I) INTERPRETATION: all finished direct jobs in the window, including rework/reviews.

    This measures campaign effort / recorded closures, as in A2's 45 hours / 8 items;
    it does not attribute a multi-item job to a guessed item. Whole durations belong
    to the window containing DONE, not to the day of launch. Active jobs are excluded.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise OSError('Job timing unavailable')
    hours = {'agent_hours_24h': 0.0, 'agent_hours_7d': 0.0}
    for job in directory.glob('X-*'):
        done = job / 'DONE'
        if not job.is_dir() or not done.is_file():
            continue
        end = datetime.fromtimestamp(done.stat().st_mtime, UTC)
        if not now - timedelta(days=7) <= end <= now:
            continue
        start = job_start(job.name)
        if start is None or end < start:
            raise ValueError('Invalid job timing')
        duration = (end - start).total_seconds() / 3600
        hours['agent_hours_7d'] += duration
        if end >= now - timedelta(hours=24):
            hours['agent_hours_24h'] += duration
    return hours


def job_label(path):
    for line in path.read_text().splitlines():
        if line.startswith(('## Item:', '## Build:', '## Packet', '## Independent', '## Diagnosis')):
            return plain_text(re.sub(r'^##\s*(?:(?:Item:|Build:)\s*)?', '', line), 150)
    return 'Work description unavailable'


def scan_direct(directory, processes, now):
    directory = Path(directory)
    if not directory.is_dir():
        raise OSError('Direct jobs unavailable')
    running, finished = [], []
    for job in sorted(directory.glob('X-*')):
        if not job.is_dir():
            continue
        if (job / 'DONE').exists():
            result = json.loads((job / 'result.json').read_text()) if (job / 'result.json').exists() else {}
            if not isinstance(result, dict):
                raise ValueError('Unreadable direct job result')
            finished.append({'id': job.name, 'status': result.get('status')})
            continue
        # Match the folder or a child file, with a separator boundary for sibling safety.
        matches = [pid for pid, (engine, args) in processes.items()
                   if engine == 'Codex' and any(a == str(job) or a.startswith(str(job) + '/') for a in args)]
        if not matches:
            continue
        start = job_start(job.name)
        label = job_label(job / 'prompt.md')
        explicit_lines = [line for line in (job / 'prompt.md').read_text().splitlines()
                          if line.startswith(('Item:', 'Items under review:', 'Packet:'))]
        context = label + '\n' + '\n'.join(explicit_lines)
        ids = re.findall(r'\b(?:KV3-[A-Z0-9-]+|[A-Z][A-Za-z0-9]*-\d+[A-Za-z0-9-]*)\b', context)
        item = ', '.join(dict.fromkeys(ids)) or None
        running.append({'id': job.name, 'engine': 'Codex', 'label': label, 'item': item,
                        'started_at': start.isoformat() if start else None,
                        'elapsed_seconds': max(0, (now - start).total_seconds()) if start else None,
                        'pid': matches[0]})
    return running, finished


def scan_fleet(directory, processes, now):
    directory = Path(directory)
    if not directory.is_dir():
        raise OSError('Fleet jobs unavailable')
    running, finished = [], []
    for job in sorted(directory.glob('J-*')):
        if not job.is_dir():
            continue
        state = json.loads((job / 'state.json').read_text())
        if not isinstance(state, dict):
            raise ValueError('Unreadable fleet state')
        phase = state.get('phase')
        if phase in ('ended', 'launch_failed'):
            finished.append({'id': job.name, 'status': state.get('outcome') or phase})
            continue
        if phase == 'prepared':
            continue
        if phase not in ('live', 'running', 'terminating'):
            raise ValueError('Unrecognised fleet lifecycle')
        process = processes.get(state.get('pid'))
        if not process:
            continue
        if not process[0]:
            raise ValueError('Fleet process identity unavailable')
        engine = process[0]
        declared = str(state.get('engine') or state.get('model') or '').lower()
        if ('codex' in declared or declared.startswith('gpt')) and engine != 'Codex':
            raise ValueError('Fleet process engine mismatch')
        if 'claude' in declared and engine != 'Claude':
            raise ValueError('Fleet process engine mismatch')
        start = parse_time(state.get('started_at')) or job_start(job.name)
        item = state.get('item')
        running.append({'id': job.name, 'engine': engine, 'item': item,
                        'label': TITLES.get(item) or 'Work description unavailable',
                        'started_at': start.isoformat() if start else None,
                        'elapsed_seconds': max(0, (now - start).total_seconds()) if start else None,
                        'pid': state.get('pid')})
    return running, finished


def agent_summary(running, finished, complete=True):
    running = list({r['pid']: r for r in running}.values())
    return {'count': len(running) if complete else None,
            'by_engine': {e: sum(r['engine'] == e for r in running) for e in ('Codex', 'Claude', 'Unknown')} if complete else None,
            'running': running, 'finished': finished, 'complete': complete}


def detect_agents(direct_jobs, fleet_jobs, processes, now):
    rows = process_rows(processes)
    dr, df = scan_direct(direct_jobs, rows, now)
    fr, ff = scan_fleet(fleet_jobs, rows, now)
    return agent_summary(dr + fr, df + ff)


def fetch_state():
    url = os.environ.get('KY_PROGRESS_TRACKER_URL', 'http://127.0.0.1:8767/api/state')
    parsed = urlsplit(url)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1') or parsed.username:
        raise ValueError('Tracker must be an unauthenticated loopback URL')
    with urlopen(url, timeout=120) as response:
        state = json.load(response)
    validate_state(state)
    return state


def list_processes():
    return subprocess.run(['ps', '-axo', 'pid=,command='], check=True, capture_output=True,
                          text=True, timeout=3).stdout


class Dashboard:
    def __init__(self, event_path=None, direct_jobs=None, fleet_jobs=None,
                 fetch_tracker=fetch_state, process_list=list_processes, cache_seconds=5):
        self.events = EventHistory(event_path or os.environ.get('KY_PROGRESS_EVENTS', '/Users/Dev/kalayantra/run/EVENTS.jsonl'))
        self.direct_jobs = direct_jobs or os.environ.get('KY_PROGRESS_DIRECT_JOBS', '/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs')
        self.fleet_jobs = fleet_jobs or os.environ.get('KY_PROGRESS_FLEET_JOBS', '/Users/Dev/kalayantra/run/jobs')
        self.fetch_tracker, self.process_list = fetch_tracker, process_list
        self.cache_seconds = max(0, min(cache_seconds, 5))
        self.cache, self.cached_at, self.failures = None, 0, {}
        self.last_scope, self.scope_changes = None, []

    def summary(self, now=None):
        if self.cache is not None and time.monotonic() - self.cached_at < self.cache_seconds:
            return self.cache
        now = now or datetime.now(UTC)
        sources = {}
        def read(name, callback):
            try:
                value = callback()
                self.failures.pop(name, None)
                sources[name] = {'available': True, 'checked_at': now.isoformat(), 'unavailable_since': None}
                return value
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
                since = self.failures.setdefault(name, now.isoformat())
                sources[name] = {'available': False, 'checked_at': now.isoformat(), 'unavailable_since': since}
                return None
        def tracker():
            value = self.fetch_tracker()
            validate_state(value)
            return value
        state = read('tracker', tracker)
        first_done = read('events', self.events.read)
        effort = read('job_timing', lambda: job_effort(self.direct_jobs, now))
        processes = read('processes', lambda: process_rows(self.process_list()))
        dr = read('direct_jobs', lambda: scan_direct(self.direct_jobs, processes or {}, now))
        fr = read('fleet_jobs', lambda: scan_fleet(self.fleet_jobs, processes or {}, now))
        if state is not None:
            try:
                total = sum(len(t['items']) for t in state['tracks'])
                observation = parse_time(state['generated_at'])
                if self.last_scope and observation > self.last_scope[0] and total != self.last_scope[1]:
                    before = self.last_scope[1]
                    self.scope_changes.append({'at': observation.isoformat(), 'before': before, 'after': total,
                                               'label': f'Scope changed: {before} → {total} items (observed)'})
                if self.last_scope is None or observation > self.last_scope[0]:
                    self.last_scope = (observation, total)
                result = compute_summary(state, first_done, now, first_complete=self.events.first_complete,
                                         effort=effort, scope_changes=self.scope_changes)
            except (ValueError, KeyError, TypeError):
                sources['tracker'] = {'available': False, 'checked_at': now.isoformat(),
                                      'unavailable_since': self.failures.setdefault('tracker', now.isoformat())}
                state = None
        if state is None:
            result = {k: None for k in ('observed_at', 'metrics', 'progress_lines', 'tracks', 'history', 'working_items',
                                       'up_next', 'attention', 'owner_decisions', 'milestones',
                                       'recently_completed', 'engine_status')}
        running = (dr[0] if dr else []) + (fr[0] if fr else []) if processes is not None else []
        finished = (dr[1] if dr else []) + (fr[1] if fr else [])
        complete = all(sources[k]['available'] for k in ('processes', 'direct_jobs', 'fleet_jobs'))
        result.update(generated_at=now.isoformat(), sources=sources,
                      agents=agent_summary(running, finished, complete))
        self.cache, self.cached_at = result, time.monotonic()
        return result


class Handler(BaseHTTPRequestHandler):
    dashboard = None

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/':
            body, kind = (ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8'
        elif path == '/api/summary':
            body = json.dumps(self.dashboard.summary(), ensure_ascii=False, allow_nan=False).encode()
            kind = 'application/json; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', kind)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass  # Do not persist access logs or source data.


def main():
    Handler.dashboard = Dashboard()
    port = int(os.environ.get('KY_PROGRESS_PORT', '8768'))
    with HTTPServer(('127.0.0.1', port), Handler) as httpd:
        print(f'Kāla progress dashboard: http://127.0.0.1:{port}', flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
