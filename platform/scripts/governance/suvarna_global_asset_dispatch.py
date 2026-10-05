#!/usr/bin/env python3
"""suvarna_global_asset_dispatch.py -- forced single GLOBAL-asset dispatch (the first piece of the "global request" path).

WHY THIS EXISTS
  suvarna_level_wave.py is CHART-scoped: it builds per_chart assets only and refuses a global one (NON_PER_CHART_SCOPE). An L0
  asset such as bg_phaladeepika_latta (registry scope 'global') must nevertheless be rebuilt ONCE with NIRMANA_FORCE_EXECUTE=1 so
  that its build record carries a duration (Earn.build_record). This tool is the minimal HONEST way to do that: it states the
  impact on every dependent before anything is written, takes a semantic fingerprint of the asset's table before and after, and
  dispatches exactly one forced run, once. It IMPORTS suvarna_level_wave's pure functions and gates; it copies none of them
  and edits neither suvarna_level_wave.py nor the FROZEN orchestrator.

HOW THE RUN IS RECORDED (SS accepted)
  ONE build_runs row: scope='asset_set', action='rebuild', state 'planned', plan = [the asset], chart_id = the ANCHOR chart
  (a real chart, named by --anchor-chart, used ONLY as the run's required chart_id; it is never a synthetic id). The
  plan_manifest is byte-identical in shape to dispatch_frozen_rebuild.build_manifest / suvarna_level_wave.build_level_manifest
  for a one-asset plan (the runner verifies it; this tool adds no key). The globality is declared in `triggered_by`:
      global-asset-dispatch:anchor_chart=<uuid>;impact_sha256=<first 16 hex of the impact statement sha256>
  The runner itself keeps the asset's throughput row global (chart_id NULL): runner.py `eff_chart_id = None if
  asset_scopes.get(asset_id) == 'global' else chart_id`.

WHAT IT COSTS THE ANCHOR CHART
  While the run is planned/running it holds the anchor chart's per-chart ACTIVE_RUN lock: no other build of the anchor chart can
  start (the plan prints this, with the expected duration). The tool refuses to plan or commit while ANY run of the anchor chart
  is planned / running / paused (ANCHOR_CHART_BUSY).

OPERATOR COMMANDS  (DATABASE_URL in the environment; the tool never reads a credential file and never calls gcloud in plan mode)
  1. PLAN (default; INSERT build_runs + build_run_assets, then ROLLBACK; writes the receipt with committed=false):
       python3 platform/scripts/governance/suvarna_global_asset_dispatch.py \\
           --assets bg_phaladeepika_latta --anchor-chart 482012f1-710e-4a25-994a-93821f5871aa \\
           --deployed-sha <commit whose writer inventory = the deployed image's> --deployed-job-sha <live job image sha> \\
           --receipt /path/outside/the/repo/latta_global_dispatch_receipt.json
     Read the impact statement, the pre fingerprint, the force-support result and the anchor-chart cost, then copy the
     CONFIRM TOKEN (`GLOBAL1ASSET_<12 hex>_FORCE_GLOBAL_REBUILD`).
  2. COMMIT (one forced dispatch, then it waits and verifies; the verification is mandatory, there is no flag):
       python3 platform/scripts/governance/suvarna_global_asset_dispatch.py <the same arguments> \\
           --job-sha-file /path/to/the/operators/job-sha-file --commit --confirm <token>
     Exit 0 only when the forced run completed, the force took effect (disposition 'build', NOT skip_no_delta), the asset's global
     throughput row carries a duration (last_built_at == the run's ended_at) and the post fingerprint equals the pre fingerprint.
  3. Interrupted or timed-out wait (the run exists, nothing is re-dispatched): verify the run later with
       python3 platform/scripts/governance/suvarna_global_asset_dispatch.py --assets <asset> --anchor-chart <uuid> \\
           --receipt <the same receipt path> --verify-run <run_id>

EXPECTED-CHANGE MODE (opt-in; without --expected-change the tool is exactly what it was: a rebuild passes only if the content is UNCHANGED)
  A rebuild that is MEANT to change rows (an L0 fix) has no unchanged-content path. The operator declares the change up front in a small
  JSON file and names it with `--expected-change FILE`:
      {"asset": "<the one asset>", "expected_post_row_count": <total rows of the asset's declared fingerprint unit after the rebuild>,
       "expected_post_fingerprint": "<64 hex composite, optional: from the rehearsal cluster>", "why": "<reason>",
       "decision": "<decision id>" and/or "evidence": "<pointer>"}
  The PLAN prints the impact statement (every dependent, every chart) and a CHANGING REBUILD block naming every row a changed output
  will stale or force to rebuild, and REQUIRES `--accept-changed-output` plus every `--accept-lit-dependent <asset>@<chart|global>`. The
  confirm token binds the sha256 of the file's bytes and the acceptance. The COMMIT records pre/post fingerprints and row counts in the
  receipt (`expected_change`) and the verification PASSES only if the post state equals the declaration: the row count, the declared
  post fingerprint when given, and (when none is given) a post fingerprint that DIFFERS from the pre one (a declared change that did not
  happen is a mismatch). A mismatch is exit 11 with an honest receipt; the build cannot be undone. skip_no_delta stays exit 8.

REFUSAL CODES (exit 4, JSON `refusals`; fail closed; nothing inserted)
  NOT_EXACTLY_ONE_ASSET, NOT_GLOBAL_SCOPE (use the level wave), REGISTRY_ROW_INVALID, ANCHOR_CHART_INVALID (non-uuid / the dead
  phantom 362f9f17-... / not in the charts table), ANCHOR_CHART_BUSY, CONFLICTING_ACTIVE_RUN, ALREADY_DISPATCHED (a prior run of
  this tool exists for the asset: never a second dispatch unless --allow-redispatch <run_id> names it), LIT_DEPENDENT
  (overridable ONLY with --accept-lit-dependent <asset>@<chart|global>, one per lit row), ACCEPT_LIT_DEPENDENT_UNMATCHED,
  DURATION_COLUMN_ABSENT (asset_throughput.duration_seconds, migration 1200, is not in the database), IMAGE_DOES_NOT_RECORD_DURATION
  (the deployed image's asset_runner has no duration write), ASSET_NOT_DECLARED, FINGERPRINT_COVERAGE_PARTIAL, FINGERPRINT_NOT_DETERMINISTIC, FINGERPRINT_TABLE_EMPTY, FINGERPRINT_EQUALS_EMPTY,
  FINGERPRINT_UNREADABLE, DECLARATIONS_INVALID, EXPECTED_CHANGE_INVALID (file unreadable / malformed / another asset / a placeholder reason /
  declares no change), CHANGED_OUTPUT_NOT_ACCEPTED, RECEIPT_EXPECTED_CHANGE_MISMATCH, IMPACT_CHANGED, CONFIRM_TOKEN_MISMATCH, RECEIPT_PATH_INVALID, and every gate of the
  wave (IMAGE_SKEW, CODE_DIGEST_UNAVAILABLE, FORCE_NOT_SUPPORTED_BY_IMAGE, JOB_SHA_MISMATCH, JOB_SHA_CHANGED, DEPENDENCY_NOT_READY,
  REGISTRY_ROW_CHANGED, FAMILY_*, FORCE_FAMILY_ASSET, DEPLOYED_JOB_SHA_REQUIRED, ...).

EXIT CODES  0 ok | 1 DATABASE_URL missing | 2 bad input | 3 dispatch failed after the run was committed (terminalised or warned) |
  4 a gate refused (the receipt path is validated, clobber guard included, and probe-written BEFORE the INSERT) |
  6 unexpected / COMMIT outcome unknown / run committed but the receipt could not be written (event
  `run_committed_receipt_not_written`: the planned run is terminalised, nothing is dispatched, the run id goes to stderr) | 7 interrupted | 8 FORCE_DID_NOT_TAKE_EFFECT (skip_no_delta: a second
  dispatch is FORBIDDEN) | 9 FINGERPRINT_CHANGED_ON_FORCED_REBUILD (the build cannot be undone) | 10 the run did not end complete /
  could not be verified / carries no duration | 11 EXPECTATION_MISMATCH (expected-change mode: the post state differs from the declaration;
  the build cannot be undone).

Exec runs it; the tests use fakes only. Nothing here is run against production by the author.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fingerprint_declarations as fd  # noqa: E402
import suvarna_level_wave as slw  # noqa: E402

SCHEMA = "suvarna.global_asset_dispatch/1"
RECEIPT_SCHEMA = "suvarna-global-dispatch-receipt/v1"
IMPACT_SCHEMA = "suvarna-global-dispatch-impact/v1"
TOKEN_SCHEMA = "suvarna-global-dispatch-token/v1"

TRIGGERED_BY_PREFIX = "global-asset-dispatch:"
# build_runs.triggered_by is TEXT NOT NULL (no length limit; 00_ARCHITECTURE/briefs/nirmana/engine/measurements/A1_before_*.json
# lists "triggered_by text NOT NULL"). Nothing parses it: the only consumers compare it for EXACT equality with a fixed test
# trigger (platform/src/lib/nirmana-elevation/definitions.ts `triggered_by = ANY(testTriggers)`, snapshot.ts and definitions.ts
# `<> 'nirmana-f0-machinery-canary'`; dispatch_nirmana_campaign_wave.py keys its "one run per triggered_by" on its own strings).
# A value that starts with this prefix and carries an `=`/`;` payload equals none of them. The bound below is this tool's own.
TRIGGERED_BY_MAX_CHARS = 200
_TRIGGERED_BY_RE = re.compile(
    r"global-asset-dispatch:anchor_chart=[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12};impact_sha256=[0-9a-f]{16}")

CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"      # CLAUDE.md section B; informational (flagged in the receipt)
PHANTOM_CHART_PREFIX = "362f9f17-"                                 # the dead phantom: never an anchor
LIT_STATES = ("lit", "service_ok", "mature")                       # a row of a dependent that a changed output would stale / rebuild
RUNNER_STALES_STATES = ("lit", "service_ok")                       # staleness.py: UPDATE ... WHERE chart_id = <run chart> AND state IN these
ACTIVE_STATES_SQL = "('planned','running','paused')"
_HEX64 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_ASSET_RE = re.compile(r"[a-z][a-z0-9_]*")

EXIT_OK = 0
EXIT_NO_DATABASE_URL = slw.EXIT_NO_DATABASE_URL
EXIT_BAD_INPUT = slw.EXIT_BAD_INPUT
EXIT_DISPATCH_FAILED = slw.EXIT_DISPATCH_FAILED
REFUSAL_EXIT_CODE = slw.REFUSAL_EXIT_CODE
EXIT_UNEXPECTED = slw.EXIT_UNEXPECTED
EXIT_INTERRUPTED = slw.EXIT_INTERRUPTED
EXIT_FORCE_NOT_EFFECTIVE = 8
EXIT_FINGERPRINT_CHANGED = 9
EXIT_VERIFY_FAILED = 10
EXIT_EXPECTATION_MISMATCH = 11
EXPECTED_CHANGE_KEYS = ("asset", "expected_post_row_count", "expected_post_fingerprint", "why", "decision", "evidence")
EXPECTED_CHANGE_MAX_BYTES = 65536
EXPECTATION_CODES = ("EXPECTED_ROW_COUNT_MISMATCH", "EXPECTED_FINGERPRINT_MISMATCH", "EXPECTED_CHANGE_NOT_OBSERVED")
_PLACEHOLDER_WORDS = frozenset({"tbd", "todo", "tba", "fixme", "xxx", "placeholder", "unknown", "none", "null", "na", "n/a", "nil", "pending", "lorem", "ipsum"})
_CREDENTIAL_NAME = re.compile(r"(^\.env)|credential|secret|passw|token|\.pem$|\.key$|id_rsa|\.p12$", re.I)

# ───────────────────────── SQL (read-only except the two INSERTs) ─────────────────────────

# The exact recursive statement of asset_runner.compute_downstream_closure (a test pins it by whitespace-collapsed substring).
DOWNSTREAM_SQL = """
WITH RECURSIVE downstream AS (
    SELECT asset_id FROM asset_registry
    WHERE %s = ANY(depends_on)
    UNION
    SELECT ar.asset_id FROM asset_registry ar
    INNER JOIN downstream d ON d.asset_id = ANY(ar.depends_on)
)
SELECT asset_id FROM downstream WHERE asset_id != %s
"""

SHARED_TARGET_SQL = """
SELECT peer.asset_id
  FROM asset_registry me
  JOIN asset_registry peer ON peer.target_table = me.target_table AND peer.asset_id <> me.asset_id
 WHERE me.asset_id = %s AND me.target_table IS NOT NULL
 ORDER BY peer.asset_id
