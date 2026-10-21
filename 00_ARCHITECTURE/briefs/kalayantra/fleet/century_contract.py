#!/usr/bin/env python3
"""Generator and checker of fleet/century_contract.json, the century launch's declared facts (SR-EDGES-PROOF 2, SR-HORIZON-PUBLIC, SR-W34-LEASE).

Nothing in the contract is typed: every value is read from the source that owns it, and `--check` regenerates the file and compares it.
    horizon       start = DEFAULT_HORIZON[0] in ka_gochara_v5.py; end = the native's birth date (root CLAUDE.md §B) + 100 years. ISO 8601 UTC strings, half-open [start, end)
                  (SR-HORIZON-PUBLIC: both bounds are public, committed verbatim; SR-W34-LEASE: the carrier format is the writer's own printed form, never epoch integers)
    classes       the scored classes (gochara_rules.registry.ROW_MEMBERSHIP, the writer's SCORED_CLASSES rule) and the dispatch's `classes` selector
    policy        the contact-certification policy an unmarked (non-slice) run takes, read from the writer's own selection; the writer's config key names; final rules and
                  the in-build-verify deferral from the W3W4 pack's VERIFY_DEFERRAL.json carrier.args (SR-W3-SHAPE 3 / SR-W34-PREP-RULINGS 1) when --pack is given
    cap           the writer watchdog (migration 1395 SET writer_timeout_seconds)       timeout   the Cloud Run job task timeout (deploy.yml, the pipeline job's update step)
    image         the Cloud Run job, project, region, image repository and the writer-source digest the deployed image must carry (writer_runtime_support.get_writer_source_hash)
    + the pack-bound launch facts (generation, triggered_by, stored_scope, launch_args, output_tables, cancel_schema) that century/rebind_pins.py binds from this file.

The executor binds a century dispatch (and its dry run) to this file: the request carries `century_contract_sha256` and the executor refuses it unless it equals the sha256 of
the file's bytes at the request's reviewed_commit (executor.century_contract_problem). The sidecar import for the image digest is lazy: without the sidecar dependencies
`--write` and `--check` refuse (never skip) unless `--no-image` is given, which `--check` reports as a partial check.

    python3 century_contract.py --write --pack <W3W4 PACK dir>      regenerate the file
    python3 century_contract.py --check [--pack <PACK dir>]         exit 0 only when the committed file equals the generated one
Reads only; --write writes only the contract file. No network, no database, no git.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

FLEET = Path(__file__).resolve().parent
REPO = FLEET.parents[3]
REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json"
SCHEMA = "ky.century_contract/1"
ITEM = "J-4e"
RULINGS = ["SR-EDGES-PROOF 2", "SR-HORIZON-PUBLIC", "SR-W34-LEASE", "SR-W3-SHAPE 3", "SR-J3-CAP-LIVE"]
BIRTH_PATH = "CLAUDE.md"
HORIZON_YEARS = 100
WRITER = "platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py"
REGISTRY = "platform/python-sidecar/services/gochara_rules/registry.py"
CERTIFY = "platform/python-sidecar/services/gochara_kernel/contact_certify.py"
INPUT_VECTOR = "platform/python-sidecar/services/gochara_kernel/input_vector.py"
SHARED = "platform/scripts/v5_small_test_shared.py"
DISPATCH = "platform/scripts/dispatch_v5_century_job.py"
CANCEL = "00_ARCHITECTURE/briefs/kalayantra/fleet/century_cancel.py"
CAP_MIGRATION = "platform/migrations/1395_ka_gochara_v5_writer_timeout_72000.sql"
DEPLOY = ".github/workflows/deploy.yml"
PACK_FILE = "VERIFY_DEFERRAL.json"
SAFE = re.compile(r"[A-Za-z0-9_.-]{1,64}")


class ContractError(RuntimeError):
    """A source did not say what the contract needs: the generator refuses, it never guesses (B.10)."""


def _tree(rel: str, root: Path) -> ast.Module:
    try:
        return ast.parse((root / rel).read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise ContractError(f"cannot read {rel}: {exc}") from None


def _assign(tree: ast.Module, name: str, rel: str) -> ast.expr:
    found = [n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    found += [n.value for n in tree.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name and n.value is not None]
    if len(found) != 1:
        raise ContractError(f"{rel}: expected exactly one module-level assignment of {name}, found {len(found)}")
    return found[0]


def _literal(rel: str, name: str, root: Path):
    try:
        return ast.literal_eval(_assign(_tree(rel, root), name, rel))
    except ValueError:
        raise ContractError(f"{rel}: {name} is not a literal") from None


def _utc_datetime(node: ast.expr, what: str) -> dt.datetime:
    """`datetime(Y, M, D, tzinfo=timezone.utc)` -> that instant."""
    ok = (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "datetime" and len(node.args) == 3
          and len(node.keywords) == 1 and node.keywords[0].arg == "tzinfo" and ast.unparse(node.keywords[0].value) == "timezone.utc")
    if not ok:
        raise ContractError(f"{what} is not datetime(Y, M, D, tzinfo=timezone.utc)")
    return dt.datetime(*(ast.literal_eval(a) for a in node.args), tzinfo=dt.timezone.utc)


def horizon(root: Path) -> dict:
    node = _assign(_tree(WRITER, root), "DEFAULT_HORIZON", WRITER)
    if not (isinstance(node, ast.Tuple) and len(node.elts) == 2):
        raise ContractError("DEFAULT_HORIZON is not a two-element tuple")
    start = _utc_datetime(node.elts[0], "DEFAULT_HORIZON start")
    m = re.search(r"\bborn (\d{4})-(\d{2})-(\d{2})\b", (root / BIRTH_PATH).read_text(encoding="utf-8"))
    if not m:
        raise ContractError(f"{BIRTH_PATH}: no 'born YYYY-MM-DD' (§B Subject)")
    year, month, day = (int(x) for x in m.groups())
    try:
        end = dt.datetime(year + HORIZON_YEARS, month, day, tzinfo=dt.timezone.utc)
    except ValueError:
        raise ContractError("birth date + 100 years is not a calendar date") from None
    if not start < end:
        raise ContractError("horizon start is not before its end")
    return {"start": start.isoformat(), "end": end.isoformat(), "interval": "[start, end)",
            "start_source": f"{WRITER} DEFAULT_HORIZON[0]", "end_source": f"{BIRTH_PATH} §B birth date + {HORIZON_YEARS} years"}


def classes(root: Path, shared_args: dict) -> dict:
    membership = _literal(REGISTRY, "ROW_MEMBERSHIP", root)
    scored = sorted(c for c, k in membership.items() if k is not None)
    if not scored:
        raise ContractError("no scored class")
    return {"selector": shared_args["classes"], "scored": scored, "count": len(scored), "source": f"{REGISTRY} ROW_MEMBERSHIP (value not None)"}


def policy(root: Path, pack: Path | None) -> dict:
    """The sink policy an unmarked run takes is the `else` arm of the writer's own selection; STRICT = the raise policy (contact_certify.POLICY_RAISE)."""
    selected = [n.value for n in ast.walk(_tree(WRITER, root)) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "policy" for t in n.targets)
                and isinstance(n.value, ast.IfExp)]
    if len(selected) != 1 or not isinstance(selected[0].orelse, ast.Attribute):
        raise ContractError(f"{WRITER}: the writer's sink-policy selection (policy = A if slice else B) was not found exactly once")
    name = selected[0].orelse.attr
    sink = _literal(CERTIFY, name, root)
    final_key = re.search(r'ctx\.config\.get\("(gochara_v5_final_rules)"\)', (root / WRITER).read_text(encoding="utf-8"))
    if not final_key:
        raise ContractError(f"{WRITER}: the final-rules config key was not found")
    defer_key = _literal(WRITER, "DEFER_VERIFY_KEY", root)
    out = {"certification": {"sink_policy": sink, "strict": name == "POLICY_RAISE", "source": f"{WRITER} policy selection, unmarked arm ({name})"},
           "config_keys": {"final_rules": final_key.group(1), "defer_in_build_verify": defer_key, "result_policy": _literal(WRITER, "_RESULT_POLICY_KEY", root)},
           "final_rules": None, "defer_in_build_verify": None, "result_policy": None, "source": None}
    if pack is not None:
        body = (pack / PACK_FILE).read_bytes()
        args = (json.loads(body).get("carrier") or {}).get("args") or {}
        for key in ("final_rules", "defer_in_build_verify"):
            if args.get(key) not in ("true", "false"):
                raise ContractError(f"{PACK_FILE} carrier.args.{key} is not 'true' or 'false'")
            out[key] = args[key] == "true"
        if args.get("result_policy") not in _literal(SHARED, "CENTURY_RESULT_POLICIES", root):
            raise ContractError(f"{PACK_FILE} carrier.args.result_policy is not one of the named result policies")
        out["result_policy"] = args["result_policy"]
        out["source"] = {"file": PACK_FILE, "sha256": hashlib.sha256(body).hexdigest(), "ruling": "SR-W3-SHAPE 3; SR-W34-PREP-RULINGS 1"}
    return out


