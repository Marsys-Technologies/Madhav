#!/usr/bin/env python3
"""census_postprocess.py -- the smallest census post-processor (owner decision N-152: one line per asset, no ledger).

Reads the stamped census files of ONE layer set at ONE registry revision and writes two outputs (each as .md + .json, deterministic,
the only date is the --date argument, no clock is read):
  CERTIFIED_LIST  one line per CERTIFIED asset: asset, revision, census file ref (name + sha256 prefix), measured-PASS count,
                  ruled-N/A count, date, known findings text (from the optional --findings JSON, asset -> text).
  FIX_LIST        every other asset: each non-PASS, non-ruled-N/A criterion with verdict and census cause text, grouped by asset then
                  by cause class (CAUSE_CLASSES below; unknown text is a visible 'unclassified', never dropped).
CERTIFIED = every rollup criterion is PASS, or an N/A that carries a rule_id AND a decision (a ruled N/A) (N-154: Build.history too).
Never certified with a FAIL / PARTIAL / NO_DETECTOR / INCONCLUSIVE / unstamped / undecided cell. Build.history is read as the census
states it (not re-implemented here); tool_commit / tool_dirty are recorded in the header, never refused on.  REFUSES (exit 2, one message) on: unstamped input, a synthetic/scratch/scoped census, mixed
revisions / fingerprints / databases, a missing, extra or duplicate layer, a head/rollup stamp mismatch, duplicate assets, an asset in
the rollup but not in the layer list (or vice versa), a non-uniform criterion set, or an asset count differing from --assets-expected.
Read-only: no database, no network.  Usage: census_postprocess.py --census F [F ...] --date YYYY-MM-DD --out-dir D
[--layers L0,L1,L2] [--assets-expected 82] [--criteria-expected 25] [--findings findings.json]"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys

PASS, NA = "PASS", "N/A"
SCRATCH_LABEL = re.compile(r"synthetic|scratch|fixture|sandbox", re.I)
SCRATCH_DB = re.compile(r"^(nt_|scratch|synthetic|fixture|sandbox|disposable)", re.I)
UNCLASSIFIED = "(?) unclassified"
# Build.completion PASS that rests on count equality alone: the cell's measured text carries no integrity statement (asset_census `_completion_integrity` appends
# "the declared integrity_check_sql holds (...)" to a PASS only when the asset declares an integrity_check_sql and it ran and held). REPORTING ONLY: no verdict moves.
BUILD_COMPLETION = "Build.completion"
INTEGRITY_HOLDS = "integrity_check_sql holds"
COUNTS_ONLY_LIMITATION = "Build.completion: counts only (no integrity statement)"
# Carr ceilings: a ruled N/A under one of these rule ids certifies the asset AT A CEILING; the limitation is shown on its line (SS N-156)
RATIFIED_LABEL = "Ratified judgment (N-235)"
CEILING_RULES = {"Carr.D3#measured:single-derivation": "Carr: single-derivation",
                 "Carr.D1#measured:transcription-not-verified": "D1: unverified transcription",
                 # N-177 (SS 2026-10-07): the closed-list residual UNSOURCED_DECLARED of Ldgr.source_presence: a CHECKED, declared "no traceable source" reading is a ruled N/A that certifies the asset AT a ceiling, exactly as the Carr ceilings
                 "Ldgr.source_presence#measured:unsourced-declared": "Ldgr: unsourced (declared)",
                 # SS N-235: a ratified-judgment seed (system-authored constants / counts / priors): Carr.D1/D2/D3 all read N/A by `ratified_judgment`; the asset is certified AT this ceiling, named on its line
                 "Carr.D1#measured:ratified_judgment": RATIFIED_LABEL, "Carr.D2#measured:ratified_judgment": RATIFIED_LABEL, "Carr.D3#measured:ratified_judgment": RATIFIED_LABEL}

# Ordered cause-class table: first row whose predicate holds wins.  (class, test on (criterion, verdict, state, text))
CAUSE_CLASSES = (
    ("(b) declaration missing: prose_fields", lambda c, v, s, t: "prose_fields" in t and "undeclared" in t),
    ("(c) ruling or declaration", lambda c, v, s, t: "N/A rule undecided" in t or "applicability undecidable" in t
        or v == NA),    # only unruled N/A cells are classified (a ruled one never reaches here): it needs a ruling
    ("(d) needs a rebuild", lambda c, v, s, t: "unclassified NULL" in t or "no recorded duration" in t),
    ("(a) detector/declaration (carriage)", lambda c, v, s, t: c.startswith("Carr.") and "not measured (applies)" in t),
    ("(a) detector", lambda c, v, s, t: v == "PARTIAL" and (   # by-design PARTIAL ("never PASS" / "structural only"): a missing PASS path, not a defect
        "never PASS" in t or "never reads PASS" in t or "structural only" in t)),
    ("(e) defect in data or code", lambda c, v, s, t: v in ("FAIL", "PARTIAL") and s == "MEASURED"),
    ("(a) detector", lambda c, v, s, t: v in ("NO_DETECTOR", "FAIL", "PARTIAL")),   # the catch-all for a known non-passing verdict
)
CLASS_ORDER = [c for c, _ in CAUSE_CLASSES if c != "(a) detector"][:5] + ["(a) detector", UNCLASSIFIED]


class Refused(Exception):
    pass


def classify(criterion: str, verdict: str, state: str, text: str) -> str:
    for name, test in CAUSE_CLASSES:
        if test(criterion, verdict, state, text or ""):
            return name
    return UNCLASSIFIED      # e.g. INCONCLUSIVE or an unknown verdict: visible, never dropped


# ───────────────────────── N-268 (owner direction via SS): the certification bar with NAMED ceilings and disclosure gaps ─────────────────────────
# bar n268: an asset is CERTIFIED when nothing is found wrong and every unverifiable point is NAMED on its certificate. The list below is CLOSED and CHECKED: each pattern is matched on the cell's OWN evidence text (its cause / measured text),
# anchored from the first to the last character; a text with ANY other finding, an unknown segment, a hidden (truncated) part, or another shape stays a BLOCKER. No criterion is blanket-released: a cell is named only when its
# whole text is the closed shape. The cell stays PARTIAL / NO_DETECTOR in every count (nothing is converted to PASS); only the certification verdict changes. bar strict = the older reading (every cell PASS or a ruled N/A).
BAR_N268, BAR_STRICT = "n268", "strict"
BAR_LABELS = {BAR_N268: "bar: N-268 (named ceilings and disclosure gaps)", BAR_STRICT: "bar: strict (every criterion PASS or a ruled N/A)"}
KIND_CEILING, KIND_GAP = "ceiling", "gap"
_LIT = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"")


def _strip_lits(s: str) -> str:
    return _LIT.sub("<S>", s)


def _plural(n: int, w: str) -> str:
    return f"{n} {w}"


# (a) Vocab.alias: every whole value found is canonical; the only caveats are embedded text / a bounded sample / unread columns (leaf cap, statement timeout)
_V_PRE = re.compile(r"vocabulary values found by value in (\d+) column\(s\): (.+?); every whole value found is canonical(?:, but: (.+))?", re.S)
_V_ITEM = r"[\w.]+ \([a-z]+(?:/[a-z]+)*: (?:short aliases only|[^;()]+)(?:; registered bg_ontology aliases, counted canonical: [^;()]+)?\)"
_V_FOUND = re.compile(rf"{_V_ITEM}(?:, {_V_ITEM})*")
_V_BAD_WORDS = re.compile(r"non-canonical|not canonical|MIXED|mixed|unregistered|variant|FAIL|short alias only|one short alias|NO rows|vacuous", re.I)
_V_SAMPLE = re.compile(r"([\w.]+) was read by a bounded sample only")
_V_EMB_ITEM = re.compile(r"([\w.]+) \(<S>(?:, <S>)*\)")
_V_UNREAD = (re.compile(r"([\w.]+): part of the column could not be sampled \(leaf cap \d+ reached\)"),
             re.compile(r"([\w.]+): the rest of the column was not read \(the existence probe exceeded the statement timeout: ERROR: canceling statement due to statement timeout\)"))


def m_vocab(aid: str, text: str):
    t = text.replace("alias(es)", "aliases")
    m = _V_PRE.fullmatch(t)
    if not m or m.group(3) is None:
        return None
    n, found, tail = int(m.group(1)), m.group(2), m.group(3)
    if _V_BAD_WORDS.search(found) or not _V_FOUND.fullmatch(found) or len(re.findall(r"(?:^|, )[\w.]+ \(", found)) != n:
        return None
    emb, samp, unread, mode = [], [], [], None
    for seg in _strip_lits(tail).split("; "):
        if seg.startswith("embedded vocabulary, spelling unchecked: "):
            seg, mode = seg[len("embedded vocabulary, spelling unchecked: "):], "emb"
        elif seg.startswith("unread: "):
            seg, mode = seg[len("unread: "):], "unread"
        elif _V_SAMPLE.fullmatch(seg):
            samp.append(_V_SAMPLE.fullmatch(seg).group(1))
            mode = None
            continue
        if mode == "emb" and _V_EMB_ITEM.fullmatch(seg):
            emb.append(_V_EMB_ITEM.fullmatch(seg).group(1))
        elif mode == "unread" and any(r.fullmatch(seg) for r in _V_UNREAD):
            unread.append(next(r.fullmatch(seg) for r in _V_UNREAD if r.fullmatch(seg)).group(1))
        else:
            return None                                     # MIXED families, a short alias, a non-canonical clause, a zero-row table, an unknown segment: a finding, not a caveat
    if not (emb or samp or unread):
        return None
    parts = ["every whole value found is canonical; not verified:"]
    if emb:
        parts.append(f"embedded text, spelling unchecked, in {', '.join(emb)};")
    if samp:
        parts.append(f"bounded sample only: {', '.join(samp)};")
    if unread:
        parts.append(f"unread: {', '.join(unread)};")
    return " ".join(parts).rstrip(";")


# (b) Build.dag: an acyclic, fully existing edge set whose ONLY issue is that the parse is incomplete (dynamic table names / SQL not traced to a literal)
_D_PRE = re.compile(r"(\d+) declared edge\(s\); exists: all \1 are active registry assets \(every layer\); cycle: (\S+) is on no dependency cycle \(registry-wide graph\); "
                    r"reads-match: \d+ resolved read\(s\) of other assets' tables are covered by declared edges or exempt \(see below\), but the parse is incomplete — (.+)", re.S)
_D_ITEMS = (re.compile(r"[\w./-]+\.py:\d+: a table is named dynamically \(<S>\), so the read is not resolvable"),
            re.compile(r"[\w./-]+\.py:\d+: execute\(\) is given SQL that is not traced to a literal \(<S>\), so what it reads is not resolvable"))
_D_BEDROCK = re.compile(r"\d+ read\(s\) of bedrock-named table\(s\) owned only by L0 assets \([a-z_]+(?:, [a-z_]+)*\) need no declared edge \(dag_edge_guard exemption list; stricter than the guard, "
                        r"which exempts by table name alone; provisional interpretation of T4, to be confirmed at the J1 review\)")


def m_dag(aid: str, text: str):
    m = _D_PRE.fullmatch(text)
    if not m or m.group(2) != aid:
        return None
    n_parse = 0
    for seg in _D_BEDROCK.sub("<BEDROCK>", _strip_lits(m.group(3))).split("; "):      # the bedrock note carries its own '; ' inside a parenthesis: protect the exact known wording first
        if any(r.fullmatch(seg) for r in _D_ITEMS):
            n_parse += 1
        elif seg != "<BEDROCK>":
            return None                                     # a SOFT-tier chart_facts note, a missing edge, a cycle, an unknown segment: not the closed shape
    if not n_parse:
        return None
    return f"dependency graph acyclic and every declared edge exists; the read parse is incomplete at {n_parse} dynamic site(s) of the shared helper (not resolvable by static parse)"


# (c) Narr.lint: only allowlisted violations
_L = re.compile(r"only allowlisted narration lint violation\(s\) in scope: ([a-z][a-z-]* platform/[\w./-]+\.py:\d+(?:; [a-z][a-z-]* platform/[\w./-]+\.py:\d+)*)")


def m_lint(aid: str, text: str):
    m = _L.fullmatch(text)
    if not m:
        return None
    rules = sorted({x.split(" ", 1)[0] for x in m.group(1).split("; ")})
    return f"only allowlisted narration lint violations ({', '.join(rules)}; {len(m.group(1).split('; '))} site(s))"


# (d) Narr.checkable: only the whole-table upper-bound count note
_C = re.compile(r"checkable rows per declared entry: ([^\s,;=]+=\d+(?:, [^\s,;=]+=\d+)*); the count is a whole-table upper bound \(count_sql unparseable, unshared table that carries chart_id\): rows of other charts may count")


def m_checkable(aid: str, text: str):
    return "checkable-row counts are whole-table upper bounds (count_sql unparseable): rows of other charts may count" if _C.fullmatch(text) else None


# (f) Dens.served: the answer is served but no tier column is in its served select (it does not state its verification level); nothing else in the text
_DS_PRE = re.compile(r"STRUCTURAL: \d+ module\(s\) reach it by code: [^;]+; a referencing capability declares density_contract but (.+)", re.S)
_DS_ITEM = re.compile(r"[\w./\[\]-]+\.ts: no tier column in its served select")


def m_dens(aid: str, text: str):
    m = _DS_PRE.fullmatch(text)
    if not m:
        return None
    items = m.group(1).split("; ")
    if not all(_DS_ITEM.fullmatch(i) for i in items):
        return None
    return f"served but does not state its verification level: no tier column in the served select of {', '.join(i.split(':', 1)[0] for i in items)}"


# (g) Null.blank_rows / Null.schema_default: no blank or placeholder row found; the writer scan's ONLY findings are complete, untruncated constant_write literals
_N_ITEM_START = re.compile(r"; (?=[^\s;]+ [\w./-]+\.py:\d+ \()")
_N_ITEM = re.compile(r"[^\s;]+ [\w./-]+\.py:\d+ \(constant_write\) the column is written a literal: .+", re.S)
_N_SCAN = r" and the scan is not clean; writer scan NOT clean - literal problems: (.+)"
_N_BLANK = re.compile(r"no blank or placeholder row among the checkable prose rows; schema defaults are read by Null\.schema_default and writer literal fallbacks and constant columns are not measured, "
                      r"so the writer source is scanned for them \(E5\.7\)" + _N_SCAN, re.S)
_N_DEFAULT = re.compile(r"no schema default on the declared prose column\(s\) [\w.$\[\]*, ]+; writer literal fallbacks and constant columns are not measured here, so the writer source is scanned for them "
                        r"\(E5\.7\)" + _N_SCAN, re.S)


def _null_constants(rx, text: str, lead: str):
    m = rx.fullmatch(text)
    if not m:
        return None
    body = m.group(1)
    if body.rstrip().endswith("...") or "| unresolved" in body or "literal_fallback" in body or "outside every declared waiver" in body or "scan finding(s)" in body:
        return None                                         # truncated listing / unresolved write path / another finding class: not provably only constant_write
    items = _N_ITEM_START.split(body)
    if not all(_N_ITEM.fullmatch(i) for i in items):
        return None
    return f"{lead}; the writer scan reports {len(items)} constant_write literal(s) of curated text (disclosed, not a blank or placeholder)"


def m_null_blank(aid: str, text: str):
    return _null_constants(_N_BLANK, text, "no blank or placeholder row among the checkable prose rows")


def m_null_default(aid: str, text: str):
    return _null_constants(_N_DEFAULT, text, "no schema default on the declared prose columns")


# (e) NO_DETECTOR cells classed '(a) detector' whose whole text states only that the instrument cannot measure: printed as 'not measurable: <reason>'
_NM = (
    ("Build.completion", "census-role-denied", "the integrity SQL needs an object the census role may not read (measured at build time under the runner role)",
     re.compile(r"NO_DETECTOR — integrity not measurable under the census role: ERROR: \d+: permission denied for function \w+; denied object: function \w+; the asset's integrity SQL needs objects the census role may not read\. "
                r"Declared way to measure it: .*do NOT widen the census role \(it is NOT widened, and this is not a verdict on the data\) \[integrity_check_sql sha256:[0-9a-f]+, [\d.]+s\]; counts: rows_written=(\d+) = live=\1 \([^()]*\)", re.S)),
    ("Build.completion", "view-object", "a view: completion consistency is not measurable for a view",
     re.compile(r"NO_DETECTOR — view: live=\d+ \(counted by the census from the view \w+ \(chart-scoped\); the registry count_sql is a constant \(SELECT \d+ AS count\); chart [0-9a-f]{8}\); "
                r"build record rows_written=\d+ counts the view object, not rows — completion consistency is not measurable for a view")),
    ("Dens.served", "no-served-select", "no served SELECT of its table was found: whether it is served cannot be told by code",
     re.compile(r"NO_DETECTOR — \d+ module\(s\) reach it by code: [^;]+, but no served `SELECT \.\.\. FROM` its table was found \(no served select\): whether it is served cannot be told by code"
                r"(?:; also a served select outside the scanned serving roots \(not graded\): [^;]+)?")),
    ("Dens.served", "shared-table", "only a shared table is referenced: the served surface cannot be attributed to it by code",
     re.compile(r"NO_DETECTOR — only a table other assets share \((\w+)\) is referenced, by \d+ module\(s\): [^;]+; the served surface cannot be attributed to \1 by code \(never the closable N/A\)")),
    ("Earn.build_record", "receipt-overwritten", "the named run's receipt was overwritten by a newer one (destroyed by design, not contradicted)",
     re.compile(r"NO_DETECTOR — named run [0-9a-f]{8}'s own receipt is gone: a NEWER probe-shaped receipt overwrote it \(receipts are upserted, only the latest survives\), "
                r"so the declared probe cannot be verified: the evidence was destroyed by design, not contradicted")),
    ("Earn.build_record", "skip-no-delta", "no build was due (healthy skip_no_delta): nothing to exercise",
     re.compile(r"healthy non-execution \(skip_no_delta\) — no build was due; latest attempt at any chart \(global build record\): run [0-9a-f]{8} complete/skip_no_delta \(\d{4}-\d{2}-\d{2}\)")),
    ("Vocab.alias", "empty-owned-tables", "the owned tables hold no rows in any candidate column (vacuous)",
     re.compile(r"NO_DETECTOR — the owned table\(s\) [\w, ]+ hold no rows in any candidate column \(\d+ column\(s\) read\): vacuous, not N/A")),
    ("Vocab.identity", "empty-table", "the table is empty: uniqueness is vacuous on 0 rows",
     re.compile(r"NO_DETECTOR — table empty: uniqueness under \([\w, ]+\) is vacuous on 0 rows")),
    ("Ldgr.source_presence", "empty-table", "the table has no rows: the source reading is vacuous",
     re.compile(r"row-level K1 source: NO_DETECTOR — \w+ has no rows: classical_citation names a source on 0 rows \(vacuous\)")),
    ("Ldgr.source_presence", "statement-timeout", "the existence read exceeded the statement timeout: no source verdict was reached",
     re.compile(r"NO_DETECTOR — the existence read of \w+ \(first violating row, bounded sample, no counting\) also exceeded the statement timeout \(ERROR: canceling statement due to statement timeout\): "
                r"no source verdict was reached, so this is neither a PASS nor a FAIL; the check needs a longer per-check timeout or a narrower read")),
)

NAMED_PARTIALS = (   # (pattern id, criterion, kind, matcher): verdict PARTIAL only
    ("vocab-canonical-with-caveats", "Vocab.alias", KIND_CEILING, m_vocab),
    ("dag-parse-incomplete", "Build.dag", KIND_CEILING, m_dag),
    ("narr-lint-allowlisted", "Narr.lint", KIND_CEILING, m_lint),
    ("narr-checkable-upper-bound", "Narr.checkable", KIND_CEILING, m_checkable),
    ("dens-no-tier-column", "Dens.served", KIND_GAP, m_dens),
    ("null-blank-constant-write", "Null.blank_rows", KIND_GAP, m_null_blank),
    ("null-default-constant-write", "Null.schema_default", KIND_GAP, m_null_default),
)
NAMED_PATTERN_IDS = tuple(p[0] for p in NAMED_PARTIALS) + tuple(f"not-measurable:{c}:{i}" for c, i, _, _ in _NM)


def named_item(aid: str, name: str, ck: dict):
    """The NAMED ceiling / disclosure gap a non-passing cell is, or None (it stays a blocker). CHECKED on the cell's own evidence text, anchored whole; PARTIAL patterns need verdict PARTIAL, the not-measurable shapes need
    verdict NO_DETECTOR AND the cause class '(a) detector'."""
    text, v = ck.get("cause"), ck.get("v")
    if not isinstance(text, str) or not text:
        return None
    if v == "PARTIAL":
        for pid, crit, kind, fn in NAMED_PARTIALS:
            if crit == name:
                why = fn(aid, text)
                if why:
                    return dict(criterion=name, kind=kind, pattern=pid, reason=why)
        return None
    if v == "NO_DETECTOR" and classify(name, v, ck.get("state") or "", text) == "(a) detector":
        for crit, pid, why, rx in _NM:
            if crit == name and rx.fullmatch(text):
                return dict(criterion=name, kind=KIND_CEILING, pattern=f"not-measurable:{name}:{pid}", reason=f"not measurable: {why}")
    return None


def is_counts_only_completion(cells: dict) -> bool:
    """True when the asset's Build.completion cell is a PASS whose measured text states no integrity result (count equality alone)."""
    ck = cells.get(BUILD_COMPLETION)
    return bool(ck) and ck.get("v") == PASS and INTEGRITY_HOLDS not in str(ck.get("cause") or "")


