#!/usr/bin/env python3
"""flip_detector.py: S-L1 class-flip detector and attribution-hook validator (SS N-64 acceptance tool). READ-ONLY. Tooling only: it never writes to the database.

This is a VERDICT-DECIDING tool (it produces the W7 flip report and validates the lane hooks). Its tests live in
platform/scripts/governance/__tests__/test_flip_detector.py (with mutation proof in test_flip_detector_mutations.py).

  --snapshot <native|abhinandan|kiran|CHART_UUID> [--out FILE.json.gz] [--no-dashas] [--no-daily]
        Capture the current production class-level state of one chart (chart_facts incl. verification tier, chart_divisionals,
        chart_dashas) plus the global panchanga_daily table into one gzip JSON: the pre-rebuild baseline. Prints path + sha256.
  --compare <SNAPSHOT.json.gz> [--against OTHER_SNAPSHOT.json.gz] [--out REPORT.json] [--hooks-dir DIR] [--require-lanes a,b,c]
                               [--no-dashas] [--no-daily] [--allow-not-checked]
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
            range), HOOK_ERROR (invalid hook file or a --require-lanes lane with no hook). Warning class (never fails):
            OPTIONAL_ABSENT (an entry marked "optional": true saw no change).
        Exit codes:
            0  verdict PASS, or verdict NOT_CHECKED with --allow-not-checked (the summary still prints every NOT CHECKED item)
            2  verdict FAIL: STOP THE WAVE, GO TO SS
            3  verdict ALERT: a FORENSIC anchor changed (wins over 2 and 4)
            4  verdict NOT_CHECKED and --allow-not-checked was not passed
  --validate-hooks [--hooks-dir DIR] [--require-lanes a,b,c] [--out REPORT.json]     lint the hook files only (no database access); exit 0 or 2

Database access (read-only): set FLIP_READER to an executable that takes one SQL string as argv[1] and prints tab-separated rows, no header
(a psql wrapper that sources your reader credentials is the usual choice). If unset, `psql` from PATH is used with the libpq PG* environment.
Only statements beginning with SELECT are ever sent. Credentials are never read or printed by this script.
Snapshot store: --out, else $FLIP_SNAPSHOT_DIR, else /Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots.

Hook schema, matching rules, NOT CHECKED semantics and the W7 hand read-back SQL: see FLIP_DETECTOR_README.md next to this file.
"""
import sys, os, re, json, gzip, glob, hashlib, argparse, collections, subprocess, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEFAULT_HOOKS_DIR = os.path.join(REPO_ROOT, "00_ARCHITECTURE", "briefs", "suvarna", "exec", "s_l1_attribution_hooks")
TOOL_VERSION = "2.0"
DEFAULT_SNAPSHOT_DIR = "/Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots"
CHARTS = {"native": "482012f1-710e-4a25-994a-93821f5871aa", "abhinandan": "1c826d5a-41cb-4450-b4dc-59d440e5f75a", "kiran": "cb73cd3d-9eba-4220-9902-0de91566e980"}
NATIVE = CHARTS["native"]
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")
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
W_OPTIONAL_ABSENT = "OPTIONAL_ABSENT"
EXIT_PASS, EXIT_FAIL, EXIT_ALERT, EXIT_NOT_CHECKED = 0, 2, 3, 4

# The tier changes this detector cannot machine-check. They are printed on EVERY compare as NOT CHECKED: the detector never reads
# chart_dashas.verification_pass_status nor l1_tajik_varsha_year_lords, so it can neither confirm nor refute a hook about them.
STANDING_NOT_CHECKED = (
    {"id": "chart_dashas.tier", "table": "chart_dashas", "what": "chart_dashas verification_pass_status (mudda and narayana tier)",
     "reason": "the detector compares dasha row sets and start shifts, never the dasha tier column", "readback": "W7 hand read-back: chart_dashas tier SQL in FLIP_DETECTOR_README.md"},
    {"id": "l1_tajik_varsha_year_lords.tier", "table": "l1_tajik_varsha_year_lords", "what": "l1_tajik_varsha_year_lords verification_pass_status",
     "reason": "the table is not one of the four tables the detector reads", "readback": "W7 hand read-back: l1_tajik_varsha_year_lords tier SQL in FLIP_DETECTOR_README.md"},
)


# ------------------------------------------------------------------ read-only reader
def q(sql, retries=4):
    if not re.match(r"^\s*select\b", sql, re.I):
        raise RuntimeError("flip_detector is read-only: only SELECT statements are allowed")
    reader = os.environ.get("FLIP_READER")
    for i in range(retries):
        if reader:
            r = subprocess.run([reader, sql], capture_output=True, text=True)
        else:
            r = subprocess.run(["psql", "-X", "-A", "-F", "\t", "-t", "-c", sql], capture_output=True, text=True)
        if r.returncode == 0:
            break
        if i == retries - 1:
            raise RuntimeError(r.stderr.strip()[:500])
        time.sleep(5 * (i + 1))  # transient connection loss / statement timeout on the shared reader
    return [ln.split("\t") for ln in r.stdout.splitlines() if ln != ""]


