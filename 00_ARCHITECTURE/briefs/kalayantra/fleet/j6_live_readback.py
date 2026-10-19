#!/usr/bin/env python3
"""J-6l preparation: exact response capture and honest soak recording.

Proposed evidence schemas, not deployed endpoint contracts. The consumer-path
receipt is owed by an independent verifier; the existing explicit-generation
route is insufficient. No default soak duration or acceptance rule is supplied.
The CLI imports an operator-captured HTTP observation; it never contacts a URL,
reads an authentication secret, dispatches, changes runtime, or writes a receipt.
A callable transport supports a future governed live capture without coupling
this preparation to a production client or inventing the absent consumer path.

(I) INTERPRETATION: the owner rule is opaque evidence here. Measurement and
recording can be prepared now; deciding that rule and independent acceptance
remain J-6l-a61. All emitted acceptance fields stay null.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, urlsplit

from head_operation import CANONICAL_CHART, Refused, load_json, sha, raw_sha, wire

BINDING_KEYS = {'operation_id','request_sha256','receipt_sha256','readback_receipt_sha256',
                'chart_id','generation','manifest_id'}
HEX64 = re.compile(r'[0-9a-f]{64}\Z')


def instant(value):
    parsed = dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:
        raise Refused('timezone_required')
    return parsed.astimezone(dt.timezone.utc)


def binding_check(binding):
    import uuid
    if (set(binding) != BINDING_KEYS or binding['chart_id'] != CANONICAL_CHART or binding['generation'] != '5.0'
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,79}',binding['operation_id'])
            or str(uuid.UUID(binding['manifest_id'])) != binding['manifest_id']
            or any(not HEX64.fullmatch(binding[k]) for k in ('request_sha256','receipt_sha256','readback_receipt_sha256'))):
        raise Refused('complete_exact_flip_binding_required')


def deployment_check(deployment):
    if (deployment.get('schema') != 'ky.j6_deployment_observation/1'
            or not re.fullmatch(r'sha256:[0-9a-f]{64}',deployment.get('image_digest',''))
            or not re.fullmatch(r'[0-9a-f]{40}',deployment.get('commit',''))):
        raise Refused('deployed_image_and_commit_required')
    url = deployment['url']; parsed = urlsplit(url)
    if (parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.fragment
            or any(k.lower().replace('-','_') in ('generation','manifest_id') for k,_ in parse_qsl(parsed.query))):
        raise Refused('actual_authority_consumer_url_required')
    migrations = deployment.get('migrations')
    if (not isinstance(migrations,list) or not migrations
            or any(set(m) != {'filename','sha256'} or not re.fullmatch(r'[0-9]+_[A-Za-z0-9_]+\.sql',m['filename'])
                   or not HEX64.fullmatch(m['sha256']) for m in migrations)
            or len({m['filename'] for m in migrations}) != len(migrations)):
        raise Refused('exact_deployed_migration_hash_set_required')
    instant(deployment['observed_at'])
    return url


def _response(body, binding):
    env = load_json(body)
    if (not isinstance(env,dict) or env.get('schema') != 'gochara_v5_windows/1'
            or any(env.get(k) != binding[k] for k in ('chart_id','generation','manifest_id'))
            or env.get('refusal') is not None or 'refusal' not in env
            or env.get('manifest_status') != 'published' or env.get('stored_scope') == 'test_slice'
            or 'test_slice' in env or (env.get('seal') or {}).get('manifest_id') != binding['manifest_id']
            or not isinstance(env.get('classes'),list) or not env['classes']
            or any(c.get('completeness') != 'complete_within_scope' for c in env['classes'])):
        raise Refused('exact_complete_published_non_slice_served_response_required')
    return env


def capture(binding, deployment, consumer_path, transport):
    """Capture one response through a separately attested authority consumer path.

    Independent path evidence binds endpoint, deployed identity set and flip.
    Calling a named-generation reader never earns this path receipt. Transport
    provides exact bytes and actual status/time/final URL; redirects must agree.
    """
    binding_check(binding)
    url = deployment_check(deployment)
    if (consumer_path.get('schema') != 'ky.j6_consumer_path/1' or consumer_path.get('url') != url
            or consumer_path.get('mode') != 'authority' or consumer_path.get('result') != 'ACCEPTED'
            or consumer_path.get('by') not in ('v1','v2','v3','v4')
            or consumer_path.get('binding') != binding or consumer_path.get('deployment_sha256') != sha(deployment)
            or not HEX64.fullmatch(consumer_path.get('evidence_sha256',''))):
        raise Refused('independent_authority_consumer_path_receipt_required')
    observed = transport(url)
    raw = observed['body']
    if (observed.get('url') != url or observed.get('status') != 200 or not isinstance(raw,bytes)
            or not 0 < len(raw) <= 4*1024*1024 or instant(observed['observed_at']) < instant(deployment['observed_at'])):
        raise Refused('successful_http_observation_after_deployment_required')
    env = _response(raw,binding)
    return dict(schema='ky.j6_live_capture/1',binding=dict(binding),acceptance=None,production_activated=False,
                deployment=deployment,deployment_sha256=sha(deployment),consumer_path=consumer_path,
                consumer_path_sha256=sha(consumer_path),response=dict(url=url,status=observed['status'],
                    observed_at=observed['observed_at'],sha256=raw_sha(raw),bytes=len(raw),
                    body_base64=base64.b64encode(raw).decode('ascii'),served_generation=env['generation'],
                    served_manifest_id=env['manifest_id']))


def _sample(sample,binding):
    if sample.get('schema') != 'ky.j6_live_capture/1' or sample.get('binding') != binding or sample.get('acceptance') is not None:
        raise Refused('same_operation_capture_required')
    response = sample['response']
    raw = base64.b64decode(response['body_base64'],validate=True)
    if response['sha256'] != raw_sha(raw) or response['bytes'] != len(raw):
        raise Refused('sample_response_digest_mismatch')
    # Re-evaluate the actual payload, deployment, path receipt and hashes, rather
    # than accepting a sample's declared true/complete marker.
    checked = capture(binding,sample['deployment'],sample['consumer_path'],lambda _:dict(response,body=raw))
    if checked != sample:
        raise Refused('sample_capture_changed')
    return instant(response['observed_at'])


def record_soak(binding, observations, *, owner_rule_raw=None):
    """Measure the sample span and bind all evidence; never decide an exit rule.

    No periodic process, sleep, default threshold or PASS flag. An owner-defined
    rule may be attached verbatim. Gaps, outages and other owner-rule metrics
    must be supplied as independent observations before a verifier accepts soak;
    successful response samples alone never imply continuous health.
    """
    binding_check(binding)
    if not isinstance(observations,list) or not observations:
        raise Refused('actual_observations_required')
    times = [_sample(sample,binding) for sample in observations]
    if times != sorted(times) or len({s['deployment_sha256'] for s in observations}) != 1:
        raise Refused('ordered_samples_of_one_deployment_required')
    if owner_rule_raw is not None:
        if not isinstance(owner_rule_raw,bytes) or not owner_rule_raw:
            raise Refused('owner_rule_evidence_bytes_required')
        rule = load_json(owner_rule_raw)
        if not isinstance(rule,dict) or not rule:
            raise Refused('owner_rule_evidence_object_required')
    return dict(schema='ky.j6_soak_record/1',binding=dict(binding),acceptance=None,
                observations=observations,observations_sha256=sha(observations),sample_count=len(times),
                first_observed_at=times[0].isoformat(),last_observed_at=times[-1].isoformat(),
                elapsed_seconds=(times[-1]-times[0]).total_seconds(),
                owner_rule_base64=base64.b64encode(owner_rule_raw).decode('ascii') if owner_rule_raw is not None else None,
                owner_rule_sha256=raw_sha(owner_rule_raw) if owner_rule_raw is not None else None,
                missing=['independent_soak_acceptance'] if owner_rule_raw is not None else ['owner_soak_rule_and_live_readback_acceptance'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,allow_abbrev=False)
    commands = parser.add_subparsers(dest='command',required=True)
    capture_cmd = commands.add_parser('capture',allow_abbrev=False)
    for name in ('binding','deployment','consumer-path','http-observation','body'):
        capture_cmd.add_argument('--'+name,required=True,type=Path)
    soak_cmd = commands.add_parser('soak',allow_abbrev=False)
    soak_cmd.add_argument('--binding',required=True,type=Path)
    soak_cmd.add_argument('--observations',required=True,type=Path)
    soak_cmd.add_argument('--owner-rule',type=Path)
    args = parser.parse_args(argv)
    try:
        binding = load_json(args.binding.read_bytes())
        if args.command == 'capture':
            observation = load_json(args.http_observation.read_bytes())
            observation['body'] = args.body.read_bytes()
            result = capture(binding,load_json(args.deployment.read_bytes()),load_json(args.consumer_path.read_bytes()),lambda _:observation)
        else:
            result = record_soak(binding,load_json(args.observations.read_bytes()),
                                 owner_rule_raw=args.owner_rule.read_bytes() if args.owner_rule else None)
        print(wire(result).decode())
        return 0
    except Exception:
        print('J6l evidence refused; inspect the bound inputs',file=sys.stderr)
        return 8


if __name__ == '__main__':
    raise SystemExit(main())
