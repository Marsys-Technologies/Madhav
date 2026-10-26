#!/usr/bin/env python3
"""flip_detector.py: S-L1 class-flip detector and attribution-hook validator (SS N-64 acceptance tool). READ-ONLY. Tooling only: it never writes to the database.

This is a VERDICT-DECIDING tool (it produces the W7 flip report and validates the lane hooks). Its tests live in
platform/scripts/governance/__tests__/test_flip_detector.py (with mutation proof in test_flip_detector_mutations.py).

  --snapshot <native|abhinandan|kiran|CHART_UUID> [--out FILE.json.gz] [--no-dashas] [--no-daily]
        Capture the current production class-level state of one chart (chart_facts incl. verification tier, chart_divisionals,
        chart_dashas) plus the global panchanga_daily table into one gzip JSON: the pre-rebuild baseline. Prints path + sha256.
  --compare <SNAPSHOT.json.gz> [--against OTHER_SNAPSHOT.json.gz] [--out REPORT.json] [--hooks-dir DIR] [--require-lanes a,b,c]
                               [--no-dashas] [--no-daily] [--allow-not-checked] [--i-know-dashas-are-not-compared]
        Compare the snapshot with production (read-only), or with OTHER_SNAPSHOT (offline, no database), and attribute every
        difference to a lane hook file (all top-level *.json in --hooks-dir).
        Verdict classes (the JSON field "verdict"; never PASS while anything below FAIL / ALERT / NOT_CHECKED exists):
            ALERT        a FORENSIC anchor changed (native chart only); wins over everything
            FAIL         at least one failure class (below) is non-empty
            NOT_CHECKED  nothing failed, but the detector cannot machine-check some declared-or-standing scopes (always the case in
                         production: chart_dashas tier and l1_tajik_varsha_year_lords tier are never compared). Never counted as a pass.
            PASS         nothing failed and nothing is NOT CHECKED (only reachable when the standing NOT CHECKED registry is empty)
        Failure classes: UNDECLARED_CHANGE (no hook declares the changed row/category/column), KIND_MISMATCH (a hook declares the
            category but not this KIND of change), DECLARED_BUT_ABSENT (a non-optional hook entry saw no change at all),
            EXPECTATION_MISMATCH (expected_count violated), DASHA_SHIFT_UNDECLARED (a dasha start shift outside every declared
            range), HOOK_ERROR (invalid hook file or a --require-lanes lane with no hook), EMPTY_READ (a compared table has zero rows in
            either state). Warning class (never fails):
            OPTIONAL_ABSENT (an entry marked "optional": true saw no change).
        Exit codes:
            0  verdict PASS, or verdict NOT_CHECKED with --allow-not-checked (the summary still prints every NOT CHECKED item)
            2  verdict FAIL: STOP THE WAVE, GO TO SS
            3  verdict ALERT: a FORENSIC anchor changed (wins over 2 and 4)
            4  verdict NOT_CHECKED and --allow-not-checked was not passed
            5  READ_ERROR: the read failed or cannot be trusted (psql failure after retries, timeout, incomplete or mis-split result,
               session not read-only). A report with verdict READ_ERROR is still written. Also for --snapshot, including a snapshot whose
               read returned zero rows in a table that must have rows (nothing is written: no snapshot, no .sha256, no temporary file).
            6  REFUSED: --no-dashas / --no-daily together with --require-lanes without --i-know-dashas-are-not-compared; or --snapshot
               onto an existing file (a baseline is never overwritten)
  --validate-hooks [--hooks-dir DIR] [--require-lanes a,b,c] [--out REPORT.json]     lint the hook files only (no database access); exit 0 or 2

Database access (read-only): set FLIP_READER to an executable that takes one SQL SCRIPT as argv[1], runs it in one psql session (every result
set printed) and prints tab-separated rows, no header (a psql wrapper that sources your reader credentials is the usual choice). If unset,
`psql` from PATH is used with the libpq PG* environment. The tables are read in ONE `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY`
transaction (a concurrent build cannot tear the read); only SELECT statements are ever placed in it; PGOPTIONS gets
`-c default_transaction_read_only=on` (the operator's own options are kept) and nothing is read unless the session reports
transaction_read_only = on. Timeout per attempt: $FLIP_TIMEOUT_SEC (default 120 s). Error text is cut to 200 characters with DSNs and
passwords removed. Credentials are never read or printed by this script.
Snapshot store: --out, else $FLIP_SNAPSHOT_DIR, else /Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots.

Hook schema, matching rules, NOT CHECKED semantics and the W7 hand read-back SQL: see FLIP_DETECTOR_README.md next to this file.
"""
import sys, os, re, json, gzip, glob, hashlib, argparse, collections, subprocess, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_HOOKS_DIR = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "briefs", "suvarna", "exec", "s_l1_attribution_hooks")
TOOL_VERSION = "2.3"
DEFAULT_SNAPSHOT_DIR = "/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots"
CHARTS = {"native": "482012f1-710e-4a25-994a-93821f5871aa", "abhinandan": "1c826d5a-41cb-4450-b4dc-59d440e5f75a", "kiran": "cb73cd3d-9eba-4220-9902-0de91566e980"}
NATIVE = CHARTS["native"]
# A FULL ISO timestamp (date, time, optional seconds / fraction / zone). A text fact that merely starts like one is not a timestamp.
ISO = re.compile(r"^\d{4}-\d\d-\d\d[T ]\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d(:?\d\d)?)?$")
PHANTOM_PREFIX = "362f9f17"  # the dead phantom chart id (CLAUDE.md section B): refused whatever UUID shape it arrives in
CLASS_NUM_KEYS = {"pada", "house_d1", "sign_num", "sign_id", "number", "number_in_lunar_month", "nakshatra_id", "nakshatra_num", "amsa_number",
                  "chalit_house_sripati", "whole_sign_house", "nakshatra_pada", "tithi_id", "vara_id", "yoga_id", "karana_id", "house_num"}
NOT_CLASS_INT = {"longitude_sidereal", "degree_in_sign", "longitude", "longitude_deg"}
AYANS = ("lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical")
ANCHORS = [("SUN sign = Capricorn", ("graha_position", "SUN", "sign"), "Capricorn", AYANS),
           ("MOON nakshatra = Purva Bhadrapada", ("graha_position", "MOON", "nakshatra"), "Purva Bhadrapada", AYANS),
           ("LAGNA sign = Aries", ("graha_position", "LAGNA", "sign"), "Aries", AYANS),
           ("Tithi = Shukla Tritiya", ("panchanga_tithi", "TITHI_BIRTH", "name"), "Shukla Tritiya", ("INVARIANT",)),
           ("Vara = Ravivara", ("panchanga_vara", "VARA_BIRTH", "name"), "Ravivara", ("INVARIANT",)),
           ("Yoga = Shiva", ("panchanga_yoga", "YOGA_BIRTH", "name"), "Shiva", ("INVARIANT",)),
           ("Karana = Garaja", ("panchanga_karana", "KARANA_BIRTH", "name"), "Garaja", ("INVARIANT",))]
DAILY_COLS = ["date", "tithi_id", "paksha", "vara_id", "nakshatra_id", "moon_nakshatra", "yoga_id", "karana_id", "karana_second_id", "tithi_name", "vara", "yoga", "karana"]

TABLES = ("chart_facts", "chart_divisionals", "chart_dashas", "panchanga_daily")
# Tables a hook may name but the detector never reads. An entry on one of these is always NOT CHECKED (never silently passed).
UNCOMPARED_TABLES = ("l1_tajik_varsha_year_lords",)
HOOK_TABLES = TABLES + UNCOMPARED_TABLES
CHANGE_TYPES = ("value", "appeared", "disappeared", "occurrence_count", "tier")
# chart_dashas is compared as a row set only (appeared / disappeared) plus start shifts; its tier is NOT compared.
DASHA_CHANGE_TYPES = ("appeared", "disappeared", "tier")
HOOK_FIELDS = {"lane", "ruling", "pr", "description", "charts", "may_change"}
ENTRY_FIELDS = {"table", "kind", "categories", "fact_keys", "ayanamsha_ids", "systems", "change_types", "expected_direction", "expected_count", "shift_range_sec", "note", "optional"}