def cap(root: Path) -> dict:
    text = (root / CAP_MIGRATION).read_text(encoding="utf-8")
    values = re.findall(r"^\s*SET writer_timeout_seconds\s*=\s*(\d+)\s*$", text, re.M)
    if len(values) != 1:
        raise ContractError(f"{CAP_MIGRATION}: expected exactly one 'SET writer_timeout_seconds = N'")
    return {"writer_timeout_seconds": int(values[0]), "source": CAP_MIGRATION}


def task_timeout(root: Path) -> dict:
    lines = (root / DEPLOY).read_text(encoding="utf-8").splitlines()
    found = []
    for i, line in enumerate(lines):
        if "gcloud run jobs update brahma-build-pipeline-job" in line:
            for j in range(i, min(i + 14, len(lines))):
                m = re.match(r"\s*--task-timeout=(\d+)\b", lines[j])
                if m:
                    found.append((int(m.group(1)), j + 1))
                    break
    if len(found) != 1:
        raise ContractError(f"{DEPLOY}: expected exactly one task timeout on the brahma-build-pipeline-job update step, found {len(found)}")
    return {"cloud_run_task_timeout_seconds": found[0][0], "source": f"{DEPLOY}:{found[0][1]}"}


def image(root: Path, with_digest: bool) -> dict:
    out = {k.lower(): _literal(DISPATCH, k, root) for k in ("LAUNCH_JOB", "LAUNCH_PROJECT", "LAUNCH_REGION")}
    out = {"job": out["launch_job"], "project": out["launch_project"], "region": out["launch_region"]}
    m = re.search(r"--image=(\S+brahma-pipeline):\$\{\{ env\.DEPLOY_SHA \}\}", (root / DEPLOY).read_text(encoding="utf-8"))
    if not m:
        raise ContractError(f"{DEPLOY}: the pipeline job's --image=<repository>:${{{{ env.DEPLOY_SHA }}}} was not found")
    out["repository"] = m.group(1)
    out["writer_source_digest"] = writer_source_digest(root) if with_digest else None
    out["digest_source"] = "pipeline.orchestrator.writer_runtime_support.get_writer_source_hash('ka_gochara_v5')"
    return out


