"""kyjob_engines v1.0, status: built, pending review (KV3-B-KYJOB-ENGINES).

Codex adapter only. Claude never imports this during launch planning. All controller
commands use ctx.sh/ky/act; no tool runs on import. The reviewed kyqualify/kyboot
producers own argv, guards and stream parsing. (I) denotes a conservative packet
interpretation: linked worktrees, exact file scope, no unproved action replay.
Changelog: v1.0 (2026-10-13): engine selection, guarded landing and silence timeout.
Campaign add-on (2026-10-13): launch-pinned kyroute owns/shared scope and blocking landing checks.
Fix B1 (2026-10-13): unreadable persisted activity/log or launch/landing checkpoints hold; no invented replay.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
import time

import kyaction as ka
import kyboot as boot
import kyqualify as qualify
import kyschema

HERE = Path(__file__).resolve().parent
FIELDS = ('engine', 'launch_config_path', 'sandbox_mode', 'stall_seconds')
HEX = re.compile(r'^[0-9a-f]{40}$')


class Refusal(Exception):
    pass


class Hold(Refusal):
    pass


# Role adapter postures; the existing code landing protocol remains BUILD/REWORK only.
READ_ONLY_KINDS = {"VERIFY", "PRE-ACCEPT", "POST-READBACK", "RULING"}
CODE_LANDING_KINDS = {"BUILD", "REWORK"}
MODEL_KINDS = READ_ONLY_KINDS | CODE_LANDING_KINDS | {"ARTIFACT", "REQUEST-PREP", "MODEL", "PLAN"}


def metadata(job):
    mode = job.get('sandbox_mode', 'locked')
    return dict(engine='codex', sandbox_mode=mode,
                sandbox='full (owner direction 2026-10-12)' if mode == 'full' else 'locked')


def selection(job):
    engine = qualify.engine_of(job)
    if engine not in ('claude', 'codex'):
        raise Refusal('engine must be claude or codex; null/unknown never falls back')
    if engine == 'claude':
        if any(k in job for k in FIELDS[1:]):
            raise Refusal('Claude job carries Codex-only launch fields')
        return
    if job.get('kind') not in MODEL_KINDS:
        raise Refusal('Codex kind has no model role adapter')
    mode = job.get('sandbox_mode', 'locked')
    if mode not in ('locked', 'full'):
        raise Refusal('sandbox_mode must be locked or explicitly full')
    seconds = job.get('stall_seconds', 300)
    if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds <= 0:
        raise Refusal('stall_seconds must be positive seconds')
    path = job.get('launch_config_path')
    if not isinstance(path, str) or not os.path.isabs(path) or os.path.normpath(path) != path:
        raise Refusal('launch_config_path must be an absolute normalised path')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pointer(job):
    path = Path(job['worktree']) / '.git'
    if not stat.S_ISREG(path.lstat().st_mode):
        raise Refusal('the working copy needs a regular .git pointer file')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with io.open(fd, 'rb') as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise Refusal('the .git pointer is not a regular file')
        return hashlib.sha256(f.read()).hexdigest()


def launch_config(job, env):
    selection(job)
    try:
        cfg = kyschema.load_json(job['launch_config_path'])
    except (OSError, ValueError) as exc:
        raise Refusal('launch configuration cannot be read') from exc
    if not isinstance(cfg, dict) or qualify.engine_of(cfg) != 'codex':
        raise Refusal('job and launch configuration engines do not match')
    errors = qualify.validate_codex_config(cfg)
    if errors:
        raise Refusal('; '.join(errors))
    for name in ('worktree', 'prompt_path', 'role', 'model', 'effort'):
        if cfg[name] != job[name]:
            raise Refusal('launch configuration does not match job ' + name)
    if cfg['model'] != 'gpt-6.1-sol' or cfg['effort'] != 'high':
        raise Refusal('Codex jobs require gpt-6.1-sol/high')
    if cfg['sandbox'] != 'workspace-write' or cfg['network'] is not False or cfg['writable_dirs']:
        raise Refusal('Codex base requires workspace-write, network off and no extra writable roots')
    if any(job.get(k) is not None for k in ('claude_bin', 'permission_mode', 'max_turns', 'mcp_config')) \
            or job.get('extra_lean_flags') or job.get('disallowed_tools'):
        raise Refusal('mixed Claude launch fields in a Codex job')
    verifier = job['kind'] in READ_ONLY_KINDS
    if verifier != qualify.job_rooted(cfg):
        raise Refusal('VERIFY must be job-rooted; builders must be worktree-rooted'
                          if job['kind'] in ('BUILD', 'REWORK', 'VERIFY') else
                          'read-only roles must be job-rooted; builders must be worktree-rooted')
    if not verifier and cfg.get('commit_mode') != 'launcher':
        raise Refusal('Codex builder commit_mode must be launcher')
    if cfg['child_path'] != env['PATH'] or any(n not in env for n in cfg['env_names']):
        raise Refusal('configuration environment/path does not match the job')
    if 'JOB_SCRATCH' not in cfg['env_names']:
        raise Refusal('Codex job must receive JOB_SCRATCH')
    common, why = qualify.git_common_dir(job['worktree'])
    if common is None:
        raise Refusal('common Git directory cannot be observed: ' + str(why))
    for path in (job['job_scratch'], job['tmp_path']):
        root = os.path.realpath(path)
        if qualify._covers(root, common) or qualify._covers(common, root):
            raise Refusal('job scratch/TMPDIR overlaps the common Git directory')
    return cfg


def argv(cfg, job):
    """Only the cockpit's three full-mode changes to the reviewed base builder."""
    out = qualify.build_argv(cfg, job['job_scratch'])
    if job.get('sandbox_mode', 'locked') == 'full':
        if out.count('-s') != 1 or out[out.index('-s') + 1] != 'workspace-write':
            raise Refusal('the reviewed base argv has no unique workspace-write sandbox')
        out[out.index('-s') + 1] = 'danger-full-access'
        for key in ('sandbox_workspace_write.network_access=', 'sandbox_workspace_write.exclude_slash_tmp='):
            positions = [i for i, v in enumerate(out) if v.startswith(key)]
            if len(positions) != 1 or out[positions[0] - 1] != '-c':
                raise Refusal('the reviewed base argv has no unique sandbox setting')
            i = positions[0]
            del out[i - 1:i + 1]
    return out


