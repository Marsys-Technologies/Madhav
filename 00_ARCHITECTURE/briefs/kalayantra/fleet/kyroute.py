#!/usr/bin/env python3
"""kyroute.py — builder-tier routing for KĀLA-YANTRA v3 (plan v2.7 §9; the FROZEN manifest of §3).

  kyroute.py packet   --packet <abs PACKET.md> --model <abs plan_model.json> --repo <abs> [--frozen <abs>]
  kyroute.py diff     --repo <abs> --base <40-hex> --head <40-hex> --built-tier sonnet|opus [--frozen <abs>]
  kyroute.py escalate --tier sonnet|opus --red-loops N --max-loops M --rejected K

`packet` routes what an item declares (the packet front matter's d1_paths and the plan-model item's brief.owns,
brief.shared, brief.migration, brief.op); `diff` routes what a head actually changed, before VERIFY. stdout is
one JSON object {"mode","decision","tier","packet_tier","computed_tier","reasons":[{"rule","path","detail"}],
"frozen":[],"head"}; `escalate` prints {"decision": "CONTINUE" | "OPUS_REWORK" | "BLOCK"}.

Exit 0 ROUTE · 1 REQUEUE_OPUS_REWORK (a Sonnet-built diff hit an Opus rule; the head is preserved for the
dispatcher to re-queue) · 3 STOP (a FROZEN path: native authorisation) · 64 usage · 66 an input, the manifest
included, is missing, unreadable or invalid · 70 internal error. No tier is printed on 3, 64, 66 or 70.

A tier comes only from a rule that ran (CLAUDE.md §N.8): an input that cannot be read is a refusal, never
"sonnet", and an item or diff that names no path at all is Opus (`no_paths`). Whatever is doubtful errs to Opus:
an entry that is not a path is prose (`prose_entry`); an owns glob that can overlap a rule matches it; a glob or
directory entry that covers a FROZEN path is STOP. A packet may raise the tier, never lower it.

Read-only: git is asked only for `cat-file -e` and `diff` (KY_GIT, an ABSOLUTE path, default /usr/bin/git), with
--no-optional-locks; nothing is checked out, reset, stashed, deleted or written. Stdlib only; no credential and
no environment listing.
"""
import argparse
import json
import os
import re
import subprocess
import sys

TIERS = ("sonnet", "opus")
DEFAULT_GIT = "/usr/bin/git"
DEFAULT_MANIFEST = os.path.join(os.path.dirname(os.path.realpath(__file__)), "FROZEN_PATHS.txt")
GIT_TIMEOUT = 300
DETAIL_MAX = 160

# Plan §9 "Opus is forced by": one row per glob of the excerpt, in its order (test_rule_table_is_the_plan_excerpt).
# `**/*ephemeris*` is any segment containing "ephemeris", case-insensitively; `migration_file` is precheck.sh's
# ^platform/(supabase/)?migrations/.*\.sql$.
_EPHEMERIS = "**/*" + "".join("[%s%s]" % (c, c.upper()) for c in "ephemeris") + "*/**"
_RULE_GLOBS = [
    ("platform/python-sidecar/{ga_writers,brahmagyan/ganita,pyjhora_adapter,panchang_engine}/**", None),
    ("platform/python-sidecar/services/{kala_core/sky,gochara_kernel}/**", None),
    ("platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py", None),
    ("**/*ephemeris*", [_EPHEMERIS]),
    ("platform/scripts/temporal/**", None),
    ("platform/scripts/migrate.ts", None),
    ("platform/migrations/**", None),
    ("platform/src/proxy.ts", None),
    ("platform/src/lib/{auth,security,share,limits,mcp}/**", None),
    ("platform/src/app/api/{auth,admin,db}/**", None),
    (".github/workflows/**", None),
    ("infra/**", None),
    ("platform/scripts/governance/**", None),
    ("00_ARCHITECTURE/briefs/kalayantra/fleet/**", None),
    ("migration_file", ["platform/migrations/**/*.sql", "platform/supabase/migrations/**/*.sql"]),
]
NONE_METADATA = (None, "", "NONE")   # brief.migration / brief.op values that are not migration metadata