# Verdict classes, failure classes, warning class (see the module docstring).
V_ALERT, V_FAIL, V_NOT_CHECKED, V_PASS = "ALERT", "FAIL", "NOT_CHECKED", "PASS"
F_UNDECLARED, F_KIND, F_ABSENT, F_EXPECT, F_DASHA, F_HOOK = ("UNDECLARED_CHANGE", "KIND_MISMATCH", "DECLARED_BUT_ABSENT", "EXPECTATION_MISMATCH",
                                                             "DASHA_SHIFT_UNDECLARED", "HOOK_ERROR")
F_EMPTY = "EMPTY_READ"
FAILURE_CLASSES = (F_UNDECLARED, F_KIND, F_ABSENT, F_EXPECT, F_DASHA, F_HOOK, F_EMPTY)
REPORT_REQUIRED_KEYS = ("failures", "failure_counts", "not_checked", "chart_id")
W_OPTIONAL_ABSENT = "OPTIONAL_ABSENT"
EXIT_PASS, EXIT_FAIL, EXIT_ALERT, EXIT_NOT_CHECKED = 0, 2, 3, 4
EXIT_READ_ERROR = 5  # the read itself failed or cannot be trusted (psql failure, timeout, incomplete or malformed read, session not read-only)
EXIT_REFUSED = 6     # the invocation was refused (a dasha/daily skip together with --require-lanes without --i-know-dashas-are-not-compared; a baseline overwrite)
RO_PGOPTIONS = "-c default_transaction_read_only=on"

# The tier changes this detector cannot machine-check. They are printed on EVERY compare as NOT CHECKED: the detector never reads
# chart_dashas.verification_pass_status nor l1_tajik_varsha_year_lords, so it can neither confirm nor refute a hook about them.
_OTHER = "W7 hand read-back: 'Other tables the detector never reads' in FLIP_DETECTOR_README.md"
STANDING_NOT_CHECKED = (
    {"id": "chart_dashas.tier", "table": "chart_dashas", "what": "chart_dashas verification_pass_status (mudda, narayana, yogini, ashtottari, chara_karaka, naisargika, vimshottari tier)",
     "reason": "the detector never compares the dasha tier column (when chart_dashas is compared at all, only row sets and start shifts)", "readback": "W7 hand read-back: chart_dashas tier SQL in FLIP_DETECTOR_README.md"},
    {"id": "l1_tajik_varsha_year_lords.tier", "table": "l1_tajik_varsha_year_lords", "what": "l1_tajik_varsha_year_lords verification_pass_status",
     "reason": "the table is not one of the four tables the detector reads", "readback": "W7 hand read-back: l1_tajik_varsha_year_lords tier SQL in FLIP_DETECTOR_README.md"},
    {"id": "chart_vichara", "table": "chart_vichara", "what": "chart_vichara (ga_vichara rows: counts, dedupe, sorted constituent_fact_ids, leverage as-of)",
     "reason": "the table is not one of the four tables the detector reads: an empty flip report says nothing about ga_vichara",
     "readback": "W7: run evidence/ga_vichara_writer_ACCEPTANCE.sql (it exists only on PR 2970's branch until the S-L1 integration brings it into s_l1_attribution_hooks/evidence/); every row must read ok = t"},
    {"id": "ga_yoga_firings.strength", "table": "ga_yoga_firings", "what": "ga_yoga_firings strength (constituent_bala_v1)", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "bodha_msr_signals", "table": "bodha_msr_signals", "what": "bodha_msr_signals (shadbala_norm)", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "bodha_rm_resonances", "table": "bodha_rm_resonances", "what": "bodha_rm_resonances", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "ga_condition_composite", "table": "ga_condition_composite", "what": "ga_condition_composite", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "ga_medical", "table": "ga_medical", "what": "ga_medical", "reason": "table not read by the detector", "readback": _OTHER},
    {"id": "ga_vastu_*", "table": "ga_vastu_*", "what": "ga_vastu_* tables", "reason": "tables not read by the detector", "readback": _OTHER},
    {"id": "ga_prashna_*", "table": "ga_prashna_*", "what": "ga_prashna_* tables", "reason": "tables not read by the detector", "readback": _OTHER},
    {"id": "prashna_charts", "table": "prashna_charts", "what": "prashna_charts", "reason": "table not read by the detector", "readback": _OTHER},
)


# ------------------------------------------------------------------ read-only reader
class ReadError(Exception):
    """The read failed or cannot be trusted. The CLI maps it to exit 5 (READ_ERROR) with a report; the message is already scrubbed."""


def _scrub(text):
    """At most 200 characters of a process error, with anything that looks like a DSN or a password removed first."""
    t = str(text or "").strip()
    t = re.sub(r"(?i)(postgres(?:ql)?://)\S+", r"\1***", t)
    t = re.sub(r"(?i)\b(password|passwd|pwd|pgpassword|secret|token)\b(\s*[=:]\s*)\S+", r"\1\2***", t)
    return t[:200]


def _read_env():
    env = dict(os.environ)
    env["PGOPTIONS"] = (env.get("PGOPTIONS", "") + " " + RO_PGOPTIONS).strip()  # the operator's own options are kept
    return env


def _timeout_sec():
    try:
        return float(os.environ.get("FLIP_TIMEOUT_SEC", "120"))
    except ValueError:
        return 120.0


def _select_only(sql):
    if not re.match(r"^\s*select\b", sql, re.I) or ";" in sql.strip().rstrip(";"):
        raise RuntimeError("flip_detector is read-only: only a single SELECT statement is allowed")


def _exec(text, script):
    """Run one SQL string (script=False: -c) or one SQL script (script=True: psql reads it on stdin, so every result set is printed)."""
    reader = os.environ.get("FLIP_READER")
    if reader:
        cmd, inp = [reader, text], None
    elif script:
        cmd, inp = ["psql", "-X", "-q", "-A", "-t", "-F", "\t", "-v", "ON_ERROR_STOP=1", "-f", "-"], text
    else:
        cmd, inp = ["psql", "-X", "-A", "-F", "\t", "-t", "-c", text], None
    return subprocess.run(cmd, input=inp, capture_output=True, text=True, env=_read_env(), timeout=_timeout_sec())


def _run(text, script, retries):
    last = ""
    for i in range(retries):
        try:
            r = _exec(text, script)
            if r.returncode == 0:
                return r.stdout
            last = _scrub(r.stderr) or f"exit status {r.returncode}"
        except subprocess.TimeoutExpired:
            last = f"timed out after {_timeout_sec():g} s"
        except OSError as ex:
            last = _scrub(f"cannot start the reader: {ex}")
        if i < retries - 1:
            time.sleep(5 * (i + 1))  # transient connection loss / statement timeout on the shared reader
    raise ReadError(f"read failed after {retries} attempts: {last}")


def q(sql, retries=4):
    """One SELECT, tab-separated rows. Read-only is requested through PGOPTIONS on every call."""
    _select_only(sql)
    return [ln.split("\t") for ln in _run(sql, False, retries).splitlines() if ln != ""]


SENTINEL = re.compile(r"^@@END:([a-z_]+)@@$")


def q_txn(named, retries=4):
    """ONE repeatable-read, read-only transaction in ONE psql session: BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY; every SELECT; COMMIT.
    All tables are therefore read from one snapshot (a concurrent build cannot tear it). `named` is [(name, select)]; each result set is
    followed by an @@END:name@@ marker row, and a missing marker (a wrapper that returned only the last result) is a ReadError.
    Returns {name: [row, ...]} with rows split on tabs."""
    script = ["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"]
    for name, sql in named:
        _select_only(sql)
        script += [sql.strip().rstrip(";"), f"select '@@END:{name}@@'"]
    script.append("COMMIT")
    out = _run(";\n".join(script) + ";\n", True, retries)
    got, buf, order = {}, [], []
    lines = out.splitlines()
    if lines and lines[0] == "BEGIN":      # psql command tags (printed unless -q; a wrapper may print them): never data
        lines = lines[1:]
    if lines and lines[-1] == "COMMIT":
        lines = lines[:-1]
    for ln in lines:
        m = SENTINEL.match(ln)
        if m:
            got[m.group(1)] = buf
            order.append(m.group(1))
            buf = []
        else:
            buf.append(ln.split("\t"))
    want = [n for n, _ in named]
    if order != want:
        raise ReadError(f"incomplete read: expected result sets {want}, got {order} (the reader must print every result set of a script)")
    return got