def plan(job, own, helper):
    """Same-process shell plan, with existing prompt/refusal/boundary checks."""
    helper['check_prompt'](job)
    bounded = helper['check_boundary_form'](job)
    env = dict(helper['job_environment'](job, own))
    cfg = launch_config(job, env)
    deadline = helper['parse_deadline'](job['deadline'])
    if deadline is None or not time.time() < deadline <= time.time() + cfg['deadline_seconds']:
        raise Refusal('Codex deadline is missing, past or exceeds configured duration')
    version = qualify.codex_version_text(cfg['codex_bin'])
    found = qualify.version_tuple(version)
    minimum = qualify.version_tuple(cfg['codex_min_version'])
    if found is None or found < minimum:
        raise Refusal('Codex program version is unknown or below the configured minimum')
    command = argv(cfg, job)
    before = (job.get('checkpoint') or {}).get('codex_launch')
    cfg_hash = digest(job['launch_config_path'])
    if before:
        if cfg_hash != before.get('config_sha256') or pointer(job) != before.get('pointer'):
            raise Refusal('Codex launch inputs changed after controller preparation')
    prefix = helper['prepare_boundary'](job['job_id'], own) if bounded else []
    pairs = [(n, env[n]) for n in cfg['env_names']]
    parts = ['ky.jobplan/1', job['worktree'], job['prompt_path'], job['stdout_path'], job['stderr_path']]
    parts += prefix + ['/usr/bin/env', '-i'] + ['%s=%s' % p for p in pairs] + command
    record = dict(job_id=job['job_id'], cwd=job['worktree'], argv=command,
                  env_names=sorted(cfg['env_names']), launch_config_path=job['launch_config_path'],
                  launch_config_sha256=cfg_hash, at=helper['utc_now_text'](), **metadata(job))
    if before:
        # Controller checkpoint is prepared before spawn (fleet/kyd_jobs.py:683-690, 782-787).
        for key in ('packet_sha256', 'scope_kind', 'paths', 'model_sha256', 'patterns', 'scope_ignored'):
            if key in before:
                record[key] = before[key]
    helper['write_atomic'](os.path.join(job['job_scratch'], 'kyjob.plan'),
                           b''.join(p.encode() + b'\0' for p in parts))
    helper['write_atomic'](os.path.join(job['job_scratch'], 'kyjob.launch.json'),
                           (json.dumps(record, sort_keys=True, indent=1) + '\n').encode())


def result_schema(job):
    return kyschema.load_json(HERE / 'schemas' / ('job_result_launcher_commit.json'
                             if job.get('kind') in CODE_LANDING_KINDS else 'job_result.json'))


def tool_env():
    # ctx.sh builds an allowlist itself; guards also receive no inherited Git overrides.
    return dict(PATH='/opt/homebrew/bin:/usr/bin:/bin', HOME=os.environ.get('HOME', ''),
                USER=os.environ.get('USER', ''), LANG='en_US.UTF-8', GIT_OPTIONAL_LOCKS='0')


def git(ctx, job, *args):
    rc, out, err = ctx.sh(['/usr/bin/git', '-C', job['worktree'], *args], env=tool_env())
    if rc is None:
        raise Hold('Git outcome unknown: ' + args[0])
    if rc != 0:
        raise Refusal('git %s refused: %s' % (args[0], ka.flat(err, 400)))
    return out


def remote_head(ctx, job):
    ref = 'refs/heads/' + job['branch']
    out = git(ctx, job, 'ls-remote', 'origin', ref)
    rows = [line.split() for line in out.splitlines() if line.strip()]
    if not rows:
        return None
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != ref or not HEX.fullmatch(rows[0][0]):
        raise Hold('origin branch observation is ambiguous')
    return rows[0][0]


def guards(job):
    # kyboot's guard needs only engine/worktree/work_root, not a bootstrap input schema.
    return boot.codex_guards(dict(engine='codex', worktree=job['worktree'],
                                  work_root='job' if job['kind'] in READ_ONLY_KINDS else 'worktree'), tool_env())


