#!/usr/bin/env python3
"""U-M-03: the executor kinds `gochara_role_provisioning_dispatch` (--execute) and `gochara_role_provisioning_dispatch_dryrun` (--dry-run).

They dispatch ONE workflow, .github/workflows/gochara-role-provisioning-oneshot.yml (workflow_dispatch only, environment data-plane-production-cutover), at one of
three stages (the reviewed script platform/scripts/gochara-provision-roles.sh):
  create-roles       acts 1 + 2a of runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md (verifier and sealer roles with PASSWORD NULL); needs the verifier dsn_tail.
  grant-l1-reads     J-4b-a55j (SR-GRANTS-MINIMAL): SELECT on chart_facts and chart_dashas for the two principals; takes NO dsn_tail.
  sealer-credential  J-4b-a55j (SR-GRANTS-MINIMAL): the sealer password generated in the run and its DSN written straight to Secret Manager; needs the SEALER's
                     TCP-loopback dsn_tail @127.0.0.1:5432/<db> (runbook line 62: the two roles' tails differ).
The `sealer-password` stage (act 2b with a person-staged password) is not served here and is refused.

This program never reads, prints or forwards a credential: the ownership-admin secret lives in the workflow's protected environment and is read only there. It
prints non-secret facts (the lease verdict, the input names, a digest prefix of the DSN tail). Its own environment is the executor's filtered child environment; the
one `gh` call gets a further allowlist of it (no database URL, no token variable).

Lease-aware like the protected-window dispatchers (W2-M-08, fleet/window_lease_gate.py): the dispatch REFUSES unless `window_lease_id` is the ONE ACTIVE unexpired
lease on origin/campaign-coordination (a foreign ACTIVE lease, an unreadable table, or an own lease that is not ACTIVE all refuse). Under the executor the request's
own `lease_id` must be that same lease. The dry run runs every check, including the lease gate, and makes no `gh` call.

The wire form of `dsn_tail` is the executor's SAFE_ARG alphabet, which has no `?`: the query separator is written `,` and restored here (`@/db,host=/cloudsql/x:y:z`
-> `@/db?host=/cloudsql/x:y:z`). The tail must start with `@`; the alphabet has no second `@` and the tail no `pass...` word (no credentials).

Exit status: 0 = dispatched (or dry-run plan ok), 1 = refused or `gh` failed, 2 = bad usage.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from window_lease_gate import read_table, verdict, SAFE_ID   # noqa: E402  (the lease reading is shared with the protected-window dispatchers)

WORKFLOW = "gochara-role-provisioning-oneshot.yml"
STAGES = {"create-roles": True, "grant-l1-reads": False, "sealer-credential": True}      # stage -> whether the workflow input dsn_tail is needed
SEALER_TAIL = re.compile(r"^@127\.0\.0\.1:5432/[A-Za-z0-9_]+$")
CONFIRM = "PROVISION-GOCHARA-ROLES"
DSN_WIRE = re.compile(r"^@[A-Za-z0-9._/:=+-]+(,[A-Za-z0-9._/:=+-]+)?$")   # executor.SAFE_ARG minus `@` after the first (no credentials), `,` at most once
GH_ENV_ALLOW = ("HOME", "PATH", "LANG", "LC_ALL", "TZ", "TMPDIR", "USER", "LOGNAME", "XDG_CONFIG_HOME", "GH_CONFIG_DIR", "GH_HOST")


def refusal(why: str) -> tuple[None, str]:
    return None, "REFUSED: " + why


def dsn_tail(wire: str) -> tuple[str | None, str | None]:
    """(real tail, None) or (None, reason). The real tail is what the workflow input and gochara-provision-roles.sh receive."""
    if not DSN_WIRE.fullmatch(wire or ""): return None, "dsn_tail is not a plain @host/db,params string"
    if re.search(r"(?i)pass", wire): return None, "dsn_tail must carry no credential (a 'pass...' word is present)"
    return wire.replace(",", "?", 1), None


def plan(args, environ, repo: str) -> tuple[dict | None, str]:
    """(workflow inputs, one-line reason). inputs is None on refusal. Reads only git (the lease table) and KY_OPERATION_REQUEST."""
    if args.stage not in STAGES: return refusal(f"stage must be one of {', '.join(STAGES)} (sealer-password is act 2b with a staged password, not served by this kind)")
    if args.confirm != CONFIRM: return refusal(f"confirm must be exactly {CONFIRM}")
    tail = None
    if STAGES[args.stage]:
        tail, why = dsn_tail(args.dsn_tail)
        if why: return refusal(why)
        if args.stage == "sealer-credential" and not SEALER_TAIL.fullmatch(tail): return refusal("sealer-credential needs the sealer's loopback tail @127.0.0.1:5432/<db>")
    elif args.dsn_tail: return refusal(f"stage {args.stage} takes no dsn_tail")
    own = (args.window_lease_id or "").strip()
    if not own or not SAFE_ID.fullmatch(own): return refusal("window_lease_id must name the lease this window runs under")
    try: request = json.loads(environ.get("KY_OPERATION_REQUEST") or "null")
    except ValueError: request = None
    if isinstance(request, dict) and request.get("lease_id") not in (None, "") and request["lease_id"] != own:
        return refusal("window_lease_id is not the request's own lease_id")
    ok, reason = verdict(read_table(repo), own)
    if not ok: return None, reason
    return {"stage": args.stage, **({"dsn_tail": tail} if tail is not None else {}), "confirm": CONFIRM}, reason


def gh_environment(environ) -> dict:
    return {k: v for k, v in environ.items() if k in GH_ENV_ALLOW}


def main(argv: list[str] | None = None, environ=None) -> int:
    environ = os.environ if environ is None else environ
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="run every check including the lease gate; make no gh call")
    mode.add_argument("--execute", action="store_true", help="dispatch the workflow")
    ap.add_argument("--stage", default="")
    ap.add_argument("--dsn_tail", default="")
    ap.add_argument("--confirm", default="")
    ap.add_argument("--window_lease_id", default="")
    ap.add_argument("--repo", default=os.getcwd(), help="a checkout whose origin carries campaign-coordination (default: the working directory)")
    ap.add_argument("--gh", default="gh")
    args = ap.parse_args(argv)
    inputs, reason = plan(args, environ, args.repo)
    print(reason)
    if inputs is None: return 1
    shown = ", ".join(sorted(inputs)) + (f" (dsn_tail sha256 {hashlib.sha256(inputs['dsn_tail'].encode()).hexdigest()[:12]})" if "dsn_tail" in inputs else "")
    if args.dry_run:
        print(f"DRY RUN: would dispatch {WORKFLOW} on main with inputs {shown}; no gh call made")
        return 0
    cmd = [args.gh, "workflow", "run", WORKFLOW, "--ref", "main"] + [x for k, v in inputs.items() for x in ("-f", f"{k}={v}")]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=gh_environment(environ), timeout=120)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"FAILED: gh could not be run ({type(exc).__name__})")
        return 1
    if p.returncode:
        print(f"FAILED: gh workflow run exited {p.returncode}")
        return 1
    print(f"DISPATCHED: {WORKFLOW} on main with inputs {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
