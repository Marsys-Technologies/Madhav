#!/usr/bin/env python3
"""generate_level_map.py -- Suvarna E6.3: the frozen LEVEL_MAP.json and FAMILY_ASSETS.json generators.

Both files are SNAPSHOTS taken at J1 from the asset registry; wave membership is read only from them (plan 1.2, arch
6.1, Track E brief 8). This script computes them from a registry INPUT and never reads a database.

LEVEL_MAP.json   {"version", "frozen_at", "registry_revision", "levels": {"<asset_id>": <level>}}
    level = longest-path depth in the dependency DAG of the ACTIVE assets: an asset with no dependency is level 0,
    otherwise 1 + the highest level among its dependencies. A dependency CYCLE is an error (never level 0); so is an
    active asset that depends on an id the registry does not hold as an active asset (Build.dag's own rule).
FAMILY_ASSETS.json  {"version", "frozen_at", "registry_revision", "family_gochara", "family_sangam", "family_kshetra",
    "family_readers_L3", "family_readers_L4", "family_readers_L5", "family_set"}   (family_set = union of the six)
    The six lists are INPUT (`--family-input`); this script invents no member. Every member must be an active registry
    asset; a reader list's members must sit in that layer.

Registry input: JSON list of {"asset_id", "layer", "depends_on", "active"} rows, exported read-only from the live
`asset_registry` by whoever holds the reader login (this script and its tests never connect to anything), or -- as a
NON-AUTHORITATIVE stand-in -- parsed from the repo's seed `platform/scripts/seed/asset_registry_seed.ts`
(`--registry-seed`). The seed is not production: later migrations rewrite `depends_on` and retire rows, so a map
frozen from the seed must be re-derived from the live registry before J1 (a warning says so).

    python3 generate_level_map.py --registry-json reg.json --family-input fam.json --out-dir 00_ARCHITECTURE/control
Exit: 0 written · 2 refused (LevelMapError, nothing written) · 5 script error.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

LEVEL_MAP_FILE = "LEVEL_MAP.json"
FAMILY_ASSETS_FILE = "FAMILY_ASSETS.json"
FAMILY_LIST_KEYS = ("family_gochara", "family_sangam", "family_kshetra",
                    "family_readers_L3", "family_readers_L4", "family_readers_L5")
READER_LAYER = {"family_readers_L3": "kala", "family_readers_L4": "phala", "family_readers_L5": "mimamsa"}
REGISTRY_ROW_KEYS = ("asset_id", "layer", "depends_on", "active")
_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_HERE = Path(__file__).resolve().parent


class LevelMapError(ValueError):
    """The registry or family input cannot yield a frozen map; nothing is written."""


# ───────────────────────────── registry input ─────────────────────────────

def validate_registry(rows) -> list[dict]:
    """Normalised rows [{asset_id, layer, depends_on(tuple), active}], or LevelMapError."""
    if not isinstance(rows, list) or not rows:
        raise LevelMapError("the registry input must be a non-empty JSON list of rows")
    out, seen = [], set()
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            raise LevelMapError(f"registry row {i} is not an object")
        missing = [k for k in REGISTRY_ROW_KEYS if k not in r]
        if missing:
            raise LevelMapError(f"registry row {i} lacks {missing}")
        aid, layer, deps, active = r["asset_id"], r["layer"], r["depends_on"], r["active"]
        if not (isinstance(aid, str) and _ASSET.fullmatch(aid)):
            raise LevelMapError(f"registry row {i}: bad asset_id {aid!r}")
        if aid in seen:
            raise LevelMapError(f"duplicate registry row for {aid}")
        seen.add(aid)
        if not (isinstance(layer, str) and layer.strip()):
            raise LevelMapError(f"{aid}: layer must be non-blank text")
        if not isinstance(active, bool):
            raise LevelMapError(f"{aid}: active must be a boolean, got {active!r}")
        if not isinstance(deps, (list, tuple)) or any(not (isinstance(d, str) and _ASSET.fullmatch(d)) for d in deps):
            raise LevelMapError(f"{aid}: depends_on must be a list of asset ids")
        if len(set(deps)) != len(deps):
            raise LevelMapError(f"{aid}: depends_on lists an id twice")
        out.append(dict(asset_id=aid, layer=layer, depends_on=tuple(deps), active=active))
    return out


def load_registry_json(path) -> list[dict]:
    try:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise LevelMapError(f"cannot read the registry input {path}: {type(e).__name__}: {e}") from e
    return validate_registry(rows)


# ───────────────────────────── levels ─────────────────────────────

def compute_levels(rows) -> dict[str, int]:
    """Longest-path depth of every ACTIVE asset (roots = 0). A cycle, or an active asset depending on an id that is
    not an active registry asset, raises LevelMapError. Iterative (no recursion limit); deterministic order."""
    rows = validate_registry(list(rows))
    active = {r["asset_id"]: r for r in rows if r["active"]}
    if not active:
        raise LevelMapError("the registry holds no active asset")
    all_ids = {r["asset_id"] for r in rows}
    for aid in sorted(active):
        for d in active[aid]["depends_on"]:
            if d not in active:
                why = "an inactive asset" if d in all_ids else "an id the registry does not hold"
                raise LevelMapError(f"{aid} depends on {d}, {why}: a level cannot be computed past a dangling edge")
    levels: dict[str, int] = {}
    state: dict[str, int] = {}                       # 1 = on the DFS stack, 2 = done
    for root in sorted(active):
        if root in levels:
            continue
        stack = [(root, iter(sorted(active[root]["depends_on"])))]
        state[root] = 1
        path = [root]
        while stack:
            node, it = stack[-1]
            advanced = False
            for dep in it:
                if state.get(dep) == 1:
                    cyc = path[path.index(dep):] + [dep]
                    raise LevelMapError("dependency cycle: " + " -> ".join(cyc))
                if dep not in levels:
                    state[dep] = 1
                    path.append(dep)
                    stack.append((dep, iter(sorted(active[dep]["depends_on"]))))
                    advanced = True
                    break
            if advanced:
                continue
            deps = active[node]["depends_on"]
            levels[node] = 0 if not deps else 1 + max(levels[d] for d in deps)
            state[node] = 2
            stack.pop()
            path.pop()
    return dict(sorted(levels.items()))


# ───────────────────────────── the two documents ─────────────────────────────

def _check_meta(version, frozen_at, registry_revision):
    if not (isinstance(version, str) and version.strip()):
        raise LevelMapError("version must be non-blank text")
    if not isinstance(frozen_at, str):
        raise LevelMapError("frozen_at must be an ISO-8601 timestamp with a timezone")
    try:
        ok = dt.datetime.fromisoformat(frozen_at).tzinfo is not None
    except ValueError:
        ok = False
    if not ok:
        raise LevelMapError(f"frozen_at {frozen_at!r} is not a timezone-aware ISO-8601 timestamp")
    if isinstance(registry_revision, bool) or not isinstance(registry_revision, int) or registry_revision < 1:
        raise LevelMapError(f"registry_revision must be an int >= 1, got {registry_revision!r}")


def build_level_map(rows, *, version, frozen_at, registry_revision) -> dict:
    _check_meta(version, frozen_at, registry_revision)
    return {"version": version, "frozen_at": frozen_at, "registry_revision": registry_revision,
            "levels": compute_levels(rows)}


def load_family_input(path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise LevelMapError(f"cannot read the family input {path}: {type(e).__name__}: {e}") from e
    return validate_family_input(data)


def validate_family_input(data) -> dict:
    if not isinstance(data, dict):
        raise LevelMapError("the family input must be a JSON object")
    keys = {k for k in data if not str(k).startswith("_")}          # `_`-prefixed keys are provenance notes
    if keys != set(FAMILY_LIST_KEYS):
        raise LevelMapError(f"the family input must carry exactly {list(FAMILY_LIST_KEYS)}; "
                            f"missing {sorted(set(FAMILY_LIST_KEYS) - keys)}, unexpected {sorted(keys - set(FAMILY_LIST_KEYS))}")
    out = {}
    for k in FAMILY_LIST_KEYS:
        v = data[k]
        if not isinstance(v, list) or any(not (isinstance(a, str) and _ASSET.fullmatch(a)) for a in v):
            raise LevelMapError(f"{k} must be a list of asset ids")
        if len(set(v)) != len(v):
            raise LevelMapError(f"{k} lists an asset twice")
        out[k] = sorted(v)
    return out


def build_family_assets(lists, rows, *, version, frozen_at, registry_revision) -> dict:
    _check_meta(version, frozen_at, registry_revision)
    lists = validate_family_input(lists)
    rows = validate_registry(list(rows))
    active = {r["asset_id"]: r for r in rows if r["active"]}
    for k in FAMILY_LIST_KEYS:
        for a in lists[k]:
            if a not in active:
                raise LevelMapError(f"{k}: {a} is not an active registry asset")
            want = READER_LAYER.get(k)
            if want is not None and active[a]["layer"] != want:
                raise LevelMapError(f"{k}: {a} is in layer {active[a]['layer']!r}, not {want!r}")
    doc = {"version": version, "frozen_at": frozen_at, "registry_revision": registry_revision}
    for k in FAMILY_LIST_KEYS:
        doc[k] = lists[k]
    doc["family_set"] = sorted(set().union(*[set(lists[k]) for k in FAMILY_LIST_KEYS]))
    return doc


# ───────────────────────────── the repo seed, as a stand-in registry ─────────────────────────────

def _ts_code(text: str) -> str:
    """`text` with // and /* */ comments blanked; string and template literals are kept verbatim (the splitter
    below skips their bodies when it counts brackets)."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"`":
            j = i + 1
            while j < n and text[j] != c:
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise LevelMapError("unterminated string literal in the seed")
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j < 0:
                raise LevelMapError("unterminated block comment in the seed")
            out.append(re.sub(r"[^\n]", " ", text[i:j + 2]))
            i = j + 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _ts_top_level_split(code: str, open_ch: str, close_ch: str, start: int):
    """Split the bracketed region beginning just after `start` (the index of its opening bracket) into top-level
    comma-separated items; returns (items, end_index_of_closing_bracket)."""
    items, depth, i, n, item_start = [], 0, start + 1, len(code), start + 1
    while i < n:
        c = code[i]
        if c in "'\"`":
            j = i + 1
            while j < n and code[j] != c:
                j += 2 if code[j] == "\\" else 1
            i = j + 1
            continue
        if c in "{[(":
            depth += 1
        elif c in "}])":
            if depth == 0:
                if c != close_ch:
                    raise LevelMapError(f"unbalanced {c!r} in the seed")
                tail = code[item_start:i]
                if tail.strip():
                    items.append(tail)
                return items, i
            depth -= 1
        elif c == "," and depth == 0:
            items.append(code[item_start:i])
            item_start = i + 1
        i += 1
    raise LevelMapError("unterminated bracket in the seed")