# N-233 R3 (SS ruling): the CLOSED vocabulary of RULED RESIDUALS. A residual is a NAMED, declared way for a cell to read "no stronger reading exists" without a defect: it counts as a ruled N/A (not a blocker) for certification, and
# ONLY a residual in this closed list does (the list is the engine's own: asset_census.NA_RULE_DECISIONS holds every rule id with its decision text; the residuals below are the subset the certified list names). A residual is
# CHECKED here, never trusted: the cell must be N/A (a NO_DETECTOR that carries a residual-looking rule id is still a NO_DETECTOR), its rule id must be in the engine's closed list AND belong to its own criterion, and its
# decision text must be the engine's text for that rule. An undeclared NO_DETECTOR, a residual rule id the engine does not declare, a forged decision, or a residual on another criterion's cell blocks.
RULED_RESIDUALS = {
    "Carr.D1#measured:transcription-not-verified": "D1: unverified transcription",
    "Carr.D2#measured:no-per-witness-values": "D2: no per-witness values",
    "Carr.D3#measured:single-derivation": "D3: single derivation (no second method)",
    "Ldgr.source_presence#measured:unsourced-declared": "Ldgr: unsourced (declared)",
    "Carr.D1#measured:ratified_judgment": "D1: ratified judgment (N-235)",
    "Carr.D2#measured:ratified_judgment": "D2: ratified judgment (N-235)",
    "Carr.D3#measured:ratified_judgment": "D3: ratified judgment (N-235)",
}
_ENGINE_RULES: dict | None = None


