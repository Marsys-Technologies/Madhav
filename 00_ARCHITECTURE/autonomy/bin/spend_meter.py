#!/usr/bin/env python3
"""Nirmana spend meter. Sums token usage from Claude Code transcripts for this
repo and appends one reading to state/SPEND.jsonl. See plan §18.9 / CHARTER.md.

Never estimates a cost (charter H6): cost_usd is null unless every model that
has usage in this window has a complete, non-null rate row in PRICING.json.
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

REPO_NAME = "Madhav"
PROJECTS_DIR = os.path.expanduser("~/.claude/projects")

BIN_DIR = os.path.dirname(os.path.abspath(__file__))
AUTONOMY_DIR = os.path.dirname(BIN_DIR)
STATE_DIR = os.path.join(AUTONOMY_DIR, "state")
CAMPAIGN_STATE_PATH = os.path.join(STATE_DIR, "CAMPAIGN_STATE.json")
PRICING_PATH = os.path.join(STATE_DIR, "PRICING.json")
SPEND_PATH = os.path.join(STATE_DIR, "SPEND.jsonl")

USAGE_CLASS_TO_KEY = {
    "input_tokens": "input",
    "output_tokens": "output",
    "cache_creation_input_tokens": "cache_creation",
    "cache_read_input_tokens": "cache_read",
}


def discover_transcript_files():
    """Find every session transcript for this repo, including nested
    subagent transcripts. Reports the project-directory layout found rather
    than assuming a fixed glob, per the setup instructions."""
    if not os.path.isdir(PROJECTS_DIR):
        return [], []
    project_dirs = sorted(
        d for d in glob.glob(os.path.join(PROJECTS_DIR, f"*{REPO_NAME}*"))
        if os.path.isdir(d)
    )
    files = set()
    for d in project_dirs:
        files.update(glob.glob(os.path.join(d, "*.jsonl")))
        files.update(glob.glob(os.path.join(d, "*", "subagents", "*.jsonl")))
        files.update(glob.glob(os.path.join(d, "*", "*.jsonl")))
    return sorted(files), project_dirs


def iso_to_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_file(path):
    """Return (first_timestamp, usage_records) for one transcript file.
    usage_records is a list of (model, usage_dict)."""
    first_ts = None
    records = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = rec.get("timestamp")
            if first_ts is None and ts:
                first_ts = ts
            message = rec.get("message")
            if not isinstance(message, dict):
                continue
            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue
            model = message.get("model", "unknown")
            records.append((model, usage))
    return first_ts, records


def compute_cost(by_model_totals, pricing):
    """Never estimate. Only return a number if every model present here has
    a complete rate row (all four classes, all non-null) in PRICING.json."""
    rates = (pricing or {}).get("models", {})
    total = 0.0
    for model, totals in by_model_totals.items():
        row = rates.get(model)
        if not isinstance(row, dict):
            return None
        for cls_key, tokens in totals.items():
            rate = row.get(cls_key)
            if rate is None:
                return None
            total += (tokens / 1_000_000.0) * rate
    return round(total, 4)


def main():
    if not os.path.isfile(CAMPAIGN_STATE_PATH):
        print(f"FATAL: campaign state not found at {CAMPAIGN_STATE_PATH}", file=sys.stderr)
        return 1
    try:
        campaign_state = load_json(CAMPAIGN_STATE_PATH)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FATAL: could not parse {CAMPAIGN_STATE_PATH}: {e}", file=sys.stderr)
        return 1

    window_from_raw = campaign_state.get("campaign_started_ts")
    window_from_dt = iso_to_dt(window_from_raw)

    pricing = None
    if os.path.isfile(PRICING_PATH):
        try:
            pricing = load_json(PRICING_PATH)
        except (OSError, json.JSONDecodeError) as e:
            print(f"WARNING: could not parse {PRICING_PATH}: {e}", file=sys.stderr)

    files, project_dirs = discover_transcript_files()

    print(f"Projects dir: {PROJECTS_DIR}")
    print(f"Discovered {len(project_dirs)} project director{'y' if len(project_dirs)==1 else 'ies'} matching *{REPO_NAME}*:")
    for d in project_dirs:
        print(f"  {d}")

    if not files:
        print(f"FATAL: no transcript files found under {PROJECTS_DIR} matching *{REPO_NAME}*", file=sys.stderr)
        print("Nothing written to SPEND.jsonl.", file=sys.stderr)
        return 1

    print(f"Discovered {len(files)} transcript files (top-level sessions + nested subagent transcripts).")

    by_class = {v: 0 for v in USAGE_CLASS_TO_KEY.values()}
    by_model = {}
    sessions_counted = 0
    sessions_skipped_window = 0
    read_errors = 0

    for path in files:
        try:
            first_ts, records = scan_file(path)
        except OSError as e:
            read_errors += 1
            print(f"WARNING: could not read {path}: {e}", file=sys.stderr)
            continue

        if window_from_dt is not None:
            first_dt = iso_to_dt(first_ts)
            if first_dt is None or first_dt < window_from_dt:
                sessions_skipped_window += 1
                continue

        if not records:
            continue

        sessions_counted += 1
        for model, usage in records:
            by_model.setdefault(model, {v: 0 for v in USAGE_CLASS_TO_KEY.values()})
            for cls, key in USAGE_CLASS_TO_KEY.items():
                v = usage.get(cls, 0) or 0
                by_class[key] += v
                by_model[model][key] += v

    if sessions_counted == 0 and read_errors == len(files):
        print("FATAL: every discovered transcript file failed to read.", file=sys.stderr)
        print("Nothing written to SPEND.jsonl.", file=sys.stderr)
        return 1

    totals_all_four = sum(by_class.values())
    totals_output = by_class["output"]

    cost_usd = compute_cost(by_model, pricing)
    pricing_state = "filled" if cost_usd is not None else "unfilled"

    note_bits = []
    if window_from_raw is None:
        note_bits.append("campaign_started_ts is null: counted ALL discovered sessions, no window filter applied.")
    else:
        note_bits.append(f"windowed to sessions at/after {window_from_raw} ({sessions_skipped_window} sessions excluded).")
    if read_errors:
        note_bits.append(f"{read_errors} transcript file(s) could not be read.")
    if pricing_state == "unfilled":
        note_bits.append("PRICING.json rates incomplete for one or more active models; cost_usd withheld (never estimated).")
    note = " ".join(note_bits)

    reading = {
        "ts": now_iso(),
        "window_from": window_from_raw,
        "sessions": sessions_counted,
        "by_class": by_class,
        "by_model": by_model,
        "totals": {"tokens_all": totals_all_four, "output_tokens": totals_output},
        "cost_usd": cost_usd,
        "pricing_state": pricing_state,
        "note": note,
    }

    with open(SPEND_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(reading, sort_keys=True) + "\n")

    print()
    print("=== Spend meter reading ===")
    print(f"Sessions counted: {sessions_counted} (skipped by window: {sessions_skipped_window}, read errors: {read_errors})")
    print(f"By class: {json.dumps(by_class)}")
    print(f"By model: {json.dumps(by_model, indent=2)}")
    totals_no_cache_read = by_class["input"] + by_class["output"] + by_class["cache_creation"]
    print(f"Totals: output-only={totals_output:,}  input+output+cache_creation={totals_no_cache_read:,}  all-four-classes={totals_all_four:,}")
    print(f"Cost: {cost_usd if cost_usd is not None else 'null (pricing_state=unfilled)'}")
    print(f"Note: {note}")
    print(f"Appended to {SPEND_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
