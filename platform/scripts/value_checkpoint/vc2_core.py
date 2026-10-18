"""VC-2 arm generator, pure core: pins, pair selection, rendering, blinding, digest, gate.

Claims come from the sealed declaration `KSHETRA_ABLATION_PREREGISTRATION_v1_1.md` and
`preregistration.json` (NR-KALA-R12-20261006; PLAN §9 row 7). This module reads no database,
scores nothing, adjudicates nothing and holds no outcome text: events enter only as
(event_id, date) so that the selection inventory can count them (prereg §3).
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
VC_DIR = REPO / "00_ARCHITECTURE/briefs/l3_families/value_checkpoint"
DECLARATION = "KSHETRA_ABLATION_PREREGISTRATION_v1_1.md"
PROTOCOL = "preregistration.json"
OUTPUTS_REL = "00_ARCHITECTURE/briefs/l3_families/value_checkpoint/outputs"
RENDERER_VERSION = "vc2.render/1"
PRNG_ID = "sha256-counter-fisher-yates/1"
ARMS = ("A", "A_prime", "B")
LABELS = ("P", "Q", "R")
WORD_CEILING = 1200
MAX_PAIRS = 8
BINDING_FIELDS = ("G1_head_sha", "G1_code_digest", "preregistration_commit", "declaration_sha256",
                  "protocol_sha256", "baseline_receipt_sha256", "tracker_event_ref")
SECTIONS = ("SANGAM_WINDOWS", "MONTHLY_WAVEFORM", "TRAJECTORY_SEGMENTS")
# Which registered sections each arm carries (prereg §3 table / preregistration.json arms).
ARM_SECTIONS = {"A": ("SANGAM_WINDOWS",),
                "A_prime": ("SANGAM_WINDOWS", "MONTHLY_WAVEFORM"),
                "B": ("SANGAM_WINDOWS", "MONTHLY_WAVEFORM", "TRAJECTORY_SEGMENTS")}
COLUMNS = {
    "SANGAM_WINDOWS": ("window", "start", "end", "chapters", "effect", "null_verdict", "witnesses"),
    "MONTHLY_WAVEFORM": ("year", "chapters") + tuple(f"m{m:02d}" for m in range(1, 13)),
    "TRAJECTORY_SEGMENTS": ("segment", "start", "end", "chapters", "ln_rate_start", "slope_per_day",
                            "integral_days", "promise", "clock", "modifier", "suppression", "weakest_link"),
}
CHAPTER_NAMES = ("preceding", "this")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=True)


def pretty_json(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False, ensure_ascii=True) + "\n"


# --------------------------------------------------------------------------- pins

def protocol_pins(vc_dir: Path = VC_DIR) -> dict:
    """Content pins of the sealed declaration; the seed is the first 8 hex digits of the protocol hash."""
    declaration_sha = sha256_hex((vc_dir / DECLARATION).read_bytes())
    protocol_sha = sha256_hex((vc_dir / PROTOCOL).read_bytes())
    return {"declaration_sha256": declaration_sha, "protocol_sha256": protocol_sha,
            "seed": int(protocol_sha[:8], 16)}


def seal_matches(vc_dir: Path = VC_DIR) -> bool:
    """The two declaration files hash to DECLARATION_SEAL.json (VC-1's own drift detector)."""
    seal = json.loads((vc_dir / "DECLARATION_SEAL.json").read_text())
    return all(sha256_hex((vc_dir / name).read_bytes()) == digest for name, digest in seal["files"].items())


# --------------------------------------------------------------------------- selection

def pair_hash(chart_id: str, pair_index: int) -> str:
    return sha256_hex(f"{chart_id}|{pair_index}".encode("utf-8"))


def _d(value) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value)[:10])