def resolve(c):
    return CHARTS.get(c, c)


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
        else:
            if e.get("kind") not in (None, "change"):
                errs.append(f"{w}: 'kind' must be 'change' (default) or 'dasha_shift'")
            cats = e.get("categories")
            if not (isinstance(cats, list) and cats and all(isinstance(c, str) and c for c in cats)):
                errs.append(f"{w}: 'categories' must be a non-empty list of EXACT names (no patterns): fact_category / panchanga_daily column / chart_dashas system_id")
            elif any(re.search(r"[*?\[\]()|^$\\]", c) for c in cats):
                errs.append(f"{w}: 'categories' must be exact names, not patterns")
        for f in ("fact_keys", "ayanamsha_ids"):
            if f in e and not (isinstance(e[f], list) and all(isinstance(x, str) for x in e[f])):
                errs.append(f"{w}: '{f}' must be a list of exact strings")
        ct = e.get("change_types")
        if ct is not None and not (isinstance(ct, list) and ct and set(ct) <= set(CHANGE_TYPES)):
            errs.append(f"{w}: 'change_types' must be a non-empty subset of {CHANGE_TYPES}")
        elif ct and e.get("table") == "chart_dashas" and e.get("kind") != "dasha_shift" and not set(ct) <= set(DASHA_CHANGE_TYPES):
            errs.append(f"{w}: chart_dashas row-set entries may only declare change_types within {DASHA_CHANGE_TYPES} (the detector never produces other kinds there)")
        ec = e.get("expected_count")
        if ec is not None:
            ok = isinstance(ec, dict) and set(ec) <= {"exact", "min", "max"} and ec and all(isinstance(v, int) and v >= 0 for v in ec.values()) and not ("exact" in ec and len(ec) > 1)
            if not ok:
                errs.append(f"{w}: 'expected_count' must be {{\"exact\": n}} or {{\"min\": a, \"max\": b}} (non-negative integers)")
    if "charts" in h and not (isinstance(h["charts"], list) and all(isinstance(c, str) and len(c) >= 8 for c in h["charts"])):
        errs.append(f"{fname}: 'charts' must be a list of chart-id prefixes (>= 8 chars)")
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
    return not h.get("charts") or any(chart_id.startswith(p) for p in h["charts"])


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
def read_state(chart_id, dashas=True, daily=True):
    st = {"chart_facts": []}
    for (ay,) in q(f"select distinct ayanamsha_id from chart_facts where chart_id='{chart_id}' order by 1"):
        st["chart_facts"] += q(f"""select ayanamsha_id, fact_category, fact_subject, fact_key, coalesce(fact_value_text,''), coalesce(fact_value_num::text,''),
                 coalesce(verification_pass_status,'') from chart_facts where chart_id='{chart_id}' and ayanamsha_id='{ay}'""")
    st["divisionals"] = q(f"""select ayanamsha_id, varga, graha, fact_category, fact_key, coalesce(fact_value_text,''), coalesce(fact_value_num::text,''), coalesce(sign,'')
                 from chart_divisionals where chart_id='{chart_id}'""")
    if dashas:
        rows = []
        for ay, sy in q(f"select distinct ayanamsha_id, system_id from chart_dashas where chart_id='{chart_id}' order by 1,2"):
            rows += q(f"""select ayanamsha_id, system_id, level_n, lord_graha, coalesce(kp_sublevel,''), coalesce(kp_sub_lord,''), coalesce(kp_sub_sub_lord,''),
                 start_iso::text, end_iso::text, dasha_row_id::text, coalesce(parent_row_id::text,'') from chart_dashas
                 where chart_id='{chart_id}' and ayanamsha_id='{ay}' and system_id='{sy}'""")
        st["dashas"] = dasha_label_rows(rows)
    if daily:
        st["daily"] = q("select " + ",".join(f"{c}::text" for c in DAILY_COLS) + " from panchanga_daily order by date")
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
    chart_id = resolve(a.snapshot)
    st = read_state(chart_id, not a.no_dashas, not a.no_daily)
    now = datetime.now(timezone.utc).isoformat()
    st["meta"] = {"tool": "flip_detector.py", "tool_version": "1.1", "chart_id": chart_id, "taken_at_utc": now, "db_user": q("select current_user")[0][0], "read_only": True,
                  "counts": {k: len(v) for k, v in st.items() if isinstance(v, list)}}
    d = os.environ.get("FLIP_SNAPSHOT_DIR", DEFAULT_SNAPSHOT_DIR)
    out = a.out or os.path.join(d, f"pre_rebuild_{chart_id[:8]}_{now[:10]}.json.gz")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with gzip.open(out, "wt") as f:
        json.dump(st, f)
    h = hashlib.sha256(open(out, "rb").read()).hexdigest()
    open(out + ".sha256", "w").write(f"{h}  {os.path.basename(out)}\n")
    print(f"snapshot: {out}\nsha256:   {h}\ncounts:   {st['meta']['counts']}\ntaken:    {now} as {st['meta']['db_user']}")


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
        m[k].sort(key=lambda v: (v[0] or "", float(v[1]) if v[1] not in ("", None) else float("-inf")))
    return m


