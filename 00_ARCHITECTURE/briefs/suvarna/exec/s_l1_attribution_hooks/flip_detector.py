#!/usr/bin/env python3
"""flip_detector.py: S-L1 class-flip detector (SS N-64 acceptance tool). READ-ONLY. Docs/tooling only: it never writes to the database.

  --snapshot <native|abhinandan|kiran|CHART_UUID> [--out FILE.json.gz] [--no-dashas] [--no-daily]
        Capture the current production class-level state of one chart (chart_facts incl. verification tier, chart_divisionals,
        chart_dashas) plus the global panchanga_daily table into one gzip JSON: the pre-rebuild baseline. Prints path + sha256.
  --compare <SNAPSHOT.json.gz> [--out REPORT.json] [--hooks-dir DIR] [--require-lanes a,b,c] [--no-dashas] [--no-daily]
        Read production again, compare, attribute every difference to a lane hook file (all *.json in --hooks-dir, default: the folder
        this script lives in). Exit codes:
            0  clean: no class change, or every class change attributed and every declared expectation met
            2  STOP THE WAVE, GO TO SS: an UNATTRIBUTED class/tier/dasha change, an expectation mismatch, an invalid hook file,
               or a --require-lanes lane with no hook file
            3  ALERT: a FORENSIC anchor changed (native chart only); wins over 2
  --validate-hooks [--hooks-dir DIR] [--require-lanes a,b,c]     lint the hook files only (no database access)

Database access (read-only): set FLIP_READER to an executable that takes one SQL string as argv[1] and prints tab-separated rows, no header
(a psql wrapper that sources your reader credentials is the usual choice). If unset, `psql` from PATH is used with the libpq PG* environment.
Only statements beginning with SELECT are ever sent. Credentials are never read or printed by this script.
Snapshot store: --out, else $FLIP_SNAPSHOT_DIR, else /Users/Dev/suvarna-evidence/TrackI/ephemeris_flip/snapshots.

Hook schema, matching rules and UNATTRIBUTED semantics: see README.md in this folder.
"""
import sys, os, re, json, gzip, glob, hashlib, argparse, collections, subprocess, time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
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
CHANGE_TYPES = ("value", "appeared", "disappeared", "occurrence_count", "tier")
HOOK_FIELDS = {"lane", "ruling", "pr", "description", "charts", "may_change"}
ENTRY_FIELDS = {"table", "kind", "categories", "fact_keys", "ayanamsha_ids", "systems", "change_types", "expected_direction", "expected_count", "shift_range_sec", "note"}


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
        if e.get("table") not in TABLES:
            errs.append(f"{w}: 'table' must be one of {TABLES}")
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
    for p in sorted(glob.glob(os.path.join(hooks_dir, "*.json"))):
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


def entry_matches(e, c):
    if e.get("kind") == "dasha_shift":
        return False
    if c["table"] != e["table"] or c["category"] not in e["categories"]:
        return False
    if e.get("fact_keys") and c.get("fact_key") not in e["fact_keys"]:
        return False
    if e.get("ayanamsha_ids") and c.get("ayanamsha") not in e["ayanamsha_ids"]:
        return False
    if c["change"] not in (e.get("change_types") or CHANGE_TYPES):
        return False
    return True


def applies_to_chart(h, chart_id):
    return not h.get("charts") or any(chart_id.startswith(p) for p in h["charts"])


def attribute_all(changes, hooks, chart_id):
    """Fills c['lanes'] (list of lane names, may be several; empty = UNATTRIBUTED). Returns per-entry observed counts."""
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
    return counts


def expectation_report(hooks, counts, chart_id):
    bad, rows = [], []
    for h in hooks:
        if not applies_to_chart(h, chart_id):
            continue
        for i, e in enumerate(h["may_change"]):
            ec = e.get("expected_count")
            if e.get("kind") == "dasha_shift" or ec is None:
                continue
            n = counts.get((h["lane"], i), 0)
            ok = (n == ec["exact"]) if "exact" in ec else (ec.get("min", 0) <= n <= ec.get("max", 10 ** 12))
            rows.append({"lane": h["lane"], "entry": i, "expected": ec, "observed": n, "ok": ok})
            if not ok:
                bad.append(f"EXPECTATION MISMATCH {h['lane']}[{i}] ({e['table']}:{','.join(e['categories'])}): expected {ec}, observed {n}")
    return rows, bad


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
                for e in h["may_change"]:
                    if e.get("kind") == "dasha_shift" and sy in e["systems"] and (not e.get("ayanamsha_ids") or ay in e["ayanamsha_ids"]):
                        lo, hi = e["shift_range_sec"]
                        inside = [x for x in outside if lo <= x <= hi]
                        if inside and h["lane"] not in lanes:
                            lanes.append(h["lane"])
                        outside = [x for x in outside if not (lo <= x <= hi)]
            rec["lanes"] = lanes
            rec["rows_outside_every_declared_range"] = len(outside)
            if outside:
                shift_unattrib.append(f"{ay}|{sy}: {len(outside)} of {len(moved)} shifted rows lie outside every declared dasha_shift range (mode {rec['mode_shift_sec']} s)")
        info[f"{ay}|{sy}"] = rec
    return changes, info, shift_unattrib


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


