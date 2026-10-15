#!/usr/bin/env python3
"""Produce the final manifest and installation receipt from a measured bootstrap install.

Usage: kyfinal.py build --repo REPO --run RUN --rehearsal RESULTS.json
  --live-evidence-dir EVIDENCE_DIR [--expected-fail-test-id JUNIT_CLASSNAME::NAME]
  --coverage REVIEW.json --packets LIST_OR_DIR
  --backfill-banner-file 00_ARCHITECTURE/CURRENT_STATE_v1_0.md
  --backfill-session-log 00_ARCHITECTURE/SESSION_LOG.md
  --backfill-entry-id SESSION_ID --backfill-banner-id 'EXACT BANNER TITLE'
  --out-manifest RUN/VERSIONS.json --out-receipt RUN/INSTALL_RECEIPT.json [--dry]

No service, network, git mutation or model launch. All admission checks precede
publication; a named refusal publishes nothing. --dry runs the same detectors,
including the fixed repository governance detectors, and prints the proposed records
without writing. No arbitrary validator command is accepted. See kybackfill.py for
the scoped adapter to the repository validator (which has no backfill CLI mode).

(I) INTERPRETATION: finalisation refuses deferred components; first bind/review and
reinstall the complete bundle. Source authority comes from VERSIONS.bootstrap.json,
not today's HEAD. Its observations must still match kymanifest.observe exactly.
(I) INTERPRETATION: list entries are paths relative to the list file (one per line,
blank lines and # comment lines ignored); a directory selects PACKET_*.md directly.
(I) INTERPRETATION: backfill exit evidence is INSTALL_RECEIPT.json.backfill.json;
kyversion F7 requires its path/hash, although gate A6 reads only validated.
(I) INTERPRETATION: final tracker_revision is the installer's measured package_sha256;
the entire previous measured object is retained as bootstrap_tracker_revision. It
asserts the installed package revision, not freshly observed process liveness.

(I) INTERPRETATION (T0 capture adapters): absent historical facts require a rerun
and machine-captured ky.fixture_commands/1, ky.fixture_connections/1,
ky.live_run_changes/1 and ky.fixture_resources/1 objects. Their required fields
are checked below; neither a PASS summary nor a retrospectively asserted exit
supplies a missing observation. Connection captures cover the full fixture process
tree/window and allow only its reserved loopback tracker endpoint. Cleanup records
list the started resources and the observed inventories after stopping/removal;
an explicit empty database list records a leg that created no DB.
(I) INTERPRETATION: JUnit exception ids are classname::name, matching pytest's
recorded identity. An exact, explicit allow-list exempts failure elements only;
errors always refuse. Skips/xfails remain visible in the computed receipt.
(I) INTERPRETATION: tick stdout is empty in this installation; admission requires
hash-bound command exits plus two parsed dispatcher tick log entries, and refuses
refused/failed/unknown jobs even when the dispatcher exits zero. A gate backlog
is permitted. PR captures additionally include state=OPEN; all live obligations
select the same item. Only JOURNAL_COCKPIT.md and JOURNAL_PLANNER.md may differ
in a measured full live-run before/after inventory.

Consumer map (paths relative to this directory):
  mode: kygate.sh:443; kyversion.sh:190-195 (F1)
  manifest.manifest_sha256: kygate.sh:447-454; kyversion.sh:250-259 (F3)
  final entrypoints/digest: kyversion.sh:225-246 (F2); kymanifest.py:368-371
  components/installed_path: kyversion.sh:263-281 (F4)
  generated_pairs: kyversion.sh:285-319 (F5)
  rehearsal.results {path,sha256}: kygate.sh:455-459; kyversion.sh:424-436 (F7)
  rehearsal.tested_components: kygate.sh:460-469; kyversion.sh:413-422 (F7)
  coverage {path,sha256,verdict}, packets[] {path,sha256}: kygate.sh:470-483;
    kyversion.sh:423-438 (F7)
  backfill {path,sha256,validated}: kygate.sh:484-487; kyversion.sh:425-440 (F7)
  tracker_revision: kyversion.sh:441-443 (F7)
  qualifications: kyversion.sh:323-345 (F8); activation chain:349-407 (F6)
  bootstrap measured sections: install.sh:1780-1819 (kept, except explicit mode,
    manifest binding and scalar tracker_revision conversion described above).

This does not create RELEASE_RECEIPT, OWNER_RESUME, an activation record, or remove
HOLD. Pre-resume A7 uses normal final checks. Full A7 needs the OWNER_RESUME digest
and a valid terminal activation link (kyversion D1/D2); gate N binds the release
receipt, bundle, decider and UTC timestamp (kygate.sh:525-580).
"""
import argparse
import copy
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Also work when called with python -I (the installed cockpit's form).
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kymanifest as km
import kyschema
import kybackfill

HEX = re.compile(r"[0-9a-f]{64}\Z")

# Plan: 00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_RELAUNCH_PLAN_v2_7.md:716 (B-3).
# Rulings under /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/:
# SURROGATE_ANSWER_09_B3_LEG3.md:13 (§1),36 (live PASS),40 (§6 substitution);
# SURROGATE_ANSWER_12_FASTEST_PATH.md:23 (Rest of B-3: final-bundle component tests).
# (I) INTERPRETATION: granular IDs cover every retained acceptance claim separately;
# fixture_clean_stop includes server/DB/worktree cleanup, not merely a stopped tick.
REQUIRED_OBLIGATIONS = (
    "component_tests_final_bundle", "fixture_live_events_unchanged",
    "fixture_no_live_tracker_access", "fixture_no_external_requests",
    "fixture_expected_transitions", "fixture_clean_stop",
    "live_build_by_fleet", "live_pr_opened", "live_verify_boundary",
    "live_accepted_pr_head_in_log", "live_merge_parked_no_auto_merge",
)
SUBSTITUTION = {"replaces": "fixture_model_jobs", "replacement": "live_first_item_under_watch",
                "ruling": "SURROGATE_ANSWER_09_B3_LEG3.md#6", "label": "live, not fixture"}


class Refused(Exception):
    pass


def refuse(code, detail):
    raise Refused(f"{code}: {detail}")


def strict_object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON member: " + key)
        out[key] = value
    return out


def invalid_constant(value):
    raise ValueError("non-JSON constant: " + value)


def encoded(doc):
    return (json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


class Inputs:
    """Hash every named input; recheck before publishing to detect validator/concurrent edits."""
    def __init__(self):
        self.hashes = {}

    def file(self, path, code, expected=None):
        path = Path(path)
        if not path.is_absolute():
            refuse(code, f"path is not absolute: {path}")
        try:
            if not stat.S_ISREG(path.lstat().st_mode):
                refuse(code, f"not a regular file: {path}")
            digest = km.sha256(path)
        except OSError as e:
            refuse(code, f"unreadable file: {path} ({type(e).__name__})")
        if expected is not None and digest != expected:
            refuse(code, f"hash differs: {path}")
        if str(path) in self.hashes and self.hashes[str(path)] != digest:
            refuse("inputs_changed", str(path))
        self.hashes[str(path)] = digest
        return {"path": str(path), "sha256": digest}

    def document(self, path, code):
        self.file(path, code)
        try:
            with Path(path).open(encoding="utf-8") as stream:
                doc = json.load(stream, object_pairs_hook=strict_object, parse_constant=invalid_constant)
            if not isinstance(doc, dict):
                raise ValueError("not a JSON object")
            return doc
        except (OSError, ValueError, RecursionError) as e:
            refuse(code, f"invalid JSON object: {path} ({type(e).__name__})")

    def unchanged(self):
        for path, digest in list(self.hashes.items()):
            self.file(path, "inputs_changed", digest)


def component_map(rows, code):
    if not isinstance(rows, list) or not rows:
        refuse(code, "no component entries")
    out = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("path"), str) or not row["path"] \
                or not isinstance(row.get("sha256"), str) or not HEX.fullmatch(row["sha256"]) \
                or row["path"] in out:
            refuse(code, "not distinct {path,sha256} entries")
        out[row["path"]] = row["sha256"]
    return out


# T0: summaries never confer authority. These adapters measure retained producer
# observations. Capture formats absent from the first rehearsal are deliberately
# versioned below; missing captures are unknown, never reconstructed from summaries.
# (I) INTERPRETATION: cockpit records allowed to change are ONLY these two journals.
COCKPIT_RECORDS = frozenset(('JOURNAL_COCKPIT.md', 'JOURNAL_PLANNER.md'))
FIXTURE_ROLES = {
    'component_tests_final_bundle': {'xml', 'commit'},
    'fixture_live_events_unchanged': {'before', 'after'},
    'fixture_no_live_tracker_access': {'connections', 'changes'},
    'fixture_no_external_requests': {'gh', 'connections'},
    'fixture_expected_transitions': {'dry', 'tick1', 'tick2', 'commands', 'journal', 'log'},
    'fixture_clean_stop': {'resources', 'changes'},
}


def json_text(text):
    return json.loads(text, object_pairs_hook=strict_object, parse_constant=invalid_constant)


def require(ok, name, detail):
    if not ok:
        refuse('rehearsal_obligation_' + name, detail + ' (unknown or contradictory evidence)')


class Detector:
    def __init__(self, name, row, inputs, manifest, run, live_evidence, expected_fail):
        self.name, self.inputs, self.manifest, self.run = name, inputs, manifest, run
        self.live_evidence, self.expected_fail = live_evidence, expected_fail
        self.refs = {}
        if name in FIXTURE_ROLES:
            refs = row.get('evidence')
            roles_ok = isinstance(refs, dict) and (set(refs) == FIXTURE_ROLES[name]
                or (name == 'component_tests_final_bundle' and set(refs) == {'xml'}))
            require(roles_ok and 'item' not in row,
                    name, 'required evidence roles: ' + ', '.join(sorted(FIXTURE_ROLES[name])))
            for role, ref in refs.items():
                self.refs[role] = inputs.file(ref['path'], 'rehearsal_obligation_' + name, ref['sha256'])
        else:
            self.item = row.get('item')
            require(isinstance(self.item, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', self.item)
                    and 'evidence' not in row and run is not None and live_evidence is not None,
                    name, 'live obligation needs only item plus --run and --live-evidence-dir')

    def need(self, ok, detail):
        require(ok, self.name, detail)

    def text(self, role):
        return Path(self.refs[role]['path']).read_text(encoding='utf-8')

    def doc(self, role, schema):
        doc = json_text(self.text(role))
        self.need(isinstance(doc, dict) and doc.get('schema') == schema, 'expected ' + schema)
        return doc

    def live_doc(self, path):
        ref = self.inputs.file(path, 'rehearsal_obligation_' + self.name)
        self.refs[str(path)] = ref
        return self.inputs.document(path, 'rehearsal_obligation_' + self.name)

    def events(self):
        path = self.run / 'EVENTS.jsonl'
        self.refs['events'] = self.inputs.file(path, 'rehearsal_obligation_' + self.name)
        rows = [json_text(line) for line in path.read_text(encoding='utf-8').splitlines()]
        self.need(bool(rows) and all(isinstance(r, dict) for r in rows), 'unreadable/empty event log')
        return [r for r in rows if r.get('item') == self.item]

    def registration(self):
        events = self.events()
        states = [e for e in events if e.get('kind') == 'item' and not e.get('step')]
        self.need(bool(states) and states[-1].get('state') == 'review', 'latest item state is not review')
        reg = states[-1]
        match = re.fullmatch(r'PR #([1-9][0-9]*) @ ([0-9a-f]{40})', reg.get('detail', ''))
        # Real controller may append explanatory text to the registration detail.
        if match is None:
            match = re.search(r'PR #([1-9][0-9]*) @ ([0-9a-f]{40})(?![0-9a-f])', reg.get('detail', ''))
        self.need(match is not None and isinstance(reg.get('actor'), str)
                  and re.fullmatch(r'stream-K:[A-Za-z0-9._-]+', reg['actor']), 'no dispatcher builder review registration')
        return events, reg, int(match[1]), match[2]

    def states(self, kind):
        directory = self.run / 'jobs'
        self.need(directory.is_dir() and not directory.is_symlink(), 'job directory missing')
        rows = []
        for path in sorted(directory.glob('*/state.json')):
            doc = self.live_doc(path)
            self.need(doc.get('schema') == 'ky.job/1' and doc.get('job_id') == path.parent.name,
                      'invalid job state: ' + str(path))
            if doc.get('item') == self.item and doc.get('kind') == kind:
                rows.append(doc)
        self.need(bool(rows), kind + ' job missing')
        return rows

    def pr(self, number, head):
        obs = self.live_doc(self.live_evidence / (self.item + '.pr.json'))
        self.need(type(obs.get('number')) is int and obs['number'] == number and obs.get('headRefOid') == head
                  and obs.get('state') == 'OPEN', 'PR observation must name the registered open PR/head')
        return obs

    def component_tests(self):
        # Producer: /opt/homebrew/lib/python3.14/site-packages/_pytest/junitxml.py:665-683;
        # suite properties:336-348. Sidecar is the T0 adapter when that property is absent.
        self.need(isinstance(self.manifest, dict) and self.manifest.get('components_commit'), 'manifest commit unknown')
        xml_text = self.text('xml')
        self.need('<!DOCTYPE' not in xml_text and '<!ENTITY' not in xml_text, 'DTD/entities refused')
        root = ET.fromstring(xml_text)
        self.need(root.tag in ('testsuites', 'testsuite'), 'not pytest JUnit XML')
        suites = [root] if root.tag == 'testsuite' else list(root)
        self.need(bool(suites) and all(s.tag == 'testsuite' for s in suites), 'unknown/nested JUnit structure')
        totals = dict(tests=0, failures=0, errors=0, skipped=0)
        failed_ids, skipped_ids, ids = [], [], set()
        commits = []
        for suite in suites:
            cases = suite.findall('testcase')
            counters = {k: int(suite.attrib[k]) for k in totals}
            self.need(all(v >= 0 for v in counters.values()) and counters['tests'] == len(cases), 'JUnit test count differs')
            counts = dict(tests=len(cases), failures=0, errors=0, skipped=0)
            self.need(all(c.tag in ('testcase', 'properties') for c in suite), 'unknown JUnit suite element')
            for case in cases:
                test_id = case.attrib.get('classname', '') + '::' + case.attrib.get('name', '')
                self.need(case.attrib.get('name') and case.attrib.get('classname') and test_id not in ids,
                          'missing/duplicate test identity')
                ids.add(test_id)
                failures, errors, skips = case.findall('failure'), case.findall('error'), case.findall('skipped')
                self.need(len(failures) + len(errors) + len(skips) <= 1, 'contradictory JUnit testcase')
                self.need(all(c.tag in ('properties', 'failure', 'error', 'skipped', 'system-out', 'system-err') for c in case),
                          'unknown JUnit testcase element')
                counts['failures'] += len(failures); counts['errors'] += len(errors); counts['skipped'] += len(skips)
                if failures: failed_ids.append(test_id)
                if skips: skipped_ids.append({'id': test_id, 'type': skips[0].get('type'), 'message': skips[0].get('message')})
            self.need(counts == counters, 'JUnit counters contradict testcase outcomes')
            for prop in suite.findall('./properties/property'):
                if prop.get('name') == 'components_commit': commits.append(prop.get('value'))
            for key in totals: totals[key] += counters[key]
        for key in totals:
            if key in root.attrib and root.tag == 'testsuites':
                self.need(int(root.attrib[key]) == totals[key], 'JUnit aggregate counter differs')
        if 'commit' in self.refs:
            sidecar = self.doc('commit', 'ky.test_commit/1')
            self.need(sidecar.get('components_commit') == self.manifest['components_commit']
                      and sidecar.get('junit_sha256') == self.refs['xml']['sha256'], 'tested commit/XML binding differs')
        else:
            self.need(bool(commits), 'XML commit property or hash-bound commit sidecar missing')
        self.need(all(c == self.manifest['components_commit'] for c in commits), 'JUnit recorded commit differs')
        self.need(totals['tests'] > 0 and totals['errors'] == 0, 'JUnit has zero tests or errors')
        self.need(set(failed_ids) == set(self.expected_fail), 'JUnit failures do not exactly match explicit expected-fail ids')
        return dict(totals, expected_fail_test_ids=sorted(self.expected_fail), skipped_or_xfailed=skipped_ids,
                    tested_commit=self.manifest['components_commit'])

    def live_events_unchanged(self):
        pairs = []
        for role in ('before', 'after'):
            match = re.fullmatch(r'live events:\s+([0-9]+) ([0-9a-f]{64})\s*', self.text(role))
            self.need(match is not None, 'missing recorded live EVENTS size/sha256 pair: ' + role)
            pairs.append((int(match[1]), match[2]))
        self.need(pairs[0] == pairs[1], 'live EVENTS changed')
        return {'size': pairs[0][0], 'sha256': pairs[0][1]}

    def changes(self):
        doc = self.doc('changes', 'ky.live_run_changes/1')
        def inventory(key):
            rows = doc.get(key)
            self.need(isinstance(rows, list) and bool(rows), 'missing complete live-run inventory: ' + key)
            out = {}
            for r in rows:
                self.need(isinstance(r, dict) and isinstance(r.get('path'), str) and r['path']
                          and not Path(r['path']).is_absolute() and '..' not in Path(r['path']).parts
                          and r['path'] not in out and type(r.get('size')) is int and r['size'] >= 0
                          and isinstance(r.get('sha256'), str) and HEX.fullmatch(r['sha256']), 'invalid inventory member')
                out[r['path']] = (r['size'], r['sha256'])
            self.need('EVENTS.jsonl' in out, 'inventory omits EVENTS.jsonl')
            return out
        before, after = inventory('before'), inventory('after')
        changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
        self.need(set(changed) <= COCKPIT_RECORDS, 'live-run changes outside cockpit journal allow-list: ' + ', '.join(changed))
        return changed

    def connections(self):
        doc = self.doc('connections', 'ky.fixture_connections/1')
        self.need(type(doc.get('fixture_port')) is int and 0 < doc['fixture_port'] < 65536
                  and doc.get('live_port') == 8767 and doc['fixture_port'] != 8767,
                  'fixture/live endpoint not isolated')
        pids, rows = doc.get('pids'), doc.get('connections')
        self.need(isinstance(pids, list) and bool(pids) and all(type(p) is int and p > 0 for p in pids)
                  and isinstance(rows, list) and bool(rows) and doc.get('started_at') and doc.get('ended_at'),
                  'bounded connection capture missing')
        for r in rows:
            self.need(isinstance(r, dict) and r.get('pid') in pids and r.get('host') in ('127.0.0.1', '::1')
                      and type(r.get('port')) is int and r['port'] == doc['fixture_port'],
                      'connection to live tracker, external or unknown endpoint')
        return {'fixture_port': doc['fixture_port'], 'observed_connections': len(rows)}

    def no_live_tracker_access(self):
        return dict(self.connections(), live_run_changed=self.changes())

    def no_external_requests(self):
        connection = self.connections()
        lines = self.text('gh').splitlines()
        self.need(bool(lines), 'stand-in gh log missing invocations')
        for line in lines:
            self.need(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\tpr (list|view)(?: [^\r\n]+)?', line),
                      'stand-in gh logged a non-read-only or unparseable invocation')
        return dict(connection, gh_read_only_invocations=len(lines))

    def expected_transitions(self):
        # kydispatch.py:1364-1367 (dry), 874-878 (ticks), 538-539 (journal), 1379-1388 (exit).
        plan = self.doc('dry', 'ky.dispatch_plan/1')
        self.need(isinstance(plan.get('jobs'), list) and bool(plan['jobs']), 'dry plan jobs missing')
        for j in plan['jobs']:
            self.need(isinstance(j, dict) and all(isinstance(j.get(k), str) and j[k] for k in ('kind', 'item', 'key', 'decision')),
                      'unparseable plan job')
            self.need(not j['decision'].startswith(('refused:', 'failed:', 'unknown:')), 'refused dry-plan transition')
        commands = self.doc('commands', 'ky.fixture_commands/1').get('commands')
        self.need(isinstance(commands, list) and len(commands) == 3, 'dry plus two tick exit captures missing')
        for command, arg, role in zip(commands, ('--dry', '--once', '--once'), ('dry', 'tick1', 'tick2')):
            argv = command.get('argv') if isinstance(command, dict) else None
            self.need(isinstance(argv, list) and len(argv) >= 2 and argv[-1] == arg
                      and Path(argv[-2]).name == 'kydispatch.py' and type(command.get('exit')) is int and command['exit'] == 0
                      and command.get('stdout_sha256') == self.refs[role]['sha256'], 'command/exit/output binding unknown: ' + role)
            self.need(self.text(role).strip() == '' or role == 'dry', 'unexpected tick stdout')
        journal = self.text('journal')
        lines = journal.splitlines()
        self.need(bool(lines) and all(re.fullmatch(r'- \S+ \[[^\]]+\] .+', l) for l in lines)
                  and '[dispatcher error]' not in journal, 'dispatcher journal unknown/error')
        ticks = []
        for line in self.text('log').splitlines():
            match = re.fullmatch(r'\S+ tick (\{.*\})', line)
            if match:
                tick = json_text(match[1]); ticks.append(tick)
                self.need(isinstance(tick, dict) and tick.get('waiting') in (None, 'gate')
                          and type(tick.get('jobs')) is int and tick['jobs'] > 0
                          and type(tick.get('wait:gate')) is int and 0 <= tick['wait:gate'] <= tick['jobs'], 'unknown/failed tick transition')
            else:
                job = re.fullmatch(r'\S+ tick job (\{.*\})', line)
                if job:
                    decision = json_text(job[1]).get('decision')
                    self.need(isinstance(decision, str) and not decision.startswith(('refused:', 'failed:', 'unknown:')),
                              'refused tick job transition')
                else:
                    self.need(re.fullmatch(r'\S+ (controller .+ holds the instance lock|stop: .+)', line), 'unparseable dispatcher log')
        self.need(len(ticks) == 2, 'two measured ticks missing')
        return {'dry_jobs': len(plan['jobs']), 'ticks': ticks, 'exits': [0, 0, 0]}

    def clean_stop(self):
        doc = self.doc('resources', 'ky.fixture_resources/1')
        self.need(isinstance(doc.get('started'), dict) and isinstance(doc.get('after'), dict), 'resource inventories missing')
        for kind in ('processes', 'databases', 'worktrees'):
            started, after = doc['started'].get(kind), doc['after'].get(kind)
            self.need(isinstance(started, list) and isinstance(after, list), 'resource category unknown: ' + kind)
            if kind == 'processes':
                self.need(bool(started), 'fixture server/process identity missing')
                for r in started + after:
                    self.need(isinstance(r, dict) and type(r.get('pid')) is int and r['pid'] > 0
                              and isinstance(r.get('start'), str) and bool(r['start']), 'invalid process identity')
            else:
                if kind == 'worktrees': self.need(bool(started), 'fixture worktree inventory missing')
                self.need(all(isinstance(p, str) and Path(p).is_absolute() for p in started + after), 'invalid resource path')
            self.need(all(r not in after for r in started), 'fixture resource survives: ' + kind)
        return {'live_run_changed': self.changes(), 'removed': doc['started']}

    def build_by_fleet(self):
        # kyd_jobs.py:23-25,119-125; kyd_kinds_build.py:42-48 (tracker event shapes).
        events, reg, number, head = self.registration()
        rows = self.states('BUILD')
        successes = [j for j in rows if j.get('phase') == 'ended' and j.get('outcome') == 'done'
                     and j.get('stream') == 'K' and j.get('controller_id') and j.get('slot')
                     and reg['actor'] == 'stream-K:' + j['slot'] and j.get('claim_id')]
        good = []
        for j in successes:
            claims = [e for e in events[:events.index(reg)] if e.get('kind') == 'claim' and e.get('state') == 'acquired'
                      and e.get('claim_id') == j['claim_id'] and e.get('worker_id') == j['slot'] and e.get('actor') == reg['actor']]
            if claims: good.append(j['job_id'])
        self.need(bool(good), 'no ended/done dispatcher BUILD with matching acquired claim and review lane')
        return {'jobs': good, 'pr': number, 'registered_head': head, 'builder': reg['actor']}

    def pr_opened(self):
        _, _, number, head = self.registration()
        self.pr(number, head)
        return {'pr': number, 'registered_head': head}

    def verify_boundary(self):
        # kyd_kinds_build.py:952-1004; kyboundary.sh:524-578 (including per-side facts).
        _, _, number, head = self.registration()
        rows = [j for j in self.states('VERIFY') if j.get('head') == head]
        self.need(bool(rows), 'VERIFY job at registered head missing')
        job = rows[-1]
        self.need(job.get('phase') == 'ended' and job.get('outcome') == 'done' and job.get('stream') == 'V'
                  and job.get('slot') and job.get('controller_id') and job.get('verdict_phase') == 'pre_merge'
                  and type(job.get('exit_code')) is int and job['exit_code'] == 0,
                  'VERIFY did not end done at pre_merge boundary')
        scratch = job.get('job_scratch')
        self.need(isinstance(scratch, str) and Path(scratch).is_absolute(), 'VERIFY job scratch unknown')
        check = self.live_doc(Path(scratch) / 'boundary.check.json')
        self.need(check.get('schema') == 'ky.boundary_check/1' and check.get('job_id') == job['job_id']
                  and check.get('mechanism') == 'seatbelt-file-write-deny/1' and check.get('mechanism_intact') is True
                  and check.get('result') == 'intact' and check.get('reasons') == [], 'boundary mechanism violated/unknown')
        keys = ('head_unchanged', 'status_clean', 'tracked_hashes_unchanged')
        self.need(all(check.get(k) is True for k in keys), 'boundary aggregate facts violated/unknown')
        for side, path in (('view', str(Path(scratch) / 'view')), ('worktree', job.get('worktree'))):
            facts = check.get(side)
            self.need(isinstance(facts, dict) and facts.get('path') == path and path is not None
                      and all(facts.get(k) is True for k in keys), 'boundary side facts violated/unknown: ' + side)
        return {'job': job['job_id'], 'head': head, 'mechanism': check['mechanism']}

    def accepted_pr_head_in_log(self):
        events, reg, number, head = self.registration()
        verdicts = [e for e in events[events.index(reg) + 1:] if e.get('kind') == 'verdict'
                    and e.get('phase') == 'pre_merge' and e.get('head') == head]
        self.need(bool(verdicts), 'ACCEPTED verdict at registered head missing')
        verdict = verdicts[-1]
        actor = verdict.get('actor')
        self.need(verdict.get('result') == 'ACCEPTED' and isinstance(actor, str)
                  and re.fullmatch(r'stream-V:[A-Za-z0-9._-]+', actor)
                  and actor.split(':', 1)[1] != reg['actor'].split(':', 1)[1], 'verdict rejected/unknown or same lane')
        jobs = [j for j in self.states('VERIFY') if j.get('head') == head and j.get('phase') == 'ended'
                and j.get('outcome') == 'done' and actor == 'stream-V:' + str(j.get('slot'))
                and verdict.get('detail', '').startswith('job ' + j['job_id'] + ';')]
        self.need(bool(jobs), 'verdict not bound to a completed independent VERIFY job')
        return {'head': head, 'pr': number, 'reviewer': actor, 'job': jobs[-1]['job_id']}

    def merge_parked_no_auto_merge(self):
        # kyd_kinds_land.py:390-396,827-845: durable request under HOLD_MERGES.
        accepted = self.accepted_pr_head_in_log()
        path = self.run / 'merge_requests' / (self.item + '.json')
        parked = self.live_doc(path)
        self.need(parked.get('schema') == 'ky.merge_request/1' and parked.get('item') == self.item
                  and type(parked.get('pr')) is int and parked['pr'] == accepted['pr']
                  and parked.get('registered_head') == accepted['head'] and parked.get('recorded_at'), 'parked merge request differs')
        self.refs['hold'] = self.inputs.file(self.run / 'HOLD_MERGES', 'rehearsal_obligation_' + self.name)
        self.need(not os.path.lexists(self.run / 'merge_requests' / 'queued' / (self.item + '.json')), 'merge already queued')
        pr = self.pr(accepted['pr'], accepted['head'])
        self.need('autoMergeRequest' in pr and pr['autoMergeRequest'] is None, 'PR auto-merge enabled or observation missing')
        return dict(accepted, parked_request=str(path), autoMergeRequest=None)


DETECTORS = {
    'component_tests_final_bundle': Detector.component_tests,
    'fixture_live_events_unchanged': Detector.live_events_unchanged,
    'fixture_no_live_tracker_access': Detector.no_live_tracker_access,
    'fixture_no_external_requests': Detector.no_external_requests,
    'fixture_expected_transitions': Detector.expected_transitions,
    'fixture_clean_stop': Detector.clean_stop,
    'live_build_by_fleet': Detector.build_by_fleet,
    'live_pr_opened': Detector.pr_opened,
    'live_verify_boundary': Detector.verify_boundary,
    'live_accepted_pr_head_in_log': Detector.accepted_pr_head_in_log,
    'live_merge_parked_no_auto_merge': Detector.merge_parked_no_auto_merge,
}


def check_rehearsal(doc, repo, inputs, manifest=None, run=None, live_evidence=None, expected_fail=()):
    rows = doc.get('obligations')
    if not isinstance(rows, list):
        refuse('rehearsal_obligation', 'missing obligations: ' + ', '.join(REQUIRED_OBLIGATIONS))
    indexed = {}
    for row in rows:
        name = row.get('id') if isinstance(row, dict) else None
        if not isinstance(name, str) or name not in DETECTORS or name in indexed:
            refuse('rehearsal_obligation', f'unknown/duplicate obligation: {name}')
        indexed[name] = row
    for name in REQUIRED_OBLIGATIONS:
        if name not in indexed:
            refuse('rehearsal_obligation', name + ': missing required obligation')
    # Validate the record before resolving any pointers; /2 declarations confer no authority.
    schema = inputs.document(repo / km.FLEET / 'schemas/rehearsal_results.json', 'rehearsal_schema')
    for name, row in indexed.items():
        row_findings = kyschema.validate(schema['properties']['obligations']['items'], row)
        if row_findings:
            refuse('rehearsal_obligation_' + name, '; '.join(row_findings))
    findings = kyschema.validate(schema, doc)
    if findings:
        refuse('rehearsal_schema', '; '.join(findings))
    if doc['substitutions'] != [SUBSTITUTION]:
        refuse('rehearsal_substitution', 'required: answer 09 §6, live first item replaces fixture model jobs')
    live_items = {indexed[n]['item'] for n in REQUIRED_OBLIGATIONS if n.startswith('live_') and 'item' in indexed[n]}
    if len(live_items) != 1:
        refuse('rehearsal_obligation', 'live obligations must name one first item')
    measured = []
    for name in REQUIRED_OBLIGATIONS:
        try:
            detector = Detector(name, indexed[name], inputs, manifest, run, live_evidence, expected_fail)
            facts = DETECTORS[name](detector)
            measured.append({'id': name, 'outcome': 'PASS', 'detector': 'kyfinal/3:' + name,
                             'observations': facts, 'evidence': detector.refs})
        except Refused:
            raise
        except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ET.ParseError) as e:
            refuse('rehearsal_obligation_' + name, 'unparseable evidence: ' + type(e).__name__)
    return measured

def tree_files(root):
    root = Path(root)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink():
        refuse("installed_tree", f"not an absolute regular directory: {root}")
    rows = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in dirs:
            if Path(directory, name).is_symlink():
                refuse("installed_tree", f"linked directory: {Path(directory, name)}")
        for name in files:
            path = Path(directory, name)
            if not stat.S_ISREG(path.lstat().st_mode):
                refuse("installed_tree", f"not a regular file: {path}")
            rows[str(path.relative_to(root))] = km.sha256(path)
    return rows


def tree_digest(rows):
    # install.sh:1062-1063, exactly (paths relative to the installed tree).
    return hashlib.sha256("".join(f"{sha}  {rel}\n" for rel, sha in sorted(rows.items())).encode()).hexdigest()


def installed(receipt, manifest, inputs, repo):
    want = component_map(manifest["components"], "manifest_components")
    rows = receipt.get("components")
    have = component_map(rows, "installed_bytes")
    if have != want:
        refuse("installed_bytes", "installed component set/hashes differ from the reviewed manifest")
    destinations = set()
    for row in rows:
        ref = inputs.file(row.get("installed_path", ""), "installed_bytes", row["sha256"])
        if ref["path"] in destinations:
            refuse("installed_bytes", "duplicate installed destination")
        destinations.add(ref["path"])
    trees = receipt.get("trees")
    if not isinstance(trees, dict):
        refuse("installed_tree", "bootstrap receipt has no measured trees")
    entrypoints = manifest["entrypoints"]
    bundle = trees.get("bundle")
    if not isinstance(bundle, list) or len(bundle) != len(entrypoints):
        refuse("installed_bundle", "installed bundle is not the five entrypoints")
    seen = set()
    for row in bundle:
        if not isinstance(row, dict) or row.get("role") not in entrypoints or row["role"] in seen:
            refuse("installed_bundle", "invalid/duplicate bundle role")
        seen.add(row["role"])
        entry = entrypoints[row["role"]]
        if row.get("path") != entry["path"] or row.get("sha256") != entry["sha256"]:
            refuse("installed_bundle", f"entrypoint differs: {row['role']}")
        inputs.file(row.get("installed_path", ""), "installed_bundle", row["sha256"])
    # Compare the complete destination file sets, including the installed bundle.
    for name in ("fleet_live", "tracker_live", "bin"):
        section = trees.get(name)
        if not isinstance(section, dict) or not isinstance(section.get("path"), str):
            refuse("installed_tree", f"missing measured {name} tree")
        root = Path(section["path"])
        expected = {}
        for row in rows + (bundle if name == "fleet_live" else []):
            path = Path(row["installed_path"])
            if path.is_relative_to(root):
                expected[str(path.relative_to(root))] = row["sha256"]
        actual = tree_files(root)
        if not expected or actual != expected:
            refuse("installed_tree", f"{name} has missing, changed or unbound files")
        if name != "bin":
            if section.get("files") != len(actual) or section.get("tree_sha256") != tree_digest(actual):
                refuse("installed_tree", f"{name} measured count/digest differs")
        else:
            files = section.get("files")
            if not isinstance(files, list) or len(files) != len(actual):
                refuse("installed_tree", "bin measurement differs")
            for entry in files:
                if not isinstance(entry, dict) or entry.get("name") not in actual \
                        or entry.get("path") != str(root / entry["name"]) or entry.get("sha256") != actual[entry["name"]]:
                    refuse("installed_tree", "bin file measurement differs")
                mode = "%04o" % stat.S_IMODE(Path(entry["path"]).stat().st_mode)
                if mode != entry.get("mode"):
                    refuse("installed_tree", "bin file mode differs")
    for row in rows + bundle:
        # The source blob modes are established by install.sh:661-667, not current chmod.
        commit = manifest["approved_source_commit"] if "role" in row else manifest["components_commit"]
        result = km.git(str(repo), "ls-tree", commit, "--", row["path"])
        mode = result.stdout.split()[:1]
        want_mode = {"100644": 0o644, "100755": 0o755}.get(mode[0] if mode else None)
        if result.returncode or want_mode is None or stat.S_IMODE(Path(row["installed_path"]).stat().st_mode) != want_mode:
            refuse("installed_bytes", f"installed mode differs from reviewed blob: {row['path']}")
    tracker = receipt.get("tracker_revision")
    if not isinstance(tracker, dict) or not isinstance(tracker.get("package_sha256"), str) \
            or not HEX.fullmatch(tracker["package_sha256"]):
        refuse("tracker_revision_missing", "no measured tracker package_sha256")
    if tracker["package_sha256"] != trees["tracker_live"]["tree_sha256"]:
        refuse("tracker_revision_mismatch", "measured tracker package differs from installed tracker tree")
    return tracker["package_sha256"]


def version_api(repo):
    """Use the reviewed real consumer's F2/F5/F6/F8 checks without staging or writing files.

    kyversion.sh itself executes this embedded stdlib program; only its definitions
    are loaded here. The caller has already verified it against its reviewed blob.
    """
    text = (repo / km.FLEET / "kyversion.sh").read_text(encoding="utf-8")
    program = text.split("\n: <<'KYVERSION_PY'\n", 1)[1].rsplit("\nKYVERSION_PY\n", 1)[0]
    definitions = program.rsplit("\ntry:\n    status = main(sys.argv[2:])", 1)[0]
    namespace = {"__name__": "kyfinal_version_checks"}
    exec(compile(definitions, "kyversion.sh", "exec"), namespace)
    return namespace


def check_version(api, receipt, manifest, repo, run, inputs):
    for code, findings in (
        ("final_manifest", api["check_final_manifest"](manifest, "")),
        ("installed_pairs", api["check_pairs"](manifest, "", str(repo))),
        ("loop_qualification", api["check_loop_qualifications"](receipt, "")),
    ):
        if findings:
            refuse(code, "; ".join(findings))
    links, reason = api["activation_chain"](str(run))
    if reason:
        refuse("activation_chain", reason)
    for link in links:
        inputs.file(run / link["file"], "activation_chain", link["sha256"])
    for row in receipt["qualifications"]:
        inputs.file(row["receipt"], "loop_qualification", row["receipt_sha256"])


def packet_paths(path, inputs):
    if path.is_dir() and not path.is_symlink():
        paths = sorted(path.glob("PACKET_*.md"))
    else:
        inputs.file(path, "packets_missing")
        paths = [path.parent / line.strip() for line in path.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
    if not paths:
        refuse("packets_missing", "no packets selected")
    paths = [Path(os.path.abspath(p)) for p in paths]
    if len(paths) != len(set(paths)):
        refuse("packets_duplicate", "packet list contains duplicates")
    return paths


def child_env():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_", "PYTHON")) and k != "KY_GIT"}
    env.update(GIT_OPTIONAL_LOCKS="0", PYTHONDONTWRITEBYTECODE="1")
    return env


def child(argv, cwd, code):
    try:
        return subprocess.run(argv, cwd=cwd, env=child_env(), stdin=subprocess.DEVNULL,
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=240)
    except (OSError, ValueError, subprocess.SubprocessError) as e:
        refuse(code, f"command could not complete ({type(e).__name__})")


def admit_packets(selected, repo, inputs):
    packets = []
    for packet in selected:
        ref = inputs.file(packet, "packet_not_admitted")
        done = child([sys.executable, "-I", "-B", str(repo / km.FLEET / "kypacket.py"),
                      "check", str(packet), "--repo", str(repo)], repo, "packet_not_admitted")
        try:
            report = json.loads(done.stdout)
        except ValueError:
            report = None
        if done.returncode or not isinstance(report, dict) or report.get("admitted") is not True \
                or report.get("schema") != "ky.packet_check/1" or report.get("packet") != str(packet):
            refuse("packet_not_admitted", f"{packet}: exit {done.returncode}: {' '.join(done.stderr.split())}")
        packets.append(ref)
    return packets


def observe(repo, run, bootstrap):
    try:
        review = repo / bootstrap["review"]["path"]
        return km.observe(str(repo), str(run), bootstrap["approved_source_commit"], str(review),
                          components_commit=bootstrap["components_commit"],
                          recorded_locations=bootstrap["review"].get("area_reviews", []))
    except (km.Refused, KeyError, TypeError, OSError, ValueError) as e:
        refuse("source_observation", str(e))


def build(a):
    repo, run = Path(os.path.abspath(a.repo)), Path(os.path.abspath(a.run))
    out_manifest, out_receipt = Path(os.path.abspath(a.out_manifest)), Path(os.path.abspath(a.out_receipt))
    if out_manifest != run / "VERSIONS.json" or out_receipt != run / "INSTALL_RECEIPT.json":
        refuse("output_path", "outputs must be RUN/VERSIONS.json and RUN/INSTALL_RECEIPT.json")
    inputs = Inputs()
    original = inputs.document(out_receipt, "bootstrap_receipt_missing")
    if original.get("mode") != "bootstrap":
        refuse("bootstrap_receipt_mode", "only a bootstrap receipt may be finalised")
    backup = Path(str(out_receipt) + ".bootstrap")
    backfill_path = Path(str(out_receipt) + ".backfill.json")
    for path in (out_manifest, backup, backfill_path):
        if os.path.lexists(path):
            refuse("output_exists", f"will not overwrite {path}")
    bootstrap_path = run / "VERSIONS.bootstrap.json"
    bootstrap = inputs.document(bootstrap_path, "bootstrap_manifest_missing")
    if km.with_digest(bootstrap)["manifest_sha256"] != bootstrap.get("manifest_sha256"):
        refuse("bootstrap_manifest_digest", "bootstrap manifest digest differs from content")
    if bootstrap.get("mode") != "bootstrap":
        refuse("bootstrap_manifest_mode", "not a bootstrap manifest")
    if bootstrap.get("deferred_components"):
        refuse("deferred_components", "review, bind and reinstall every component first")
    binding = original.get("manifest")
    if not isinstance(binding, dict) or binding.get("manifest_sha256") != bootstrap["manifest_sha256"] \
            or binding.get("sha256") != inputs.hashes[str(bootstrap_path)]:
        refuse("bootstrap_manifest_binding", "installer receipt does not bind this bootstrap manifest")
    source = original.get("source")
    if not isinstance(source, dict) or any(source.get(key) != bootstrap.get(key)
                                           for key in ("approved_source_commit", "components_commit")):
        refuse("bootstrap_source_binding", "installer source commits differ from bootstrap manifest")
    top = km.git(str(repo), "rev-parse", "--show-toplevel")
    if top.returncode or Path(os.path.realpath(top.stdout.strip())) != Path(os.path.realpath(repo)):
        refuse("source_repo", "--repo is not the top of a git work tree")
    observed = observe(repo, run, bootstrap)
    if km.with_digest(observed) != bootstrap:
        refuse("source_observation", "bootstrap manifest no longer matches reviewed source/probes/qualifications")
    for row in observed["components"] + list(observed["entrypoints"].values()):
        inputs.file(repo / row["path"], "source_observation", row["sha256"])
    for pair in observed["generated_pairs"]:
        for key in ("canonical", "compatibility"):
            inputs.file(repo / pair[key], "source_observation", pair["sha256"])
    inputs.file(repo / observed["review"]["path"], "source_observation", observed["review"]["sha256"])
    for row in observed["review"]["area_reviews"]:
        inputs.file(repo / row["record"], "source_observation", row["record_sha256"])
    for row in [observed["probes"]] + observed["qualifications"]:
        inputs.file(row["path"], "source_observation", row["sha256"])
    tracker_revision = installed(original, observed, inputs, repo)
    rehearsal_path, coverage_path = Path(os.path.abspath(a.rehearsal)), Path(os.path.abspath(a.coverage))
    rehearsal = inputs.document(rehearsal_path, "rehearsal_unreadable")
    tested = component_map(rehearsal.get("tested_components"), "tested_components_mismatch")
    if tested != component_map(observed["components"], "manifest_components"):
        refuse("tested_components_mismatch", "rehearsal did not test the exact final component hashes")
    measured = check_rehearsal(rehearsal, repo, inputs, observed, run,
                               Path(os.path.abspath(a.live_evidence_dir)), a.expected_fail_test_id)
    coverage = inputs.document(coverage_path, "coverage_unreadable")
    # Area-review records use review.verdict; aggregate reviews use top-level verdict.
    nested = coverage.get("review")
    verdicts = ([coverage["verdict"]] if "verdict" in coverage else [])
    if isinstance(nested, dict) and "verdict" in nested:
        verdicts.append(nested["verdict"])
    if not verdicts or any(v != "ACCEPTED" for v in verdicts):
        refuse("coverage_not_accepted", "coverage review verdict is not unambiguously ACCEPTED")
    selection = Path(os.path.abspath(a.packets))
    selected = packet_paths(selection, inputs)
    packets = admit_packets(selected, repo, inputs)
    manifest = copy.deepcopy(observed)
    manifest.update(schema="ky.versions/1", mode="final", authorises="final reviewed installed bundle")
    manifest.pop("deferred_note")
    manifest = km.with_digest(manifest)
    receipt = copy.deepcopy(original)
    receipt.update(mode="final", bootstrap_tracker_revision=copy.deepcopy(original["tracker_revision"]),
                   tracker_revision=tracker_revision)
    receipt["manifest"] = {"path": str(out_manifest), "sha256": hashlib.sha256(encoded(manifest)).hexdigest(),
                           "manifest_sha256": manifest["manifest_sha256"]}
    receipt["rehearsal"] = {"results": inputs.file(rehearsal_path, "rehearsal_unreadable"),
                            "sha256": inputs.hashes[str(rehearsal_path)], "tested_components": rehearsal["tested_components"],
                            "detectors": measured, "expected_fail_test_ids": sorted(a.expected_fail_test_id)}
    receipt["coverage"] = dict(inputs.file(coverage_path, "coverage_unreadable"), verdict="ACCEPTED")
    receipt["packets"] = packets
    api = version_api(repo)
    check_version(api, receipt, manifest, repo, run, inputs)
    try:
        evidence = kybackfill.validate(repo, a.backfill_banner_file, a.backfill_session_log,
                                       a.backfill_entry_id, a.backfill_banner_id, inputs)
    except kybackfill.Invalid as e:
        refuse("backfill_validator_failed", str(e))
    receipt["backfill"] = {"path": str(backfill_path), "sha256": hashlib.sha256(encoded(evidence)).hexdigest(),
                           "validated": evidence["exit_code"] == 0}
    inputs.unchanged()
    if packet_paths(selection, inputs) != selected:
        refuse("inputs_changed", "packet directory selection changed")
    if observe(repo, run, bootstrap) != observed:
        refuse("inputs_changed", "source observations changed during validation")
    installed(original, manifest, inputs, repo)   # reverify installed bytes against FINAL manifest
    if admit_packets(selected, repo, inputs) != packets:
        refuse("inputs_changed", "packet admission changed during validation")
    check_version(api, receipt, manifest, repo, run, inputs)
    if check_rehearsal(rehearsal, repo, inputs, observed, run,
                       Path(os.path.abspath(a.live_evidence_dir)), a.expected_fail_test_id) != measured:
        refuse("inputs_changed", "rehearsal observations changed during validation")
    inputs.unchanged()
    proposed = {"manifest": manifest, "receipt": receipt, "backfill_evidence": evidence}
    if a.dry:
        print(json.dumps(proposed, indent=1, sort_keys=True, ensure_ascii=False))
        return 0
    # No refusal path above has written. Reserve all new files exclusively; roll back
    # publication on I/O failure. Receipt replacement is last (the acceptance switch).
    files = [(backup, out_receipt.read_bytes()), (backfill_path, encoded(evidence)), (out_manifest, encoded(manifest))]
    created = []
    temporary = Path(str(out_receipt) + ".kyfinal.tmp")
    try:
        for path, data in files + [(temporary, encoded(receipt))]:
            with path.open("xb") as stream:
                created.append(path)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        os.replace(temporary, out_receipt)
    except OSError as e:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        refuse("publication_failed", type(e).__name__)
    print(json.dumps({"out_manifest": str(out_manifest), "out_receipt": str(out_receipt),
                      "manifest_sha256": manifest["manifest_sha256"], "components": len(manifest["components"])}))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("build")
    for name in ("repo", "run", "rehearsal", "coverage", "packets", "backfill-banner-file",
                 "backfill-session-log", "backfill-entry-id", "backfill-banner-id", "out-manifest", "out-receipt"):
        command.add_argument("--" + name, required=True)
    command.add_argument("--live-evidence-dir", required=True)
    command.add_argument("--expected-fail-test-id", action="append", default=[],
                         help="explicit JUnit classname::name exception; recorded in receipt")
    command.add_argument("--dry", action="store_true")
    args = parser.parse_args(argv)
    try:
        return build(args)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, IndexError) as e:
        print(f"refused: input_unreadable: {type(e).__name__}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