def _ts_str(raw: str, what: str) -> str:
    m = re.fullmatch(r"\s*(?:'([^'\\]*)'|\"([^\"\\]*)\")\s*", raw)
    if not m:
        raise LevelMapError(f"{what} is not a plain string literal in the seed: {raw.strip()[:60]!r}")
    return m.group(1) if m.group(1) is not None else m.group(2)


def load_registry_from_seed(path) -> list[dict]:
    """Rows [{asset_id, layer, depends_on, active}] parsed read-only from asset_registry_seed.ts's `ASSETS` literal.
    Strict: an entry whose asset_id/layer/depends_on/is_active is not a plain literal raises."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as e:
        raise LevelMapError(f"cannot read the seed {path}: {e}") from e
    code = _ts_code(text)
    m = re.search(r"export const ASSETS:\s*AssetDef\[\]\s*=\s*\[", code)
    if not m:
        raise LevelMapError("`export const ASSETS: AssetDef[] = [` not found in the seed")
    entries, _end = _ts_top_level_split(code, "[", "]", m.end() - 1)
    rows = []
    for k, ent in enumerate(entries):
        ent = ent.strip()
        if not (ent.startswith("{") and ent.endswith("}")):
            raise LevelMapError(f"seed ASSETS entry {k} is not an object literal")
        fields, _ = _ts_top_level_split(ent, "{", "}", 0)
        kv = {}
        for f in fields:
            km = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:(.*)$", f, re.S)
            if km:
                kv[km.group(1)] = km.group(2)
        for need in ("asset_id", "layer", "depends_on", "is_active"):
            if need not in kv:
                raise LevelMapError(f"seed ASSETS entry {k} has no `{need}`")
        aid = _ts_str(kv["asset_id"], f"entry {k} asset_id")
        dm = re.fullmatch(r"\s*\[(.*)\]\s*", kv["depends_on"], re.S)
        if not dm:
            raise LevelMapError(f"{aid}: depends_on is not an array literal in the seed")
        deps = [_ts_str(x, f"{aid}.depends_on") for x in _ts_top_level_split("[" + dm.group(1) + "]", "[", "]", 0)[0]]
        act = kv["is_active"].strip()
        if act not in ("true", "false"):
            raise LevelMapError(f"{aid}: is_active is not a boolean literal in the seed")
        rows.append(dict(asset_id=aid, layer=_ts_str(kv["layer"], f"{aid}.layer"), depends_on=deps, active=act == "true"))
    return validate_registry(rows)


# ───────────────────────────── CLI ─────────────────────────────

def _default_registry_revision() -> int:
    """asset_census.REGISTRY_REVISION, read as source (never imported) from this checkout."""
    src = _HERE.parent.parent / "platform" / "scripts" / "governance" / "asset_census.py"
    try:
        for st in ast.parse(src.read_text(encoding="utf-8")).body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and getattr(st.targets[0], "id", None) == "REGISTRY_REVISION":
                v = ast.literal_eval(st.value)
                if isinstance(v, int) and not isinstance(v, bool):
                    return v
    except (OSError, SyntaxError, ValueError):
        pass
    raise LevelMapError("could not read REGISTRY_REVISION from asset_census.py; pass --registry-revision")


def _write_atomic(path: Path, doc: dict):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate LEVEL_MAP.json and FAMILY_ASSETS.json (E6.3).")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--registry-json", help="[{asset_id, layer, depends_on, active}] exported read-only from asset_registry")
    src.add_argument("--registry-seed", help="NON-AUTHORITATIVE: parse asset_registry_seed.ts instead of a live export")
    ap.add_argument("--family-input", required=True, help="JSON with the six family lists (no member is invented here)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--frozen-at", default=None, help="ISO-8601 with timezone (default: now, UTC)")
    ap.add_argument("--registry-revision", type=int, default=None, help="default: asset_census.REGISTRY_REVISION")
    ap.add_argument("--force", action="store_true", help="overwrite existing files (a frozen map is otherwise refused)")
    a = ap.parse_args(argv)
    try:
        if a.registry_seed:
            rows = load_registry_from_seed(a.registry_seed)
            print("WARNING: levels derived from the repo seed, not the live registry; re-derive from a live export "
                  "before J1.", file=sys.stderr)
        else:
            rows = load_registry_json(a.registry_json)
        rev = a.registry_revision if a.registry_revision is not None else _default_registry_revision()
        frozen = a.frozen_at or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        lm = build_level_map(rows, version=a.version, frozen_at=frozen, registry_revision=rev)
        fa = build_family_assets(load_family_input(a.family_input), rows, version=a.version, frozen_at=frozen,
                                 registry_revision=rev)
        out = Path(a.out_dir)
        if not out.is_dir():
            raise LevelMapError(f"--out-dir {out} is not a directory")
        targets = {out / LEVEL_MAP_FILE: lm, out / FAMILY_ASSETS_FILE: fa}
        existing = [str(p) for p in targets if p.exists()]
        if existing and not a.force:
            raise LevelMapError(f"refusing to overwrite a frozen file: {existing} (pass --force)")
    except LevelMapError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    for p, doc in targets.items():
        _write_atomic(p, doc)
    levels = lm["levels"]
    print(json.dumps(dict(assets=len(levels), max_level=max(levels.values()), family_set=len(fa["family_set"]),
                          registry_revision=rev, frozen_at=frozen)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"generate_level_map: script error -- {exc}", file=sys.stderr)
        sys.exit(5)