def enumerate_pairs(chart_id: str, chapters: list, coverage: dict, events: list) -> list:
    """Every adjacent mahadasa pair whose two chapters lie inside the LEL-covered span.

    chapters: chronological dicts {ref, lord, start, end}. pair_index is the zero-based position of the
    first chapter in that sequence (immutable, chronological). Chapter bounds are half-open, so an event
    on the shared boundary belongs to the later chapter and an event on the pair's end date to the next.
    Event counts are unique event ids; outcome text never enters.
    """
    cov_start, cov_end = _d(coverage["start"]), _d(coverage["end"])
    seen = {}
    for event in events:
        seen.setdefault(str(event["event_id"]), _d(event["date"]))
    result = []
    for index in range(len(chapters) - 1):
        first, second = chapters[index], chapters[index + 1]
        start, middle, end = _d(first["start"]), _d(first["end"]), _d(second["end"])
        if middle != _d(second["start"]):
            continue  # not adjacent
        if not (cov_start <= start and end <= cov_end):
            continue
        count = sum(1 for day in seen.values() if start <= day < end)
        result.append({"pair_index": index, "first_ref": first["ref"], "second_ref": second["ref"],
                       "first_lord": first["lord"], "second_lord": second["lord"],
                       "start": start.isoformat(), "boundary": middle.isoformat(), "end": end.isoformat(),
                       "lel_event_count": count, "lel_coverage_ref": coverage["ref"],
                       "hash": pair_hash(chart_id, index)})
    return result


def ordinary_threshold(counts: list):
    """Nearest-rank lower quartile: sorted counts, one-based rank ceil(0.25 N), ties included."""
    if not counts:
        return None
    rank = (len(counts) + 3) // 4
    return sorted(counts)[rank - 1]


def select_pairs(chart_id: str, eligible: list) -> dict:
    """At most eight pairs by ascending (sha256(chart|index), index); lowest-hash ordinary reserved first."""
    threshold = ordinary_threshold([p["lel_event_count"] for p in eligible])
    ordered = sorted(eligible, key=lambda p: (p["hash"], p["pair_index"]))
    ordinary = [p for p in ordered if p["lel_event_count"] <= threshold] if threshold is not None else []
    chosen = []
    if ordinary:
        chosen.append(ordinary[0])
    for pair in ordered:
        if len(chosen) >= MAX_PAIRS:
            break
        if all(pair["pair_index"] != c["pair_index"] for c in chosen):
            chosen.append(pair)
    reserved = ordinary[0]["pair_index"] if ordinary else None
    selected = []
    for rank, pair in enumerate(chosen):
        selected.append(dict(pair, selection_rank=rank, reserved_ordinary=pair["pair_index"] == reserved,
                             ordinary=threshold is not None and pair["lel_event_count"] <= threshold))
    selected.sort(key=lambda p: p["pair_index"])
    status = "ok" if selected else "insufficient_evidence"
    return {"status": status, "eligible_count": len(eligible), "ordinary_threshold": threshold,
            "ordinary_present": bool(ordinary), "selected": selected}


# --------------------------------------------------------------------------- blinding

def _stream(seed: int, key: str):
    counter = 0
    while True:
        block = hashlib.sha256(f"{seed}|{key}|{counter}".encode()).digest()
        for offset in range(0, 32, 8):
            yield int.from_bytes(block[offset:offset + 8], "big")
        counter += 1


def permute(seed: int, key: str, items: tuple) -> list:
    """Fisher-Yates driven by a pinned SHA-256 counter stream (PRNG_ID); rejection-sampled, no bias."""
    values = list(items)
    stream = _stream(seed, key)
    limit = 1 << 64
    for position in range(len(values) - 1, 0, -1):
        n = position + 1
        bound = limit - (limit % n)
        draw = next(stream)
        while draw >= bound:
            draw = next(stream)
        swap = draw % n
        values[position], values[swap] = values[swap], values[position]
    return values


def order_map(seed: int, chart_id: str, pair_index: int) -> dict:
    """label -> arm for one pair."""
    arms = permute(seed, f"{chart_id}|{pair_index}", ARMS)
    return {label: arm for label, arm in zip(LABELS, arms)}


# --------------------------------------------------------------------------- rendering