def _rows(got, name, ncols):
    rows = got[name]
    for r in rows:
        if len(r) != ncols:
            raise ReadError(f"{name}: a row has {len(r)} columns, expected {ncols} (a tab or newline inside a text value mis-splits rows); the read cannot be trusted")
    return rows


UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def normalize_chart_id(c):
    """The ONE place a chart id is normalised (trim, braces, lower case) and validated as a UUID; anything else raises ValueError.
    Everything that interpolates a chart id into SQL, compares it with NATIVE or matches a hook 'charts' prefix goes through here."""
    t = str(c).strip().strip("{}").strip().lower()
    if t.replace("-", "").startswith(PHANTOM_PREFIX):
        raise ValueError("refused: the dead phantom chart id 362f9f17 is never read or compared")
    if not UUID_RE.match(t):
        raise ValueError(f"not a chart UUID: {str(c)[:60]!r}")
    return t


def resolve(c):
    key = str(c).strip().lower()
    return normalize_chart_id(CHARTS.get(key, c))


def ts_parse(s):
    s = s.replace(" ", "T")
    if s.endswith("+00"):
        s += ":00"
    return datetime.fromisoformat(s)


# ------------------------------------------------------------------ hooks
class HookError(Exception):
    pass


def validate_hook(h, fname):
    errs = []
    if not isinstance(h, dict):
        return [f"{fname}: top level must be an object"]
    unknown = set(h) - HOOK_FIELDS
    if unknown:
        errs.append(f"{fname}: unknown top-level fields {sorted(unknown)}")
    stem = os.path.splitext(os.path.basename(fname))[0]
    if h.get("lane") != stem:
        errs.append(f"{fname}: 'lane' must equal the file stem '{stem}'")
    if not isinstance(h.get("ruling"), str) or not h.get("ruling"):
        errs.append(f"{fname}: 'ruling' (the name shown in attribution) is required")
    if not isinstance(h.get("description"), str) or not h.get("description").strip():
        errs.append(f"{fname}: 'description' is required")
    pr = h.get("pr")
    if not ((isinstance(pr, str) and pr.strip()) or (isinstance(pr, int) and not isinstance(pr, bool) and pr > 0)):
        errs.append(f"{fname}: 'pr' (PR number or branch of the fix) is required")
    mc = h.get("may_change")
    if not isinstance(mc, list) or not mc:
        errs.append(f"{fname}: 'may_change' must be a non-empty list (an empty placeholder hook is not allowed; leave the file absent instead)")
        return errs
    for i, e in enumerate(mc):
        w = f"{fname} may_change[{i}]"
        if not isinstance(e, dict):
            errs.append(f"{w}: must be an object")
            continue
        unknown = set(e) - ENTRY_FIELDS
        if unknown:
            errs.append(f"{w}: unknown fields {sorted(unknown)}")
        if e.get("table") not in HOOK_TABLES:
            errs.append(f"{w}: 'table' must be one of {HOOK_TABLES}")
        if "optional" in e and not isinstance(e["optional"], bool):
            errs.append(f"{w}: 'optional' must be true or false")
        if e.get("kind") == "dasha_shift":
            if e.get("table") != "chart_dashas":
                errs.append(f"{w}: kind dasha_shift requires table chart_dashas")
            sr = e.get("shift_range_sec")
            if not (isinstance(sr, list) and len(sr) == 2 and all(isinstance(x, (int, float)) for x in sr) and sr[0] <= sr[1]):
                errs.append(f"{w}: dasha_shift needs shift_range_sec [lo, hi] (seconds, current minus snapshot)")
            if not (isinstance(e.get("systems"), list) and e.get("systems")):
                errs.append(f"{w}: dasha_shift needs a non-empty 'systems' list (exact system_id)")
            if "expected_count" in e:
                errs.append(f"{w}: 'expected_count' is not supported on a dasha_shift entry (it would be ignored); use 'optional' or leave the entry without a count")
        else:
            if e.get("kind") not in (None, "change"):
                errs.append(f"{w}: 'kind' must be 'change' (default) or 'dasha_shift'")
            cats = e.get("categories")
            if not (isinstance(cats, list) and cats and all(isinstance(c, str) and c for c in cats)):
                errs.append(f"{w}: 'categories' must be a non-empty list of EXACT names (no patterns): fact_category / panchanga_daily column / chart_dashas system_id")
            elif any(re.search(r"[*?\[\]()|^$\\]", c) for c in cats):
                errs.append(f"{w}: 'categories' must be exact names, not patterns")
        for f in ("fact_keys", "ayanamsha_ids"):
            if f in e and not (isinstance(e[f], list) and e[f] and all(isinstance(x, str) and x for x in e[f])):
                errs.append(f"{w}: '{f}' must be a NON-EMPTY list of exact strings (omit the field to match all; an empty list would broaden, not narrow)")
        ct = e.get("change_types")
        if ct is not None and not (isinstance(ct, list) and ct and set(ct) <= set(CHANGE_TYPES)):
            errs.append(f"{w}: 'change_types' must be a non-empty subset of {CHANGE_TYPES}")
        elif ct and e.get("table") == "chart_dashas" and e.get("kind") != "dasha_shift" and not set(ct) <= set(DASHA_CHANGE_TYPES):
            errs.append(f"{w}: chart_dashas row-set entries may only declare change_types within {DASHA_CHANGE_TYPES} (the detector never produces other kinds there)")
        ec = e.get("expected_count")
        if ec is not None:
            ok = (isinstance(ec, dict) and set(ec) <= {"exact", "min", "max"} and ec and all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in ec.values())
                  and not ("exact" in ec and len(ec) > 1) and not ("min" in ec and "max" in ec and ec["min"] > ec["max"]))
            if not ok:
                errs.append(f"{w}: 'expected_count' must be {{\"exact\": n}} or {{\"min\": a, \"max\": b}} (non-negative integers, not booleans; min must not exceed max)")
    if "charts" in h and not (isinstance(h["charts"], list) and h["charts"] and all(isinstance(c, str) and re.match(r"^[0-9a-fA-F-]{8,}$", c) for c in h["charts"])):
        errs.append(f"{fname}: 'charts' must be a NON-EMPTY list of hex chart-id prefixes (>= 8 chars); omit the field to apply to every chart")
    elif any(isinstance(c, str) and c.replace("-", "").lower().startswith(PHANTOM_PREFIX) for c in h.get("charts", [])):
        errs.append(f"{fname}: 'charts' names the dead phantom chart id {PHANTOM_PREFIX} (refused)")
    return errs


def load_hooks(hooks_dir, required=()):
    """-> (hooks, errors). Every *.json in the folder is a lane hook. Errors make the run exit 2."""
    hooks, errors = [], []
    if not os.path.isdir(hooks_dir):
        return hooks, [f"HOOKS DIR NOT FOUND: {hooks_dir}"]
    files = sorted(glob.glob(os.path.join(hooks_dir, "*.json")))  # top level only: sub-folders (evidence/) are never hooks
    if not files:
        errors.append(f"NO HOOK FILES: {hooks_dir} contains no top-level *.json")
    for p in files:
        try:
            h = json.load(open(p))
        except Exception as ex:
            errors.append(f"{os.path.basename(p)}: not valid JSON ({ex})")
            continue
        errs = validate_hook(h, p)
        if errs:
            errors += errs
        else:
            hooks.append(h)
    present = {h["lane"] for h in hooks}
    for lane in required:
        if lane and lane not in present:
            errors.append(f"MISSING HOOK: lane '{lane}' has no valid {lane}.json in {hooks_dir} (blocker: its fix may change facts nothing attributes)")
    return hooks, errors