def engine_rule_decisions() -> dict:
    """The engine's closed N/A rule table (asset_census.NA_RULE_DECISIONS: rule id -> decision text), loaded once, by file path (no database, no network: the module only defines tables at import)."""
    global _ENGINE_RULES
    if _ENGINE_RULES is None:
        mod = sys.modules.get("asset_census")
        if mod is None:
            import importlib.util
            spec = importlib.util.spec_from_file_location("asset_census", pathlib.Path(__file__).resolve().with_name("asset_census.py"))
            mod = importlib.util.module_from_spec(spec)
            sys.modules["asset_census"] = mod
            spec.loader.exec_module(mod)
        _ENGINE_RULES = dict(mod.NA_RULE_DECISIONS)
    return _ENGINE_RULES


def ruled_na_problem(name: str, ck: dict) -> str | None:
    """None when `ck` (the cell of criterion `name`) is a RULED N/A the engine's closed list backs; else why it is not (for the fix list / the tests)."""
    if ck.get("v") != NA:
        return f"verdict {ck.get('v')} is not N/A"
    rid, dec = ck.get("rule_id"), ck.get("decision")
    if not rid or not dec:
        return "an N/A without a rule id and a decision is unruled"
    rules = engine_rule_decisions()
    if rid not in rules:
        return f"rule id {rid!r} is not in the engine's closed N/A rule list"
    if not str(rid).startswith(name + "#"):
        return f"rule id {rid!r} is not a rule of criterion {name}"
    if dec != rules[rid]:
        return f"the decision text of {rid!r} is not the engine's text for it"
    return None