def guard_differences(before, after):
    if not isinstance(before, dict) or not isinstance(after, dict):
        return ['unknown guards']
    def unreadable(value):
        return value is None or (isinstance(value, dict) and any(unreadable(v) for v in value.values())) \
            or (isinstance(value, list) and any(unreadable(v) for v in value))
    if unreadable(before) or unreadable(after):
        return ['unreadable nested guard']
    try:
        out = boot.git_guard_changes(before.get('git'), after.get('git'))
    except (KeyError, TypeError):
        return ['unknown Git guard shape']
    if before.get('worktree') != after.get('worktree'):
        out.append('verifier working copy changed')
    # None is unreadable even when both observations happen to equal None.
    if 'worktree' in before and before['worktree'] is None:
        out.append('unknown verifier working copy')
    return out


def packet_scope(job):
    try:
        text = Path(job['packet_path']).read_text()
        doc = kyschema.load_json_text(text.split('```json\n', 1)[1].split('\n```', 1)[0])
        paths = doc['d1_paths']
    except (OSError, ValueError, KeyError, IndexError) as exc:
        raise Refusal('packet has no readable d1_paths') from exc
    if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p
            or os.path.isabs(p) or os.path.normpath(p) != p or '..' in p.split('/') for p in paths):
        raise Refusal('packet d1_paths must enumerate normalised relative files')
    return paths


def launch_scope(ctx, job):
    """Bootstrap exact files; campaign compiled patterns, never re-parsed at landing."""
    try:
        text = Path(job['packet_path']).read_text()
        doc = kyschema.load_json_text(text.split('```json\n', 1)[1].split('\n```', 1)[0])
        kind = doc['kind']
    except (OSError, ValueError, KeyError, IndexError) as exc:
        raise Refusal('packet has no readable kind') from exc
    if kind == 'bootstrap':
        return dict(scope_kind='bootstrap', paths=packet_scope(job))
    if kind not in ('feature', 'artifact', 'operation', 'schema-prerequisite'):
        raise Refusal('packet kind cannot authorize a Codex builder')
    import kyroute as route
    try:
        # ctx.model is the dispatcher model path (fleet/kydispatch.py:144, 376).
        # Use its own brief reader and entry parser (fleet/kyroute.py:286-346, 406-417).
        model_hash = digest(ctx.model)
        brief = route.model_brief(ctx.model, job['item']) or {}
        patterns, ignored = [], []
        for field in ('owns', 'shared'):
            entries = route.string_list(brief.get(field), 'brief.' + field)
            for entry in entries:
                text, prose = route.normalise(entry, job['worktree'])
                pats = None if prose else route.entry_patterns(text, job['worktree'])
                if not pats:
                    ignored.append(dict(source='brief.' + field, entry=entry))
                    continue
                for pat in pats:
                    if pat not in patterns:
                        patterns.append(pat)
        # (I) INTERPRETATION: refuse a model that changes while its launch scope is read,
        # so the pinned digest cannot name different bytes from the parsed authority.
        if digest(ctx.model) != model_hash:
            raise Refusal('plan model changed while preparing Codex scope')
    except (OSError, AttributeError, route.InputError) as exc:
        raise Refusal('plan model scope cannot be read: ' + str(exc)) from exc
    if not patterns:
        raise Refusal('item owns/shared enumerate no machine-readable path; '
                      'run this item on Claude or normalise its owns')
    # JSON transport of kyroute's compiled tuple/frozenset representation
    # (fleet/kyroute.py:96-156); this preserves directory expansion at launch.
    encoded = json.loads(json.dumps(patterns, default=lambda chars: sorted(chars)))
    return dict(scope_kind='campaign', paths=[], model_sha256=model_hash,
                patterns=encoded, scope_ignored=ignored)


def campaign_violation(launch, paths):
    """Return a tracker block detail before any stage/commit/push effect."""
    import kyroute as route
    try:
        # Exact manifest, failing closed if unreadable (fleet/kyroute.py:35, 218-242).
        frozen = route.read_manifest(route.DEFAULT_MANIFEST)
    except route.InputError as exc:
        raise Refusal('frozen manifest cannot be read: ' + str(exc)) from exc
    # FROZEN wins over any other violation, as in fleet/kyd_kinds_build.py:483-487.
    for path in paths:
        if path in frozen:
            return 'freeze: ' + path
    patterns = [tuple(segment if isinstance(segment, str) else
                      tuple(token if isinstance(token, str) else frozenset(token)
                            for token in segment)
                      for segment in pat) for pat in launch['patterns']]
    for path in paths:
        # Literal matcher (fleet/kyroute.py:159-197), and its existing control-plane
        # rule table / matcher (fleet/kyroute.py:54-57, 200-205).
        literal = route.literal(path)
        if any(rule in ('00_ARCHITECTURE/briefs/kalayantra/fleet/**',
                        'platform/scripts/governance/**', '.github/workflows/**', 'infra/**')
               for rule in route.path_rules([literal])):
            return 'control_plane: ' + path
        parts = path.split('/')
        test = (any(p in ('tests', '__tests__', 'test') for p in parts[:-1])
                or re.fullmatch(r'test_.*\.py|.*_test\.py|.*\.test\.tsx?|.*\.spec\.ts', parts[-1], flags=re.DOTALL))
        if not test and not any(route.overlaps(pat, literal) for pat in patterns):
            return 'outside_owns: ' + path
    return None