def same_num(a, b):
    if a in ("", None) or b in ("", None):
        return (a in ("", None)) and (b in ("", None))
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a))) + 1e-9


def diff_table(table, A, B, nkey):
    """A,B: key -> sorted occurrence lists [(t, n, tier)]. nkey = (index of fact_category, index of fact_key) inside the key tuple.
    Returns (class_and_tier_changes, continuous_stats)."""
    out = []
    cont = {"compared": 0, "changed": 0, "max_abs_delta": 0.0}
    for k in sorted(set(A) | set(B)):
        a, b = A.get(k), B.get(k)
        cat, key = k[nkey[0]], k[nkey[1]]
        base = {"table": table, "key": list(k), "category": cat, "fact_key": key, "ayanamsha": k[0]}
        if a is None or b is None:
            vals = b if a is None else a
            if {kind_of(v[0], v[1], key) for v in vals} <= {"continuous", "time"}:
                continue  # an appearing/disappearing continuous or timestamp value is not a class change
            out.append({**base, "change": "appeared" if a is None else "disappeared", "value": [list(v[:2]) for v in vals][:2]})
            continue
        if len(a) != len(b):
            out.append({**base, "change": "occurrence_count", "before": len(a), "after": len(b)})
        for x, y in zip(a, b):
            kd = kind_of(x[0], x[1], key)
            if kd == "continuous":
                cont["compared"] += 1
                if not same_num(x[1], y[1]):
                    cont["changed"] += 1
                    try:
                        cont["max_abs_delta"] = max(cont["max_abs_delta"], abs(float(y[1]) - float(x[1])))
                    except (TypeError, ValueError):
                        pass
            elif kd != "time" and ((x[0] or "") != (y[0] or "") or not same_num(x[1], y[1])):
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


def decide_verdict(rep):
    """The ONE place a verdict is decided. ALERT > FAIL > NOT_CHECKED > PASS. PASS only when no failure class is non-empty AND nothing is
    NOT CHECKED. It reads the report's own failure lists, so a failure can never be hidden by a stale 'verdict' field."""
    if rep.get("ALERT_anchor_changed"):
        return V_ALERT
    if any(rep["failures"].get(k) for k in (F_UNDECLARED, F_KIND, F_ABSENT, F_EXPECT, F_DASHA, F_HOOK)):
        return V_FAIL
    if rep.get("not_checked"):
        return V_NOT_CHECKED
    return V_PASS


