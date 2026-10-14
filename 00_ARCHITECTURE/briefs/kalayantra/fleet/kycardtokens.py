#!/usr/bin/env python3
"""kycardtokens.py — measures each role card in model tokens with the real program (plan v2.7 §7:
a role card is ≤ 1.5 k tokens). A byte count is not a token count: the first B-0c cards, sized
by bytes, measured 37 % over the cap.

  kycardtokens.py measure --cards-dir DIR --out DIR/TOKEN_MEASUREMENT.json --scratch DIR
  kycardtokens.py check   --cards-dir DIR --record DIR/TOKEN_MEASUREMENT.json   (no program run)

`measure` sends each card (plus one fixed instruction line) through the plan §7 launch line in an
empty scratch directory and subtracts a baseline run that carries only the instruction line; the
difference in input tokens (fresh + cache-written + cache-read) is the card's size. A run that
fails or reports no usage makes that card "unknown", which `check` refuses — never a guessed number.
`check` passes only when every card file has a record with its current sha256 and tokens ≤ the cap.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import kyprobe  # noqa: E402

CAP = 1500
MODEL = "claude-opus-5-5"
TAIL = "\n\nReply with exactly OK and use no tool.\n"
EXCLUDE = ("COVERAGE_",)          # tables that are never sent to a job


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def cards(cards_dir):
    return sorted(n for n in os.listdir(cards_dir) if n.endswith(".md") and not n.startswith(EXCLUDE))


def one(name, text, a):
    d = os.path.join(a.scratch, name)
    os.makedirs(os.path.join(a.scratch, "empty"), exist_ok=True)
    os.makedirs(d, exist_ok=True)
    spec = {"id": name, "context": "shell", "kind": "tokens", "model_requested": a.model, "cwd": os.path.join(a.scratch, "empty"),
            "setting_sources": "project", "extra_flags": [], "nonce": None, "write_target": None,
            "argv": kyprobe.build_argv(a.claude_bin, a.model, a.mcp_config, a.add_dir, "project", (), 1),
            "prompt": text + TAIL, "prompt_path": os.path.join(d, "prompt.txt"), "stdout_path": os.path.join(d, "stdout.jsonl"),
            "stderr_path": os.path.join(d, "stderr.log"), "tmp_path": os.path.join(d, "tmp"),
            "home": os.environ.get("HOME", ""), "user": os.environ.get("USER", "")}
    rec = kyprobe.run_one(spec, a.timeout)
    ok = kyprobe.sign_in(rec) == "works"
    return name, ((rec.get("result") or {}).get("input_tokens_total") if ok else None)


def cmd_measure(a):
    version = kyprobe.claude_version(a.claude_bin)
    if version is None or version < kyprobe.MIN_VERSION:
        print("refused: %s is below the pinned version" % a.claude_bin, file=sys.stderr)
        return 70
    if os.path.exists(a.scratch):
        print("refused: scratch directory exists: " + a.scratch, file=sys.stderr)
        return 73
    names = cards(a.cards_dir)
    texts = {"__baseline__": ""}
    for n in names:
        texts[n] = open(os.path.join(a.cards_dir, n), encoding="utf-8").read()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        got = dict(pool.map(lambda kv: one(kv[0], kv[1], a), texts.items()))
    base = got["__baseline__"]
    out = {"schema": "ky.card_tokens/1", "cap": CAP, "model": a.model, "claude_version": ".".join(map(str, version)),
           "method": "input tokens of (card + fixed instruction) minus input tokens of (fixed instruction), plan §7 launch line, empty directory",
           "baseline_input_tokens": base if isinstance(base, int) else "unknown",
           "measured_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cards": {}}
    for n in names:
        p = os.path.join(a.cards_dir, n)
        tokens = got[n] - base if isinstance(got[n], int) and isinstance(base, int) and got[n] > base else "unknown"
        out["cards"][n] = {"sha256": sha(p), "bytes": os.path.getsize(p), "tokens": tokens}
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, a.out)
    print(json.dumps({n: c["tokens"] for n, c in out["cards"].items()}))
    return cmd_check(argparse.Namespace(cards_dir=a.cards_dir, record=a.out))


def problems(cards_dir, record):
    try:
        doc = json.load(open(record))
    except (OSError, ValueError):
        return ["measurement record missing or unreadable: " + record]
    out = []
    for n in cards(cards_dir):
        rec = (doc.get("cards") or {}).get(n)
        if not isinstance(rec, dict):
            out.append("%s: never measured" % n)
        elif rec.get("sha256") != sha(os.path.join(cards_dir, n)):
            out.append("%s: changed since it was measured" % n)
        elif not isinstance(rec.get("tokens"), int) or isinstance(rec.get("tokens"), bool) or rec["tokens"] < 1:
            out.append("%s: tokens unknown" % n)
        elif rec["tokens"] > CAP:
            out.append("%s: %d tokens exceeds the cap of %d" % (n, rec["tokens"], CAP))
    return out


def cmd_check(a):
    found = problems(a.cards_dir, a.record)
    for line in found:
        print("refused: " + line, file=sys.stderr)
    return 1 if found else 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    here = os.path.dirname(os.path.realpath(__file__))
    m = sub.add_parser("measure")
    m.add_argument("--cards-dir", default=os.path.join(here, "cards"))
    m.add_argument("--out", required=True)
    m.add_argument("--scratch", required=True)
    m.add_argument("--model", default=MODEL)
    m.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN", "/Users/Dev/.local/bin/claude"))
    m.add_argument("--mcp-config", default=os.path.join(here, "mcp.none.json"))
    m.add_argument("--add-dir", default=os.environ.get("KY_ROOT", "/Users/Dev/kalayantra"))
    m.add_argument("--timeout", type=int, default=240)
    m.set_defaults(fn=cmd_measure)
    c = sub.add_parser("check")
    c.add_argument("--cards-dir", default=os.path.join(here, "cards"))
    c.add_argument("--record", required=True)
    c.set_defaults(fn=cmd_check)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