def is_ruled_na(ck: dict, name: str | None = None) -> bool:
    """A ruled N/A: N/A with a rule id and a decision (N-154); with `name` (every caller in this module that knows the criterion) it is also CHECKED against the engine's closed rule list (N-233 R3)."""
    if name is None:
        return ck.get("v") == NA and bool(ck.get("rule_id")) and bool(ck.get("decision"))
    return ruled_na_problem(name, ck) is None


def load(path: pathlib.Path, overlay: bool = False) -> dict:
    """Validate one census file; returns dict(layer, head, assets{aid: {criterion: cell+cause}}, ref). `overlay=True` (N-268) accepts a SCOPED delta census (head / rollup carry `scope`) and REQUIRES it to be scoped;
    a full census is refused there, and a scoped one is refused everywhere else."""
    raw = pathlib.Path(path).read_bytes()
    try:
        d = json.loads(raw)
    except ValueError:
        raise Refused(f"{path.name}: not valid JSON")
    found = [k for k in d if re.fullmatch(r"L\d", k)] if isinstance(d, dict) else []
    if len(found) != 1 or not isinstance(d.get("rollup"), dict):
        raise Refused(f"{path.name}: expected exactly one layer key and a rollup (found layers {found})")
    layer, head, roll = found[0], d[found[0]], d["rollup"]
    if d.get("synthetic") or d.get("scratch") or head.get("synthetic") or head.get("scratch") \
            or SCRATCH_LABEL.search(str(d.get("label", "")) + str(head.get("label", "")) + str(head.get("census_label", ""))) \
            or (not overlay and ("scope" in head or "scope" in roll)):
        raise Refused(f"{path.name}: synthetic, scratch or scoped census (label); a certified list is read from full production censuses")
    if overlay and not ("scope" in head and "scope" in roll):
        raise Refused(f"{path.name}: an overlay file must be a SCOPED delta census (no scope in its head / rollup)")
    ident = head.get("db_identity")
    if not (isinstance(ident, dict) and ident.get("schema") and ident.get("database") and ident.get("system_id_sha256")):
        raise Refused(f"{path.name}: unstamped (no usable db_identity stamp)")
    if SCRATCH_DB.search(ident["database"]):
        raise Refused(f"{path.name}: db_identity names a scratch database ({ident['database']})")
    rev, fp = head.get("registry_revision"), head.get("registry_fingerprint")
    if rev is None or not fp:
        raise Refused(f"{path.name}: unstamped (no registry_revision / registry_fingerprint in the layer head)")
    if (roll.get("registry_revision"), roll.get("registry_fingerprint")) != (rev, fp):
        raise Refused(f"{path.name}: the layer stamp (revision {rev}, fingerprint {str(fp)[:12]}) does not match the file's own rollup")
    rl = (roll.get("layers") or {}).get(layer)
    if set(roll.get("layers") or {}) != {layer} or not isinstance(rl, dict):
        raise Refused(f"{path.name}: the rollup does not cover exactly layer {layer}")
    listed = [a.get("asset_id") for a in head.get("assets") or []]
    if len(set(listed)) != len(listed):
        raise Refused(f"{path.name}: duplicate asset in the layer list")
    if set(listed) != set(rl):
        diff = sorted(set(listed) ^ set(rl))
        raise Refused(f"{path.name}: asset(s) {diff[:5]} are in only one of the layer list and the rollup")
    meas = {a["asset_id"]: a.get("measurements") or {} for a in head["assets"]}
    assets = {}
    for aid, gates in rl.items():
        cells = {}
        for g in gates.values():
            if (g.get("registry_revision"), g.get("registry_fingerprint")) != (rev, fp):
                raise Refused(f"{path.name}: {aid} gate {g.get('gate')} is unstamped or stamped with another revision/fingerprint")
            for ck in g.get("checks") or []:
                name = ck["criterion"]
                if name in cells:
                    raise Refused(f"{path.name}: {aid} has {name} twice")
                m = (meas[aid].get(name) or {}).get("measured") if ck.get("state") == "MEASURED" else None
                cells[name] = dict(ck, cause=m if isinstance(m, str) and m else (ck.get("reason") or ""))
        assets[aid] = cells
    return dict(layer=layer, rev=rev, fp=fp, scope_assets=sorted((head.get("scope") or {}).get("assets") or []), tool=(head.get("tool_commit"), head.get("tool_dirty")), db=(ident["database"], ident["system_id_sha256"]), assets=assets,
                ref=f"{path.name}#{hashlib.sha256(raw).hexdigest()[:12]}")