"""

IMPACT_REGISTRY_SQL = """
SELECT ar.asset_id, ar.layer, ar.scope, ar.asset_kind, ar.is_active, ar.has_writer, ar.target_table
  FROM asset_registry ar
 WHERE ar.asset_id = ANY(%s)
 ORDER BY ar.asset_id
"""

IMPACT_THROUGHPUT_SQL = """
SELECT at.asset_id, at.chart_id::text AS chart_id, at.state, at.last_built_at, f.freshness_state
  FROM asset_throughput at
  LEFT JOIN LATERAL (
        SELECT freshness_state FROM asset_freshness af
         WHERE af.asset_id = at.asset_id AND af.chart_id IS NOT DISTINCT FROM at.chart_id
         ORDER BY af.observed_at DESC LIMIT 1) f ON true
 WHERE at.asset_id = ANY(%s)
 ORDER BY at.asset_id, at.chart_id NULLS FIRST
"""

# The exact probe asset_runner._duration_columns_present runs (migration 1200 adds the column).
DURATION_COLUMN_SQL = """SELECT 1 FROM information_schema.columns
               WHERE table_schema = 'public' AND table_name = 'asset_throughput'
                 AND column_name = 'duration_seconds'"""

CHART_EXISTS_SQL = "SELECT id::text AS id FROM charts WHERE id = %s"

ANCHOR_ACTIVE_SQL = """SELECT id, chart_id, state FROM build_runs
                        WHERE chart_id=%s AND state IN ('planned','running','paused')"""

CONFLICT_RUNS_SQL = """
SELECT br.id, br.chart_id::text AS chart_id, br.state, bra.asset_id
  FROM build_runs br JOIN build_run_assets bra ON bra.run_id = br.id
 WHERE br.state IN ('planned','running','paused') AND bra.asset_id = ANY(%s)
 ORDER BY br.id, bra.asset_id
"""

PRIOR_DISPATCH_SQL = """
SELECT br.id, br.state, br.plan_manifest_digest, br.triggered_by
  FROM build_runs br JOIN build_run_assets bra ON bra.run_id = br.id
 WHERE left(br.triggered_by, %s) = %s AND bra.asset_id = %s
 ORDER BY br.created_at, br.id