def fmt(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format(value, ".9g")
    return str(value)


def _cell(value) -> str:
    text = fmt(value)
    return re.sub(r"\s+", "_", text) if text else "empty"


def _row(tag: str, cells) -> str:
    return "\t".join([tag] + [_cell(c) for c in cells])


def chapters_of(start: str, end: str, boundary: str) -> str:
    """Which chapter(s) of the pair a half-open [start, end) interval touches (date grain)."""
    first = _d(start) < _d(boundary)
    second = _d(end) > _d(boundary)
    return "both" if first and second else ("preceding" if first else "this")


def count_words(body: str) -> int:
    return len(body.split())


def render_body(arm: str, unit: dict) -> str:
    """The one renderer for every arm: identical scaffold, a section is data or explicit 'unavailable'."""
    if arm not in ARM_SECTIONS:
        raise ValueError("unknown arm")
    pair, data = unit["pair"], unit["data"]
    lines = [_row("PAIR", ["Q06", "preceding_vs_this"]),
             _row("CHAPTER", ["preceding", pair["first_lord"], pair["start"], pair["boundary"]]),
             _row("CHAPTER", ["this", pair["second_lord"], pair["boundary"], pair["end"]]),
             _row("CLASS", [unit["event_class"]])]
    for section in SECTIONS:
        lines.append(_row("SECTION", [section]))
        lines.append(_row("COLUMNS", COLUMNS[section]))
        if section not in ARM_SECTIONS[arm]:
            lines.append(_row("UNAVAILABLE", ["not_in_this_arm"]))
            continue
        rows = data[section]
        if not rows:
            lines.append(_row("NONE", ["none_in_span"]))
        for item in rows:
            lines.append(_row("ROW", item))
    return "\n".join(lines) + "\n"


def build_unit_data(pair: dict, sources: dict) -> dict:
    """Arm-independent, per-(pair,class) section rows from one snapshot; the arms differ only in which they show."""
    span = (_d(pair["start"]), _d(pair["end"]))
    boundary = pair["boundary"]

    windows = []
    for w in sources["sangam"]:
        if _d(w["end"]) > span[0] and _d(w["start"]) < span[1]:
            windows.append((w["window"], w["start"][:10], w["end"][:10], chapters_of(w["start"], w["end"], boundary),
                            w["effect"], w["null_verdict"], ",".join(w["witnesses"]) or "none"))
    windows.sort(key=lambda r: (r[1], r[2], r[0]))

    # One row per calendar year, one cell per month (year x month table): every month is shown, in 14 words a year
    # instead of 3 per month, so a decade-long chapter fits the word ceiling without dropping any month.
    # A month inside the span with no stored Taranga row is 'null' (honest gap); outside the span is '-'.
    by_month = {_d(m["month"]).isoformat(): m["integral"] for m in sources["taranga"]}
    mid = _d(boundary)
    months = []
    for year in range(span[0].year, (span[1] - timedelta(days=1)).year + 1):
        cells, touched = [], set()
        for month in range(1, 13):
            first = date(year, month, 1)
            after = date(year + (month == 12), month % 12 + 1, 1)
            in_first = first < mid and after > span[0]   # month overlaps the preceding chapter [start, boundary)
            in_second = after > mid and first < span[1]   # month overlaps this chapter [boundary, end)
            if in_first or in_second:
                value = by_month.get(first.isoformat())
                cells.append("null" if value is None else value)
                touched.update(n for n, hit in (("preceding", in_first), ("this", in_second)) if hit)
            else:
                cells.append("-")
        months.append((year, "both" if len(touched) == 2 else next(iter(touched)), *cells))
    months.sort()

    segments = []
    for s in sources["segments"]:
        if _d(s["end"]) > span[0] and _d(s["start"]) < span[1]:
            segments.append((s["index"], s["start"][:10], s["end"][:10], chapters_of(s["start"], s["end"], boundary),
                             s["alpha"], s["gamma"], s["integral_days"], s["promise"], s["clock"], s["modifier"],
                             s["suppression"], s["weakest_link"]))
    segments.sort(key=lambda r: (r[1], r[0]))
    return {"SANGAM_WINDOWS": windows, "MONTHLY_WAVEFORM": months, "TRAJECTORY_SEGMENTS": segments}


def build_units(selection: dict, snapshot: dict, classes: list) -> list:
    """One unit per (selected pair, intended class). Unavailable inputs are reported, never rendered quiet."""
    units = []
    for pair in selection["selected"]:
        for cls in classes:
            event_class = cls["event_class"]
            unit = {"unit_id": f"pair{pair['pair_index']:03d}__{event_class}", "pair": pair,
                    "event_class": event_class, "status": "ok", "reason": None}
            src = snapshot["sources"].get(event_class)
            if not cls.get("calibrated") or cls.get("synthetic_prior"):
                unit.update(status="not_evaluable", reason="class_prior_not_calibrated_or_unprovenanced")
            elif src is None or any(src[k] is None for k in ("sangam", "taranga", "segments")):
                missing = [k for k in ("sangam", "taranga", "segments") if src is None or src[k] is None]
                unit.update(status="not_evaluable", reason="arm_input_unavailable:" + ",".join(missing))
            else:
                unit["data"] = build_unit_data(pair, src)
            units.append(unit)
    return units


def render_unit_files(unit: dict, seed: int, chart_id: str) -> dict:
    """Arm texts, word counts and the budget decision for one unit (overflow => not_evaluable, never trimmed)."""
    if unit["status"] != "ok":
        return {"words": None, "bodies": None}
    bodies = {arm: render_body(arm, unit) for arm in ARMS}
    words = {arm: count_words(bodies[arm]) for arm in ARMS}
    over = [arm for arm in ARMS if words[arm] > WORD_CEILING]
    if over:
        unit.update(status="not_evaluable", reason="budget_overflow:" + ",".join(over))
        return {"words": words, "bodies": None}
    return {"words": words, "bodies": bodies}


# --------------------------------------------------------------------------- outputs

def generate(snapshot: dict, classes: list, pins: dict, mode: str, binding: dict = None) -> dict:
    """Pure function: snapshot (+ declared classes) -> {relative path: bytes}. Second call must equal the first."""
    chart_id = snapshot["chart_id"]
    eligible = enumerate_pairs(chart_id, snapshot["chapters"], snapshot["lel_coverage"], snapshot["events"])
    selection = select_pairs(chart_id, eligible)
    units = build_units(selection, snapshot, classes) if selection["status"] == "ok" else []
    files = {}
    order = {}
    unit_rows = []
    for unit in units:
        rendered = render_unit_files(unit, pins["seed"], chart_id)
        row = {"unit_id": unit["unit_id"], "pair_index": unit["pair"]["pair_index"], "event_class": unit["event_class"],
               "status": unit["status"], "reason": unit["reason"], "words": rendered["words"]}
        if rendered["bodies"] is not None:
            pair_index = unit["pair"]["pair_index"]
            if pair_index not in order:
                order[pair_index] = order_map(pins["seed"], chart_id, pair_index)
            row["input_rows"] = {s: len(unit["data"][s]) for s in SECTIONS}
            row["arm_files"] = {}
            row["judge_files"] = {}
            for arm in ARMS:
                text = rendered["bodies"][arm].encode("utf-8")
                path = f"arms/{unit['unit_id']}/{arm}.txt"
                files[path] = text
                row["arm_files"][arm] = sha256_hex(text)
            for label, arm in order[pair_index].items():
                packet = (f"LABEL\t{label}\n" + rendered["bodies"][arm]).encode("utf-8")
                path = f"judge_packet/{unit['unit_id']}/{label}.txt"
                files[path] = packet
                row["judge_files"][label] = sha256_hex(packet)
        unit_rows.append(row)
    if any(r["status"] == "ok" for r in unit_rows):
        files["judge_packet/RUBRIC.json"] = pretty_json(judge_rubric()).encode("utf-8")
    sealed = {f"{chart_id}|{k}": v for k, v in sorted(order.items())}
    files["sealed/order_map.json"] = pretty_json(sealed).encode("utf-8")
    manifest = {
        "schema": "ky.vc2_manifest/1", "mode": mode, "chart_id": chart_id, "generation": snapshot["generation"],
        "synthetic": bool(snapshot.get("synthetic")), "evaluation_eligible": bool(snapshot.get("evaluation_eligible")),
        "pins": pins, "binding": binding, "renderer_version": RENDERER_VERSION, "prng": PRNG_ID,
        "word_ceiling": WORD_CEILING, "arms": list(ARMS), "labels": list(LABELS),
        "source_snapshot_sha256": snapshot_hash(snapshot), "source_pins": snapshot.get("pins", {}),
        "lel_coverage": snapshot["lel_coverage"], "selection": selection_inventory(selection, eligible),
        "classes": classes, "units": unit_rows, "order_map_sha256": sha256_hex(files["sealed/order_map.json"]),
        "partial_blinding_disclosed": True, "actual_scores": None, "actual_verdict": None,
    }
    files["manifest.json"] = pretty_json(manifest).encode("utf-8")
    return files


def judge_rubric() -> dict:
    protocol = json.loads((VC_DIR / PROTOCOL).read_text())
    return {"rubric": protocol["rubric"],
            "disclosure": "Blinding is partial: arm shape and component columns reveal which information an output carries.",
            "instructions": "Score each of P, Q, R independently from the output alone. Cite output lines for nonzero scores. "
                            "Use cannot_tell where unsure; never infer what an output could have said."}


def selection_inventory(selection: dict, eligible: list) -> dict:
    return {"status": selection["status"], "eligible_count": selection["eligible_count"],
            "ordinary_threshold": selection["ordinary_threshold"], "ordinary_present": selection["ordinary_present"],
            "eligible": eligible, "selected_pair_indexes": [p["pair_index"] for p in selection["selected"]],
            "selected": selection["selected"]}


def snapshot_hash(snapshot: dict) -> str:
    """Content hash of the shared source snapshot; independent of the order a database returned rows in."""
    body = {k: v for k, v in snapshot.items() if k not in ("pins", "sources", "events")}
    body["events"] = sorted(snapshot["events"], key=canonical_json)
    body["sources"] = {cls: {key: (None if rows is None else sorted(rows, key=canonical_json))
                             for key, rows in src.items()} for cls, src in snapshot["sources"].items()}
    return sha256_hex(canonical_json(body).encode("utf-8"))


def repro_digest(files: dict) -> dict:
    listing = {path: sha256_hex(data) for path, data in sorted(files.items())}
    body = "".join(f"{path}\0{digest}\n" for path, digest in listing.items())
    return {"schema": "ky.vc2_repro_digest/1", "files": listing, "digest": sha256_hex(body.encode("utf-8"))}


# --------------------------------------------------------------------------- readiness gate

def _hex(value, length) -> bool:
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{%d}" % length, value) is not None


def git_show(commit: str, rel_path: str, repo: Path = REPO) -> bytes:
    return subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{rel_path}"], check=True,
                          capture_output=True, timeout=30).stdout