def scope_matches(e, c):
    """The entry declares this row/category/column (table, category, fact_key, ayanamsha), whatever KIND of change it is."""
    if e.get("kind") == "dasha_shift":
        return False
    if c["table"] != e["table"] or c["category"] not in e["categories"]:
        return False
    if e.get("fact_keys") and c.get("fact_key") not in e["fact_keys"]:
        return False
    if e.get("ayanamsha_ids") and c.get("ayanamsha") not in e["ayanamsha_ids"]:
        return False
    return True


def entry_matches(e, c):
    """Scope matches AND the change kind is one the entry declares (omitted change_types = all five kinds)."""
    return scope_matches(e, c) and c["change"] in (e.get("change_types") or CHANGE_TYPES)


def applies_to_chart(h, chart_id):
    if "charts" not in h:
        return True
    return any(chart_id.lower().startswith(p.lower()) for p in h["charts"])


def attribute_all(changes, hooks, chart_id):
    """Fills c['lanes'] (lane names, may be several; empty = UNATTRIBUTED) and c['kind_mismatch'] (for an unattributed change, the
    {lane: declared change_types} of every entry that declares its category but not its KIND). Returns per-entry observed counts."""
    counts = collections.Counter()
    for c in changes:
        c["lanes"] = []
        for h in hooks:
            if not applies_to_chart(h, chart_id):
                continue
            for i, e in enumerate(h["may_change"]):
                if entry_matches(e, c):
                    counts[(h["lane"], i)] += 1
                    if h["lane"] not in c["lanes"]:
                        c["lanes"].append(h["lane"])
        km = {}
        if not c["lanes"]:
            for h in hooks:
                if not applies_to_chart(h, chart_id):
                    continue
                for e in h["may_change"]:
                    if scope_matches(e, c):  # the hook declares this category, but not this KIND of change
                        km.setdefault(h["lane"], set()).update(e.get("change_types") or CHANGE_TYPES)
        c["kind_mismatch"] = {lane: sorted(v) for lane, v in sorted(km.items())}
    return counts


def entry_observability(e, have_dash, have_daily):
    """-> None if the detector can observe this entry, else the reason it cannot (the entry is then NOT CHECKED, not 'absent')."""
    if e.get("table") in UNCOMPARED_TABLES:
        return f"table {e['table']} is never read by the detector"
    if e.get("table") == "chart_dashas":
        if not have_dash:
            return "chart_dashas not compared in this run (--no-dashas or absent from the snapshot)"
        if e.get("kind") != "dasha_shift" and set(e.get("change_types") or ()) == {"tier"}:
            return "the detector never compares the chart_dashas tier column"
    if e.get("table") == "panchanga_daily" and not have_daily:
        return "panchanga_daily not compared in this run (--no-daily or absent from the snapshot)"
    return None


def expectation_report(hooks, counts, chart_id, have_dash=True, have_daily=True, shift_counts=None):
    """-> (expectation rows, EXPECTATION_MISMATCH messages, DECLARED_BUT_ABSENT messages, OPTIONAL_ABSENT warnings, entry-level NOT CHECKED).
    An entry that declares expected_count is judged by that bound (a bound with min 0 explicitly allows no change). An entry with no
    expected_count that observed nothing is DECLARED_BUT_ABSENT unless it is marked optional (then a warning). An entry the detector
    cannot observe is NOT CHECKED, never absent and never passing."""
    shift_counts = shift_counts or {}
    bad, rows, absent, warn, unchecked = [], [], [], [], []
    for h in hooks:
        if not applies_to_chart(h, chart_id):
            continue
        for i, e in enumerate(h["may_change"]):
            why = entry_observability(e, have_dash, have_daily)
            label = f"{h['lane']}[{i}] ({e['table']}:{','.join(e.get('categories') or e.get('systems') or [])})"
            if why:
                unchecked.append({"lane": h["lane"], "entry": i, "table": e["table"], "reason": why})
                continue
            n = shift_counts.get((h["lane"], i), 0) if e.get("kind") == "dasha_shift" else counts.get((h["lane"], i), 0)
            ec = e.get("expected_count")
            if ec is not None and e.get("kind") != "dasha_shift":
                ok = (n == ec["exact"]) if "exact" in ec else (ec.get("min", 0) <= n <= ec.get("max", 10 ** 12))
                rows.append({"lane": h["lane"], "entry": i, "expected": ec, "observed": n, "ok": ok})
                if not ok:
                    bad.append(f"EXPECTATION MISMATCH {label}: expected {ec}, observed {n}")
            elif n == 0:
                if e.get("optional"):
                    warn.append(f"{W_OPTIONAL_ABSENT} {label}: optional entry observed no change")
                else:
                    absent.append(f"DECLARED BUT ABSENT {label}: the hook declares this change and nothing changed (mark the entry \"optional\": true if absence is acceptable)")
    return rows, bad, absent, warn, unchecked


# ------------------------------------------------------------------ read production
def read_state(chart_id, dashas=True, daily=True, info=None):
    """Read one chart (and the global panchanga_daily) in ONE repeatable-read read-only transaction. The session must report
    transaction_read_only = on (requested through PGOPTIONS, proven by the first statement) or nothing is read."""
    chart_id = normalize_chart_id(chart_id)  # the only interpolated operator-controlled value: a UUID or nothing
    named = [("ro", "select current_setting('transaction_read_only')"), ("usr", "select current_user"),
             ("facts", f"""select ayanamsha_id, fact_category, fact_subject, fact_key, coalesce(fact_value_text,''), coalesce(fact_value_num::text,''),
                 coalesce(verification_pass_status,'') from chart_facts where chart_id='{chart_id}' order by ayanamsha_id, fact_category, fact_subject, fact_key"""),
             ("divs", f"""select ayanamsha_id, varga, graha, fact_category, fact_key, coalesce(fact_value_text,''), coalesce(fact_value_num::text,''), coalesce(sign,'')
                 from chart_divisionals where chart_id='{chart_id}'""")]
    if dashas:
        named.append(("dashas", f"""select ayanamsha_id, system_id, level_n, lord_graha, coalesce(kp_sublevel,''), coalesce(kp_sub_lord,''), coalesce(kp_sub_sub_lord,''),
                 start_iso::text, end_iso::text, dasha_row_id::text, coalesce(parent_row_id::text,'') from chart_dashas
                 where chart_id='{chart_id}'"""))
    if daily:
        named.append(("daily", "select " + ",".join(f"{c}::text" for c in DAILY_COLS) + " from panchanga_daily order by date"))
    got = q_txn(named)
    if got["ro"] != [["on"]]:
        raise ReadError(f"database session is not read-only (transaction_read_only={got['ro']!r}); refusing to read")
    if info is not None:
        info["db_user"] = got["usr"][0][0] if got["usr"] and got["usr"][0] else ""
    st = {"chart_facts": _rows(got, "facts", 7), "divisionals": _rows(got, "divs", 8)}
    if dashas:
        st["dashas"] = dasha_label_rows(_rows(got, "dashas", 11))
    if daily:
        st["daily"] = _rows(got, "daily", len(DAILY_COLS))
    return st


def dasha_label_rows(rows):
    byid = {r[9]: r for r in rows}

    def lab(r):
        s = r[3]
        if r[4]:
            s += ":" + r[4] + ":" + r[5] + ":" + r[6]
        return s
    paths = {}
    for r in sorted(rows, key=lambda r: int(r[2])):
        base = paths.get(r[10], "") if r[10] in byid else ""
        paths[r[9]] = base + "/" + lab(r)
    return [[r[0], r[1], int(r[2]), paths[r[9]], r[7], r[8]] for r in rows if r[1] != "scope_cap"]