def writer_source_digest(root: Path) -> str:
    sidecar = str(root / "platform/python-sidecar")
    sys.path.insert(0, sidecar)
    try:
        from pipeline.orchestrator.writer_runtime_support import get_writer_source_hash
        return get_writer_source_hash("ka_gochara_v5")
    except Exception as exc:     # a missing dependency is a refusal, never a skipped check
        raise ContractError(f"the writer-source digest needs the sidecar dependencies ({type(exc).__name__}); use --no-image for a partial check") from None
    finally:
        sys.path.remove(sidecar)


def _create_columns(text: str, table: str) -> set[str]:
    cols: set[str] = set()
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(?:public\.)?" + re.escape(table) + r"\s*\(", text):
        depth, j = 1, m.end()
        while depth and j < len(text):
            depth += (text[j] == "(") - (text[j] == ")")
            j += 1
        body = re.sub(r"--[^\n]*", "", text[m.end():j - 1])
        parts, depth, cur = [], 0, ""
        for c in body:
            depth += (c == "(") - (c == ")")
            if c == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += c
        parts.append(cur)
        for part in parts:
            words = part.split()
            if words and words[0].upper() not in ("CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "EXCLUDE", "LIKE") and re.fullmatch(r"[a-z_][a-z0-9_]*", words[0]):
                cols.add(words[0])
    for m in re.finditer(r"ALTER TABLE (?:ONLY )?(?:IF EXISTS )?(?:public\.)?" + re.escape(table) + r"\b(.*?);", text, re.S):
        cols.update(a.group(1) for a in re.finditer(r"ADD COLUMN (?:IF NOT EXISTS )?([a-z_][a-z0-9_]*)", re.sub(r"--[^\n]*", "", m.group(1))))
    return cols


def output_tables(root: Path, shared) -> list[dict]:
    """Every generation-scoped table the century run fills for (chart_id, generation): the shared module's ABSENCE_TABLES (output + near-miss), each proven by its CREATE TABLE
    migration to carry chart_id and generation. class_column: `event_class` when the table has it; the coverage table partitions its class rows by partition_kind = 'event_class'
    in partition_key (its WHERE is recorded)."""
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in sorted((root / "platform/migrations").glob("*.sql")))
    out = []
    for table, extra in shared.ABSENCE_TABLES:
        cols = _create_columns(text, table)
        if not {"chart_id", "generation"} <= cols:
            raise ContractError(f"{table}: no migration creates it with chart_id and generation columns")
        where = re.sub(r"^\s*AND\s+", "", extra).strip() or None
        column = "event_class" if "event_class" in cols else None
        if where and where.replace(" ", "") == "partition_kind='event_class'":
            column = "partition_key" if "partition_key" in cols else None
        out.append({"object": table, "table": "public." + table, "class_column": column, "where": where})
    return out


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def launch_args(shared, pol: dict, hz: dict) -> dict:
    """The request's exact five `args` (F-CHANNEL, SR-W34-PREP-RULINGS 1, OD-1; shared.CENTURY_ARG_KEYS): `classes` all, the two policy booleans as 'true'/'false', the horizon as
    '<start>,<end>' (the committed horizon, verbatim: SR-HORIZON-PUBLIC) and the numeric-result policy. The three policy values are pack-sourced and stay null without --pack. (I) INTERPRETATION: the launch
    args are derived from the facts the contract already commits, so a request that differs from them in any value is refused by `century_contract_problem`."""
    if set(shared.CENTURY_ARG_KEYS) != {"classes", "final_rules", "defer_in_build_verify", "horizon", "result_policy"}:
        raise ContractError("the century request's argument keys changed; the contract's launch_args generator must be reviewed")
    flag = lambda value: None if value is None else ("true" if value else "false")
    return {"classes": "all", "final_rules": flag(pol["final_rules"]), "defer_in_build_verify": flag(pol["defer_in_build_verify"]), "horizon": f"{hz['start']},{hz['end']}",
            "result_policy": pol["result_policy"]}


def derive(root: Path = REPO, pack: Path | None = None, with_digest: bool = True) -> dict:
    root = Path(root)
    shared = _load(root / SHARED, "century_contract_shared")
    pol, hz = policy(root, pack), horizon(root)
    args = launch_args(shared, pol, hz)
    contract = {
        "schema": SCHEMA, "item": shared.CENTURY_ITEM, "rulings": RULINGS,
        "generation": shared.GENERATION, "triggered_by": shared.CENTURY_TRIGGERED_BY,
        "stored_scope": _literal(INPUT_VECTOR, "STORED_SCOPE", root),
        "launch_args": args, "cancel_schema": _literal(CANCEL, "SCHEMA", root),
        "horizon": hz, "classes": classes(root, args), "policy": pol,
        "cap": cap(root), "timeout": task_timeout(root), "image": image(root, with_digest),
        "output_tables": output_tables(root, shared),
    }
    for key in ("generation", "triggered_by", "stored_scope"):
        if not SAFE.fullmatch(contract[key]):
            raise ContractError(f"{key} is not a safe literal")
    if contract["item"] != ITEM:
        raise ContractError("the century item changed")
    check_cap_below_timeout(contract["cap"], contract["timeout"])
    return contract


def check_cap_below_timeout(cap_: dict, timeout_: dict) -> None:
    if cap_["writer_timeout_seconds"] >= timeout_["cloud_run_task_timeout_seconds"]:
        raise ContractError("the writer cap is not below the Cloud Run task timeout: the watchdog could never fire first")


def render(contract: dict) -> bytes:
    return (json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def compare(committed: dict, derived: dict, *, with_digest: bool, with_pack: bool) -> list[str]:
    """Why `committed` is not what the sources give. Without --pack the pack-sourced policy values are only type-checked; with --no-image the digest is not compared."""
    want = json.loads(json.dumps(derived))
    have = json.loads(json.dumps(committed))
    if not with_digest:
        want["image"]["writer_source_digest"] = have.get("image", {}).get("writer_source_digest")
    if not with_pack:
        for key in ("final_rules", "defer_in_build_verify", "result_policy", "source"):
            want["policy"][key] = have.get("policy", {}).get(key)
        if have.get("launch_args", {}).get("result_policy") not in _literal(SHARED, "CENTURY_RESULT_POLICIES", REPO):
            return ["launch_args.result_policy is not a named result policy"]
        want["launch_args"]["result_policy"] = have["launch_args"]["result_policy"]
        for key in ("final_rules", "defer_in_build_verify"):
            if not isinstance(have.get("policy", {}).get(key), bool):
                return [f"policy.{key} is not a boolean"]
            if have.get("launch_args", {}).get(key) not in ("true", "false"):
                return [f"launch_args.{key} is not 'true' or 'false'"]
            want["launch_args"][key] = have["launch_args"][key]
    return [k for k in sorted(set(want) | set(have)) if want.get(k) != have.get(k)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--pack", type=Path, default=None)
    ap.add_argument("--no-image", action="store_true")
    ap.add_argument("--root", type=Path, default=REPO)
    a = ap.parse_args(argv)
    path = a.root / REL
    try:
        if a.write:
            if a.pack is None or a.no_image:
                raise ContractError("--write needs --pack and the image digest: a contract with a null fact is not written")
            body = render(derive(a.root, a.pack, True))
            path.write_bytes(body)
            print(json.dumps({"written": REL, "sha256": sha256(body)}, sort_keys=True))
            return 0
        derived = derive(a.root, a.pack, not a.no_image)
        differing = compare(json.loads(path.read_text(encoding="utf-8")), derived, with_digest=not a.no_image, with_pack=a.pack is not None)
        print(json.dumps({"check": REL, "sha256": sha256(path.read_bytes()), "equal": not differing, "differs_in": differing,
                          "partial": bool(a.no_image or a.pack is None)}, sort_keys=True))
        return 0 if not differing else 1
    except (ContractError, OSError, ValueError) as exc:
        print(f"century_contract: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