# Diff content rules, by substring on added and removed lines.
_IMPORT = re.compile(r"(?<![A-Za-z])import(?![A-Za-z])|(?<![A-Za-z_])from(?![A-Za-z_])")
_EPHEMERIS_LIB = re.compile(r"swisseph|jhora", re.I)
CONTENT_RULES = [
    ("lit_state", lambda s: "'lit'" in s or '"lit"' in s),
    ("verification_pass_status", lambda s: "verification_pass_status" in s),
    ("swisseph_jhora_import", lambda s: bool(_IMPORT.search(s) and _EPHEMERIS_LIB.search(s))),
]

SHA = re.compile(r"^[0-9a-f]{40}$")
HUNK = re.compile(rb"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
PATCH_HEADERS = (b"index ", b"old mode ", b"new mode ", b"deleted file mode ", b"new file mode ", b"--- ", b"+++ ")
GIT_QUOTED = re.compile(r"[\x00-\x1f\x7f\"\\]")
MANIFEST_BANNED = re.compile(r"[\s\x00-\x1f\x7f*?\[\]{}\\]")


class Usage(Exception):
    """exit 64"""


class InputError(Exception):
    """exit 66"""


# --- globs ---------------------------------------------------------------------------------------------------

DSTAR, STAR, ANY = "**", "*", "?"   # a whole `**` segment; within a segment: any run; any one character


def expand(text):
    """Brace alternatives of a glob, as a list; an unbalanced brace is a ValueError."""
    start = text.find("{")
    if start < 0:
        if "}" in text:
            raise ValueError("unbalanced }")
        return [text]
    depth, parts, last = 0, [], start + 1
    for i in range(start, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                parts.append(text[last:i])
                return [text[:start] + q + tail for p in parts for q in expand(p) for tail in expand(text[i + 1:])]
        elif c == "," and depth == 1:
            parts.append(text[last:i])
            last = i + 1
    raise ValueError("unbalanced {")


def _segment(seg):
    if seg == "**":
        return DSTAR
    out, i = [], 0
    while i < len(seg):
        c = seg[i]
        if c == "*":
            if not out or out[-1] != STAR:
                out.append(STAR)
        elif c == "?":
            out.append(ANY)
        elif c == "[":
            end = seg.find("]", i + 2)
            if end < 0:
                raise ValueError("unclosed [")
            body = seg[i + 1:end]
            if body[0] in "!^":
                out.append(ANY)          # a negated class: any one character, which errs to a match
            else:
                chars, j = set(), 0
                while j < len(body):
                    if j + 2 < len(body) and body[j + 1] == "-":
                        lo, hi = ord(body[j]), ord(body[j + 2])
                        if hi < lo or hi - lo > 0x100:
                            raise ValueError("bad range")
                        chars.update(chr(k) for k in range(lo, hi + 1))
                        j += 3
                    else:
                        chars.add(body[j])
                        j += 1
                out.append(frozenset(chars))
            i = end
        elif c in "{}":
            raise ValueError("brace")
        else:
            out.append(frozenset(c))
        i += 1
    return tuple(out)


def pattern(glob):
    """One brace-free glob as a tuple of segments; ValueError when it cannot be parsed."""
    return tuple(_segment(s) for s in glob.split("/"))


def literal(path):
    """A path as a pattern in which every character stands for itself."""
    return tuple(tuple(frozenset(c) for c in s) for s in path.split("/"))


def _walk(a, b, wild, same):
    """Do two sequences with a run-wildcard (`wild`) share a member? `same` compares two plain elements."""
    seen, stack = set(), [(0, 0)]
    while stack:
        i, j = stack.pop()
        if (i, j) in seen:
            continue
        seen.add((i, j))
        if i == len(a) and j == len(b):
            return True
        if i < len(a) and a[i] == wild:
            stack.append((i + 1, j))
            if j < len(b):
                stack.append((i, j + 1))
        elif j < len(b) and b[j] == wild:
            stack.append((i, j + 1))
            if i < len(a):
                stack.append((i + 1, j))
        elif i < len(a) and j < len(b) and same(a[i], b[j]):
            stack.append((i + 1, j + 1))
    return False


def _chars(x, y):
    return x == ANY or y == ANY or bool(x & y)


def _segments(x, y):
    return _walk(x, y, STAR, _chars)


def overlaps(a, b):
    """True when some path matches both patterns (`**` is zero or more segments, `*` never crosses a `/`)."""
    return _walk(a, b, DSTAR, _segments)


PATH_RULES = [(name, tuple(g for src in (globs or [name]) for g in expand(src))) for name, globs in _RULE_GLOBS]
_COMPILED = [(name, [pattern(g) for g in globs]) for name, globs in PATH_RULES]


def path_rules(pats):
    return [name for name, rule_pats in _COMPILED if any(overlaps(p, r) for p in pats for r in rule_pats)]


# --- inputs --------------------------------------------------------------------------------------------------

def read_bytes(path, what):
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError as e:
        raise InputError("%s %s: %s" % (what, path, e.strerror or e))


def read_manifest(path):
    """The entries of FROZEN_PATHS.txt, or InputError: a manifest that is not whole never means "nothing is frozen"."""
    what = "frozen manifest"
    raw = read_bytes(path, what)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputError("%s %s: not UTF-8" % (what, path))
    entries = []
    for n, line in enumerate(text.split("\n"), 1):
        if line == "" or line.startswith("#"):
            continue
        where = "%s %s line %d" % (what, path, n)
        if MANIFEST_BANNED.search(line):
            raise InputError("%s: white space, a control character (CR included), a glob or a backslash" % where)
        if line.startswith("/") or any(s in ("", ".", "..") for s in line.split("/")):
            raise InputError("%s: not an exact repository-relative file path" % where)
        if line in entries:
            raise InputError("%s: duplicate entry" % where)
        entries.append(line)
    if not entries:
        raise InputError("%s %s: no entries" % (what, path))
    return entries


def _no_duplicate_keys(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("duplicate key %r" % k)
        out[k] = v
    return out


def _no_constant(name):
    raise ValueError("constant %s" % name)


def strict_json(text):
    return json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_no_constant)


def read_json(path, what):
    try:
        return strict_json(read_bytes(path, what).decode("utf-8"))
    except (ValueError, RecursionError) as e:
        raise InputError("%s %s: not strict JSON (%s)" % (what, path, e))


def read_front_matter(path):
    """The packet front matter as KV3-B-KYPACKET defines it: line 1 is ```json, up to the next line of exactly ```."""
    try:
        lines = read_bytes(path, "packet").decode("utf-8").split("\n")
    except UnicodeDecodeError:
        raise InputError("packet %s: not UTF-8" % path)
    if lines[0] != "```json" or "```" not in lines[1:]:
        raise InputError("packet %s: no front matter (first line ```json, closed by a line of ```)" % path)
    try:
        fm = strict_json("\n".join(lines[1:lines.index("```", 1)]))
    except (ValueError, RecursionError) as e:
        raise InputError("packet %s: front matter is not strict JSON (%s)" % (path, e))
    if not isinstance(fm, dict):
        raise InputError("packet %s: front matter is not one JSON object" % path)
    if not isinstance(fm.get("id"), str) or not fm["id"]:
        raise InputError("packet %s: id is not a string" % path)
    if fm.get("build_tier") not in TIERS or not isinstance(fm["build_tier"], str):
        raise InputError("packet %s: build_tier is not sonnet or opus" % path)
    return fm


def string_list(value, what):
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise InputError("%s is not a list of strings" % what)
    return value


def model_brief(path, item_id):
    """The brief of the model item with this id; None when the model has no such item."""
    doc = read_json(path, "plan model")
    if not isinstance(doc, dict) or not isinstance(doc.get("items"), list):
        raise InputError("plan model %s: no items list" % path)
    if not all(isinstance(i, dict) for i in doc["items"]):
        raise InputError("plan model %s: an item is not an object" % path)
    found = [i for i in doc["items"] if i.get("id") == item_id]
    if len(found) > 1:
        raise InputError("plan model %s: %d items with id %s" % (path, len(found), item_id))
    if not found:
        return None
    brief = found[0].get("brief")
    if brief is None:
        return {}
    if not isinstance(brief, dict):
        raise InputError("plan model %s: the brief of %s is not an object" % (path, item_id))
    return brief


# --- entries -------------------------------------------------------------------------------------------------

def normalise(entry, repo):
    """(repository-relative text, is_prose). Prose: white space, a `.`/`..`/empty segment, or absolute elsewhere."""
    text = entry
    if text.startswith("/"):
        root = repo.rstrip("/") + "/"
        if not text.startswith(root):
            return entry, True
        text = text[len(root):]
    while text.startswith("./"):
        text = text[2:]
    segs = text.split("/")
    if segs[-1] == "" and len(segs) > 1:
        segs = segs[:-1]                 # one trailing slash: a directory
    if any(c.isspace() or c == "\x00" for c in text) or any(s in ("", ".", "..") for s in segs):
        return entry, True
    return text, False


def entry_patterns(text, repo):
    """The patterns an owns/shared/d1 entry stands for, or None when it cannot be read as a path or glob."""
    is_dir = text.endswith("/")
    text = text.rstrip("/")
    try:
        pats = [pattern(g) for g in expand(text)]
    except ValueError:
        return None
    if is_dir or (pats == [literal(text)] and os.path.isdir(os.path.join(repo, text))):
        pats = [p + (DSTAR,) for p in pats]   # a directory covers everything under it
    return pats


def reason(rule, path, detail):
    return {"rule": rule, "path": path, "detail": detail}


def unique(reasons):
    out = []
    for r in reasons:
        if r not in out:
            out.append(r)
    return out


def result(mode, decision=None, packet_tier=None, computed_tier=None, reasons=(), frozen=(), head=None):
    tier = None
    if decision in ("ROUTE", "REQUEUE_OPUS_REWORK"):
        tier = "opus" if "opus" in (packet_tier, computed_tier) else "sonnet"
    return {"mode": mode, "decision": decision, "tier": tier, "packet_tier": packet_tier,
            "computed_tier": computed_tier, "reasons": list(reasons), "frozen": list(frozen), "head": head}


def decide(mode, tier_in, reasons, freezes, head=None):
    """(exit code, result) from the rules that ran; `tier_in` is the packet's build_tier or the diff's --built-tier."""
    if freezes:
        return 3, result(mode, "STOP", reasons=unique(freezes), frozen=sorted({r["path"] for r in freezes}), head=head)
    reasons = unique(reasons)
    computed = "opus" if reasons else "sonnet"
    if mode == "diff" and tier_in == "sonnet" and computed == "opus":
        return 1, result(mode, "REQUEUE_OPUS_REWORK", tier_in, computed, reasons, head=head)
    return 0, result(mode, "ROUTE", tier_in, computed, reasons, head=head)


# --- packet --------------------------------------------------------------------------------------------------

def absolute(path, name):
    if not os.path.isabs(path):
        raise Usage("%s must be an absolute path: %s" % (name, path))
    return path


def repo_dir(path):
    repo = absolute(path, "--repo").rstrip("/") or "/"
    if not os.path.isdir(repo):
        raise InputError("--repo %s: not a directory" % repo)
    return repo


def cmd_packet(args):
    for name in ("packet", "model", "frozen"):
        absolute(getattr(args, name), "--" + name)
    repo = repo_dir(args.repo)
    frozen = read_manifest(args.frozen)
    fm = read_front_matter(args.packet)
    sources = [("d1_paths", string_list(fm.get("d1_paths"), "packet %s: d1_paths" % args.packet))]
    brief = model_brief(args.model, fm["id"])
    if brief is None and not sources[0][1]:
        raise InputError("plan model %s has no item %s and the packet has no d1_paths" % (args.model, fm["id"]))
    brief = brief or {}
    for field in ("owns", "shared"):
        sources.append(("brief." + field, string_list(brief.get(field), "plan model %s: %s brief.%s" % (args.model, fm["id"], field))))

    reasons, freezes, entries = [], [], 0
    for source, values in sources:
        for entry in values:
            entries += 1
            text, prose = normalise(entry, repo)
            pats = None if prose else entry_patterns(text, repo)
            if pats is None:
                reasons.append(reason("prose_entry", entry, source))
                continue
            text = text.rstrip("/")
            freezes += [reason("freeze", f, "%s: %s" % (source, entry)) for f in frozen
                        if any(overlaps(p, literal(f)) for p in pats)]
            reasons += [reason(rule, text, source) for rule in path_rules(pats)]
    for field in ("migration", "op"):
        value = brief.get(field)
        if not any(value is n or (isinstance(value, str) and value == n) for n in NONE_METADATA):
            reasons.append(reason("migration_metadata", None, "brief.%s = %s" % (field, json.dumps(value)[:DETAIL_MAX])))
    if not entries:
        reasons.append(reason("no_paths", None, "no d1_paths, brief.owns or brief.shared entry: no path rule ran"))
    return decide("packet", fm["build_tier"], reasons, freezes)


# --- diff ----------------------------------------------------------------------------------------------------

def git(repo, *args):
    exe = os.environ.get("KY_GIT") or DEFAULT_GIT
    if not os.path.isabs(exe):
        raise Usage("KY_GIT must be an absolute path: %s" % exe)
    env = {k: v for k, v in os.environ.items()
           if k not in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                        "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE", "GIT_EXTERNAL_DIFF")}
    argv = [exe, "--no-optional-locks", "--no-pager", "-c", "core.quotePath=false", "-C", repo] + list(args)
    try:
        p = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           env=env, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise InputError("git %s: %s" % (args[0], e))
    if p.returncode != 0:
        raise InputError("git %s exited %d: %s" % (args[0], p.returncode, p.stderr.decode("utf-8", "replace").strip()[:300]))
    return p.stdout


def changed_lines(patch, paths):
    """[(path, "added"|"removed", line number, text)] from a -U0 patch whose sections follow `paths` one for one."""
    out, section, old_left, new_left, old_no, new_no = [], -1, 0, 0, 0, 0
    lines = patch.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    for line in lines:
        if old_left or new_left:
            if line.startswith(b"-") and old_left:
                out.append((paths[section], "removed", old_no, line[1:]))
                old_left, old_no = old_left - 1, old_no + 1
            elif line.startswith(b"+") and new_left:
                out.append((paths[section], "added", new_no, line[1:]))
                new_left, new_no = new_left - 1, new_no + 1
            elif line.startswith(b" ") and old_left and new_left:
                old_left, new_left, old_no, new_no = old_left - 1, new_left - 1, old_no + 1, new_no + 1
            elif not line.startswith(b"\\"):
                raise InputError("git diff: a hunk ends early")
        elif line.startswith(b"diff --git "):
            section += 1
            if section >= len(paths):
                raise InputError("git diff: more patch sections than changed paths")
            p = paths[section]
            if not GIT_QUOTED.search(p) and line.decode("utf-8", "replace") != "diff --git a/%s b/%s" % (p, p):
                raise InputError("git diff: patch section %d is not %s" % (section + 1, p))
        elif section < 0:
            raise InputError("git diff: unexpected output before the first patch section")
        elif HUNK.match(line):
            m = HUNK.match(line)
            old_no, new_no = int(m.group(1)), int(m.group(3))
            old_left = 1 if m.group(2) is None else int(m.group(2))
            new_left = 1 if m.group(4) is None else int(m.group(4))
        elif not line.startswith(PATCH_HEADERS) and not line.startswith(b"\\"):
            raise InputError("git diff: unrecognised patch line %r" % line[:80])
    if old_left or new_left:
        raise InputError("git diff: the patch is truncated")
    if section + 1 != len(paths):
        raise InputError("git diff: %d patch sections for %d changed paths" % (section + 1, len(paths)))
    return out


def cmd_diff(args):
    absolute(args.frozen, "--frozen")
    for name in ("base", "head"):
        if not SHA.match(getattr(args, name)):
            raise Usage("--%s must be 40 lower-case hex digits" % name)
    repo = repo_dir(args.repo)
    frozen = read_manifest(args.frozen)
    for name in ("base", "head"):
        git(repo, "cat-file", "-e", getattr(args, name) + "^{commit}")
    names = git(repo, "diff", "--name-only", "--no-renames", "-z", args.base, args.head)
    paths = [p.decode("utf-8", "replace") for p in names.split(b"\0") if p]

    freezes = [reason("freeze", p, "changed path") for p in paths if p in frozen]
    reasons = [reason(rule, p, "changed path") for p in paths for rule in path_rules([literal(p)])]
    if not paths:
        reasons.append(reason("no_paths", None, "the diff changes no path: no path rule ran"))
    else:
        patch = git(repo, "diff", "--no-renames", "--no-color", "--no-ext-diff", "--no-textconv", "--text", "-U0",
                    "--src-prefix=a/", "--dst-prefix=b/", args.base, args.head)
        for path, side, number, raw in changed_lines(patch, paths):
            text = raw.decode("utf-8", "replace")
            for rule, hit in CONTENT_RULES:
                if hit(text):
                    reasons.append(reason(rule, path, "%s line %d: %s" % (side, number, text.strip()[:DETAIL_MAX])))
    return decide("diff", args.built_tier, reasons, freezes, head=args.head)


# --- escalate ------------------------------------------------------------------------------------------------

def count(text, name, least=0):
    if not re.match(r"^[0-9]{1,9}$", text) or int(text) < least:
        raise Usage("%s must be an integer >= %d: %s" % (name, least, text))
    return int(text)


def cmd_escalate(args):
    red, rejected = count(args.red_loops, "--red-loops"), count(args.rejected, "--rejected")
    spent = red >= count(args.max_loops, "--max-loops", 1)
    if args.tier == "sonnet":
        decision = "OPUS_REWORK" if rejected >= 1 or spent else "CONTINUE"
    else:
        decision = "BLOCK" if rejected >= 2 or spent else "CONTINUE"
    return 0, {"decision": decision}


# --- main ----------------------------------------------------------------------------------------------------

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Usage(message)


def parser():
    ap = Parser(prog="kyroute.py", add_help=False, allow_abbrev=False)
    sub = ap.add_subparsers(dest="mode", required=True, parser_class=Parser)
    p = sub.add_parser("packet", add_help=False, allow_abbrev=False)
    p.add_argument("--packet", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--frozen", default=DEFAULT_MANIFEST)
    p.set_defaults(run=cmd_packet)
    d = sub.add_parser("diff", add_help=False, allow_abbrev=False)
    d.add_argument("--repo", required=True)
    d.add_argument("--base", required=True)
    d.add_argument("--head", required=True)
    d.add_argument("--built-tier", required=True, choices=TIERS)
    d.add_argument("--frozen", default=DEFAULT_MANIFEST)
    d.set_defaults(run=cmd_diff)
    e = sub.add_parser("escalate", add_help=False, allow_abbrev=False)
    e.add_argument("--tier", required=True, choices=TIERS)
    e.add_argument("--red-loops", required=True)
    e.add_argument("--max-loops", required=True)
    e.add_argument("--rejected", required=True)
    e.set_defaults(run=cmd_escalate)
    return ap


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    mode = argv[0] if argv and argv[0] in ("packet", "diff", "escalate") else None
    try:
        try:
            args = parser().parse_args(argv)
            code, out = args.run(args)
        except Usage as e:
            code, out, message = 64, None, "usage: %s" % e
        except InputError as e:
            code, out, message = 66, None, str(e)
    except BaseException as e:  # an internal error must never look like exit 1 (re-queue) or print a tier
        code, out, message = 70, None, "internal error: %s: %s" % (type(e).__name__, e)
    if out is None:
        sys.stderr.write("kyroute: %s\n" % message)
        out = {"decision": None} if mode == "escalate" else result(mode)
    sys.stdout.write(json.dumps(out) + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