def cmd_snapshot(a):
    """Never overwrites: a baseline is evidence. An existing file (or .sha256) at the target is refused (exit 6); pick another --out."""
    chart_id = resolve(a.snapshot)
    info = {}
    try:
        st = read_state(chart_id, not a.no_dashas, not a.no_daily, info)
    except ReadError as ex:
        print(f"READ ERROR: {ex}", file=sys.stderr)
        return EXIT_READ_ERROR
    empties = empty_tables(st, not a.no_dashas, not a.no_daily)
    if empties:
        # the baseline is the evidence the whole flip report rests on: a snapshot of an empty read would be saved with a .sha256 and could not be overwritten
        print(f"READ ERROR: EMPTY READ: {', '.join(empties)} returned zero rows for chart {chart_id}; no snapshot was written "
              "(check the reader's grants / row-level security and the chart id)", file=sys.stderr)
        return EXIT_READ_ERROR
    now = datetime.now(timezone.utc).isoformat()
    st["meta"] = {"tool": "flip_detector.py", "tool_version": TOOL_VERSION, "chart_id": chart_id, "taken_at_utc": now, "db_user": info.get("db_user", ""), "read_only": True,
                  "single_transaction": "REPEATABLE READ READ ONLY", "no_dashas": bool(a.no_dashas), "no_daily": bool(a.no_daily),
                  "counts": {k: len(v) for k, v in st.items() if isinstance(v, list)}}
    d = os.environ.get("FLIP_SNAPSHOT_DIR", DEFAULT_SNAPSHOT_DIR)
    out = a.out or os.path.join(d, f"pre_rebuild_{chart_id[:8]}_{now[:10]}_{now[11:19].replace(':', '')}.json.gz")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if os.path.exists(out) or os.path.exists(out + ".sha256"):
        print(f"REFUSED: {out} (or its .sha256) already exists; a baseline is never overwritten. Choose another --out or move the old file.", file=sys.stderr)
        return EXIT_REFUSED
    # atomic: both files are written under temporary names and linked into place only after everything succeeded (link fails if the target exists: never overwrites)
    tmp, tmp_sha = f"{out}.tmp{os.getpid()}", f"{out}.sha256.tmp{os.getpid()}"
    try:
        with gzip.open(tmp, "wt") as f:
            json.dump(st, f)
        h = hashlib.sha256(open(tmp, "rb").read()).hexdigest()
        with open(tmp_sha, "w") as f:
            f.write(f"{h}  {os.path.basename(out)}\n")
        os.link(tmp, out)
        try:
            os.link(tmp_sha, out + ".sha256")
        except OSError:
            os.unlink(out)
            raise
    except FileExistsError:
        print(f"REFUSED: {out} (or its .sha256) appeared meanwhile; a baseline is never overwritten.", file=sys.stderr)
        return EXIT_REFUSED
    finally:
        for t in (tmp, tmp_sha):
            if os.path.exists(t):
                os.unlink(t)
    print(f"snapshot: {out}\nsha256:   {h}\ncounts:   {st['meta']['counts']}\ntaken:    {now} as {st['meta']['db_user']}")
    return 0


# ------------------------------------------------------------------ classification and diff
def kind_of(t, n, key):
    if t:
        return "time" if ISO.match(t) else "class_text"
    if n not in ("", None):
        if key in CLASS_NUM_KEYS:
            return "class_num"
        try:
            f = float(n)
            if abs(f - round(f)) < 1e-9 and key not in NOT_CLASS_INT:
                return "class_num"
        except ValueError:
            pass
        return "continuous"
    return "class_text"


def occ_map(rows, keyfn, valfn):
    m = collections.defaultdict(list)
    for r in rows:
        m[keyfn(r)].append(valfn(r))
    for k in m:
        # the tier is part of the sort key: two rows equal in value but different in tier must pair in a fixed order, whatever order the database returned
        m[k].sort(key=lambda v: (v[0] or "", float(v[1]) if v[1] not in ("", None) else float("-inf"), (v[2] if len(v) > 2 else "") or ""))
    return m


def same_num(a, b):
    if a in ("", None) or b in ("", None):
        return (a in ("", None)) and (b in ("", None))
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a))) + 1e-9


def diff_table(table, A, B, nkey):
    """A,B: key -> sorted occurrence lists [(t, n, tier)]. nkey = (index of fact_category, index of fact_key) inside the key tuple.
    Returns (class_and_tier_changes, continuous_stats)."""
    out = []
    cont = {"compared": 0, "changed": 0, "max_abs_delta": 0.0, "to_non_numeric": 0, "keys_appeared": 0, "keys_disappeared": 0,
            "time_keys_appeared": 0, "time_keys_disappeared": 0, "time_to_non_time": 0}
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        cat, key = k[nkey[0]], k[nkey[1]]
        base = {"table": table, "key": list(k), "category": cat, "fact_key": key, "ayanamsha": k[0]}
        if a is None or b is None:
            vals = b if a is None else a
            kinds = {kind_of(v[0], v[1], key) for v in vals}
            if kinds == {"time"}:
                cont["time_keys_appeared" if a is None else "time_keys_disappeared"] += 1
                continue  # an appearing/disappearing timestamp-valued fact is not a class change
            if "continuous" in kinds:  # a continuous key that appears or disappears IS a change (it can trigger declared/undeclared logic)
                cont["keys_appeared" if a is None else "keys_disappeared"] += 1
            out.append({**base, "change": "appeared" if a is None else "disappeared", "value": [list(v[:2]) for v in vals][:2]})
            continue
        if len(a) != len(b):
            out.append({**base, "change": "occurrence_count", "before": len(a), "after": len(b)})
        for x, y in zip(a, b):
            kd = kind_of(x[0], x[1], key)
            if kd == "continuous":
                cont["compared"] += 1
                if (y[0] or "") != "" or y[1] in ("", None):
                    # the continuous number became NULL or text (1.694 -> 'no_data'): a number was lost, which is a value change
                    cont["changed"] += 1
                    cont["to_non_numeric"] += 1
                    out.append({**base, "change": "value", "before": [x[0], x[1]], "after": [y[0], y[1]]})
                elif not same_num(x[1], y[1]):
                    cont["changed"] += 1
                    try:
                        cont["max_abs_delta"] = max(cont["max_abs_delta"], abs(float(y[1]) - float(x[1])))
                    except (TypeError, ValueError):
                        pass
            elif kd == "time":
                if kind_of(y[0], y[1], key) != "time":
                    # a timestamp-valued fact that became NULL or non-timestamp text lost its timestamp: a value change (a changed timestamp is not)
                    cont["time_to_non_time"] += 1
                    out.append({**base, "change": "value", "before": [x[0], x[1]], "after": [y[0], y[1]]})
            elif (x[0] or "") != (y[0] or "") or not same_num(x[1], y[1]):
                out.append({**base, "change": "value", "before": [x[0], x[1]], "after": [y[0], y[1]]})
            if len(x) > 2 and x[2] != y[2]:
                out.append({**base, "change": "tier", "before": x[2], "after": y[2]})
    return out, cont