def build(files: list[pathlib.Path], layers: list[str], expected: int | None, criteria_expected: int | None,
          date: str, findings: dict, bar: str = BAR_N268, overlays: list | None = None) -> dict:
    if bar not in BAR_LABELS:
        raise Refused(f"unknown --bar {bar!r} (one of {sorted(BAR_LABELS)})")
    loaded = [load(pathlib.Path(f)) for f in files]
    seen = [x["layer"] for x in loaded]
    for l in sorted(set(seen)):
        if seen.count(l) > 1:
            raise Refused(f"layer {l} given in more than one file")
    if set(seen) - set(layers):
        raise Refused(f"layer(s) {sorted(set(seen) - set(layers))} are outside the required layer set {layers}")
    if set(layers) - set(seen):
        raise Refused(f"missing required layer(s) {sorted(set(layers) - set(seen))}")
    if len({(x["rev"], x["fp"]) for x in loaded}) != 1:
        raise Refused("files are at different registry revisions or fingerprints: "
                      + ", ".join(f"{x['layer']}=r{x['rev']}/{x['fp'][:8]}" for x in loaded))
    if len({x["db"] for x in loaded}) != 1:
        raise Refused("files carry different db_identity stamps (not one database)")
    all_assets, ref = {}, {}
    for x in loaded:
        for aid, cells in x["assets"].items():
            if aid in all_assets:
                raise Refused(f"asset {aid} appears in more than one file")
            all_assets[aid], ref[aid] = cells, (x["layer"], x["ref"])
    overlay_info = []
    for f in overlays or []:
        o = load(pathlib.Path(f), overlay=True)
        if o["layer"] not in layers or o["rev"] != loaded[0]["rev"] or o["db"] != loaded[0]["db"]:
            raise Refused(f"overlay {pathlib.Path(f).name}: layer / registry revision / database does not match the full census")
        if not o["assets"] or sorted(o["assets"]) != o["scope_assets"]:
            raise Refused(f"overlay {pathlib.Path(f).name}: its rollup assets are not exactly its declared scope")
        for aid, cells in o["assets"].items():
            if aid not in all_assets or ref[aid][0] != o["layer"]:
                raise Refused(f"overlay {pathlib.Path(f).name}: asset {aid} is not an asset of layer {o['layer']} in the full census")
            if set(cells) != set(all_assets[aid]):
                raise Refused(f"overlay {pathlib.Path(f).name}: asset {aid} has another criterion set than the full census")
            if any(aid in x["assets"] for x in overlay_info):
                raise Refused(f"asset {aid} is overlaid by more than one file")
        for aid, cells in o["assets"].items():
            all_assets[aid] = cells
        overlay_info.append(dict(file=o["ref"], layer=o["layer"], registry_fingerprint=o["fp"], base_registry_fingerprint=loaded[0]["fp"], assets=sorted(o["assets"])))
    if expected is not None and len(all_assets) != expected:
        raise Refused(f"expected {expected} assets, the files carry {len(all_assets)}")
    sets = {frozenset(c) for c in all_assets.values()}
    if len(sets) != 1 or (criteria_expected is not None and len(next(iter(sets))) != criteria_expected):
        raise Refused(f"the criterion set is not uniform across assets (or not {criteria_expected}): {sorted(len(s) for s in sets)}")
    rev = loaded[0]["rev"]
    certified, fixes, counts_only, named_blocked = [], {}, [], {}
    for aid in sorted(all_assets):
        cells = all_assets[aid]
        limits = [COUNTS_ONLY_LIMITATION] if is_counts_only_completion(cells) else []
        bad, named = [], []
        for name in sorted(cells):
            ck = cells[name]
            if ck["v"] == PASS or is_ruled_na(ck, name):
                continue
            item = named_item(aid, name, ck) if bar == BAR_N268 else None
            if item:                                         # N-268: a closed, checked, NAMED ceiling / disclosure gap: printed on the certificate, not a blocker (the cell stays PARTIAL / NO_DETECTOR in the counts)
                named.append(item)
                continue
            if ck["v"] == NA:                                # an N/A that is not a RULED one (N-233 R3: not backed by the engine's closed rule list): say why, never silently drop it
                ck = dict(ck, cause=f"{ck['cause']} [not a ruled N/A: {ruled_na_problem(name, ck)}]")
            bad.append(dict(layer=ref[aid][0], criterion=name, verdict=ck["v"], cause=ck["cause"],
                            cause_class=classify(name, ck["v"], ck.get("state") or "", ck["cause"])))
        if limits:
            counts_only.append(dict(asset=aid, layer=ref[aid][0], certified=not bad))
        if bad:
            fixes[aid] = bad
            if named:
                named_blocked[aid] = named
        else:
            certified.append(dict(asset=aid, layer=ref[aid][0], revision=rev, census=ref[aid][1],
                                  measured_pass=sum(c["v"] == PASS for c in cells.values()),
                                  ruled_na=sum(is_ruled_na(c, n) for n, c in cells.items()), date=date,
                                  ceilings=sorted({CEILING_RULES[c["rule_id"]] for n, c in cells.items() if is_ruled_na(c, n) and c.get("rule_id") in CEILING_RULES}),
                                  ruled_residuals=sorted({RULED_RESIDUALS[c["rule_id"]] for n, c in cells.items() if is_ruled_na(c, n) and c.get("rule_id") in RULED_RESIDUALS}),
                                  limitations=limits, named=named, findings=str(findings.get(aid, ""))))
    d2 = [c.get("Carr.D2") for c in all_assets.values()]
    other = {}
    for c in d2:
        if not (c and is_ruled_na(c, "Carr.D2") and c.get("rule_id") == D2_NO_PER_WITNESS):
            k = (c or {}).get("v", "missing") if not (c and is_ruled_na(c, "Carr.D2")) else "ruled N/A under another rule"
            other[k] = other.get(k, 0) + 1
    carr_d2 = dict(assets=len(d2), na_no_per_witness=len(d2) - sum(other.values()), other=dict(sorted(other.items())))
    return dict(bar=bar, bar_label=BAR_LABELS[bar], overlays=overlay_info, named_not_blocking_on_fix_list=named_blocked,
                carr_d2=carr_d2, build_completion_counts_only=dict(limitation=COUNTS_ONLY_LIMITATION, assets_of=len(all_assets), count=len(counts_only), assets=counts_only),
                registry_revision=rev, registry_fingerprint=loaded[0]["fp"], db_identity=dict(zip(("database", "system_id_sha256"), loaded[0]["db"])),
                layers=sorted(layers), date=date,
                tool=[dict(tool_commit=c, tool_dirty=dirty) for c, dirty in sorted({x["tool"] for x in loaded}, key=str)], assets=len(all_assets), certified=certified, fix_list=fixes)