def check_readiness(*, receipt_path: Path, binding_path: Path, eligibility: dict, outputs_dir: Path,
                    vc_dir: Path = VC_DIR, show=git_show) -> list:
    """Reasons real generation is not allowed; empty list means the freeze order in prereg §2 is satisfied.

    Fail-closed: any missing or inconsistent input is a reason. The tracker read-back that the binding
    precedes VC-2 READY is the cockpit's duty (prereg §2 step 3) and is not claimed here.
    """
    reasons = []
    pins = protocol_pins(vc_dir)
    if not seal_matches(vc_dir):
        reasons.append("declaration_seal_mismatch")
    receipt = None
    try:
        raw_receipt = Path(receipt_path).read_bytes()
        receipt = json.loads(raw_receipt)
        if (receipt.get("schema") != "ky.g1_baseline/1" or not _hex(receipt.get("merged_head"), 40)
                or not _hex(receipt.get("code_digest"), 64)):
            reasons.append("g1_receipt_malformed")
            receipt = None
    except (OSError, ValueError):
        reasons.append("g1_receipt_absent_or_unreadable")
    binding = None
    try:
        binding = json.loads(Path(binding_path).read_bytes())
    except (OSError, ValueError):
        reasons.append("binding_receipt_absent_or_unreadable")
    if binding is not None:
        missing = [f for f in BINDING_FIELDS if not binding.get(f)]
        if missing:
            reasons.append("binding_fields_missing:" + ",".join(missing))
        elif not (_hex(binding["G1_head_sha"], 40) and _hex(binding["G1_code_digest"], 64)
                  and _hex(binding["preregistration_commit"], 40) and _hex(binding["declaration_sha256"], 64)
                  and _hex(binding["protocol_sha256"], 64) and _hex(binding["baseline_receipt_sha256"], 64)):
            reasons.append("binding_fields_malformed")
        else:
            if binding["declaration_sha256"] != pins["declaration_sha256"]:
                reasons.append("binding_declaration_hash_differs_from_files")
            if binding["protocol_sha256"] != pins["protocol_sha256"]:
                reasons.append("binding_protocol_hash_differs_from_files")
            if receipt is not None:
                if binding["G1_head_sha"] != receipt["merged_head"]:
                    reasons.append("binding_g1_head_differs_from_receipt")
                if binding["G1_code_digest"] != receipt["code_digest"]:
                    reasons.append("binding_g1_code_digest_differs_from_receipt")
                if binding["baseline_receipt_sha256"] != sha256_hex(raw_receipt):
                    reasons.append("binding_receipt_hash_differs_from_receipt_bytes")
            try:
                rel = vc_dir.relative_to(REPO).as_posix() if vc_dir.is_relative_to(REPO) else vc_dir.name
            except AttributeError:  # Python < 3.9 fallback; not expected
                rel = vc_dir.name
            try:
                landed_decl = sha256_hex(show(binding["preregistration_commit"], f"{rel}/{DECLARATION}"))
                landed_prot = sha256_hex(show(binding["preregistration_commit"], f"{rel}/{PROTOCOL}"))
                if landed_decl != binding["declaration_sha256"] or landed_prot != binding["protocol_sha256"]:
                    reasons.append("landed_commit_content_differs_from_binding")
            except (subprocess.SubprocessError, OSError):
                reasons.append("preregistration_commit_unreadable")
    reasons.extend(check_eligibility(eligibility))
    try:
        stray = [p for p in Path(outputs_dir).rglob("*") if p.is_file() and p.name != "README.md"]
    except OSError:
        stray = []
    if stray:
        reasons.append("preexisting_outputs_invalidate_run")
    return reasons