def compare_states(snap, cur, hooks, chart_id, have_dash=True, have_daily=True, hook_errors=(), standing_not_checked=STANDING_NOT_CHECKED):
    """Pure function (no I/O): the whole comparison. Returns the report dict (JSON-serializable, deterministic ordering).
    `standing_not_checked` is the registry of scopes the detector never compares; production always uses STANDING_NOT_CHECKED."""
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
    rep = {"tool_version": TOOL_VERSION, "chart_id": chart_id, "changes_total": len(changes), "unattributed": len(unattrib),
           "unattributed_examples": unattrib[:50],
           "by_table_category_change_lane": [[list(k), v] for k, v in sorted(by.items(), key=lambda kv: (-kv[1], kv[0]))],
           "continuous": {"chart_facts": cont1, "chart_divisionals": cont2}, "dashas": dinfo,
           "dasha_shift_unattributed": shift_unattrib, "expectations": exp_rows, "expectation_mismatches": exp_bad,
           "failure_counts": {F_UNDECLARED: len(undeclared), F_KIND: len(kind_mm), F_ABSENT: len(absent), F_EXPECT: len(exp_bad),
                              F_DASHA: len(shift_unattrib), F_HOOK: len(hook_errors)},
           "failures": {F_UNDECLARED: [_brief(c) for c in undeclared[:50]], F_KIND: [_brief(c) for c in kind_mm[:50]], F_ABSENT: absent,
                        F_EXPECT: exp_bad, F_DASHA: shift_unattrib, F_HOOK: list(hook_errors)},
           "warnings": warn, "not_checked": not_checked, "changes": changes}
    if chart_id == NATIVE:
        rep["anchors"], rep["ALERT_anchor_changed"] = anchors_check(cur["chart_facts"])
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
    for k, n in rep["failure_counts"].items():
        if not n:
            L.append(f"ok   {k}: 0")
    for w in rep["warnings"]:
        L.append(f"WARNING {w}")
    for n in rep["not_checked"]:
        by = ",".join(n["declared_by_lanes"]) or "-"
        L.append(f"NOT CHECKED {n['id']}: {n['what']} | {n['reason']} | declared by: {by} | {n['readback']}")
    if rep["not_checked"]:
        L.append("NOT CHECKED items are never counted as passing" + ("; exit 0 only because --allow-not-checked was passed" if allow_not_checked and v == V_NOT_CHECKED else ""))
    for k, n in rep["by_table_category_change_lane"][:30]:
        L.append(f"   {n:7d}  {k[0]:18s} {k[1]:42s} {k[2]:16s} {k[3]}")
    c = rep["continuous"]["chart_facts"]
    L.append(f"continuous (chart_facts): compared {c['compared']} changed {c['changed']} max |delta| {c['max_abs_delta']:.6g}")
    if rep["dashas"]:
        L.append("dasha shifts: " + json.dumps({k: (x.get("rows_shifted"), x.get("mode_shift_sec"), x.get("lanes")) for k, x in sorted(rep["dashas"].items()) if x.get("rows_shifted")}, sort_keys=True))
    if rep["chart_id"] == NATIVE and not rep["ALERT_anchor_changed"]:
        L.append("anchors: 7 of 7 OK")
    return L


def _csv(x):
    return [y for y in (x or "").split(",") if y]


def cmd_compare(a):
    snap = json.load(gzip.open(a.compare, "rt"))
    chart_id = snap["meta"]["chart_id"]
    hooks, herrs = load_hooks(a.hooks_dir or DEFAULT_HOOKS_DIR, _csv(a.require_lanes))
    if a.against:
        cur = json.load(gzip.open(a.against, "rt"))
        if cur["meta"]["chart_id"] != chart_id:
            print(f"ERROR: --against snapshot is for chart {cur['meta']['chart_id']}, not {chart_id}", file=sys.stderr)
            return EXIT_FAIL
        have_dash = "dashas" in snap and "dashas" in cur and not a.no_dashas
        have_daily = "daily" in snap and "daily" in cur and not a.no_daily
    else:
        have_dash = "dashas" in snap and not a.no_dashas
        have_daily = "daily" in snap and not a.no_daily
        cur = read_state(chart_id, have_dash, have_daily)
    rep = compare_states(snap, cur, hooks, chart_id, have_dash, have_daily, hook_errors=herrs)
    rep["meta"] = {"snapshot": a.compare, "against": a.against, "snapshot_meta": snap["meta"], "compared_at_utc": datetime.now(timezone.utc).isoformat(),
                   "hook_lanes_loaded": [h["lane"] for h in hooks], "allow_not_checked": bool(a.allow_not_checked)}
    code = exit_code(rep, a.allow_not_checked)
    rep["exit_code"] = code
    for ln in render_summary(rep, a.allow_not_checked):
        print(ln)
    out = a.out or a.compare.replace(".json.gz", "") + f"_COMPARE_{rep['meta']['compared_at_utc'][:19].replace(':', '')}.json"
    with open(out, "w") as f:
        json.dump(rep, f, indent=1, sort_keys=True)
    print("report:", out, "| exit", code)
    return code


def validate_report(hooks_dir, required=()):
    hooks, errs = load_hooks(hooks_dir, required)
    return {"mode": "validate-hooks", "tool_version": TOOL_VERSION, "hooks_dir": hooks_dir, "required_lanes": list(required),
            "valid_lanes": sorted(h["lane"] for h in hooks), "errors": errs, "verdict": V_FAIL if errs else V_PASS}


def cmd_validate(a):
    rep = validate_report(a.hooks_dir or DEFAULT_HOOKS_DIR, _csv(a.require_lanes))
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
    a = ap.parse_args(argv)
    if sum(map(bool, (a.snapshot, a.compare, a.validate_hooks))) != 1:
        ap.error("exactly one of --snapshot / --compare / --validate-hooks")
    if a.against and not a.compare:
        ap.error("--against needs --compare")
    if a.snapshot:
        cmd_snapshot(a)
        return 0
    return cmd_compare(a) if a.compare else cmd_validate(a)


if __name__ == "__main__":
    sys.exit(main())