def changed_paths(status):
    """Both endpoints of every rename/copy, individual untracked files, no shell quoting."""
    parts, i, paths = status.split('\0'), 0, []
    while i < len(parts):
        part = parts[i]; i += 1
        if not part:
            continue
        if len(part) < 4 or part[2] != ' ':
            raise Refusal('unreadable Git status')
        paths.append(part[3:])
        if part[0] in 'RC' or part[1] in 'RC':
            if i >= len(parts) or not parts[i]:
                raise Refusal('unreadable rename endpoint')
            paths.append(parts[i]); i += 1
    return sorted(set(paths))


def prepare(ctx, job):
    """Snapshot before a model may run; all evidence stays in the controller checkpoint."""
    cp = job.get('checkpoint')
    if not isinstance(cp, dict):
        cp = job['checkpoint'] = {}
    if 'codex_launch' in cp:
        return
    if job['kind'] not in CODE_LANDING_KINDS | READ_ONLY_KINDS:
        # (I) INTERPRETATION: a template/role mapping does not authorize adapting
        # code landing (claims, commit/push/PR) to operation/planning completion.
        raise Refusal('Codex %s completion adapter is unqualified; no code landing authority' % job['kind'])
    if job['kind'] not in ('BUILD', 'REWORK', 'VERIFY') and (
            not isinstance(job.get('packet_path'), str) or not os.path.isabs(job['packet_path'])):
        raise Refusal('Codex launch snapshot requires a packet_path; kind is unqualified without one')
    ptr = pointer(job)  # BEFORE any Git, including guard derivation.
    branch = git(ctx, job, 'rev-parse', '--abbrev-ref', 'HEAD').strip()
    head = git(ctx, job, 'rev-parse', 'HEAD').strip()
    builder = job['kind'] not in READ_ONLY_KINDS
    if not HEX.fullmatch(head):
        raise Refusal('launch HEAD cannot be observed')
    if builder and (branch != job['branch'] or branch in ('main', 'HEAD')):
        raise Refusal('launch branch/HEAD is not the assigned item branch')
    if not builder and (job['kind'] == 'VERIFY' or job.get('head') is not None) and head != job.get('head'):
        raise Refusal('verifier source is not at its registered head')
    if git(ctx, job, 'diff', '--cached', '--name-only', '-z'):
        raise Refusal('the initial index is not clean')
    before = guards(job)
    if guard_differences(before, before):
        raise Refusal('launch guards cannot be observed')
    scope = launch_scope(ctx, job) if builder else dict(paths=[])
    cp['codex_launch'] = dict(pointer=ptr, branch=branch, head=head,
                             git_dir=git(ctx, job, 'rev-parse', '--absolute-git-dir').strip(),
                             remote_head=remote_head(ctx, job) if builder else None, packet_sha256=digest(job['packet_path']),
                             **scope, guards=before,
                             config_sha256=digest(job['launch_config_path']) if job.get('launch_config_path') else None,
                             **metadata(job))


def stalled(job, now):
    cp = job.get('checkpoint')
    if not isinstance(cp, dict):
        cp = job['checkpoint'] = {}
    activity = cp.get('codex_activity')
    def seconds(value):
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    if not seconds(now) or not seconds(job.get('stall_seconds', 300)) or job.get('stall_seconds', 300) <= 0:
        raise Hold('silence clock or threshold is unknown')
    if activity is not None:
        if (not isinstance(activity, dict) or not seconds(activity.get('launched_at'))
                or not seconds(activity.get('last_growth_at'))
                or not activity['launched_at'] <= activity['last_growth_at'] <= now
                or not isinstance(activity.get('bytes'), list) or len(activity['bytes']) != 2
                or any(type(n) is not int or n < 0 for n in activity['bytes'])):
            raise Hold('persisted launch/activity times or byte counts are unknown')
    elif job.get('pid') is not None:
        raise Hold('persisted launch/activity times are missing; silence cannot be reconstructed')
    sizes = []
    for key in ('stdout_path', 'stderr_path'):
        try:
            observed = os.lstat(job[key])
            if not stat.S_ISREG(observed.st_mode):
                raise Hold('activity log is not a regular file: ' + key)
            sizes.append(observed.st_size)
        except FileNotFoundError:
            if activity is not None:
                raise Hold('activity log observation is missing: ' + key)
            sizes.append(0)  # Before spawn only: launcher has not created its logs yet.
        except OSError as exc:
            raise Hold('activity log observation is unreadable: ' + key) from exc
    if activity is None:
        activity = cp['codex_activity'] = dict(launched_at=now, last_growth_at=now, bytes=sizes,
                                               **metadata(job))
    elif any(n < old for n, old in zip(sizes, activity['bytes'])):
        raise Hold('activity log shrank; persisted silence cannot be reconstructed')
    elif any(n > old for n, old in zip(sizes, activity['bytes'])):
        activity['last_growth_at'] = now
    activity.update(bytes=sizes, duration_seconds=now - activity['launched_at'],
                    silence_seconds=now - activity['last_growth_at'],
                    stdout_path=job['stdout_path'], stderr_path=job['stderr_path'],
                    deadline=job.get('deadline'))
    return activity['silence_seconds'] >= job.get('stall_seconds', 300)