def check_eligibility(eligibility: dict) -> list:
    """Consent, real outcomes, eligibility, canonical scope, coverage, and six provenanced calibrated classes."""
    reasons = []
    protocol = json.loads((VC_DIR / PROTOCOL).read_text())
    if not isinstance(eligibility, dict):
        return ["eligibility_declaration_absent"]
    if eligibility.get("chart_id") not in protocol["population"]["chart_scope"]:
        reasons.append("chart_outside_canonical_scope")
    if eligibility.get("synthetic") is not False:
        reasons.append("synthetic_chart_refused")
    for key in ("evaluation_eligible", "real_outcome_records"):
        if eligibility.get(key) is not True:
            reasons.append(f"{key}_not_true")
    if not eligibility.get("consent_ref"):
        reasons.append("consent_reference_absent")
    cov = eligibility.get("lel_coverage") or {}
    if not (cov.get("ref") and cov.get("start") and cov.get("end")):
        reasons.append("lel_coverage_declaration_absent")
    classes = eligibility.get("classes") or []
    ids = [c.get("event_class") for c in classes]
    if len(classes) != 6 or len(set(ids)) != 6 or not all(ids):
        reasons.append("six_distinct_class_identities_required")
    if any(not c.get("prior_provenance") or c.get("synthetic_prior") or not c.get("calibrated") for c in classes):
        reasons.append("class_prior_provenance_absent_or_synthetic")
    return reasons