def _cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\t", " ")


def tool_str(r: dict) -> str:
    return ",".join(f"{str(t['tool_commit'])[:9]}{'(dirty)' if t['tool_dirty'] else ''}" for t in r["tool"])


D2_NO_PER_WITNESS = "Carr.D2#measured:no-per-witness-values"
D3_CEILING, D1_CEILING = CEILING_RULES["Carr.D3#measured:single-derivation"], CEILING_RULES["Carr.D1#measured:transcription-not-verified"]
LDGR_CEILING = CEILING_RULES["Ldgr.source_presence#measured:unsourced-declared"]


def ceiling_counts(r: dict) -> tuple:
    """(certified at the D3 ceiling only, at the D1 ceiling only, at both): the two CARR ceilings, as before (`Carr.D2` is NOT a ceiling and never counted here; `Carr.D1#measured:not-a-transcription` is a plain
    N/A). An asset that is also at the Ldgr ceiling still counts here by its Carr ceilings; `ldgr_ceiling_count` counts the Ldgr one."""
    a = sum(1 for c in r["certified"] if D3_CEILING in c["ceilings"] and D1_CEILING not in c["ceilings"])
    b = sum(1 for c in r["certified"] if D1_CEILING in c["ceilings"] and D3_CEILING not in c["ceilings"])
    both = sum(1 for c in r["certified"] if D3_CEILING in c["ceilings"] and D1_CEILING in c["ceilings"])
    return a, b, both


