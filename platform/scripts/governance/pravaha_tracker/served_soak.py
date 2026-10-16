"""Deterministic measurement of a preregistered, independently reviewed soak.

This validates recorded evidence; it neither samples a live service nor makes a
ruling effective. An independent review must pin the effective rule's exact
bytes/decision in its matching step. Duration, cadence and latency have no
production defaults. Explicit-generation HTTP probes cannot qualify.
(I) INTERPRETATION: samples cover the closed rule window at exact cadence;
late/absent/duplicate samples, provenance drift, incomplete classes or a
rollback invalidate the soak rather than shortening its denominator.
"""
import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import re

from pravaha_tracker.completion import CompletionError
from pravaha_tracker.operation_evidence import load_bound


def instant(value):
    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        raise CompletionError('soak timestamps require timezone')
    return dt.astimezone(timezone.utc)


def number(value, *, positive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0 or positive and value == 0:
        raise CompletionError('soak bounds must be finite nonnegative numbers')
    return value


def check_soak(evidence, path, *, request, readback, reviewed_step):
    try:
        _check_soak(evidence, path, request=request, readback=readback, reviewed_step=reviewed_step)
    except (ValueError, TypeError, KeyError, OverflowError, binascii.Error) as exc:
        raise CompletionError('invalid measured soak evidence') from exc


def _check_soak(evidence, path, *, request, readback, reviewed_step):
    reference = evidence.get('rule')
    rule, _ = load_bound(reference, path)
    if (rule.get('schema') != 'ky.soak_rule/1'
            or reviewed_step.get('soak_rule_sha256') != reference['sha256']
            or not rule.get('decision_id')
            or reviewed_step.get('effective_soak_decision') != rule['decision_id']):
        raise CompletionError('soak rule must be pinned by the independent effective-rule review')
    start, end = instant(rule['start']), instant(rule['end'])
    cadence = number(rule['cadence_s'], positive=True)
    lateness = number(rule['max_lateness_s'])
    latency = number(rule['max_latency_ms'], positive=True)
    seconds = (end - start).total_seconds()
    count = seconds / cadence
    if (instant(rule['approved_at']) > start or end > datetime.now(timezone.utc)
            or seconds <= 0 or not count.is_integer() or count > 100000):
        raise CompletionError('soak window must follow rule approval and span whole bounded cadence intervals')
    if lateness >= cadence:
        raise CompletionError('soak lateness may not hide a missing interval')
    classes = rule['required_classes']
    if (not isinstance(classes, list) or not classes or len(classes) != len(set(classes))
            or any(not isinstance(name, str) or not name for name in classes)):
        raise CompletionError('soak must preregister distinct required classes')
    if evidence.get('rollback_operation_id') is not None:
        raise CompletionError('rollback invalidates the soak window')
    if rule['transport'] != 'authority_selected_http':
        raise CompletionError('soak requires authority-selected serving transport')
    if (rule['chart_id'] != '482012f1-710e-4a25-994a-93821f5871aa' or rule['generation'] != '5.0'
            or request.get('kind') != 'publish_head' or request.get('chart_id') != rule['chart_id']
            or (request.get('args') or {}).get('generation') != rule['generation']
            or (request.get('args') or {}).get('manifest-id') != rule['manifest_id']
            or any(readback.get(key) != rule[key] for key in ('chart_id', 'generation', 'manifest_id', 'deployment'))):
        raise CompletionError('soak target differs from accepted publication/readback')
    deployment = rule['deployment']
    if not isinstance(deployment, dict) or any(not deployment.get(k) for k in
                                               ('commit', 'image_digest', 'migration_set_sha256')):
        raise CompletionError('soak requires deployed code, image and migration identities')
    if (not re.fullmatch(r'[0-9a-f]{40}', str(deployment['commit']))
            or not re.fullmatch(r'sha256:[0-9a-f]{64}', str(deployment['image_digest']))
            or not re.fullmatch(r'[0-9a-f]{64}', str(deployment['migration_set_sha256']))):
        raise CompletionError('soak deployment identities must be immutable digests')
    expected = [start + timedelta(seconds=n*cadence) for n in range(int(count)+1)]
    samples = evidence['samples']
    if not isinstance(samples, list) or len(samples) != len(expected):
        raise CompletionError('soak missing or duplicate scheduled samples')
    for sample, scheduled in zip(samples, expected):
        if (instant(sample['scheduled_at']) != scheduled
                or not 0 <= (instant(sample['observed_at']) - scheduled).total_seconds() <= lateness
                or number(sample['latency_ms']) > latency or sample.get('http_status') != 200
                or sample.get('transport') != rule['transport'] or sample.get('deployment') != deployment):
            raise CompletionError('soak cadence, latency, transport or deployment failed')
        raw = base64.b64decode(sample['response_base64'], validate=True)
        if not raw or hashlib.sha256(raw).hexdigest() != sample['response_sha256']:
            raise CompletionError('soak response bytes do not match sample digest')
        body = json.loads(raw)
        if (not isinstance(body, dict) or body.get('schema') != 'gochara_v5_windows/1'
                or 'refusal' not in body or body.get('refusal') is not None
                or body.get('manifest_status') != 'published'
                or any(body.get(key) != rule[key] for key in ('chart_id', 'generation', 'manifest_id'))
                or not isinstance(body.get('seal'), dict)
                or any(body['seal'].get(key) != rule[key] for key in ('chart_id', 'generation', 'manifest_id'))):
            raise CompletionError('soak served provenance or domain refusal failed')
        rows = body.get('classes')
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise CompletionError('soak class evidence missing')
        names = [row.get('event_class') for row in rows]
        if (any(not isinstance(name, str) or not name for name in names)
                or len(names) != len(set(names)) or any(name not in names for name in classes)
                or any(row.get('completeness') != 'complete_within_scope' for row in rows)):
            raise CompletionError('soak class coverage is missing, duplicated or incomplete')