def dasha_diff(snap, cur, hooks, chart_id):
    """Pair rows by (ayanamsha, system, level, lord path) then nearest start within 10 days. Returns (changes, info).
    Row-set changes (a row exists in only one side) are class changes of table chart_dashas, category = system_id.
    A start shift is attributed only by a 'dasha_shift' hook entry whose system and shift_range_sec contain it; 0 s = no change."""
    def groups(rows):
        g = collections.defaultdict(list)
        for ay, sy, lv, p, s, e in rows:
            g[(ay, sy, lv, p)].append(ts_parse(s))
        for k in g:
            g[k].sort()
        return g
    gs, gc = groups(snap), groups(cur)
    tol = 10 * 86400.0
    changes, shifts = [], collections.defaultdict(list)
    shift_counts = collections.Counter()  # (lane, entry index) -> shifted rows that fall inside that dasha_shift entry's declared range
    for k in sorted(set(gs) | set(gc)):
        a, b = gs.get(k, []), gc.get(k, [])
        i = j = 0
        while i < len(a) and j < len(b):
            d = (b[j] - a[i]).total_seconds()
            if abs(d) <= tol:
                shifts[(k[0], k[1])].append(d)
                i += 1
                j += 1
            elif d > 0:
                changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "disappeared", "start": a[i].isoformat()})
                i += 1
            else:
                changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "appeared", "start": b[j].isoformat()})
                j += 1
        for x in a[i:]:
            changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "disappeared", "start": x.isoformat()})
        for x in b[j:]:
            changes.append({"table": "chart_dashas", "key": list(k), "category": k[1], "fact_key": "row", "ayanamsha": k[0], "change": "appeared", "start": x.isoformat()})
    info = {}
    shift_unattrib = []
    for (ay, sy), v in sorted(shifts.items()):
        moved = [x for x in v if abs(x) > 2.0]
        rec = {"rows": len(v), "rows_shifted": len(moved), "min": min(v), "max": max(v)}
        if moved:
            c = collections.Counter(round(x) for x in moved)
            rec["mode_shift_sec"], cnt = c.most_common(1)[0]
            rec["share_of_shifted_at_mode"] = round(cnt / len(moved), 4)
            lanes = []
            outside = list(moved)
            for h in hooks:
                if not applies_to_chart(h, chart_id):
                    continue
                for ei, e in enumerate(h["may_change"]):
                    if e.get("kind") == "dasha_shift" and sy in e["systems"] and (not e.get("ayanamsha_ids") or ay in e["ayanamsha_ids"]):
                        lo, hi = e["shift_range_sec"]
                        shift_counts[(h["lane"], ei)] += len([x for x in moved if lo <= x <= hi])
                        inside = [x for x in outside if lo <= x <= hi]
                        if inside and h["lane"] not in lanes:
                            lanes.append(h["lane"])
                        outside = [x for x in outside if not (lo <= x <= hi)]
            rec["lanes"] = lanes
            rec["rows_outside_every_declared_range"] = len(outside)
            if outside:
                shift_unattrib.append(f"{ay}|{sy}: {len(outside)} of {len(moved)} shifted rows lie outside every declared dasha_shift range (mode {rec['mode_shift_sec']} s)")
        info[f"{ay}|{sy}"] = rec
    return changes, info, shift_unattrib, shift_counts


def anchors_check(cur_facts):
    m = collections.defaultdict(list)
    for r in cur_facts:
        m[(r[0], r[1], r[2], r[3])].append(r[4])
    res, alert = [], False
    for name, (cat, subj, key), want, ayans in ANCHORS:
        for ay in ayans:
            vals = m.get((ay, cat, subj, key), [])
            ok = bool(vals) and all(v == want for v in vals)
            res.append({"anchor": name, "ayanamsha": ay, "values": vals, "expected": want, "ok": ok})
            alert |= not ok
    return res, alert


def _declared_by(hooks, chart_id, table, tier_only_scope):
    out = []
    for h in hooks:
        if not applies_to_chart(h, chart_id):
            continue
        for e in h["may_change"]:
            if e.get("table") != table or e.get("kind") == "dasha_shift":
                continue
            if tier_only_scope and "tier" not in (e.get("change_types") or CHANGE_TYPES):
                continue
            if h["lane"] not in out:
                out.append(h["lane"])
    return sorted(out)


def report_is_malformed(rep):
    """A report missing the keys the verdict is decided from (or with the wrong shapes) is never PASS and never a crash."""
    if not isinstance(rep, dict) or any(k not in rep for k in REPORT_REQUIRED_KEYS):
        return True
    return not isinstance(rep["failures"], dict) or not isinstance(rep["failure_counts"], dict) or not isinstance(rep["not_checked"], list)


def decide_verdict(rep):
    """The ONE place a verdict is decided. ALERT > FAIL > NOT_CHECKED > PASS. PASS only when no failure class is non-empty AND nothing is
    NOT CHECKED. It reads the report's own failure lists, so a failure can never be hidden by a stale 'verdict' field. A malformed report
    (missing failures / failure_counts / not_checked) is FAIL: a saved report JSON must never be trusted for its 'verdict' field."""
    if report_is_malformed(rep):
        return V_FAIL
    if rep.get("ALERT_anchor_changed"):
        return V_ALERT
    if any(rep["failures"].get(k) for k in FAILURE_CLASSES):
        return V_FAIL
    if rep.get("not_checked"):
        return V_NOT_CHECKED
    return V_PASS


def empty_tables(st, have_dash, have_daily):
    """Tables that must hold rows but hold none in this state: chart_facts and chart_divisionals always; chart_dashas / panchanga_daily when they are
    read. Used by compare_states (EMPTY_READ failure) and by --snapshot (a baseline of an empty read is refused)."""
    return [label for label, key, on in (("chart_facts", "chart_facts", True), ("chart_divisionals", "divisionals", True), ("chart_dashas", "dashas", have_dash),
                                         ("panchanga_daily", "daily", have_daily)) if on and not st.get(key)]