def ldgr_ceiling_count(r: dict) -> int:
    """Certified assets at the Ldgr ceiling (UNSOURCED_DECLARED, N-177)."""
    return sum(1 for c in r["certified"] if LDGR_CEILING in c["ceilings"])


def ratified_count(r: dict) -> int:
    """Certified assets at the ratified-judgment ceiling (SS N-235)."""
    return sum(1 for c in r["certified"] if RATIFIED_LABEL in c["ceilings"])


def ceiling_summary(r: dict) -> str:
    a, b, both = ceiling_counts(r)
    n = sum(1 for c in r["certified"] if c["ceilings"])
    return (f"ceilings: {n} of {len(r['certified'])} certified assets are at a declared ceiling ({D3_CEILING} {a}; {D1_CEILING} {b}; both {both}; {LDGR_CEILING} {ldgr_ceiling_count(r)}; {RATIFIED_LABEL} {ratified_count(r)})")


def d2_line(r: dict) -> str:
    d = r["carr_d2"]
    if d["na_no_per_witness"] == d["assets"]:
        return "Carr.D2: N/A on every asset (no per-witness values stored, N-156)"
    return (f"Carr.D2: ruled N/A (no per-witness values stored, N-156) on {d['na_no_per_witness']} of {d['assets']} assets; "
            + ", ".join(f"{k} {v}" for k, v in sorted(d["other"].items())) + " on the rest")


def counts_only_summary(r: dict) -> str:
    c = r["build_completion_counts_only"]
    return f"Build.completion counts only (no integrity statement): {c['count']} of {c['assets_of']} assets"


def counts_only_footer(r: dict) -> list:
    """The output footer: the assets whose Build.completion PASS rests on count equality alone, each with where it sits (certified or on the fix list). Reporting only."""
    c = r["build_completion_counts_only"]
    out = ["", f"Known limitation, {c['limitation']}: {c['count']} of {c['assets_of']} assets have a Build.completion PASS that rests on count equality alone (its measured text states no "
            f"'{INTEGRITY_HOLDS}'). This is reporting only: no verdict changed."]
    out += [f"- {x['asset']} ({x['layer']}; {'CERTIFIED' if x['certified'] else 'on the FIX_LIST'})" for x in c["assets"]] or ["- (none)"]
    return out