"""

RUN_ROW_SQL = "SELECT id::text AS id, chart_id::text AS chart_id, state, triggered_by, plan_manifest_digest FROM build_runs WHERE id = %s"

RUN_ASSET_SQL = "SELECT state, disposition, started_at, ended_at, error FROM build_run_assets WHERE run_id = %s AND asset_id = %s"

GLOBAL_RECORD_SQL = "SELECT state, last_built_at, duration_seconds FROM asset_throughput WHERE asset_id = %s AND chart_id IS NULL"

CHART_BOUND_RECORD_SQL = "SELECT chart_id::text AS chart_id, state FROM asset_throughput WHERE asset_id = %s AND chart_id IS NOT NULL"

# The two INSERTs have the wave's exact text (suvarna_level_wave.insert_run); a test pins the whitespace-collapsed equality.
INSERT_RUN_SQL = """
            INSERT INTO build_runs
              (id, chart_id, scope, scope_target, action, state, plan,
               plan_manifest, plan_manifest_digest, triggered_by)
            VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb,
                    %s::jsonb, %s, %s)
            """
INSERT_RUN_ASSET_SQL = """INSERT INTO build_run_assets (run_id, asset_id, position, state)
                   VALUES (%s, %s, %s, 'queued')"""


# ───────────────────────── small helpers ─────────────────────────

def canonical_json(value: object) -> str:
    return slw.canonical_json(value)


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _iso(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return (v if v.tzinfo else v.replace(tzinfo=timezone.utc)).astimezone(timezone.utc).isoformat(timespec="microseconds")
    return str(v)


def _utc_iso(now: Callable[[], datetime]) -> str:
    return now().astimezone(timezone.utc).isoformat(timespec="seconds")


def _norm_sql(sql: str) -> str:
    return " ".join(sql.split())


def _refuse(code: str, detail: str, **extra: Any) -> slw.LevelWaveRefusal:
    return slw.LevelWaveRefusal([{"code": code, "detail": detail, **extra}])


def _emit(out, event: str, **fields) -> None:
    out.write(json.dumps({"schema": SCHEMA, "event": event, **fields}, sort_keys=True, default=str) + "\n")
    flush = getattr(out, "flush", None)
    if flush is not None:
        flush()


# ───────────────────────── input validation ─────────────────────────

def parse_single_asset(values: Sequence[str]) -> str:
    """`--assets` must name EXACTLY ONE asset. Zero, two or more, an empty entry or a duplicate is NOT_EXACTLY_ONE_ASSET; a
    malformed id or an @file form is bad input (an explicit single id is required: no list files here)."""
    entries: list[str] = []
    for raw in values or ():
        if raw.strip().startswith("@"):
            raise slw.LevelWaveError("--assets @file is not supported here: name the one asset")
        entries += [e.strip() for e in raw.split(",")]
    if len(entries) != 1 or not entries[0]:
        raise _refuse("NOT_EXACTLY_ONE_ASSET", f"a global dispatch builds exactly one asset; --assets named {len(entries)} entr"
                      f"{'y' if len(entries) == 1 else 'ies'} ({entries!r})", entries=entries)
    if not _ASSET_RE.fullmatch(entries[0]):
        raise slw.LevelWaveError(f"--assets: malformed asset id {entries[0]!r}")
    return entries[0]


def validate_anchor_format(anchor: str | None) -> str:
    """A canonical lower-case hyphenated uuid, and never the dead phantom 362f9f17-... (existence in `charts` is checked later)."""
    text = (anchor or "").strip()
    try:
        canonical = str(uuid.UUID(text))
    except (ValueError, AttributeError):
        raise _refuse("ANCHOR_CHART_INVALID", f"--anchor-chart {anchor!r} is not a uuid") from None
    if canonical != text:
        raise _refuse("ANCHOR_CHART_INVALID", f"--anchor-chart must be the canonical lower-case hyphenated uuid ({canonical})")
    if canonical.startswith(PHANTOM_CHART_PREFIX):
        raise _refuse("ANCHOR_CHART_INVALID", "the 362f9f17-... chart id is a dead phantom: never an anchor")
    return canonical


def parse_accept_flags(values: Sequence[str] | None) -> list[str]:
    out: list[str] = []
    for raw in values or ():
        asset, sep, chart = raw.partition("@")
        if not sep or not asset or not chart or "@" in chart or not _ASSET_RE.fullmatch(asset):
            raise slw.LevelWaveError(f"--accept-lit-dependent {raw!r}: the form is <asset>@<chart uuid | global>")
        out.append(f"{asset}@{chart}")
    if len(set(out)) != len(out):
        raise slw.LevelWaveError("--accept-lit-dependent names the same dependent twice")
    return sorted(out)


def parse_redispatch(values: Sequence[str] | None) -> list[str]:
    out = []
    for raw in values or ():
        try:
            out.append(str(uuid.UUID(raw.strip())))
        except ValueError:
            raise slw.LevelWaveError(f"--allow-redispatch {raw!r} is not a run id (uuid)") from None
    return sorted(set(out))


EXPECTED_TEXT_MAX_CHARS = 500


def _declared_text_problem(v: Any, min_chars: int) -> str | None:
    """None when `v` is a real one-line declaration text: a str, trimmed, no control / line-separator character, at least `min_chars`
    characters and two words, no placeholder word (tbd, todo, n/a, none, unknown, pending ...)."""
    import unicodedata  # noqa: PLC0415
    if not isinstance(v, str) or v != v.strip():
        return "is not a trimmed string"
    if any(unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in v):
        return "contains a control or line-separator character (one visible line)"
    words = re.findall(r"[^\W_]+(?:[./'-][^\W_]+)*", v)
    if len(v) > EXPECTED_TEXT_MAX_CHARS:
        return f"is longer than {EXPECTED_TEXT_MAX_CHARS} characters"
    if len(v) < min_chars or len(words) < 2:
        return f"is too short to be a real statement (at least {min_chars} characters and 2 words)"
    if any(w.casefold() in _PLACEHOLDER_WORDS for w in words):
        return "contains a placeholder word (TBD / todo / n/a / none / unknown / pending ...)"
    return None


def load_expected_change(path: str | None, asset: str) -> tuple[dict, str]:
    """The operator's declared change (`--expected-change FILE`): returns (spec, sha256 of the file's BYTES). Refuses (EXPECTED_CHANGE_INVALID)
    a missing / non-regular / oversized / credential-looking / non-.json file, malformed JSON (a duplicate key included), a key outside
    EXPECTED_CHANGE_KEYS, another asset, a non-integer or < 1 expected_post_row_count, a declared post fingerprint that is not 64 lower-case hex,
    a `why` / `decision` / `evidence` that is a placeholder, and a file that carries neither a decision nor an evidence pointer. Reads this one
    file only; never a credential file."""
    def bad(why: str):
        raise _refuse("EXPECTED_CHANGE_INVALID", f"--expected-change {path!r}: {why}")
    if not path:
        bad("no path")
    p = Path(path).expanduser()
    if p.is_symlink():
        bad("is a symbolic link: name the file itself")
    try:
        resolved = p.resolve(strict=True)
    except (OSError, RuntimeError):
        bad("cannot be resolved (missing, or a link loop)")
    for name in (p.name, resolved.name):                 # the resolved name too: a parent-directory link must not hide an env / credential file
        if not name.endswith(".json") or _CREDENTIAL_NAME.search(name):
            bad("must be a .json file that is not named like an environment or credential file")
    try:
        fd_ = os.open(str(resolved), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))   # O_NONBLOCK: a FIFO named x.json must not block the open; S_ISREG refuses it next
    except OSError as exc:
        bad(f"cannot be opened ({type(exc).__name__})")
    try:
        import stat as _stat  # noqa: PLC0415
        if not _stat.S_ISREG(os.fstat(fd_).st_mode):
            bad("is not a regular file")
        chunks, total = [], 0
        while total <= EXPECTED_CHANGE_MAX_BYTES:        # at most MAX+1 bytes are ever read
            chunk = os.read(fd_, EXPECTED_CHANGE_MAX_BYTES + 1 - total)
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        raw = b"".join(chunks)
    except OSError as exc:
        bad(f"cannot be read ({type(exc).__name__})")
    finally:
        os.close(fd_)
    if len(raw) > EXPECTED_CHANGE_MAX_BYTES:
        bad(f"is larger than {EXPECTED_CHANGE_MAX_BYTES} bytes")

    def no_dups(pairs):
        d = {}
        for k, v in pairs:
            if k in d:
                raise ValueError("duplicate key")       # the key itself is never echoed
            d[k] = v
        return d
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=no_dups)
    except json.JSONDecodeError as exc:
        bad(f"is not valid JSON (line {exc.lineno}, column {exc.colno})")
    except (ValueError, RecursionError) as exc:
        bad("is not valid JSON" + (" (a duplicate key)" if str(exc) == "duplicate key" else f" ({type(exc).__name__})"))
    if not isinstance(doc, dict):
        bad("must be a JSON object")
    extra = sorted(set(doc) - set(EXPECTED_CHANGE_KEYS))
    if extra:
        bad(f"unknown key(s) {extra}")
    if doc.get("asset") != asset:
        bad(f"declares asset {doc.get('asset')!r}, this run is for {asset!r}")
    n = doc.get("expected_post_row_count")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        bad("expected_post_row_count must be an integer >= 1 (a rebuild to an empty table is never an expected change)")
    fp = doc.get("expected_post_fingerprint")
    if fp is not None and not (isinstance(fp, str) and _HEX64.fullmatch(fp)):
        bad("expected_post_fingerprint must be null or 64 lower-case hex")
    why = _declared_text_problem(doc.get("why"), 15)
    if why:
        bad(f"why {why}")
    if doc.get("decision") is None and doc.get("evidence") is None:
        bad("needs a `decision` (a decision id) and/or an `evidence` pointer")
    if doc.get("decision") is not None:
        d = doc["decision"]
        m = re.fullmatch(r"([A-Za-z]{1,4})-?([0-9]{1,6})[A-Za-z0-9._-]{0,24}", d) if isinstance(d, str) else None
        if not m or m.group(1).casefold() in _PLACEHOLDER_WORDS or int(m.group(2)) == 0:
            bad("decision must be a decision id such as N-150 (a placeholder, a bare word or a zero number is not one)")
    if doc.get("evidence") is not None:
        ev = _declared_text_problem(doc["evidence"], 10)
        if ev:
            bad(f"evidence {ev}")
    spec = {"asset": asset, "expected_post_row_count": n, "expected_post_fingerprint": fp, "why": doc["why"],
            "decision": doc.get("decision"), "evidence": doc.get("evidence")}
    return spec, hashlib.sha256(raw).hexdigest()


def check_expected_change_vs_pre(spec: Mapping[str, Any], pre: Mapping[str, Any]) -> None:
    """EXPECTED_CHANGE_INVALID when the declared post fingerprint EQUALS the pre fingerprint: that declares no change (use the default,
    unchanged-content mode)."""
    if spec.get("expected_post_fingerprint") is not None and spec["expected_post_fingerprint"] == pre["composite"]:
        raise _refuse("EXPECTED_CHANGE_INVALID", "expected_post_fingerprint equals the PRE fingerprint: that declares no change; omit "
                      "--expected-change for a rebuild that must leave the content alone")


def unit_row_count(fp: Mapping[str, Any]) -> int:
    """The total rows of a fingerprint's tables (the unit's declared tables)."""
    return sum(int(v["rows"]) for v in fp["tables"].values())


def changed_output_lines(impact: Mapping[str, Any], spec: Mapping[str, Any], pre_rows: int | None) -> list[str]:
    """The CHANGING REBUILD block of the plan: the declared change, then every dependent row (every chart) a changed output stales or
    forces to rebuild, marking the rows the runner stales itself (the anchor chart's lit / service_ok rows)."""
    lines = [f"CHANGING REBUILD of {impact['asset']}: declared post rows {spec['expected_post_row_count']} (pre {'not read yet' if pre_rows is None else pre_rows})"
             + (f", declared post fingerprint {spec['expected_post_fingerprint']}" if spec.get("expected_post_fingerprint")
                else ", no post fingerprint declared (the post fingerprint must differ from the pre one)")
             + f"; why: {spec['why']}"]
    n = 0
    for d in impact["dependents"]:
        for t in d["throughput"]:
            if t["lit"]:
                n += 1
                lines.append(f"  - {d['asset_id']}@{t['chart_id'] or 'global'} is {t['state']}: staled / rebuilt by a changed output"
                             + (" (the runner stales this row: the anchor chart's)" if t["runner_stales_if_output_changes"] else
                                " (its next build is not delta-skipped: this asset's last_built_at moves)"))
    if not n:
        lines.append("  (no lit dependent row)")
    return lines


def check_receipt_path(path: str | None, repo: str, in_repo_ok: bool) -> Path:
    if not path:
        raise slw.LevelWaveError("--receipt is required")
    p = Path(path).expanduser()
    if not p.parent.is_dir():
        raise _refuse("RECEIPT_PATH_INVALID", f"the receipt directory {p.parent} does not exist")
    resolved, root = p.resolve(), Path(repo).resolve()
    if not in_repo_ok and (resolved == root or root in resolved.parents):
        raise _refuse("RECEIPT_PATH_INVALID", f"the receipt must not be written inside the repo ({root}) unless --receipt-in-repo "
                      "is given")
    if p.is_dir():
        raise _refuse("RECEIPT_PATH_INVALID", f"{p} is a directory")
    return p


# ───────────────────────── the registry candidate (a global asset) ─────────────────────────

def accept_global_candidate(asset: str, rows: Sequence[Mapping[str, Any]]) -> dict[str, dict]:
    """The wave's own `accept_candidates` decides active / writer / service / duplicate rows; its ONE scope refusal
    (NON_PER_CHART_SCOPE, which is this tool's whole point) is the only one dropped, and replaced by the converse rule here:
    the asset's registry scope must be exactly 'global' (NOT_GLOBAL_SCOPE; a per_chart asset belongs to the level wave)."""
    try:
        by_id = slw.accept_candidates([asset], rows)
    except slw.LevelWaveRefusal as exc:
        rest = [r for r in exc.refusals if r.get("code") != "NON_PER_CHART_SCOPE"]
        if rest:
            raise slw.LevelWaveRefusal(rest) from None
        by_id = {r["asset_id"]: dict(r) for r in rows}
    scope = by_id[asset].get("scope")
    if scope != "global":
        raise _refuse("NOT_GLOBAL_SCOPE", f"{asset} has registry scope {scope!r}: this tool rebuilds GLOBAL assets only; "
                      "use suvarna_level_wave.py for a per_chart asset", asset=asset, scope=scope)
    return by_id


# ───────────────────────── impact statement ─────────────────────────

def build_impact_statement(*, asset: str, anchor_chart: str, target_table: str | None, downstream: Sequence[str],
                           shared_target_peers: Sequence[str], registry: Sequence[Mapping[str, Any]],
                           throughput: Sequence[Mapping[str, Any]], unit_siblings: Sequence[str] = ()) -> dict:
    """Pure: the closed impact statement for one asset. `downstream` = the transitive depends_on closure (the runner's own),
    `shared_target_peers` = other active writers of the same registry target_table. Every dependent is listed with its registry
    scope and EVERY asset_throughput row it has (any chart) with freshness; `lit` is a row a changed output would stale or force a
    rebuild of (LIT_STATES). The statement is deterministic: its sha256 is bound into the confirm token and the receipt."""
    ids = sorted(set(downstream) | set(shared_target_peers) | set(unit_siblings))
    reg = {r["asset_id"]: r for r in registry}
    rows_by_asset: dict[str, list[Mapping[str, Any]]] = {}
    for t in throughput:
        rows_by_asset.setdefault(t["asset_id"], []).append(t)
    dependents, lit_rows = [], []
    for a in ids:
        r = reg.get(a, {})
        relations = [name for name, members in (("shares_target_table", shared_target_peers), ("transitive_depends_on", downstream),
                                              ("sibling_in_fingerprint_unit", unit_siblings))
                     if a in members]
        trows = []
        for t in sorted(rows_by_asset.get(a, []), key=lambda x: (x.get("chart_id") is not None, str(x.get("chart_id") or ""))):
            chart = None if t.get("chart_id") is None else str(t["chart_id"])
            is_lit = t.get("state") in LIT_STATES
            trows.append({
                "chart_id": chart, "state": t.get("state"), "freshness": t.get("freshness_state"),
                "fresh": t.get("freshness_state") == "fresh", "lit": is_lit, "last_built_at": _iso(t.get("last_built_at")),
                "runner_stales_if_output_changes": chart == anchor_chart and t.get("state") in RUNNER_STALES_STATES,
            })
            if is_lit:
                lit_rows.append({"asset": a, "chart": chart if chart is not None else "global"})
        dependents.append({
            "asset_id": a, "relations": relations, "layer": r.get("layer"), "scope": r.get("scope"),
            "asset_kind": r.get("asset_kind"), "is_active": r.get("is_active"), "has_writer": r.get("has_writer"),
            "target_table": r.get("target_table"), "throughput": trows,
            "lit_rows": sum(1 for x in trows if x["lit"]),
        })
    return {
        "schema": IMPACT_SCHEMA, "asset": asset, "anchor_chart": anchor_chart, "asset_target_table": target_table,
        "dependents": dependents,
        "lit_dependent_rows": sorted(lit_rows, key=lambda x: (x["asset"], x["chart"])),
        "summary": {"dependents": len(dependents), "dependents_with_lit_rows": len({x["asset"] for x in lit_rows}),
                    "lit_rows": len(lit_rows)},
        "reading_note": ("a lit row is a throughput row of a dependent (any chart) in state "
                         f"{'/'.join(LIT_STATES)}; the runner marks stale only the rows of the RUN's chart (the anchor) in state "
                         f"{'/'.join(RUNNER_STALES_STATES)} and only when the asset's output actually changed; a rebuild also "
                         "moves the asset's last_built_at, which every dependent's upstream hash reads, so a dependent's next "
                         "build is never delta-skipped"),
    }


def impact_lines(impact: Mapping[str, Any]) -> list[str]:
    s = impact["summary"]
    lines = [f"IMPACT of rebuilding {impact['asset']} (global; anchor chart {impact['anchor_chart']}): "
             f"{s['dependents']} dependent(s), {s['lit_rows']} lit row(s) across {s['dependents_with_lit_rows']} dependent(s)"]
    for d in impact["dependents"]:
        lines.append(f"  - {d['asset_id']} [{d['layer']}/{d['scope']}/{d['asset_kind']}] via {','.join(d['relations'])}: "
                     + ("no asset_throughput row" if not d["throughput"] else "; ".join(
                         f"{t['chart_id'] or 'global'}={t['state']}/{t['freshness'] or 'no receipt'}" for t in d["throughput"])))
    if not impact["dependents"]:
        lines.append("  (no dependent asset)")
    return lines


def read_impact(cur, *, asset: str, anchor_chart: str, target_table: str | None, unit_siblings: Sequence[str] = ()) -> dict:
    """Read-only SELECTs through `cur`: the downstream closure, the shared-target peers, their registry rows and every throughput
    row with its latest freshness. Returns build_impact_statement(...)."""
    cur.execute(DOWNSTREAM_SQL, (asset, asset))
    downstream = sorted({r["asset_id"] for r in cur.fetchall()})
    cur.execute(SHARED_TARGET_SQL, (asset,))
    peers = sorted({r["asset_id"] for r in cur.fetchall()})
    siblings = sorted(set(unit_siblings) - {asset})
    ids = sorted(set(downstream) | set(peers) | set(siblings))
    registry, throughput = [], []
    if ids:
        cur.execute(IMPACT_REGISTRY_SQL, (ids,))
        registry = [dict(r) for r in cur.fetchall()]
        cur.execute(IMPACT_THROUGHPUT_SQL, (ids,))
        throughput = [dict(r) for r in cur.fetchall()]
    return build_impact_statement(asset=asset, anchor_chart=anchor_chart, target_table=target_table, downstream=downstream,
                                  shared_target_peers=peers, registry=registry, throughput=throughput, unit_siblings=siblings)


def read_impact_via(connect, *, asset: str, anchor_chart: str, target_table: str | None, unit_siblings: Sequence[str] = ()) -> dict:
    conn = connect()
    try:
        impact = read_impact(conn.cursor(), asset=asset, anchor_chart=anchor_chart, target_table=target_table, unit_siblings=unit_siblings)
        conn.rollback()
        return impact
    finally:
        conn.close()


def check_lit_dependents(impact: Mapping[str, Any], accepted: Sequence[str]) -> None:
    """LIT_DEPENDENT: every lit row of a dependent must be named by --accept-lit-dependent <asset>@<chart|global>. An accept flag
    that names no lit row is refused too (a stale override is never silently carried)."""
    lit = {f"{x['asset']}@{x['chart']}" for x in impact["lit_dependent_rows"]}
    acc = set(accepted)
    bad = []
    unaccepted = sorted(lit - acc)
    if unaccepted:
        bad.append({"code": "LIT_DEPENDENT", "rows": unaccepted,
                    "detail": f"{len(unaccepted)} dependent row(s) are lit and a changed output would stale or rebuild them: "
                              + ", ".join(unaccepted) + ". Name each with --accept-lit-dependent <asset>@<chart|global> to proceed."})
    unmatched = sorted(acc - lit)
    if unmatched:
        bad.append({"code": "ACCEPT_LIT_DEPENDENT_UNMATCHED", "rows": unmatched,
                    "detail": "--accept-lit-dependent names no lit row of the impact statement: " + ", ".join(unmatched)})
    if bad:
        raise slw.LevelWaveRefusal(bad)


# ───────────────────────── semantic fingerprint (committed declarations) ─────────────────────────

def load_declarations_or_refuse(path: str | Path):
    try:
        return fd.load_declarations(path)
    except fd.DeclarationError as exc:
        raise slw.LevelWaveRefusal([{"code": "DECLARATIONS_INVALID", "detail": f"{path}: " + "; ".join(
            f"{c} {p}: {m}" for c, p, m in exc.problems[:10])}]) from None


WRITERS_REL = "platform/python-sidecar/pipeline/orchestrator/writers"
UNIT_SEP = "+"        # a composed fingerprint unit is the `+`-joined ids of its comparison units (ids are [a-z0-9_], so `+` never occurs in one)


def writer_siblings(repo: str, asset: str) -> list[str]:
    """The OTHER asset ids registered on the SAME writer class as `asset` (stacked `@register('x')` decorators: ONE class, one run, several asset ids; e.g.
    BgMedicalMappingsWriter serves bg_sign_medical, bg_nakshatra_medical and bg_medical_mappings). Read with ast from EVERY `.py` under the checkout's writers directory
    (recursive; `__tests__`, `tests` and `__pycache__` directories are skipped), never imported. ONLY the decorator form `@register('x')` on a class is scanned; the call form `register('x')(Cls)` is not read (no writer in the tree uses it; a future one would be
    invisible here, so keep the decorator form). FAILS CLOSED (WRITER_SCAN_UNAVAILABLE): a missing writers directory; an unparseable file; ANY `register(...)`
    call whose first argument is not a string literal (or a module-level string constant) or that is starred, keyword-only or empty (a `register(asset_id=...)` or
    `register(*ids)` could register the asset and the scan could not see it, whatever the file says); and an asset that NO scanned class registers (a scan that found
    nothing about the asset proves nothing about its run). Two classes in one file (bg_phaladeepika_vedha.py) are two runs: they are NOT siblings.
    LIMIT (documented, not closed here): the tables a writer writes through helper modules are not read from code; they rest on the declarations' `tables_written`
    and the write evidence of each declared table, which are human-curated (the declarations validator checks the evidence lines, not the whole call graph)."""
    root = Path(repo) / WRITERS_REL
    if not root.is_dir():
        raise _refuse("WRITER_SCAN_UNAVAILABLE", f"the writers directory {WRITERS_REL} is not in the checkout: the writer-run siblings of {asset} cannot be established")
    out: set[str] = set()
    found = False
    for f in sorted(root.rglob("*.py")):
        rel = f.relative_to(root)
        if any(part in ("__tests__", "tests", "__pycache__") for part in rel.parts[:-1]):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except (OSError, ValueError, SyntaxError) as exc:
            raise _refuse("WRITER_SCAN_UNAVAILABLE", f"{rel} cannot be parsed ({type(exc).__name__}): the writer-run siblings of {asset} cannot be established") from None
        consts = {n.targets[0].id: n.value.value for n in tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                  and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            ids = []
            for dec in node.decorator_list:
                if not (isinstance(dec, ast.Call) and getattr(dec.func, "id", getattr(dec.func, "attr", None)) == "register"):
                    continue
                a0 = dec.args[0] if dec.args else None
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    ids.append(a0.value)
                elif isinstance(a0, ast.Name) and a0.id in consts:
                    ids.append(consts[a0.id])
                else:
                    raise _refuse("WRITER_SCAN_UNAVAILABLE", f"{rel}: class {node.name} has a register(...) call that is not a literal positional id (empty, keyword, starred or "
                                  f"a non-constant): it may register {asset}, so the writer-run siblings cannot be established")
            if asset in ids:
                found = True
                out |= set(ids)
    if not found:
        raise _refuse("WRITER_SCAN_UNAVAILABLE", f"no writer class under {WRITERS_REL} registers {asset}: the writer run (and its siblings) cannot be established")
    return sorted(out - {asset})


def _declared_entry(decls, asset: str):
    assets = getattr(decls, "assets", None)
    return assets.get(asset) if isinstance(assets, dict) else None


def declared_unit_or_refuse(decls, asset: str, siblings: Sequence[str] = ()) -> str:
    """The fingerprint unit of a forced rebuild of `asset`: the comparison units of EVERY asset whose rows the run writes, joined with `+`.
    The run writes the asset itself and each writer-run sibling (`siblings`, see writer_siblings). For each such asset the units are its own tables (if any) and every
    group it belongs to, so a MIXED member (own tables and a shared table: bg_doshas, bg_yogas, bg_dasha_systems) fingerprints its shared `brahma_ontology` table too, and a
    shared writer (bg_medical_mappings: bg_sign_medical, bg_nakshatra_medical) fingerprints every table the run touches (SS ruling 1). One unit -> that unit's id
    (receipts of plain assets are unchanged); several -> `own+sibling+grp_x`, with a composite over the unit composites. Refused, all reasons together: an asset or sibling
    that is undeclared or has no tables and no group (ASSET_NOT_DECLARED / WRITER_SIBLING_NOT_DECLARED), a partial declaration, a SEEDED group (copied from production,
    never rebuilt), and any unit that is not deterministic: none can show that a forced rebuild left the content alone."""
    units = decls.units()
    members = [asset] + sorted(set(siblings) - {asset})
    comps: list[str] = []
    bad: list[dict] = []
    for m in members:
        entry = _declared_entry(decls, m)
        mine: list[str] = []
        if entry is None:                                                  # a stand-in declarations object (no `assets`): the asset-only reading
            if m in units and units[m]["kind"] == "asset":
                mine.append(m)
        elif entry.get("status") == "declared":
            if entry.get("tables"):
                mine.append(m)
            for g in entry.get("groups") or []:
                mine.append(decls.group_unit(g))
        if not mine or any(u not in units for u in mine):
            un = decls.undeclared_assets().get(m)
            code = "ASSET_NOT_DECLARED" if m == asset else "WRITER_SIBLING_NOT_DECLARED"
            if m == asset:
                detail = f"{m} is not a declared fingerprint unit of its own in {Path(decls.path).name}" + (f" (undeclared: {un['reason_code']})" if un else "")
            else:
                detail = (f"{m} is written by the same writer run as {asset} but is not a declared fingerprint unit in {Path(decls.path).name}"
                          + (f" (undeclared: {un['reason_code']})" if un else "") + ": a table the run writes would never be fingerprinted")
            bad.append({"code": code, "asset": m, "detail": detail})
            continue
        if m in decls.partial_assets():
            bad.append({"code": "FINGERPRINT_COVERAGE_PARTIAL", "asset": m,
                        "detail": f"{m}'s declaration is partial: a fingerprint of part of its output cannot show it unchanged"})
        for u in mine:
            if u not in comps:
                comps.append(u)
    for u in comps:
        if units[u].get("seeded"):
            bad.append({"code": "GROUP_UNIT_SEEDED", "asset": asset, "unit": u,
                        "detail": f"{u} is a SEEDED group (copied from production, never rebuilt: its content is not reproducible): an equal fingerprint is not expected from a rebuild"})
        if decls.reproducibility(u) != ["deterministic"]:
            bad.append({"code": "FINGERPRINT_NOT_DETERMINISTIC", "asset": asset, "unit": u,
                        "detail": f"{u} is declared {decls.reproducibility(u)}: an equal fingerprint is not expected from a rebuild"})
    if bad:
        raise slw.LevelWaveRefusal(bad)
    return UNIT_SEP.join(comps)


def unit_siblings(decls, asset: str, unit: str, writer_sibs: Sequence[str] = ()) -> list[str]:
    """The OTHER assets whose rows are inside the fingerprint unit or written by the same run: the members of every group unit of `unit` and the writer-run siblings.
    A concurrent run of one of them would change the very tables this run is judged on, so they are listed in the impact statement (their lit rows need acceptance)
    and a planned / running / paused run of any of them refuses (CONFLICTING_ACTIVE_RUN). [] for an asset whose unit is its own and which shares no writer run."""
    units = decls.units()
    out = set(writer_sibs)
    for u in unit.split(UNIT_SEP):
        if u != asset:
            out |= set(units.get(u, {}).get("members", []))
    return sorted(out - {asset})


def read_fingerprint(fp_connect, decls, unit: str, *, reader=fd.unit_fingerprints, code: str = "FINGERPRINT_UNREADABLE") -> dict:
    """The unit's fingerprint through the committed declarations, on a READ-ONLY connection with TUPLE rows (E5.5's load_rows
    zips column names with row values). {unit, definition, declarations_sha256, composite, tables: {t: {sha256, rows}}}. A composed unit (`a+b+grp_x`) is read in
    ONE reader call; its composite is the sha256 of the canonical JSON {"units": {unit: composite}} and the result also carries `units` and `table_units`
    (table -> its unit). A table claimed by two of the units is refused (a declaration defect)."""
    parts = unit.split(UNIT_SEP)
    conn = fp_connect()
    try:
        raw = reader(conn, decls, parts)
        conn.rollback()
        if len(parts) == 1:
            composite = raw["fingerprints"][unit]
            tables = {t: {"sha256": v["sha256"], "rows": int(v["rows"])} for t, v in sorted(raw["tables"][unit].items())}
            extra: dict[str, Any] = {}
        else:
            composite = sha256_json({"schema": "suvarna-composed-unit/v1", "units": {u: raw["fingerprints"][u] for u in parts}})
            tables, table_units = {}, {}
            for u in parts:
                for t, v in sorted(raw["tables"][u].items()):
                    if t in tables:
                        raise ValueError(f"table {t} is claimed by two units of {unit}")
                    tables[t] = {"sha256": v["sha256"], "rows": int(v["rows"])}
                    table_units[t] = u
            extra = {"units": parts, "table_units": dict(sorted(table_units.items()))}
    except slw.LevelWaveError:
        raise
    except Exception as exc:  # noqa: BLE001 -- an unreadable table is a refusal / failure, never an empty fingerprint
        raise _refuse(code, f"the fingerprint of {unit} could not be read: {type(exc).__name__}: {exc}") from None
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass
    return {"unit": unit, "definition": raw["definition"], "declarations_sha256": raw["declarations_sha256"],
            "composite": composite, "tables": tables, **extra}


def check_pre_fingerprint(fp: Mapping[str, Any], decls, *, empty_fn=fd.empty_table_fingerprint) -> None:
    bad = []
    for table, v in fp["tables"].items():
        if v["rows"] == 0:
            bad.append({"code": "FINGERPRINT_TABLE_EMPTY", "table": table,
                        "detail": f"{table} holds 0 rows: a fingerprint of nothing proves nothing about a forced rebuild"})
        if v["sha256"] == empty_fn(decls, (fp.get("table_units") or {}).get(table, fp["unit"]), table):
            bad.append({"code": "FINGERPRINT_EQUALS_EMPTY", "table": table,
                        "detail": f"{table}'s fingerprint equals the fingerprint of an empty table"})
    if not _HEX64.fullmatch(str(fp.get("composite", ""))):
        bad.append({"code": "FINGERPRINT_UNREADABLE", "detail": "the composite fingerprint is not a sha256"})
    if bad:
        raise slw.LevelWaveRefusal(bad)


# ───────────────────────── token ─────────────────────────

def build_confirm_token(*, manifest_digest: str, asset: str, anchor_chart: str, image_sha: str, impact_sha256: str,
                        pre_fingerprint: str, accepted_lit: Sequence[str], allow_redispatch: Sequence[str],
                        expected_change_sha256: str | None = None, accepted_changed_output: bool = False) -> str:
    """`GLOBAL1ASSET_<12 hex>_FORCE_GLOBAL_REBUILD`: a hash over the plan manifest digest, the asset, the anchor chart, the deployed
    image sha and the impact statement sha, plus (stricter than the minimum) the pre fingerprint and the two operator overrides, so a
    token authorises exactly the plan, the table content and the overrides it was printed for. Never equal to a level-wave token
    (those end `_FROZEN_REBUILD`)."""
    body = {"schema": TOKEN_SCHEMA, "manifest_digest": manifest_digest, "asset": asset, "anchor_chart": anchor_chart,
            "image_sha": image_sha, "impact_sha256": impact_sha256, "pre_fingerprint": pre_fingerprint,
            "accepted_lit_dependents": sorted(accepted_lit), "allow_redispatch": sorted(allow_redispatch)}
    if expected_change_sha256 is not None:      # expected-change mode ONLY: the file's bytes and the acceptance are bound; absent, the token is exactly what it always was
        body["expected_change_sha256"] = expected_change_sha256
        body["accepted_changed_output"] = bool(accepted_changed_output)
    h = sha256_json(body)
    return f"GLOBAL1ASSET_{h[:12].upper()}_FORCE_GLOBAL_REBUILD"


def build_triggered_by(anchor_chart: str, impact_sha256: str) -> str:
    value = f"{TRIGGERED_BY_PREFIX}anchor_chart={anchor_chart};impact_sha256={impact_sha256[:16]}"
    if len(value) > TRIGGERED_BY_MAX_CHARS or not _TRIGGERED_BY_RE.fullmatch(value):
        raise slw.LevelWaveError(f"triggered_by {value!r} is malformed or too long")
    return value


# ───────────────────────── receipt (closed schema) ─────────────────────────

RECEIPT_KEYS = ("schema", "run_id", "asset", "anchor_chart", "anchor_is_canonical", "manifest_digest", "image_sha", "inventory_sha",
                "impact", "impact_sha256", "pre_fingerprint", "post_fingerprint", "confirm_token", "committed", "triggered_by",
                "accepted_lit_dependents", "execution_name", "verification", "planned_at", "committed_at", "verified_at", "expected_change")


def new_receipt(**fields: Any) -> dict:
    base: dict[str, Any] = {k: None for k in RECEIPT_KEYS}      # expected_change stays None outside expected-change mode
    base.update({"schema": RECEIPT_SCHEMA, "committed": False, "accepted_lit_dependents": []})
    unknown = set(fields) - set(RECEIPT_KEYS)
    if unknown:
        raise slw.LevelWaveError(f"receipt fields outside the closed schema: {sorted(unknown)}")
    base.update(fields)
    if base["expected_change"] is None:
        del base["expected_change"]                     # without --expected-change the receipt has exactly the keys it always had
    return base


def validate_receipt(doc: Any) -> None:
    """The closed `suvarna-global-dispatch-receipt/v1` schema: exactly RECEIPT_KEYS, typed, and self-consistent (the impact sha256
    is the sha256 of the impact statement it carries; a committed receipt names its run). Raises LevelWaveError."""
    def bad(why: str):
        raise slw.LevelWaveError(f"receipt invalid: {why}")
    if not isinstance(doc, dict):
        bad("not an object")
    required = set(RECEIPT_KEYS) - {"expected_change"}      # a receipt written before expected-change mode has no such key: it stays valid
    if not (required <= set(doc) <= set(RECEIPT_KEYS)):
        bad(f"keys differ (extra {sorted(set(doc) - set(RECEIPT_KEYS))}, missing {sorted(required - set(doc))})")
    ec = doc.get("expected_change")
    if ec is not None:
        if not (isinstance(ec, dict) and set(ec) == {"file_sha256", "spec", "accepted_changed_output", "pre_row_count", "post_row_count", "outcome"}):
            bad("expected_change must carry exactly file_sha256, spec, accepted_changed_output, pre_row_count, post_row_count, outcome")
        if not (isinstance(ec["file_sha256"], str) and _HEX64.fullmatch(ec["file_sha256"]) and isinstance(ec["spec"], dict)
                and ec["accepted_changed_output"] is True and isinstance(ec["pre_row_count"], int) and not isinstance(ec["pre_row_count"], bool)
                and (ec["post_row_count"] is None or (isinstance(ec["post_row_count"], int) and not isinstance(ec["post_row_count"], bool)))
                and ec["outcome"] in (None, "MET", "MISMATCH")):
            bad("expected_change is malformed")
        if ec["spec"].get("asset") != doc.get("asset"):
            bad("expected_change names another asset")
    if doc["schema"] != RECEIPT_SCHEMA:
        bad("schema")
    if not isinstance(doc["committed"], bool):
        bad("committed must be a bool")
    if doc["run_id"] is not None:
        try:
            uuid.UUID(str(doc["run_id"]))
        except ValueError:
            bad("run_id is not a uuid")
    if doc["committed"] and doc["run_id"] is None:
        bad("a committed receipt names its run_id")
    if doc["committed"] and not doc["committed_at"]:
        bad("a committed receipt carries committed_at")
    if not isinstance(doc["asset"], str) or not _ASSET_RE.fullmatch(doc["asset"]):
        bad("asset")
    if validate_anchor_format(doc["anchor_chart"]) != doc["anchor_chart"]:
        bad("anchor_chart")
    if not isinstance(doc["manifest_digest"], str) or not _HEX64.fullmatch(doc["manifest_digest"]):
        bad("manifest_digest is not a sha256")
    if not isinstance(doc["image_sha"], str) or not _HEX40.fullmatch(doc["image_sha"]):
        bad("image_sha is not a 40-hex commit")
    if not isinstance(doc["impact"], dict) or doc["impact"].get("schema") != IMPACT_SCHEMA:
        bad("impact")
    if doc["impact_sha256"] != sha256_json(doc["impact"]):
        bad("impact_sha256 is not the sha256 of the impact statement")
    pre = doc["pre_fingerprint"]
    if not isinstance(pre, dict) or not _HEX64.fullmatch(str(pre.get("composite", ""))):
        bad("pre_fingerprint")
    if doc["post_fingerprint"] is not None and not _HEX64.fullmatch(str((doc["post_fingerprint"] or {}).get("composite", ""))):
        bad("post_fingerprint")
    if not isinstance(doc["confirm_token"], str) or not re.fullmatch(r"GLOBAL1ASSET_[0-9A-F]{12}_FORCE_GLOBAL_REBUILD", doc["confirm_token"]):
        bad("confirm_token")
    if doc["triggered_by"] is not None and not _TRIGGERED_BY_RE.fullmatch(str(doc["triggered_by"])):
        bad("triggered_by")
    if not isinstance(doc["accepted_lit_dependents"], list):
        bad("accepted_lit_dependents")
    for k in ("planned_at", "committed_at", "verified_at"):
        if doc[k] is not None:
            try:
                datetime.fromisoformat(str(doc[k]))
            except ValueError:
                bad(f"{k} is not an ISO timestamp")
    if doc["planned_at"] is None:
        bad("planned_at is required")


def check_receipt_overwrite(path: Path, doc: Mapping[str, Any]) -> None:
    """The clobber guard. A file already at `path` is replaced only when it is a valid receipt of the SAME asset and anchor that is
    not committed yet, or the very run this call continues (same run_id). Raises RECEIPT_PATH_INVALID otherwise."""
    if not path.exists():
        return
    try:
        old = json.loads(path.read_text(encoding="utf-8"))
        validate_receipt(old)
    except (OSError, ValueError, slw.LevelWaveError):
        raise _refuse("RECEIPT_PATH_INVALID", f"{path} exists and is not a receipt of this tool: not overwritten") from None
    same = old["asset"] == doc["asset"] and old["anchor_chart"] == doc["anchor_chart"]
    continues = (not old["committed"]) or (old["run_id"] is not None and old["run_id"] == doc["run_id"])
    if not (same and continues):
        raise _refuse("RECEIPT_PATH_INVALID", f"{path} already holds a committed receipt of another run: not overwritten")


def write_receipt(path: Path, doc: dict) -> None:
    """Validate, apply the clobber guard (check_receipt_overwrite), then write atomically with mode 0600."""
    validate_receipt(doc)
    check_receipt_overwrite(path, doc)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    try:
        fd_ = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd_, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(doc, sort_keys=True, indent=1, default=str) + "\n")
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class ReceiptNotWritten(Exception):
    """The run COMMITTED but the receipt could not be written. Not a refusal: a run exists. The planned run has been terminalised
    (or the failure to do so is in `warning`); nothing was dispatched."""

    def __init__(self, run_id: str, chart_id: str, cause: BaseException, terminalise: Mapping[str, Any]):
        self.run_id, self.chart_id, self.cause = run_id, chart_id, cause
        self.terminalised = terminalise.get("terminalised")
        self.warning = terminalise.get("warning")
        self.detail = (f"run committed, receipt not written: run {run_id} (chart {chart_id}); the receipt write failed "
                       f"({type(cause).__name__}: {cause}). "
                       + ("The planned run was terminalised (state 'failed') and NOTHING was dispatched; fix the receipt path and "
                          "plan again (--allow-redispatch <run_id> names this run)." if self.terminalised is True else
                          (self.warning or f"The run's state is UNKNOWN: verify it with --verify-run {run_id}.")))
        super().__init__(self.detail)


def terminalise_planned_run(connect, run_id: str, chart_id: str, error: str, frozen) -> dict:
    """Take a committed-but-undispatched run out of the active set with the frozen dispatcher's own statement (UPDATE build_runs ...
    WHERE id = <run> AND state = 'planned'). Returns {terminalised: True | False | None, rows, warning}: it never raises (the run id
    must be reported), and it READS the affected-row count, because 0 rows means the run was NOT planned any more (it has already
    started or ended, for example a gcloud timeout whose execution started late): that is reported as such, never as 'terminalised'."""
    conn = None
    try:
        conn = connect()
        cur = conn.cursor()
        frozen.terminalize_dispatch_failure(cur, run_id=run_id, error=error)
        rows = getattr(cur, "rowcount", None)
        conn.commit()
    except Exception as exc:  # noqa: BLE001
        return {"terminalised": False, "rows": None,
                "warning": (f"run {run_id} is COMMITTED in state 'planned' and BLOCKS chart {chart_id} until it is terminalised "
                            f"(terminalise failed: {type(exc).__name__}: {exc}). Terminalise it by hand: UPDATE build_runs SET "
                            f"state='failed', ended_at=NOW(), last_error='{error[:80]}' WHERE id='{run_id}' AND state='planned'; "
                            "and abort its queued build_run_assets rows.")}
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:  # noqa: BLE001
                pass
    if rows == 0:
        return {"terminalised": False, "rows": 0,
                "warning": (f"run {run_id} was NOT terminalised: the UPDATE affected 0 rows, so the run was no longer 'planned' (it "
                            f"has already started or ended). It may be running or complete. Do NOT dispatch again; verify it with "
                            f"--verify-run {run_id}.")}
    if rows is None or rows < 0:
        return {"terminalised": None, "rows": rows,
                "warning": (f"the terminalise statement for run {run_id} ran but reported no affected-row count: the run's state is "
                            f"UNKNOWN (it may still be 'planned' and block chart {chart_id}, or already running or complete). Verify "
                            f"it with --verify-run {run_id}; do NOT dispatch again.")}
    return {"terminalised": True, "rows": rows, "warning": None}


# ───────────────────────── the transaction (plan: rolled back; commit: committed) ─────────────────────────

def check_anchor_exists(connect, anchor: str) -> None:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(CHART_EXISTS_SQL, (anchor,))
        found = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()
    if not found:
        raise _refuse("ANCHOR_CHART_INVALID", f"--anchor-chart {anchor} is not in the charts table")


def check_duration_column(connect) -> None:
    """DURATION_COLUMN_ABSENT: the point of the forced rebuild is a duration-bearing build record. Without
    asset_throughput.duration_seconds (migration 1200) asset_runner._duration_columns_present is False and the completion write
    silently omits the duration: the rebuild would complete and the verification could only fail afterwards. Refuse before any INSERT."""
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(DURATION_COLUMN_SQL)
        found = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()
    if not found:
        raise _refuse("DURATION_COLUMN_ABSENT", "asset_throughput.duration_seconds does not exist in this database (migration "
                      "1200_asset_throughput_duration_seconds.sql has not applied): a rebuild here could never carry a duration")


# What the deployed image's asset_runner must contain for the completion write to record a duration (migration 1200's column): the
# UPDATE of asset_throughput that sets the ADJACENT pair `duration_seconds = %s, rows_per_second = %s` (asset_runner.py ~1353). The
# pattern is matched against each of the code's string constants (duration_write_strings), never against comments or docstrings: the
# comment above `_DURATION_COLUMNS_PRESENT` also says `duration_seconds = %s` and must not satisfy the check.
DURATION_MARKERS = ((slw.ASSET_RUNNER_REL,
                     re.compile(r"UPDATE\s+asset_throughput\b.*?duration_seconds\s*=\s*%s\s*,\s*rows_per_second\s*=\s*%s", re.DOTALL),
                     "writes asset_throughput.duration_seconds on completion"),)


def duration_write_strings(source: str) -> list[str]:
    """The texts a duration-write marker is matched against, ONE AT A TIME (a pattern may not span two strings): the source's string
    constants (the SQL), with comments gone (the parser never produces them) and every bare-expression string statement (a docstring or a stray string) left out. Raises ValueError when
    the source does not parse: an unreadable runner is never a pass. A string assigned to a variable is not distinguished from SQL
    passed to execute(): this is a marker, not a proof, and it only ever narrows what passes."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"not parseable Python ({type(exc).__name__}: {exc})") from None
    skip = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str)}
    return [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip]


def check_image_records_duration(repo: str, job_sha: str, *, git=slw._git) -> None:
    """IMAGE_DOES_NOT_RECORD_DURATION: the deployed image (read at the pinned job sha) must carry the duration write in CODE (not in a
    comment or docstring); an unreadable or unparseable file refuses too. Companion of slw.check_image_supports_force, which covers
    the force markers only."""
    problems = []
    for rel, pat, what in DURATION_MARKERS:
        cp = git(str(repo), ["show", f"{job_sha}:{rel}"])
        if cp.returncode != 0:
            problems.append(f"{rel} at {job_sha} is unreadable ({(cp.stderr or '').strip()[:120]})")
            continue
        try:
            texts = duration_write_strings(cp.stdout or "")
        except ValueError as exc:
            problems.append(f"{rel} at {job_sha} could not be checked: {exc}")
            continue
        if not any(pat.search(t) for t in texts):
            problems.append(f"{rel} at {job_sha} does not contain code that {what}")
    if problems:
        raise _refuse("IMAGE_DOES_NOT_RECORD_DURATION", "the deployed job image would complete the rebuild without recording a "
                      "duration: " + "; ".join(problems), job_sha=job_sha, problems=problems)


def insert_global_run(connect, *, asset: str, anchor_chart: str, manifest: Mapping[str, Any], digest: str,
                      row_digests: Mapping[str, str], external: Mapping[str, Sequence[str]], impact_reader: Callable[[Any], dict],
                      impact_sha256: str, triggered_by: str, allow_redispatch: Sequence[str], token: str, confirm: str | None,
                      commit: bool, on_commit=None, meta: Mapping[str, Any] | None = None) -> dict:
    """ONE transaction: the anchor chart's advisory lock (the wave's own key, so a wave and this tool serialise on the chart) and a
    per-asset lock; ANCHOR_CHART_BUSY; CONFLICTING_ACTIVE_RUN (any chart); ALREADY_DISPATCHED; the registry row re-read and compared
    (REGISTRY_ROW_CHANGED); the asset's upstream lit+fresh (DEPENDENCY_NOT_READY); the impact statement re-read and compared
    (IMPACT_CHANGED); INSERT build_runs + build_run_assets; then ROLLBACK (plan) or COMMIT (only with the exact token).
    `on_commit(receipt)` runs the instant the COMMIT succeeds."""
    plan = [a for wave in manifest["waves"] for a in wave]
    if plan != [asset]:
        raise slw.LevelWaveError(f"the manifest plan {plan} is not exactly [{asset!r}]")
    if commit and confirm != token:
        raise _refuse("CONFIRM_TOKEN_MISMATCH", f"--commit requires --confirm {token}", expected=token)
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (slw._lock_key(anchor_chart),))
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (f"suvarna-global-asset-dispatch:{asset}",))
        cur.execute(ANCHOR_ACTIVE_SQL, (anchor_chart,))
        active = cur.fetchall()
        if active:
            raise _refuse("ANCHOR_CHART_BUSY", f"the anchor chart has planned/running/paused build run(s): {active}",
                          runs=[dict(r) for r in active])
        cur.execute(PRIOR_DISPATCH_SQL, (len(TRIGGERED_BY_PREFIX), TRIGGERED_BY_PREFIX, asset))
        prior = [dict(r) for r in cur.fetchall()]
        unnamed = [str(r["id"]) for r in prior if str(r["id"]) not in set(allow_redispatch)]
        if unnamed:
            raise _refuse("ALREADY_DISPATCHED", f"a prior run of this tool exists for {asset}: {unnamed}. A second dispatch is "
                          "forbidden unless every prior run is named with --allow-redispatch <run_id>", runs=unnamed)
        cur.execute(slw.CANDIDATES_SQL, ([asset],))
        slw.check_registry_unchanged(row_digests, [dict(r) for r in cur.fetchall()])
        slw.check_external_dependencies(cur, anchor_chart, external)
        impact_now = impact_reader(cur)
        if sha256_json(impact_now) != impact_sha256:
            raise _refuse("IMPACT_CHANGED", "the impact statement changed since the plan was made: plan again",
                          planned=impact_sha256, now=sha256_json(impact_now))
        ids = sorted({asset} | {d["asset_id"] for d in impact_now["dependents"]})
        cur.execute(CONFLICT_RUNS_SQL, (ids,))
        conflicts = [dict(r) for r in cur.fetchall()]
        if conflicts:
            raise _refuse("CONFLICTING_ACTIVE_RUN", f"a planned/running/paused run (any chart) touches the asset or a dependent: "
                          f"{conflicts}", runs=conflicts)
        run_id = str(uuid.uuid4())
        cur.execute(INSERT_RUN_SQL, (run_id, anchor_chart, manifest["scope_target"], json.dumps(plan), json.dumps(manifest), digest,
                                     triggered_by))
        for position, asset_id in enumerate(plan):
            cur.execute(INSERT_RUN_ASSET_SQL, (run_id, asset_id, position))
        receipt = {"run_id": run_id, "chart_id": anchor_chart, "assets": plan, "manifest_digest": digest, "committed": bool(commit),
                   "confirm_token": token, "triggered_by": triggered_by}
        receipt.update(dict(meta or {}))
        if commit:
            try:
                conn.commit()
            except Exception as exc:  # noqa: BLE001 -- the outcome of a failed COMMIT is unknown, never "not committed"
                raise slw.CommitOutcomeUnknown(run_id, anchor_chart, exc) from exc
            if on_commit is not None:
                on_commit(receipt)
        else:
            conn.rollback()
        return receipt
    except slw.CommitOutcomeUnknown:
        raise
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


# ───────────────────────── verification after the run ─────────────────────────

def read_run_facts(connect, run_id: str, asset: str) -> dict:
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(RUN_ASSET_SQL, (run_id, asset))
        run_asset = cur.fetchone()
        cur.execute(GLOBAL_RECORD_SQL, (asset,))
        record = [dict(r) for r in cur.fetchall()]
        cur.execute(CHART_BOUND_RECORD_SQL, (asset,))
        chart_bound = [dict(r) for r in cur.fetchall()]
        conn.rollback()
    finally:
        conn.close()
    return {"run_asset": dict(run_asset) if run_asset else None, "global_records": record, "chart_bound_records": chart_bound}


def verify_forced_run(connect, fp_connect, decls, *, run_id: str, asset: str, unit: str, pre: Mapping[str, Any], wait: Mapping[str, Any],
                      reader=fd.unit_fingerprints, expected: Mapping[str, Any] | None = None) -> dict:
    """The mandatory verification. Returns {verdict: 'PASS' | [codes], exit_code, ...}: the run state, whether the force took effect
    (the wave's own `forced_effect`: disposition 'build', never skip_no_delta), a duration-bearing build record (the asset's GLOBAL
    throughput row: duration_seconds set, last_built_at == the run asset's ended_at, as asset_census._attempt_timing links them),
    and the post fingerprint against the pre fingerprint."""
    codes: list[str] = []
    notes: list[str] = []
    eff = slw.forced_effect(connect, run_id)
    state = eff["run_state"]
    out: dict[str, Any] = {"run_state": state, "wait": wait.get("state"), "forced_effect": eff, "post_fingerprint": None,
                           "fingerprint_equal": None, "duration_seconds": None, "disposition": (eff.get("dispositions") or {}).get(asset)}
    if state != "completed":
        codes.append("RUN_NOT_COMPLETED")
        notes.append(f"the run is {state!r} (wait ended {wait.get('state')!r}); last_error={wait.get('last_error')!r}")
    if eff["forced_effective"] is False:
        codes.append("FORCE_DID_NOT_TAKE_EFFECT")
        notes.append("the run ended skip_no_delta: NIRMANA_FORCE_EXECUTE did not take effect. A SECOND DISPATCH IS FORBIDDEN "
                     "(a skip refreshes last_built_at and un-links any duration); read the job image and env, do not re-dispatch")
    elif eff["forced_effective"] is None and state == "completed":
        codes.append("FORCED_EFFECT_UNVERIFIED")
        notes.append(eff.get("note") or "the disposition could not be read")
    facts = None
    if state == "completed" and eff["forced_effective"] is True:
        try:
            facts = read_run_facts(connect, run_id, asset)
        except Exception as exc:  # noqa: BLE001 -- e.g. UndefinedColumn: the run COMPLETED, its build record could not be read
            codes.append("BUILD_RECORD_UNREADABLE")
            notes.append(f"the run COMPLETED but its build record could not be read ({type(exc).__name__}: {exc}); a missing "
                         "asset_throughput.duration_seconds column (migration 1200) is the known cause. Do not dispatch again.")
    if facts is not None:
        ra = facts["run_asset"]
        rec = facts["global_records"]
        out["chart_bound_throughput_rows"] = facts["chart_bound_records"]
        if facts["chart_bound_records"]:
            notes.append("a chart-bound asset_throughput row exists for this global asset (unexpected): " + json.dumps(
                facts["chart_bound_records"], default=str))
        ended = slw._as_dt(ra.get("ended_at")) if ra else None
        problems = []
        if not ra or ra.get("state") != "complete" or ra.get("disposition") != "build" or ended is None:
            problems.append("the build_run_assets row is not complete/build with an ended_at")
        if len(rec) != 1:
            problems.append(f"{len(rec)} global throughput rows (exactly one expected)")
        else:
            r = rec[0]
            out["duration_seconds"] = None if r.get("duration_seconds") is None else float(r["duration_seconds"])
            built = slw._as_dt(r.get("last_built_at"))
            if r.get("duration_seconds") is None:
                problems.append("the global throughput row has no duration_seconds")
            if built is None or ended is None or built != ended:
                problems.append("last_built_at is not the run asset's ended_at (a later write touched it)")
            if r.get("state") not in slw.GOOD_THROUGHPUT_STATES:
                problems.append(f"the global throughput state is {r.get('state')!r}")
        if problems:
            codes.append("BUILD_RECORD_NOT_DURATION_BEARING")
            notes += problems
    if state == "completed":
        try:
            post = read_fingerprint(fp_connect, decls, unit, reader=reader)
            out["post_fingerprint"] = post
            out["fingerprint_equal"] = post["composite"] == pre["composite"] and post["tables"] == pre["tables"]
            if expected is not None:
                # EXPECTED-CHANGE MODE: the post state must equal the DECLARATION (never "anything goes"); the unchanged-content rule is replaced, not relaxed
                pre_rows, post_rows = unit_row_count(pre), unit_row_count(post)
                out["row_counts"] = {"pre": pre_rows, "post": post_rows, "expected_post": expected["expected_post_row_count"]}
                if post_rows != expected["expected_post_row_count"]:
                    codes.append("EXPECTED_ROW_COUNT_MISMATCH")
                    notes.append(f"post rows {post_rows} != declared {expected['expected_post_row_count']} (pre {pre_rows}). The build cannot be undone by this tool.")
                if expected.get("expected_post_fingerprint") is not None:
                    if post["composite"] != expected["expected_post_fingerprint"]:
                        codes.append("EXPECTED_FINGERPRINT_MISMATCH")
                        notes.append(f"post fingerprint {post['composite']} != declared {expected['expected_post_fingerprint']} (pre {pre['composite']}).")
                elif post["composite"] == pre["composite"]:
                    codes.append("EXPECTED_CHANGE_NOT_OBSERVED")
                    notes.append(f"a change was declared but the post fingerprint equals the pre one ({pre['composite']}): the rebuild did not change the content.")
                out["expectation"] = "MET" if not any(c in EXPECTATION_CODES for c in codes) else "MISMATCH"
            elif not out["fingerprint_equal"]:
                codes.append("FINGERPRINT_CHANGED_ON_FORCED_REBUILD")
                notes.append(f"pre {pre['composite']} != post {post['composite']}: a forced rebuild of UNCHANGED content must leave "
                             "the fingerprint equal. The build cannot be undone by this tool.")
        except slw.LevelWaveRefusal as exc:
            codes.append("POST_FINGERPRINT_UNREADABLE")
            notes.append("; ".join(r["detail"] for r in exc.refusals))
    out.setdefault("expectation", None)      # None: not in expected-change mode, or the post state was never read (nothing established)
    out["codes"] = codes
    out["notes"] = notes
    out["verdict"] = "PASS" if not codes else codes
    if "FORCE_DID_NOT_TAKE_EFFECT" in codes:                       # precedence: 8 (never re-dispatch) > 11 (post differs from the declaration) > 9 (content changed) > 10
        out["exit_code"] = EXIT_FORCE_NOT_EFFECTIVE
    elif any(c in EXPECTATION_CODES for c in codes):
        out["exit_code"] = EXIT_EXPECTATION_MISMATCH
    elif "FINGERPRINT_CHANGED_ON_FORCED_REBUILD" in codes:
        out["exit_code"] = EXIT_FINGERPRINT_CHANGED
    elif codes:
        out["exit_code"] = EXIT_VERIFY_FAILED
    else:
        out["exit_code"] = EXIT_OK
    return out


# ───────────────────────── command line ─────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="suvarna_global_asset_dispatch.py", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Forced single GLOBAL-asset dispatch with an impact statement and pre/post semantic fingerprints. Reads "
                    "DATABASE_URL from the environment; never reads credential files; plan mode never touches gcloud.",
        epilog="Default is a PLAN: INSERT build_runs + build_run_assets, ROLLBACK, print the confirm token. --commit --confirm "
               "<token> dispatches ONE forced run (NIRMANA_FORCE_EXECUTE=1 is implied and always on), waits for it and verifies "
               "it (mandatory). A second dispatch for the same asset is refused unless --allow-redispatch names every prior run. "
               "Exit: 0 ok | 1 DATABASE_URL missing | 2 bad input | 3 dispatch failed | 4 refused | 6 unexpected | 7 interrupted | "
               "8 force did not take effect (no second dispatch) | 9 fingerprint changed on a forced rebuild | 10 not verified | "
               "11 post state differs from the --expected-change declaration.")
    p.add_argument("--assets", action="append", required=True, metavar="ASSET", help="exactly one global asset id")
    p.add_argument("--anchor-chart", required=True, help="a REAL chart id, used only as the run's declared anchor (never synthetic)")
    p.add_argument("--receipt", required=True, help="path of the impact receipt JSON (outside the repo unless --receipt-in-repo)")
    p.add_argument("--receipt-in-repo", action="store_true", help="allow the receipt path inside --repo")
    p.add_argument("--deployed-sha", help="commit whose committed writer digests are the deployed image's")
    p.add_argument("--deployed-job-sha", help="the LIVE deployed job image sha (DEPLOY_SHA / image, never a deploy run's head_sha)")
    p.add_argument("--job-sha-file", help="a file the operator's gate keeps holding exactly the live job sha (40 hex); required with "
                   "--commit; re-read right before the INSERT and right before the dispatch (JOB_SHA_CHANGED)")
    p.add_argument("--repo", default=str(slw.REPO_ROOT))
    p.add_argument("--family-ref", default="origin/main")
    p.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    p.add_argument("--commit", action="store_true", help="commit the run and dispatch it; omission is a rollback-only plan")
    p.add_argument("--confirm", help="required with --commit: the token the plan printed")
    p.add_argument("--accept-lit-dependent", action="append", metavar="ASSET@CHART", help="accept ONE lit dependent row (repeat per row)")
    p.add_argument("--allow-redispatch", action="append", metavar="RUN_ID", help="name a prior run of this tool for the asset")
    p.add_argument("--expected-change", metavar="FILE", help="EXPECTED-CHANGE MODE: a JSON file declaring the change this rebuild is meant to make "
                   "({asset, expected_post_row_count, expected_post_fingerprint?, why, decision/evidence}); requires --accept-changed-output; "
                   "without it a rebuild passes only if the content is UNCHANGED")
    p.add_argument("--accept-changed-output", action="store_true", help="accept that the declared change stales / rebuilds every lit dependent "
                   "the plan lists (only with --expected-change)")
    p.add_argument("--verify-run", metavar="RUN_ID", help="verify an existing run of this tool (no insert, no dispatch)")
    p.add_argument("--poll-seconds", type=float, default=15.0)
    p.add_argument("--run-timeout-seconds", type=float, default=4 * 3600.0)
    p.add_argument("--project", default="madhav-astrology")
    p.add_argument("--region", default="asia-south1")
    p.add_argument("--job", default="brahma-build-pipeline-job")
    return p


def _psycopg_connect_factory(database_url: str):
    return slw._psycopg_connect_factory(database_url)


def _psycopg_fp_connect_factory(database_url: str):
    """READ ONLY, tuple rows (E5.5's load_rows zips column names with row values)."""
    def connect():
        import psycopg  # noqa: PLC0415
        conn = psycopg.connect(database_url)
        conn.autocommit = False
        conn.read_only = True
        return conn
    return connect


def run_cli(args: argparse.Namespace, *, connect, fp_connect=None, git=slw._git, out=None, sleep=time.sleep, monotonic=time.monotonic,
            dispatch=None, now: Callable[[], datetime] | None = None, decls=None, fp_reader=fd.unit_fingerprints,
            empty_fn=fd.empty_table_fingerprint) -> int:
    """The whole command with every outside contact injected (database, git, gcloud, the clock, the fingerprint reader)."""
    out = out or sys.stdout
    now = now or (lambda: datetime.now(timezone.utc))
    committed: list[dict] = []
    try:
        return _run_cli(args, connect=connect, fp_connect=fp_connect or connect, git=git, out=out, sleep=sleep, monotonic=monotonic,
                        dispatch=dispatch, now=now, decls=decls, fp_reader=fp_reader, empty_fn=empty_fn, committed=committed)
    except slw.LevelWaveRefusal as exc:
        _emit(out, "refused", refused=True, refusals=exc.refusals, committed_runs=committed)
        return REFUSAL_EXIT_CODE
    except slw.LevelWaveError as exc:
        _emit(out, "error", error=str(exc), committed_runs=committed)
        return EXIT_BAD_INPUT
    except slw.CommitOutcomeUnknown as exc:
        _emit(out, "error", unexpected=True, commit_outcome_unknown=True, run_id=exc.run_id, chart_id=exc.chart_id, error=exc.detail,
              committed_runs=committed, warning=exc.detail)
        return EXIT_UNEXPECTED
    except ReceiptNotWritten as exc:
        _emit(out, "run_committed_receipt_not_written", unexpected=True, run_id=exc.run_id, chart_id=exc.chart_id, error=exc.detail,
              terminalised=exc.terminalised, committed_runs=committed, warning=exc.detail)
        print(f"RUN {exc.run_id} COMMITTED, RECEIPT NOT WRITTEN: " + (
            "the planned run was terminalised and nothing was dispatched." if exc.terminalised is True else (exc.warning or exc.detail)),
              file=sys.stderr)
        return EXIT_UNEXPECTED
    except KeyboardInterrupt:
        _emit(out, "interrupted", interrupted=True, committed_runs=committed,
              warning=slw._interrupt_warning(committed, args.anchor_chart) + " Verify it later with --verify-run <run_id>; never dispatch again.")
        return EXIT_INTERRUPTED
    except Exception as exc:  # noqa: BLE001 -- never an escaped traceback: the operator must see the run id
        _emit(out, "error", unexpected=True, error=f"{type(exc).__name__}: {exc}", committed_runs=committed,
              warning=("the run listed in committed_runs exists and may be planned/running: find it by run_id before anything else"
                       if committed else "no run was committed"))
        return EXIT_UNEXPECTED


def _run_cli(args, *, connect, fp_connect, git, out, sleep, monotonic, dispatch, now, decls, fp_reader, empty_fn, committed) -> int:
    emit = lambda event, **f: _emit(out, event, **f)  # noqa: E731
    asset = parse_single_asset(args.assets)
    anchor = validate_anchor_format(args.anchor_chart)
    receipt_path = check_receipt_path(args.receipt, args.repo, args.receipt_in_repo)
    accepted = parse_accept_flags(args.accept_lit_dependent)
    allow_redispatch = parse_redispatch(args.allow_redispatch)
    commit = bool(args.commit)
    if args.accept_changed_output and not args.expected_change:
        raise slw.LevelWaveError("--accept-changed-output is only for --expected-change mode: a rebuild without a declared change must leave the content unchanged")
    expected, expected_sha = load_expected_change(args.expected_change, asset) if args.expected_change else (None, None)
    if args.verify_run:
        if commit:
            raise slw.LevelWaveError("--verify-run is read-only: do not combine it with --commit")
        return _verify_run_mode(args, asset=asset, anchor=anchor, receipt_path=receipt_path, connect=connect, fp_connect=fp_connect,
                                out=out, sleep=sleep, monotonic=monotonic, now=now, decls=decls, fp_reader=fp_reader,
                                expected=expected, expected_sha=expected_sha)
    if commit and not args.job_sha_file:
        raise slw.LevelWaveError("--commit requires --job-sha-file (re-read right before the INSERT and before the dispatch)")
    if not args.deployed_job_sha or not args.deployed_sha:
        raise _refuse("DEPLOYED_JOB_SHA_REQUIRED", "--deployed-sha and --deployed-job-sha (the live deployed job image sha read at "
                      "launch) are both required")

    # 1. the wave's own gates: family, force (one asset, never a family asset), job sha binding, force support, image skew
    ref_status = slw.family_ref_status(args.repo, args.family_ref, git=git)
    family = slw.load_family_info(args.repo, args.family_ref, git=git)
    refusals = (slw.family_ref_refusals(ref_status, committing=commit) + slw.family_refusals([asset], family, committing=commit)
                + slw.force_refusals([asset], family))
    if refusals:
        raise slw.LevelWaveRefusal(refusals)
    binding = slw.check_job_sha_binding(args.repo, inventory_sha=args.deployed_sha, job_sha=args.deployed_job_sha, git=git)
    pinned = binding["deployed_job_sha"]
    slw.check_image_supports_force(args.repo, pinned, git=git)
    check_image_records_duration(args.repo, pinned, git=git)
    force_support = {"checked_at_job_sha": pinned, "result": "supported", "markers": [m[2] for m in slw._FORCE_MARKERS],
                     "duration_write_markers": [m[2] for m in DURATION_MARKERS]}
    if args.job_sha_file:
        slw.recheck_job_sha(args.repo, pinned_job_sha=pinned, job_sha_file=args.job_sha_file, git=git)
    local = slw.load_local_writer_digests(args.repo)
    deployed = slw.load_deployed_writer_digests(repo=args.repo, sha=args.deployed_sha, git=git)
    slw.check_image_skew([asset], local, deployed)
    frozen = slw._load_frozen_dispatcher() if commit else None       # before any insert: a load failure strands nothing

    # 2. registry candidate (a GLOBAL asset), anchor chart, upstream liveness, the one-asset manifest
    check_anchor_exists(connect, anchor)
    check_duration_column(connect)
    rows = slw.read_rows(connect, [asset])
    by_id = accept_global_candidate(asset, rows)
    row = by_id[asset]
    external = slw.external_dependencies([asset], {asset: row.get("depends_on") or []})
    slw.precheck_external(connect, anchor, external)
    manifest, digest = slw.build_level_manifest(chart_id=anchor, plan_waves=[[asset]], rows=by_id, writer_digests=local)
    row_digests = {asset: slw.registry_row_digest(row)}

    # 3. the fingerprint unit (declared) and the impact statement (every dependent, every chart, and every sibling writer of the unit) with the lit-dependent gate
    decls = decls or load_declarations_or_refuse(args.declarations)
    wsibs = writer_siblings(args.repo, asset)
    unit = declared_unit_or_refuse(decls, asset, wsibs)
    siblings = unit_siblings(decls, asset, unit, wsibs)
    impact_of = lambda cur: read_impact(cur, asset=asset, anchor_chart=anchor, target_table=row.get("target_table"), unit_siblings=siblings)  # noqa: E731
    impact = read_impact_via(connect, asset=asset, anchor_chart=anchor, target_table=row.get("target_table"), unit_siblings=siblings)
    impact_sha = sha256_json(impact)
    check_lit_dependents(impact, accepted)
    if expected is not None and not args.accept_changed_output:
        raise slw.LevelWaveRefusal([{"code": "CHANGED_OUTPUT_NOT_ACCEPTED", "impact_lines": impact_lines(impact),
                                     "changed_output_lines": changed_output_lines(impact, expected, None),
                                     "detail": "--expected-change declares a CHANGING rebuild: every dependent row listed above will be staled or "
                                               "rebuilt by the changed output. Read the impact, then pass --accept-changed-output (and every "
                                               "--accept-lit-dependent) to proceed."}])

    # 4. the pre fingerprint through the committed declarations
    pre = read_fingerprint(fp_connect, decls, unit, reader=fp_reader)
    check_pre_fingerprint(pre, decls, empty_fn=empty_fn)
    if expected is not None:
        check_expected_change_vs_pre(expected, pre)

    token = build_confirm_token(manifest_digest=digest, asset=asset, anchor_chart=anchor, image_sha=pinned, impact_sha256=impact_sha,
                                pre_fingerprint=pre["composite"], accepted_lit=accepted, allow_redispatch=allow_redispatch,
                                expected_change_sha256=expected_sha, accepted_changed_output=bool(args.accept_changed_output))
    triggered_by = build_triggered_by(anchor, impact_sha)
    estimate = slw.estimate_runtime([[asset]], by_id)
    planned_at = _utc_iso(now)
    cost = {"blocks_anchor_chart": True, "anchor_chart": anchor,
            "message": ("while this run is active it blocks other builds of the anchor chart (the per-chart ACTIVE_RUN lock); "
                        f"expected duration: {_expected(estimate)}"),
            "runtime_estimate": estimate}
    meta = {"deployed_job_sha": pinned, "inventory_sha": binding["inventory_sha"], "force_execute": True}
    receipt = new_receipt(asset=asset, anchor_chart=anchor, anchor_is_canonical=anchor == CANONICAL_CHART_ID, manifest_digest=digest,
                          image_sha=pinned, inventory_sha=binding["inventory_sha"], impact=impact, impact_sha256=impact_sha,
                          pre_fingerprint=pre, confirm_token=token, triggered_by=triggered_by, accepted_lit_dependents=accepted,
                          planned_at=planned_at,
                          expected_change=(None if expected is None else {
                              "file_sha256": expected_sha, "spec": expected, "accepted_changed_output": True,
                              "pre_row_count": unit_row_count(pre), "post_row_count": None, "outcome": None}))
    summary = {"asset": asset, "anchor_chart": anchor, "anchor_is_canonical": anchor == CANONICAL_CHART_ID, "scope": row["scope"],
               "manifest_digest": digest, "plan": [asset], "triggered_by": triggered_by, "deployed_job_sha": pinned,
               "force_support_check": force_support, "force_execute": True, "impact_sha256": impact_sha,
               "impact_summary": impact["summary"], "impact_lines": impact_lines(impact), "pre_fingerprint": pre,
               "declarations_sha256": decls.sha256, "anchor_chart_cost": cost, "confirm_token": token, "committed": False,
               "receipt_path": str(receipt_path), "committed_runs": committed}
    if unit != asset:                      # a group member, a mixed member or a shared writer: the fingerprint is of every table the run touches
        gus = decls.units()
        summary["fingerprint_unit"] = {"unit": unit, "units": unit.split(UNIT_SEP), "members": sorted({m for u in unit.split(UNIT_SEP) for m in gus[u]["members"]} | set(wsibs) | {asset}),
                                       "tables": [t for u in unit.split(UNIT_SEP) for t in gus[u]["tables"]], "writer_siblings": wsibs,
                                       "note": "the run writes a slice of a shared table and / or tables of sibling assets; the fingerprint covers the WHOLE of every such table, "
                                               "so the rebuild passes only if every row of every one is unchanged"}
    if expected is not None:
        summary["expected_change"] = {"file_sha256": expected_sha, "spec": expected, "pre_row_count": unit_row_count(pre),
                                      "accepted_changed_output": True, "changed_output_lines": changed_output_lines(impact, expected, unit_row_count(pre))}

    if commit and args.confirm != token:
        raise _refuse("CONFIRM_TOKEN_MISMATCH", f"--commit requires --confirm {token}", expected=token)

    # The receipt path is proven BEFORE the INSERT: the clobber guard (an existing committed receipt of another run) is a refusal
    # here, and in commit mode a probe write of the not-yet-committed receipt surfaces a permission / disk problem as a refusal
    # (exit 4) while nothing exists, instead of after a COMMIT.
    check_receipt_overwrite(receipt_path, receipt)
    if commit:
        try:
            write_receipt(receipt_path, receipt)
        except OSError as exc:
            raise _refuse("RECEIPT_PATH_INVALID", f"the receipt {receipt_path} cannot be written ({type(exc).__name__}: {exc}); "
                          "nothing was inserted") from None

    def on_commit(r):
        rec = {"run_id": r["run_id"], "asset": asset, "anchor_chart": anchor, "manifest_digest": digest, **meta}
        committed.append(rec)
        receipt.update(run_id=r["run_id"], committed=True, committed_at=_utc_iso(now))
        try:
            write_receipt(receipt_path, receipt)                  # the run id is on disk before anything else can fail
        except Exception as exc:  # noqa: BLE001 -- the run is COMMITTED: never leave it 'planned' (it would block the anchor chart)
            term = terminalise_planned_run(connect, r["run_id"], anchor, f"run committed, receipt not written: {exc}", frozen)
            raise ReceiptNotWritten(r["run_id"], anchor, exc, term) from exc
        emit("run_committed", **rec)

    run = insert_global_run(connect, asset=asset, anchor_chart=anchor, manifest=manifest, digest=digest, row_digests=row_digests,
                            external=external, impact_reader=impact_of, impact_sha256=impact_sha, triggered_by=triggered_by,
                            allow_redispatch=allow_redispatch, token=token, confirm=args.confirm if commit else None, commit=commit,
                            on_commit=on_commit if commit else None, meta=meta)
    summary["insert"] = run
    if not commit:
        write_receipt(receipt_path, receipt)
        emit("summary", **summary)
        return EXIT_OK

    summary["committed"] = True
    # `run_command` resolves subprocess.run at CALL time (the wave's default binds it at import time), so a test that blocks or
    # fakes subprocess.run can never be bypassed by this default.
    send = dispatch or (lambda run_id: slw.dispatch_run_with_timeout(
        run_id=run_id, project=args.project, region=args.region, job=args.job, force_execute=True,
        run_command=lambda *a, **k: subprocess.run(*a, **k)))
    try:
        slw.recheck_job_sha(args.repo, pinned_job_sha=pinned, job_sha_file=args.job_sha_file, git=git)     # a redeploy since the INSERT
        execution = send(run["run_id"])
    except Exception as exc:  # noqa: BLE001
        term = terminalise_planned_run(connect, run["run_id"], anchor, str(exc), frozen)      # the frozen statement prefixes 'dispatch failed:'
        warn = term["warning"]
        emit("dispatch_failed", run_id=run["run_id"], error=str(exc), warning=warn, terminalised=term["terminalised"], **meta)
        receipt["verification"] = {"verdict": ["DISPATCH_FAILED"], "codes": ["DISPATCH_FAILED"], "notes": [str(exc), warn or "terminalised"]}
        write_receipt(receipt_path, receipt)
        summary.update(dispatch_error=str(exc), terminalise_warning=warn)
        emit("summary", **summary)
        return EXIT_DISPATCH_FAILED
    receipt["execution_name"] = execution
    write_receipt(receipt_path, receipt)
    emit("run_dispatched", run_id=run["run_id"], execution_name=execution, **meta)
    summary["execution_name"] = execution
    return _finish(summary, receipt, receipt_path, connect=connect, fp_connect=fp_connect, decls=decls, unit=unit, pre=pre,
                   run_id=run["run_id"], asset=asset, args=args, out=out, sleep=sleep, monotonic=monotonic, now=now, fp_reader=fp_reader,
                   expected=expected)


def _expected(estimate: Mapping[str, Any]) -> str:
    if estimate.get("measured_seconds") is not None:
        return f"about {estimate['measured_seconds']} s (registry estimate)"
    if estimate.get("parallel_upper_bound_seconds"):
        return f"unmeasured; at most {estimate['parallel_upper_bound_seconds']} s (the writer timeout)"
    return "unmeasured (the registry carries no estimate or timeout)"


def _finish(summary, receipt, receipt_path, *, connect, fp_connect, decls, unit, pre, run_id, asset, args, out, sleep, monotonic, now,
            fp_reader, expected=None) -> int:
    """Wait for the run, verify (mandatory), update the receipt, print the verdict. Returns the exit code."""
    wait = slw.wait_for_terminal_run(connect, run_id, poll_seconds=args.poll_seconds, timeout_seconds=args.run_timeout_seconds,
                                     sleep=sleep, monotonic=monotonic)
    ver = verify_forced_run(connect, fp_connect, decls, run_id=run_id, asset=asset, unit=unit, pre=pre, wait=wait, reader=fp_reader,
                            expected=expected)
    receipt["post_fingerprint"] = ver["post_fingerprint"]
    receipt["verification"] = {k: ver[k] for k in ("verdict", "run_state", "wait", "disposition", "duration_seconds", "fingerprint_equal",
                                                   "codes", "notes")}
    if expected is not None:                              # expected-change mode ONLY: the default receipt keeps its shape
        post = ver["post_fingerprint"]
        receipt["verification"].update(expectation=ver["expectation"], row_counts=ver.get("row_counts"))
        ec = dict(receipt["expected_change"])
        # MET only when the whole verification passed; MISMATCH only when the post state was read and differs from the declaration; otherwise null (not established)
        outcome = "MET" if (ver["expectation"] == "MET" and ver["verdict"] == "PASS") else ("MISMATCH" if ver["expectation"] == "MISMATCH" else None)
        ec.update(post_row_count=None if post is None else unit_row_count(post), outcome=outcome)
        receipt["expected_change"] = ec

    receipt["verified_at"] = _utc_iso(now)
    write_receipt(receipt_path, receipt)
    _emit(out, "forced_effect", **ver["forced_effect"], wait=wait["state"])
    summary.update(verification=receipt["verification"], post_fingerprint=ver["post_fingerprint"], forced_effective=(
        ver["forced_effect"]["forced_effective"]))
    if ver["codes"]:
        summary["warning"] = " | ".join(ver["notes"])
    if "FORCE_DID_NOT_TAKE_EFFECT" in ver["codes"]:
        summary["second_dispatch"] = "FORBIDDEN"
    _emit(out, "summary", **summary)
    return ver["exit_code"]


def _verify_run_mode(args, *, asset, anchor, receipt_path, connect, fp_connect, out, sleep, monotonic, now, decls, fp_reader,
                     expected=None, expected_sha=None) -> int:
    """--verify-run: an interrupted or timed-out wait. Reads the receipt (the pre fingerprint), checks that the run is this tool's
    run of this asset on this anchor with the receipt's manifest digest, waits, verifies. Dispatches and inserts nothing."""
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise slw.LevelWaveError(f"--verify-run needs the receipt of the run: {receipt_path}: {exc}") from None
    validate_receipt(receipt)
    run_id = str(uuid.UUID(args.verify_run))
    if not (receipt["committed"] and receipt["run_id"] == run_id and receipt["asset"] == asset and receipt["anchor_chart"] == anchor):
        raise _refuse("RECEIPT_RUN_MISMATCH", "the receipt is not the committed receipt of this run, asset and anchor chart")
    rec_ec = receipt.get("expected_change")
    if (rec_ec is None) != (expected is None) or (rec_ec is not None and (rec_ec["file_sha256"] != expected_sha or rec_ec["spec"] != expected)):
        # the declaration is the one the token bound: a verify with another file (or none, or one for a receipt that has none) would grade another claim
        if rec_ec is None and expected is not None:
            what = "the receipt carries no expected change (it is a receipt of the unchanged-content mode) but an --expected-change file was given"
        elif rec_ec is not None and expected is None:
            what = "the receipt was committed under an expected-change file but none was given"
        elif rec_ec["file_sha256"] != expected_sha:
            what = "the file sha differs: the --expected-change file is not the one the receipt was committed under"
        else:
            what = "the recorded spec differs from the file's spec (the receipt was altered after the commit)"
        raise _refuse("RECEIPT_EXPECTED_CHANGE_MISMATCH", f"{what}: pass the same --expected-change file the plan used (and none for a receipt of the unchanged-content mode)")
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(RUN_ROW_SQL, (run_id,))
        found = cur.fetchone()
        conn.rollback()
    finally:
        conn.close()
    if (not found or str(found["chart_id"]) != anchor or found["triggered_by"] != receipt["triggered_by"]
            or found["plan_manifest_digest"] != receipt["manifest_digest"]):
        raise _refuse("RECEIPT_RUN_MISMATCH", f"build_runs {run_id} is not this tool's run for the receipt (chart, triggered_by or digest differ)")
    decls = decls or load_declarations_or_refuse(args.declarations)
    unit = declared_unit_or_refuse(decls, asset, writer_siblings(args.repo, asset))
    if unit != (receipt["pre_fingerprint"] or {}).get("unit"):
        raise _refuse("RECEIPT_UNIT_MISMATCH", f"the fingerprint unit of {asset} in this checkout is {unit!r} but the receipt was committed under "
                      f"{(receipt['pre_fingerprint'] or {}).get('unit')!r}: the declarations or the writers changed since the run; the post state cannot be judged against the pre state "
                      "(a drift here would read as a changed fingerprint). Verify from the checkout the run was planned on.")
    summary = {"asset": asset, "anchor_chart": anchor, "run_id": run_id, "mode": "verify-run", "receipt_path": str(receipt_path)}
    return _finish(summary, receipt, receipt_path, connect=connect, fp_connect=fp_connect, decls=decls, unit=unit,
                   pre=receipt["pre_fingerprint"], run_id=run_id, asset=asset, args=args, out=out, sleep=sleep, monotonic=monotonic,
                   now=now, fp_reader=fp_reader, expected=expected)      # the FILE is graded: its bytes matched the receipt's digest and its spec equals the recorded one


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return EXIT_NO_DATABASE_URL

    def _term(signum, frame):  # noqa: ARG001
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, _term)
    return run_cli(args, connect=_psycopg_connect_factory(database_url), fp_connect=_psycopg_fp_connect_factory(database_url))


if __name__ == "__main__":
    raise SystemExit(main())