def compare_states(snap, cur, hooks, chart_id, have_dash=True, have_daily=True, hook_errors=(), standing_not_checked=STANDING_NOT_CHECKED,
                   not_compared=None, extra_not_checked=()):
    """Pure function (no I/O): the whole comparison. Returns the report dict (JSON-serializable, deterministic ordering).
    `standing_not_checked` is the registry of scopes the detector never compares; production always uses STANDING_NOT_CHECKED.
    EMPTY_READ rule: every table compared (chart_facts, chart_divisionals always; chart_dashas / panchanga_daily when compared) must hold
    at least one row in BOTH states. A real chart always has rows in each; zero rows means the read returned nothing (for example a
    row-level-security block for the reader), and empty-versus-empty would otherwise read as 'nothing changed'.
    A table that was NOT compared in this run (have_dash / have_daily False: a flag, or a section missing from a snapshot) is never silent:
    it adds a conditional NOT CHECKED row ('<table>.not_compared') carrying the reason in `not_compared` ({table: reason}), and the summary
    prints n/a (never a green ok) for the classes it would have evaluated. `extra_not_checked` is a list of ready NOT CHECKED rows."""
    chart_id = normalize_chart_id(chart_id)
    not_compared = dict(not_compared or {})
    empty = []
    for side, st in (("snapshot", snap), ("current", cur)):
        for label in empty_tables(st, have_dash, have_daily):
            empty.append(f"EMPTY READ: {label} has zero rows in the {side} state (a real chart has rows: the read returned nothing; check reader grants / row-level security)")
    fk = lambda r: (r[0], r[1], r[2], r[3])
    fv = lambda r: (r[4], r[5], r[6])
    changes, cont1 = diff_table("chart_facts", occ_map(snap["chart_facts"], fk, fv), occ_map(cur["chart_facts"], fk, fv), (1, 3))
    dk = lambda r: (r[0], r[1], r[2], r[3], r[4])
    dv = lambda r: (r[5] or r[7], r[6], "")
    ch2, cont2 = diff_table("chart_divisionals", occ_map(snap["divisionals"], dk, dv), occ_map(cur["divisionals"], dk, dv), (3, 4))
    changes += ch2
    if have_daily:
        sd, cd = {r[0]: r for r in snap["daily"]}, {r[0]: r for r in cur["daily"]}
        for d in sorted(set(sd) | set(cd)):
            if d not in sd or d not in cd:
                changes.append({"table": "panchanga_daily", "key": [d], "category": "row", "fact_key": d, "ayanamsha": "", "change": "appeared" if d not in sd else "disappeared"})
                continue
            for c, x, y in zip(DAILY_COLS[1:], sd[d][1:], cd[d][1:]):
                if x != y:
                    changes.append({"table": "panchanga_daily", "key": [d, c], "category": c, "fact_key": d, "ayanamsha": "", "change": "value", "before": x, "after": y})
    dinfo, shift_unattrib, shift_counts = None, [], {}
    if have_dash:
        dch, dinfo, shift_unattrib, shift_counts = dasha_diff(snap["dashas"], cur["dashas"], hooks, chart_id)
        changes += dch
    counts = attribute_all(changes, hooks, chart_id)
    exp_rows, exp_bad, absent, warn, entry_unchecked = expectation_report(hooks, counts, chart_id, have_dash, have_daily, shift_counts)
    unattrib = [c for c in changes if not c["lanes"]]
    kind_mm = [c for c in unattrib if c["kind_mismatch"]]
    undeclared = [c for c in unattrib if not c["kind_mismatch"]]
    by = collections.Counter((c["table"], c["category"], c["change"], ",".join(c["lanes"]) or "UNATTRIBUTED") for c in changes)
    not_checked = [{"id": n["id"], "table": n["table"], "what": n["what"], "reason": n["reason"], "readback": n["readback"],
                    "declared_by_lanes": _declared_by(hooks, chart_id, n["table"], n["table"] == "chart_dashas"), "status": "NOT CHECKED"}
                   for n in standing_not_checked]
    not_checked += [{"id": f"{u['lane']}[{u['entry']}]", "table": u["table"], "what": "hook entry the detector cannot observe in this run", "reason": u["reason"],
                     "readback": "hand read-back", "declared_by_lanes": [u["lane"]], "status": "NOT CHECKED"} for u in entry_unchecked]
    for tname, on, what in (("chart_dashas", have_dash, "chart_dashas row sets and start shifts (a real dasha change would read as no change)"),
                            ("panchanga_daily", have_daily, "panchanga_daily rows and columns (a real panchanga change would read as no change)")):
        if not on:
            not_checked.append({"id": f"{tname}.not_compared", "table": tname, "what": what, "reason": not_compared.get(tname, f"{tname} not compared in this run"),
                                "readback": "re-run the compare WITHOUT --no-dashas / --no-daily on snapshots that carry the section",
                                "declared_by_lanes": _declared_by(hooks, chart_id, tname, False), "status": "NOT CHECKED"})
    not_checked += [dict(x, status="NOT CHECKED") for x in extra_not_checked]
    rep = {"tool_version": TOOL_VERSION, "chart_id": chart_id, "changes_total": len(changes), "unattributed": len(unattrib),
           "compared": {"chart_facts": True, "chart_divisionals": True, "chart_dashas": bool(have_dash), "panchanga_daily": bool(have_daily)},
           "unattributed_examples": unattrib[:50],
           "by_table_category_change_lane": [[list(k), v] for k, v in sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))],
           "continuous": {"chart_facts": cont1, "chart_divisionals": cont2}, "dashas": dinfo,
           "dasha_shift_unattributed": shift_unattrib, "expectations": exp_rows, "expectation_mismatches": exp_bad,
           "failure_counts": {F_UNDECLARED: len(undeclared), F_KIND: len(kind_mm), F_ABSENT: len(absent), F_EXPECT: len(exp_bad),
                              F_DASHA: len(shift_unattrib), F_HOOK: len(hook_errors), F_EMPTY: len(empty)},
           "failures": {F_UNDECLARED: [_brief(c) for c in undeclared[:50]], F_KIND: [_brief(c) for c in kind_mm[:50]], F_ABSENT: absent,
                        F_EXPECT: exp_bad, F_DASHA: shift_unattrib, F_HOOK: list(hook_errors), F_EMPTY: empty},
           "warnings": warn, "not_checked": not_checked, "changes": changes}
    if chart_id == NATIVE and cur["chart_facts"]:
        rep["anchors"], rep["ALERT_anchor_changed"] = anchors_check(cur["chart_facts"])
    elif chart_id == NATIVE:
        # an empty current chart_facts is an EMPTY_READ failure (exit 2), not an anchor ALERT: nothing was read to compare with the anchors
        rep["anchors"], rep["ALERT_anchor_changed"] = [], False
    else:
        rep["ALERT_anchor_changed"] = False
    rep["verdict"] = decide_verdict(rep)
    return rep


def _brief(c):
    b = {k: c[k] for k in ("table", "category", "fact_key", "ayanamsha", "change") if k in c}
    if c.get("kind_mismatch"):
        b["declared_kinds_by_lane"] = c["kind_mismatch"]
    for k in ("before", "after", "value"):
        if k in c:
            b[k] = c[k]
    return b


def exit_code(rep, allow_not_checked=False):
    """0 PASS (or NOT_CHECKED with allow_not_checked), 2 FAIL, 3 ALERT, 4 NOT_CHECKED without allow_not_checked."""
    v = decide_verdict(rep)
    if v == V_ALERT:
        return EXIT_ALERT
    if v == V_FAIL:
        return EXIT_FAIL
    if v == V_NOT_CHECKED:
        return EXIT_PASS if allow_not_checked else EXIT_NOT_CHECKED
    return EXIT_PASS


def render_summary(rep, allow_not_checked=False):
    """Human summary lines (deterministic)."""
    L = []
    v = decide_verdict(rep)
    if report_is_malformed(rep):
        return [f"VERDICT: {v}   exit {exit_code(rep, allow_not_checked)}   MALFORMED REPORT: needs {list(REPORT_REQUIRED_KEYS)} (a saved report is never trusted for its verdict)"]
    L.append(f"VERDICT: {v}   exit {exit_code(rep, allow_not_checked)}   chart {rep['chart_id']}")
    if rep.get("ALERT_anchor_changed"):
        L.append("ALERT: A FORENSIC ANCHOR CHANGED. STOP AND GO TO SS.")
        for r in rep.get("anchors", []):
            if not r["ok"]:
                L.append(f"    {r}")
    L.append(f"changes (class + tier + dasha row-set): {rep['changes_total']}   not attributed to any lane: {rep['unattributed']}")
    for k, n in rep["failure_counts"].items():
        if n:
            L.append(f"FAIL {k}: {n}")
            for x in rep["failures"][k][:20]:
                L.append(f"    {x if isinstance(x, str) else json.dumps(x, sort_keys=True)}")
    comp = rep.get("compared") or {}
    na = {F_DASHA: ("chart_dashas", comp.get("chart_dashas", True))}
    for k, n in rep["failure_counts"].items():
        if not n:
            if not na.get(k, ("", True))[1]:
                L.append(f"n/a  {k}: NOT EVALUATED ({na[k][0]} was not compared in this run)")
            else:
                L.append(f"ok   {k}: 0")
    for tname in ("chart_dashas", "panchanga_daily"):
        if comp and not comp.get(tname, True):
            L.append(f"n/a  {tname}: NOT COMPARED in this run (see the NOT CHECKED line)")
    for w in rep["warnings"]:
        L.append(f"WARNING {w}")
    for n in rep["not_checked"]:
        by = ",".join(n["declared_by_lanes"]) or "-"
        L.append(f"NOT CHECKED {n['id']}: {n['what']} | {n['reason']} | declared by: {by} | {n['readback']}")
    if rep["not_checked"]:
        L.append("NOT CHECKED items are never counted as passing" + ("; exit 0 only because --allow-not-checked was passed" if allow_not_checked and v == V_NOT_CHECKED else ""))
    for k, n in rep["by_table_category_change_lane"][:30]:
        L.append(f"   {n:7d}  {k[0]:18s} {k[1]:42s} {k[2]:16s} {k[3]}")
    for tname in ("chart_facts", "chart_divisionals"):
        c = rep["continuous"][tname]
        L.append(f"continuous ({tname}): compared {c['compared']} changed {c['changed']} (to NULL/text {c['to_non_numeric']}) keys appeared {c['keys_appeared']} "
                 f"disappeared {c['keys_disappeared']} timestamp->non-timestamp {c['time_to_non_time']} max |delta| {c['max_abs_delta']:.6g}")
    if rep.get("dashas"):
        L.append("dasha shifts: " + json.dumps({k: (x.get("rows_shifted"), x.get("mode_shift_sec"), x.get("lanes")) for k, x in sorted(rep["dashas"].items()) if x.get("rows_shifted")}, sort_keys=True))
    if rep["chart_id"] == NATIVE and not rep["ALERT_anchor_changed"]:
        L.append("anchors: 7 of 7 OK")
    return L


def _csv(x):
    return [y for y in (x or "").split(",") if y]