def compare_states(snap, cur, hooks, chart_id, have_dash=True, have_daily=True):
    """Pure function (no I/O): the whole comparison. Returns the report dict."""
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
    dinfo, shift_unattrib = None, []
    if have_dash:
        dch, dinfo, shift_unattrib = dasha_diff(snap["dashas"], cur["dashas"], hooks, chart_id)
        changes += dch
    counts = attribute_all(changes, hooks, chart_id)
    exp_rows, exp_bad = expectation_report(hooks, counts, chart_id)
    unattrib = [c for c in changes if not c["lanes"]]
    by = collections.Counter((c["table"], c["category"], c["change"], ",".join(c["lanes"]) or "UNATTRIBUTED") for c in changes)
    rep = {"changes_total": len(changes), "unattributed": len(unattrib), "unattributed_examples": unattrib[:50],
           "by_table_category_change_lane": [[list(k), v] for k, v in by.most_common()],
           "continuous": {"chart_facts": cont1, "chart_divisionals": cont2}, "dashas": dinfo,
           "dasha_shift_unattributed": shift_unattrib, "expectations": exp_rows, "expectation_mismatches": exp_bad, "changes": changes}
    if chart_id == NATIVE:
        rep["anchors"], rep["ALERT_anchor_changed"] = anchors_check(cur["chart_facts"])
    else:
        rep["ALERT_anchor_changed"] = False
    return rep


def exit_code(rep, hook_errors):
    if rep and rep.get("ALERT_anchor_changed"):
        return 3
    if hook_errors or (rep and (rep["unattributed"] or rep["dasha_shift_unattributed"] or rep["expectation_mismatches"])):
        return 2
    return 0


def cmd_compare(a):
    snap = json.load(gzip.open(a.compare, "rt"))
    chart_id = snap["meta"]["chart_id"]
    hooks, herrs = load_hooks(a.hooks_dir or HERE, [x for x in (a.require_lanes or "").split(",") if x])
    have_dash = "dashas" in snap and not a.no_dashas
    have_daily = "daily" in snap and not a.no_daily
    cur = read_state(chart_id, have_dash, have_daily)
    rep = compare_states(snap, cur, hooks, chart_id, have_dash, have_daily)
    rep.update({"snapshot": a.compare, "snapshot_meta": snap["meta"], "compared_at_utc": datetime.now(timezone.utc).isoformat(), "chart_id": chart_id,
                "hook_lanes_loaded": [h["lane"] for h in hooks], "hook_errors": herrs})
    code = exit_code(rep, herrs)
    if code == 3:
        print("ALERT: A FORENSIC ANCHOR CHANGED. STOP AND GO TO SS.")
        for r in rep["anchors"]:
            if not r["ok"]:
                print("   ", r)
    for e in herrs:
        print("HOOK ERROR:", e)
    print(f"chart {chart_id}: snapshot {snap['meta']['taken_at_utc']}  vs  now;  hook lanes: {rep['hook_lanes_loaded']}")
    print(f"changes (class + tier + dasha row-set): {rep['changes_total']}   UNATTRIBUTED: {rep['unattributed']}" + ("   <-- STOP THE WAVE, GO TO SS" if rep["unattributed"] else ""))
    for k, v in rep["by_table_category_change_lane"][:30]:
        print(f"   {v:7d}  {k[0]:18s} {k[1]:42s} {k[2]:16s} {k[3]}")
    for x in rep["dasha_shift_unattributed"]:
        print("UNATTRIBUTED DASHA SHIFT:", x)
    for x in rep["expectation_mismatches"]:
        print(x)
    c = rep["continuous"]["chart_facts"]
    print(f"continuous (chart_facts): compared {c['compared']} changed {c['changed']} max |delta| {c['max_abs_delta']:.6g}")
    if rep["dashas"]:
        print("dasha shifts:", {k: (v.get("rows_shifted"), v.get("mode_shift_sec"), v.get("lanes")) for k, v in rep["dashas"].items() if v.get("rows_shifted")})
    if chart_id == NATIVE and not rep["ALERT_anchor_changed"]:
        print("anchors: 7 of 7 OK")
    out = a.out or a.compare.replace(".json.gz", "") + f"_COMPARE_{rep['compared_at_utc'][:19].replace(':', '')}.json"
    json.dump(rep, open(out, "w"), indent=1)
    print("report:", out, "| exit", code)
    sys.exit(code)


def cmd_validate(a):
    hooks, herrs = load_hooks(a.hooks_dir or HERE, [x for x in (a.require_lanes or "").split(",") if x])
    print("valid hook lanes:", [h["lane"] for h in hooks])
    for e in herrs:
        print("HOOK ERROR:", e)
    sys.exit(2 if herrs else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot")
    ap.add_argument("--compare")
    ap.add_argument("--validate-hooks", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--hooks-dir")
    ap.add_argument("--require-lanes")
    ap.add_argument("--no-dashas", action="store_true")
    ap.add_argument("--no-daily", action="store_true")
    a = ap.parse_args()
    if sum(map(bool, (a.snapshot, a.compare, a.validate_hooks))) != 1:
        ap.error("exactly one of --snapshot / --compare / --validate-hooks")
    if a.snapshot:
        cmd_snapshot(a)
    elif a.compare:
        cmd_compare(a)
    else:
        cmd_validate(a)