def _state(ctx, job):
    """Fresh controller state for every effect (queue authorization cannot hide in stale state)."""
    doc, err = ka.read_json(Path(ctx.run) / 'jobs' / job['job_id'] / 'state.json')
    if err or not isinstance(doc, dict):
        raise Hold('fresh job state is unreadable')
    if doc.get('queue_authorised') or job.get('queue_authorised'):
        raise Refusal('queue authorization forbids a builder landing')
    queued = Path(ctx.run) / 'merge_requests' / 'queued' / (job['item'] + '.json')
    if os.path.lexists(queued):
        raise Refusal('the item holds a queue authorization')
    if doc.get('claim_id') != job.get('claim_id') or doc.get('branch') != job.get('branch'):
        raise Refusal('job claim/branch changed')


def fence(ctx, job, launch):
    _state(ctx, job)
    if pointer(job) != launch['pointer']:
        raise Refusal('the .git pointer changed; no Git command is allowed')
    claim, err = ka.read_json(Path(ctx.run) / 'claims' / (job['slot'] + '.json'))
    if err or not isinstance(claim, dict):
        raise Hold('claim observation is unknown')
    if (claim.get('claim_id') != job['claim_id'] or claim.get('item') != job['item']
            or claim.get('worker_id') != job['slot'] or claim.get('state') not in ('acquired', 'renewed')):
        raise Refusal('claim no longer belongs to this job')
    lock, err = ka.lock_owner(Path(ctx.run), 'item.' + job['item'])
    owners = ['%s:job.%s' % (c, job['key']) for c in (job.get('controller_id'), ctx.controller_id)]
    if err or not lock or lock.get('session_or_run_id') not in owners:
        raise Hold('the item lock is not held by this job')
    _events(ctx, job)
    _prs(ctx, job)  # fresh live queue authorization before every effect
    if digest(job['packet_path']) != launch['packet_sha256']:
        raise Refusal('the packet changed after launch')
    if git(ctx, job, 'rev-parse', '--absolute-git-dir').strip() != launch['git_dir']:
        raise Refusal('Git directory changed')
    current = guards(job)
    if guard_differences(current, current):
        raise Hold('current Codex guards cannot be observed')
    if guard_differences(launch['guards'], current):
        raise Refusal('Codex guards changed')
    if git(ctx, job, 'rev-parse', '--abbrev-ref', 'HEAD').strip() != launch['branch']:
        raise Refusal('the launch branch moved')


def _events(ctx, job):
    events = ctx.events(job['item'])
    if not isinstance(events, list):
        raise Hold('tracker events are unreadable')
    anchor = next((i for i, e in enumerate(events) if e.get('kind') == 'claim'
                   and e.get('claim_id') == job['claim_id'] and e.get('state') == 'acquired'), None)
    if anchor is None:
        raise Hold('no acquired claim event for this job')
    if events[anchor].get('actor') != 'stream-%s:%s' % (job['stream'], job['slot']):
        raise Refusal('acquired claim actor does not own this job')
    return events[anchor + 1:]


def _prs(ctx, job):
    rc, out, _ = ctx.sh(['/opt/homebrew/bin/gh', 'pr', 'list', '--head', job['branch'],
                       '--state', 'open', '--json', 'number,headRefName,headRefOid,baseRefName,mergeable,autoMergeRequest',
                       '--limit', '100'], cwd=job['worktree'], env=tool_env())
    if rc != 0:
        raise Hold('PR observation unknown')
    try:
        rows = kyschema.load_json_text(out)
    except ValueError as exc:
        raise Hold('PR observation is not JSON') from exc
    if not isinstance(rows, list) or len(rows) > 1:
        raise Refusal('expected at most one open item PR')
    if rows:
        pr = rows[0]
        if (not isinstance(pr, dict) or type(pr.get('number')) is not int or pr['number'] <= 0
                or pr.get('headRefName') != job['branch'] or pr.get('baseRefName') != 'main'
                or not HEX.fullmatch(str(pr.get('headRefOid')))):
            raise Refusal('PR branch/base/head identity mismatch')
        if pr.get('autoMergeRequest'):
            raise Refusal('a queued PR must not receive a builder push')
    return rows


def _action(ctx, job, step, inputs, effect, observer):
    def annotated(fn, *args, observing=False):
        try:
            status, detail = fn(*args)
        except Hold as exc:
            status, detail = 'unknown', dict(reason=str(exc))
        except (Refusal, OSError, ValueError, KeyError) as exc:
            status, detail = ('unknown' if observing else 'failed'), dict(reason=str(exc))
        return status, dict(detail, **metadata(job))

    status, observed = ctx.act('ACT-codex-%s-%s' % (job['job_id'], step), step,
                              dict(inputs, job_id=job['job_id'], item=job['item'], **metadata(job)),
                              dict(worktree=job['worktree'], branch=job['branch'], **metadata(job)),
                              lambda: annotated(effect), lambda record: annotated(observer, record, observing=True))
    if status != 'done':
        if status == 'unknown':
            raise Hold('%s observation unknown: %s' % (step, ka.flat(observed, 400)))
        raise Refusal('%s failed: %s' % (step, ka.flat(observed, 400)))
    return observed