def verify_sidecar(path):
    """-> ('ok' | 'absent' | 'mismatch', detail). The .sha256 written by --snapshot must match the file bytes (the baseline is evidence)."""
    sc = path + ".sha256"
    if not os.path.exists(sc):
        return "absent", f"{os.path.basename(path)}.sha256 not found: the snapshot's integrity is unverified"
    want = open(sc).read().split()[:1]
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if not want or want[0].lower() != got:
        return "mismatch", f"{os.path.basename(path)}: sha256 {got[:16]}... does not match its .sha256 sidecar ({(want[0][:16] + '...') if want else 'empty'}): the snapshot was altered or corrupted"
    return "ok", ""


def _write_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)


def cmd_compare(a):
    snap = json.load(gzip.open(a.compare, "rt"))
    try:
        chart_id = normalize_chart_id(snap["meta"]["chart_id"])
    except (ValueError, KeyError) as ex:
        print(f"ERROR: snapshot chart id is not a valid UUID: {ex}", file=sys.stderr)
        return EXIT_FAIL
    hooks, herrs = load_hooks(a.hooks_dir if a.hooks_dir is not None else DEFAULT_HOOKS_DIR, _csv(a.require_lanes))
    extra, sha_state = [], {}
    for label, path in (("snapshot", a.compare), ("against", a.against)):
        if not path:
            continue
        st_, detail = verify_sidecar(path)
        sha_state[label] = st_
        if st_ == "mismatch":
            herrs = list(herrs) + [f"SNAPSHOT INTEGRITY: {detail}"]
        elif st_ == "absent":
            extra.append({"id": f"{label}.sha256", "table": "snapshot", "what": f"integrity of the {label} file", "reason": detail,
                          "readback": "verify the file against the sha256 recorded when it was taken", "declared_by_lanes": []})
    not_compared = {}
    if a.against:
        cur = json.load(gzip.open(a.against, "rt"))
        try:
            other = normalize_chart_id(cur["meta"]["chart_id"])
        except (ValueError, KeyError):
            other = None
        if other != chart_id:
            print(f"ERROR: --against snapshot is for chart {cur['meta'].get('chart_id')}, not {chart_id}", file=sys.stderr)
            return EXIT_FAIL
        sections = {"chart_dashas": ("dashas", a.no_dashas, "--no-dashas"), "panchanga_daily": ("daily", a.no_daily, "--no-daily")}
        have = {}
        for tname, (key, flag, flagname) in sections.items():
            why = flagname if flag else ("the snapshot lacks the section" if key not in snap else ("the --against snapshot lacks the section" if key not in cur else ""))
            have[tname] = not why
            if why:
                not_compared[tname] = f"{tname} not compared in this run: {why}"
        have_dash, have_daily = have["chart_dashas"], have["panchanga_daily"]
    else:
        cur = None
        have_dash = "dashas" in snap and not a.no_dashas
        have_daily = "daily" in snap and not a.no_daily
        for tname, key, flag, flagname, on in (("chart_dashas", "dashas", a.no_dashas, "--no-dashas", have_dash), ("panchanga_daily", "daily", a.no_daily, "--no-daily", have_daily)):
            if not on:
                not_compared[tname] = f"{tname} not compared in this run: " + (flagname if flag else "the snapshot lacks the section")
    out = a.out or a.compare.replace(".json.gz", "") + f"_COMPARE_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    if cur is None:
        try:
            cur = read_state(chart_id, have_dash, have_daily)
        except ReadError as ex:
            rep = {"verdict": "READ_ERROR", "exit_code": EXIT_READ_ERROR, "chart_id": chart_id, "error": str(ex), "meta": {"snapshot": a.compare, "compared_at_utc": datetime.now(timezone.utc).isoformat()}}
            _write_json(out, rep)
            print(f"VERDICT: READ_ERROR   exit {EXIT_READ_ERROR}   {ex}\nreport: {out} | exit {EXIT_READ_ERROR}")
            return EXIT_READ_ERROR
    rep = compare_states(snap, cur, hooks, chart_id, have_dash, have_daily, hook_errors=herrs, not_compared=not_compared, extra_not_checked=extra)
    skipped = sorted(not_compared)
    rep["meta"] = {"snapshot": a.compare, "against": a.against, "snapshot_meta": snap["meta"], "compared_at_utc": datetime.now(timezone.utc).isoformat(),
                   "hook_lanes_loaded": [h["lane"] for h in hooks], "allow_not_checked": bool(a.allow_not_checked),
                   "flags": {"no_dashas": bool(a.no_dashas), "no_daily": bool(a.no_daily), "allow_not_checked": bool(a.allow_not_checked),
                             "i_know_dashas_are_not_compared": bool(a.i_know_dashas_are_not_compared), "require_lanes": _csv(a.require_lanes)},
                   "skipped_sections": skipped, "snapshot_sha256": sha_state}
    code = exit_code(rep, a.allow_not_checked)
    rep["exit_code"] = code
    for ln in render_summary(rep, a.allow_not_checked):
        print(ln)
    _write_json(out, rep)
    print("report:", out, "| exit", code)
    return code


def validate_report(hooks_dir, required=()):
    hooks, errs = load_hooks(hooks_dir, required)
    return {"mode": "validate-hooks", "tool_version": TOOL_VERSION, "hooks_dir": hooks_dir, "required_lanes": list(required),
            "valid_lanes": sorted(h["lane"] for h in hooks), "errors": errs, "verdict": V_FAIL if errs else V_PASS}


def cmd_validate(a):
    rep = validate_report(a.hooks_dir if a.hooks_dir is not None else DEFAULT_HOOKS_DIR, _csv(a.require_lanes))
    print("valid hook lanes:", rep["valid_lanes"])
    for e in rep["errors"]:
        print("HOOK ERROR:", e)
    print(f"VERDICT: {rep['verdict']}   exit {EXIT_FAIL if rep['errors'] else EXIT_PASS}")
    if a.out:
        with open(a.out, "w") as f:
            json.dump(rep, f, indent=1, sort_keys=True)
    return EXIT_FAIL if rep["errors"] else EXIT_PASS


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot")
    ap.add_argument("--compare")
    ap.add_argument("--against", help="with --compare: a second snapshot to compare against instead of reading production (offline)")
    ap.add_argument("--validate-hooks", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--hooks-dir")
    ap.add_argument("--require-lanes")
    ap.add_argument("--no-dashas", action="store_true")
    ap.add_argument("--no-daily", action="store_true")
    ap.add_argument("--allow-not-checked", action="store_true", help="exit 0 on verdict NOT_CHECKED (the NOT CHECKED items are still printed and recorded)")
    ap.add_argument("--i-know-dashas-are-not-compared", action="store_true",
                    help="required to combine --no-dashas / --no-daily with --require-lanes (the S-L1 window must compare dashas and daily)")
    a = ap.parse_args(argv)
    if sum(map(bool, (a.snapshot, a.compare, a.validate_hooks))) != 1:
        ap.error("exactly one of --snapshot / --compare / --validate-hooks")
    if a.against and not a.compare:
        ap.error("--against needs --compare")
    if a.hooks_dir is not None and not a.hooks_dir.strip():
        ap.error("--hooks-dir must not be empty (omit it to use the default S-L1 hooks folder)")
    if a.require_lanes is not None and not _csv(a.require_lanes):
        ap.error("--require-lanes must name at least one lane (omit it to require none)")
    if a.compare and (a.no_dashas or a.no_daily) and a.require_lanes and not a.i_know_dashas_are_not_compared:
        print("REFUSED: --no-dashas / --no-daily together with --require-lanes skips a check the S-L1 lanes need. Compare WITHOUT those flags, or add "
              "--i-know-dashas-are-not-compared (the report then carries NOT CHECKED rows for the skipped tables).", file=sys.stderr)
        return EXIT_REFUSED
    if a.snapshot:
        try:
            resolve(a.snapshot)
        except ValueError as ex:
            ap.error(f"--snapshot: {ex} (use native, abhinandan, kiran or a chart UUID)")
        return cmd_snapshot(a)
    return cmd_compare(a) if a.compare else cmd_validate(a)


if __name__ == "__main__":
    sys.exit(main())