def render_certified(r: dict) -> str:
    out = [f"# CERTIFIED_LIST", f"{r['bar_label']}; registry revision {r['registry_revision']} (fingerprint {r['registry_fingerprint'][:12]}); layers {','.join(r['layers'])}; "
           f"date {r['date']}; tool {tool_str(r)}; {len(r['certified'])} of {r['assets']} assets certified", ceiling_summary(r), d2_line(r), counts_only_summary(r), "",
           "| asset | revision | census file | measured PASS | ruled N/A | date | ceilings | known limitations | known findings |", "|---|---|---|---|---|---|---|---|---|"]
    out += [f"| {_cell(c['asset'])} | {c['revision']} | {_cell(c['census'])} | {c['measured_pass']} | {c['ruled_na']} | {c['date']} | {_cell('; '.join(c['ceilings']))} | {_cell('; '.join(c['limitations']))} | {_cell(c['findings'])} |"
            for c in r["certified"]]
    named = [c for c in r["certified"] if c.get("named")]
    if named:
        out += ["", f"## Named ceilings and disclosure gaps ({len(named)} of {len(r['certified'])} certified assets); the cells stay PARTIAL / NO_DETECTOR in the counts, only the certification verdict is the {r['bar_label']}"]
        for c in named:
            out.append(f"- {c['asset']}")
            out += [f"  - {n['criterion']} [{n['kind']}] ({n['pattern']}): {_cell(n['reason'])}" for n in c["named"]]
    if r.get("overlays"):
        out += ["", "## Overlay (scoped delta census; the listed assets' cells replace the full census cells)"]
        out += [f"- {o['file']} ({o['layer']}, registry fingerprint {o['registry_fingerprint'][:12]} vs base {o['base_registry_fingerprint'][:12]}): {', '.join(o['assets'])}" for o in r["overlays"]]
    return "\n".join(out + counts_only_footer(r)) + "\n"


def totals(r: dict) -> dict:
    """layer -> cause class -> number of fix-list items"""
    t: dict = {}
    for items in r["fix_list"].values():
        for it in items:
            t.setdefault(it["layer"], {}).setdefault(it["cause_class"], 0)
            t[it["layer"]][it["cause_class"]] += 1
    return {l: dict(sorted(c.items())) for l, c in sorted(t.items())}


def render_fix(r: dict) -> str:
    out = ["# FIX_LIST", f"{r['bar_label']}; registry revision {r['registry_revision']}; date {r['date']}; tool {tool_str(r)}; {len(r['fix_list'])} of {r['assets']} assets not certified", counts_only_summary(r), ""]
    limited = {x["asset"] for x in r["build_completion_counts_only"]["assets"]}
    for aid, items in r["fix_list"].items():
        out.append(f"## {aid} ({len(items)} open)")
        if aid in limited:
            out.append(f"- known limitation: {COUNTS_ONLY_LIMITATION}")
        for cls in CLASS_ORDER:
            sel = [i for i in items if i["cause_class"] == cls]
            if sel:
                out.append(f"- {cls}")
                out += [f"  - {i['criterion']} {i['verdict']}: {_cell(i['cause'])}" for i in sel]
        out.append("")
    return "\n".join(out + counts_only_footer(r)) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--census", nargs="+", required=True, type=pathlib.Path)
    ap.add_argument("--layers", default="L0,L1,L2")
    ap.add_argument("--assets-expected", type=int)
    ap.add_argument("--criteria-expected", type=int)
    ap.add_argument("--date", required=True)
    ap.add_argument("--findings", type=pathlib.Path)
    ap.add_argument("--out-dir", required=True, type=pathlib.Path)
    ap.add_argument("--bar", choices=sorted(BAR_LABELS), default=BAR_N268, help="certification bar: n268 (default; named ceilings and disclosure gaps) or strict (the older reading)")
    ap.add_argument("--overlay", nargs="+", type=pathlib.Path, default=[], help="scoped delta census file(s): their assets' cells replace the full census cells (recorded in the header)")
    a = ap.parse_args(argv)
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
            raise Refused("--date must be YYYY-MM-DD (it is an argument; no clock is read)")
        findings = json.loads(a.findings.read_bytes()) if a.findings else {}
        if not isinstance(findings, dict):
            raise Refused("--findings must be a JSON object asset -> text")
        res = build(a.census, a.layers.split(","), a.assets_expected, a.criteria_expected, a.date, findings, a.bar, a.overlay)
    except (Refused, OSError, ValueError, KeyError) as e:
        print(f"REFUSED: {e if isinstance(e, Refused) else type(e).__name__ + ': ' + str(e)}", file=sys.stderr)
        return 2
    res["totals_by_layer_and_class"] = totals(res)
    res["certified_at_a_ceiling"] = sum(1 for c in res["certified"] if c["ceilings"])
    head = {k: v for k, v in res.items() if k not in ("certified", "fix_list", "named_not_blocking_on_fix_list")}
    a.out_dir.mkdir(parents=True, exist_ok=True)
    dump = lambda o: json.dumps(o, indent=1, sort_keys=True) + "\n"
    (a.out_dir / "CERTIFIED_LIST.md").write_text(render_certified(res))
    (a.out_dir / "CERTIFIED_LIST.json").write_text(dump(dict(head, certified=res["certified"])))
    (a.out_dir / "FIX_LIST.md").write_text(render_fix(res))
    (a.out_dir / "FIX_LIST.json").write_text(dump(dict(head, fix_list=res["fix_list"], named_not_blocking_on_fix_list=res["named_not_blocking_on_fix_list"])))
    print(f"{res['bar_label']}; revision {res['registry_revision']}: {len(res['certified'])} of {res['assets']} CERTIFIED; {ceiling_summary(res)}; {d2_line(res)}; {counts_only_summary(res)}")
    for l, cs in res["totals_by_layer_and_class"].items():
        print(f"  {l}: " + "; ".join(f"{c} {n}" for c, n in cs.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