def finish(ctx, job, result):
    """Runs before kind finish/release. Unknown effects retain claim and locks."""
    import kyd_jobs as jobs
    try:
        if jobs._process(job) != 'gone':
            raise Hold('process group is not proven gone')
        if job.get('exit_code') != 0 or (job.get('result_event') or {}).get('type') != 'turn.completed':
            raise Refusal('exit 0 and final turn.completed are required')
        if result is None:
            raise Refusal('Codex result schema or identity is invalid')
        launch = job.get('checkpoint', {}).get('codex_launch')
        required = ('pointer', 'branch', 'head', 'git_dir', 'packet_sha256', 'guards', 'paths')
        if not isinstance(launch, dict) or any(key not in launch for key in required):
            raise Hold('persisted controller launch snapshot is incomplete')
        if (any(not isinstance(launch[key], str) or not launch[key]
                for key in ('pointer', 'branch', 'head', 'git_dir', 'packet_sha256'))
                or not isinstance(launch['paths'], list)
                or guard_differences(launch['guards'], launch['guards'])):
            raise Hold('persisted controller launch guards or identity are unknown')
        # Pointer before all Git, even on repeat finish or verifier paths.
        if pointer(job) != launch['pointer']:
            raise Refusal('the .git pointer changed; no Git command is allowed')
        if job['kind'] in READ_ONLY_KINDS:
            current = guards(job)
            if guard_differences(current, current):
                raise Hold('current verifier guards cannot be observed')
            if guard_differences(launch['guards'], current):
                raise Refusal('verifier working copy/guards changed')
            if result.get('head_sha') is not None or result.get('pr_number') is not None:
                raise Refusal('verifier cannot report a head or PR')
            return None  # existing build-kind publish checks/releases boundary, then publishes verdict
        if job['kind'] not in CODE_LANDING_KINDS:
            raise Refusal('Codex %s completion adapter is unqualified; no code landing authority' % job['kind'])
        fence(ctx, job, launch)
        if result['status'] == 'blocked':
            return _register(ctx, job, launch, 'block', result['blocked_reason'], None, None)
        if result['status'] != 'done':
            raise Refusal('Codex reported failed; no landing')
        return _land(ctx, job, launch, result)
    except Hold as exc:
        return dict(outcome='held', detail=str(exc), failure_fp='codex_finish_unknown', **metadata(job))
    except (Refusal, OSError, ValueError, KeyError, ka.ActionError) as exc:
        return dict(outcome='failed', detail=str(exc), failure_fp='codex_finish_refused', **metadata(job))


def _register(ctx, job, launch, verb, detail, head, pr):
    actor = 'stream-%s:%s' % (job['stream'], job['slot'])

    def observe(record):
        states = [e for e in _events(ctx, job) if e.get('kind') == 'item' and not e.get('step')]
        if states:
            last = states[-1]
            if last.get('actor') != actor:
                return 'unknown', dict(reason='latest tracker actor does not own this claim')
            if last.get('state') == ('review' if verb == 'review' else 'blocked'):
                if last.get('detail') == detail:
                    return 'done', dict(head=head, pr=pr, detail=detail, **metadata(job))
                return 'unknown', dict(reason='registration head/PR/detail changed')
        return 'not_done', dict(reason='registration absent')

    def effect():
        fence(ctx, job, launch)
        if head and (git(ctx, job, 'rev-parse', 'HEAD').strip() != head or remote_head(ctx, job) != head):
            raise Refusal('registration HEAD/origin changed')
        rc, _, err = ctx.ky(verb, job['item'], '--detail', detail, stream=job['stream'], lane=job['slot'])
        if rc is not None and rc != 0:
            return 'failed', dict(reason=ka.flat(err, 400))
        seen, data = observe(None)
        return ('done' if seen == 'done' else 'unknown'), data

    # No overwrite of a registration by another actor or at another head.
    seen, data = observe(None)
    if seen == 'unknown':
        raise Hold(data['reason'])
    _action(ctx, job, verb, dict(head=head, pr=pr, detail=detail, claim_id=job['claim_id']), effect, observe)
    if head:
        job.update(head=head, pr=pr, registered_head=head)
        ka.write_json(Path(ctx.run) / 'jobs' / job['job_id'] / 'state.json', job)
    import kyd_kinds_build as kinds
    finished = kinds.finish(ctx, job)
    if finished.get('outcome') != ('done' if verb == 'review' else 'blocked'):
        raise Hold('unchanged build-kind finish did not observe the registration')
    return dict(finished, **metadata(job))


def diff_identity(job, paths):
    """Bind actual path types and bytes, including deletions and untracked files.

    Git status hashes only names/XY flags; equality of those cannot prove that a
    recovered stage still contains the builder's measured patch (§N.8).
    """
    rows = []
    for name in paths:
        path = Path(job['worktree']) / name
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            rows.append([name, 'deleted', None])
            continue
        if stat.S_ISLNK(mode):
            data = os.readlink(path).encode()
            kind = 'symlink'
        elif stat.S_ISREG(mode):
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with io.open(fd, 'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise Hold('changed file type cannot be observed')
                data = stream.read()
            kind = 'executable' if mode & 0o111 else 'regular'
        else:
            raise Refusal('packet path is not a regular file or symlink: ' + name)
        rows.append([name, kind, ka.sha_bytes(data)])
    return ka.sha_bytes(ka.canonical(rows))


def _land(ctx, job, launch, result):
    progress = job['checkpoint'].setdefault('codex_finish', dict(**metadata(job)))
    # (I) INTERPRETATION: an existing landing intent with lost progress cannot be
    # reconstructed from current HEAD/status; retain the job for reconciliation.
    if not isinstance(progress, dict):
        raise Hold('persisted landing progress is unreadable')
    if 'paths' not in progress:
        if any(os.path.lexists(ka.record_path(ctx.run, 'ACT-codex-%s-%s' % (job['job_id'], step)))
               for step in ('stage', 'commit', 'push', 'pr', 'review')):
            raise Hold('landing action exists but persisted progress is missing')
    elif (any(key not in progress for key in ('message', 'status_sha256', 'diff_sha256', 'packet_sha256', 'parent'))
          or not isinstance(progress['paths'], list) or not progress['paths']
          or any(not isinstance(path, str) or not path for path in progress['paths'])
          or any(not isinstance(progress.get(key), str) or not progress[key]
                 for key in ('message', 'status_sha256', 'diff_sha256', 'packet_sha256', 'parent'))):
        raise Hold('persisted landing progress is incomplete')
    head = git(ctx, job, 'rev-parse', 'HEAD').strip()
    message = result['commit_message']
    if not isinstance(message, str) or not message.strip() or '\0' in message:
        raise Refusal('done needs a nonempty NUL-free commit message')
    message = message.rstrip() + '\n'
    if progress.get('message') is not None and progress['message'] != message:
        raise Refusal('result commit message changed while landing')
    if 'paths' not in progress:
        if head != launch['head']:
            raise Refusal('builder moved HEAD (self-commit)')
        if git(ctx, job, 'diff', '--cached', '--name-only', '-z'):
            raise Refusal('builder left a changed index')
        if remote_head(ctx, job) != launch['remote_head']:
            raise Refusal('origin changed since launch (self-push or concurrent update)')
        status = git(ctx, job, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
        paths = changed_paths(status)
        if launch.get('scope_kind') == 'campaign':
            if not paths:
                raise Refusal('no changes to land')
            detail = campaign_violation(launch, paths)
            if detail:
                # Same ky block --detail freeze: call shape as the Claude flow
                # (fleet/kyd_kinds_build.py:487, 670-673); _register retains job ownership.
                return _register(ctx, job, launch, 'block', detail, None, None)
        elif not paths or any(p not in launch['paths'] for p in paths):
            raise Refusal('no changes or changed/rename/untracked path outside packet d1_paths')
        prs = _prs(ctx, job)
        if prs and prs[0]['headRefOid'] != head:
            raise Refusal('existing PR head does not match launch HEAD')
        # read-only merge-tree: detects conflicts, never modifies or merges the branch.
        rc, _, _ = ctx.sh(['/usr/bin/git', '-C', job['worktree'], 'merge-tree', '--write-tree',
                           '--no-messages', head, 'origin/main'], env=tool_env())
        if rc == 1:
            return _register(ctx, job, launch, 'block', 'conflict with origin/main; controller rework required', None, None)
        if rc != 0:
            raise Hold('origin/main conflict check unknown')
        progress.update(paths=paths, message=message, status_sha256=ka.sha_bytes(status.encode()),
                        diff_sha256=diff_identity(job, paths),
                        packet_sha256=launch['packet_sha256'], parent=launch['head'])
        ka.write_json(Path(ctx.run) / 'jobs' / job['job_id'] / 'state.json', job)
    paths = progress['paths']
    folder = Path(job['job_scratch'])
    message_file = folder / 'codex-commit-message.txt'
    ka.write_atomic(message_file, message.encode())
    inputs = dict(paths=paths, parent=launch['head'], packet_sha256=launch['packet_sha256'],
                  status_sha256=progress['status_sha256'], diff_sha256=progress['diff_sha256'], message=message)

    def stage_observer(record):
        if diff_identity(job, paths) != progress['diff_sha256']:
            return 'unknown', dict(reason='checked diff bytes changed during unobserved stage')
        if git(ctx, job, 'rev-parse', 'HEAD').strip() != launch['head']:
            # stage is already recorded before commit; an unrecorded stage cannot imply a later commit.
            return 'unknown', dict(reason='HEAD changed during unobserved stage')
        staged = sorted(p for p in git(ctx, job, 'diff', '--cached', '--name-only', '-z').split('\0') if p)
        if staged == paths:
            rc, _, _ = ctx.sh(['/usr/bin/git', '-C', job['worktree'], 'diff', '--exit-code',
                               '--no-ext-diff', '--', *paths], env=tool_env())
            if rc != 0:
                return 'unknown', dict(reason='staged contents differ from the measured working copy')
            tree = git(ctx, job, 'write-tree').strip()
            if HEX.fullmatch(tree):
                return 'done', dict(tree=tree, paths=paths)
        if not staged:
            return 'not_done', dict(reason='index empty')
        return 'unknown', dict(reason='index differs from packet-checked paths')

    def stage_effect():
        fence(ctx, job, launch)
        if git(ctx, job, 'rev-parse', 'HEAD').strip() != launch['head']:
            raise Refusal('HEAD changed before stage')
        status = git(ctx, job, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
        if (ka.sha_bytes(status.encode()) != progress['status_sha256']
                or diff_identity(job, paths) != progress['diff_sha256']):
            raise Refusal('diff changed before staging')
        git(ctx, job, 'add', '-A', '--', *paths)
        seen, data = stage_observer(None)
        return ('done' if seen == 'done' else 'unknown'), data

    staged = _action(ctx, job, 'stage', inputs, stage_effect, stage_observer)
    tree = staged['tree']
    commit_inputs = dict(inputs, tree=tree)

    def commit_observer(record):
        candidate = git(ctx, job, 'rev-parse', 'HEAD').strip()
        if candidate == launch['head']:
            return 'not_done', dict(reason='launch HEAD unchanged')
        shape = git(ctx, job, 'show', '-s', '--format=%T%n%P', candidate).splitlines()
        msg = git(ctx, job, 'show', '-s', '--format=%B', candidate)
        if shape != [tree, launch['head']] or msg.rstrip() != message.rstrip():
            return 'unknown', dict(reason='commit tree/parent/message mismatch')
        if git(ctx, job, 'status', '--porcelain=v1', '-z', '--untracked-files=all'):
            return 'unknown', dict(reason='working copy changed after commit')
        return 'done', dict(head=candidate, tree=tree, parent=launch['head'])

    def commit_effect():
        fence(ctx, job, launch)
        if git(ctx, job, 'rev-parse', 'HEAD').strip() != launch['head']:
            raise Refusal('HEAD changed before commit')
        if (git(ctx, job, 'write-tree').strip() != tree
                or diff_identity(job, paths) != progress['diff_sha256']):
            raise Refusal('staged tree or checked diff bytes changed before commit')
        git(ctx, job, 'commit', '--cleanup=verbatim', '-F', str(message_file))
        seen, data = commit_observer(None)
        return ('done' if seen == 'done' else 'unknown'), data

    committed = _action(ctx, job, 'commit', commit_inputs, commit_effect, commit_observer)
    head = committed['head']
    seen, _ = commit_observer(None)
    if seen != 'done' or git(ctx, job, 'rev-parse', 'HEAD').strip() != head:
        raise Refusal('committed HEAD/diff drifted after the observed commit')
    fence(ctx, job, launch)
    rc, _, _ = ctx.sh(['/usr/bin/git', '-C', job['worktree'], 'merge-tree', '--write-tree',
                       '--no-messages', head, 'origin/main'], env=tool_env())
    if rc == 1:
        return _register(ctx, job, launch, 'block', 'conflict with origin/main; controller rework required', None, None)
    if rc != 0:
        raise Hold('origin/main conflict check for the resulting commit is unknown')
    prs = _prs(ctx, job)
    if prs and prs[0]['headRefOid'] not in (launch['head'], head):
        raise Refusal('PR head changed before push')

    def push_observer(record):
        remote = remote_head(ctx, job)
        if remote == head:
            return 'done', dict(head=head)
        if remote == launch['remote_head']:
            return 'not_done', dict(reason='origin still holds the launch observation')
        return 'unknown', dict(reason='origin moved to another head')

    def push_effect():
        fence(ctx, job, launch)
        if remote_head(ctx, job) != launch['remote_head']:
            raise Refusal('origin changed before controller push')
        if git(ctx, job, 'rev-parse', 'HEAD').strip() != head:
            raise Refusal('HEAD changed before controller push')
        git(ctx, job, 'push', 'origin', 'refs/heads/%s:refs/heads/%s' % (job['branch'], job['branch']))
        seen, data = push_observer(None)
        return ('done' if seen == 'done' else 'unknown'), data

    _action(ctx, job, 'push', dict(head=head, previous=launch['remote_head']), push_effect, push_observer)
    if remote_head(ctx, job) != head:
        raise Refusal('origin differs from the controller commit')
    body = folder / 'codex-pr-body.md'
    ka.write_atomic(body, ('%s: %s\n\n%s\n\nTests: %s\n' %
                          (job['item'], job['kind'], result['notes'], json.dumps(result['tests']))).encode())

    def pr_observer(record):
        rows = _prs(ctx, job)
        if not rows:
            return 'not_done', dict(reason='no open PR')
        pr = rows[0]
        if pr['headRefOid'] != head:
            return 'unknown', dict(reason='PR head mismatch')
        return 'done', dict(pr=pr['number'], head=head)

    def pr_effect():
        fence(ctx, job, launch)
        if remote_head(ctx, job) != head or git(ctx, job, 'rev-parse', 'HEAD').strip() != head:
            raise Refusal('HEAD/origin moved before PR creation')
        seen, data = pr_observer(None)
        if seen == 'done':
            return 'done', data
        if seen != 'not_done':
            return 'unknown', data
        rc, _, err = ctx.sh(['/opt/homebrew/bin/gh', 'pr', 'create', '--head', job['branch'], '--base', 'main',
                             '--title', job['item'] + ': Codex ' + job['kind'], '--body-file', str(body)],
                            cwd=job['worktree'], env=tool_env())
        if rc is not None and rc != 0:
            return 'failed', dict(reason=ka.flat(err, 400))
        seen, data = pr_observer(None)
        return ('done' if seen == 'done' else 'unknown'), data

    pr = _action(ctx, job, 'pr', dict(head=head, body_sha256=digest(body)), pr_effect, pr_observer)['pr']
    seen, actual = pr_observer(None)
    if seen != 'done' or actual['pr'] != pr:
        raise Refusal('PR identity changed before registration')
    return _register(ctx, job, launch, 'review', 'PR #%d @ %s' % (pr, head), head, pr)
