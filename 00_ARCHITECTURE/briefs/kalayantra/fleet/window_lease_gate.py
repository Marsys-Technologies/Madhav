#!/usr/bin/env python3
"""W2-M-08: the lease gate every protected-window dispatcher runs before it dispatches.

A protected window (deploy.yml `jataka-protected-migrations`, the Kāla auto-dispatcher `ops_guard/kala_window_auto.sh`) changes production. The prime rule of the shared
lease table (§1 of 00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md on origin/campaign-coordination) is that one campaign deploys or builds at a time, so a window
REFUSES while an ACTIVE, unexpired lease other than the window's own is held. Until now only the executor's production kinds checked it (executor.lease_live).

The table is read exactly as executor.lease_live reads it: refresh origin/campaign-coordination, `git show` the file, take the text between `## 1.` and `## 2.`, keep the
6-cell rows whose last cell starts with ACTIVE, read the expiry (cell 5, `YYYY-MM-DD HH:MM`, IST) and keep the rows still in the future. Anything that cannot be read
fails closed: a fetch or show that fails, a missing §1, an ACTIVE row whose expiry does not parse, an unsafe own-lease id. The parse is mirrored here rather than
imported because executor.py is a pinned file (test_executor_table.PINNED_EXECUTOR_SHA256); test_executor_window_lease_gate pins the two readings together.

Exit status: 0 = dispatch, 1 = refuse (the reason is the one line on stdout), 2 = bad usage.
"""
from __future__ import annotations
import argparse, datetime as dt, os, re, subprocess, sys

COORD_PATH = "00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"   # same constant as executor.COORD_PATH
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")                  # same constant as executor.SAFE_ID
REPO_LOCATING_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
                      "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_NAMESPACE")


def active_leases(table_text: str, now: dt.datetime | None = None) -> list[str] | None:
    """The ids of the ACTIVE, unexpired rows of §1, in table order; None when §1 or an ACTIVE row's expiry cannot be read (executor.lease_live's `return False` cases)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    section = table_text.split("## 1.", 1)
    if len(section) != 2: return None
    section = section[1].split("## 2.", 1)[0]
    active = []; ist = dt.timezone(dt.timedelta(hours=5, minutes=30))
    for line in section.splitlines():
        if not line.startswith("|"): continue
        cells = [s.strip() for s in line.strip().strip("|").split("|")]
        if len(cells) != 6: continue
        if not re.match(r"^ACTIVE(?:\s|$)", cells[5].replace("*", "").strip()): continue
        try: expiry = dt.datetime.strptime(cells[4][:16], "%Y-%m-%d %H:%M").replace(tzinfo=ist)
        except ValueError: return None
        if expiry > now: active.append(cells[0].replace("*", "").strip())
    return active


def verdict(table_text: str | None, own_lease: str = "", now: dt.datetime | None = None) -> tuple[bool, str]:
    """(dispatch?, one-line reason). `own_lease` is the lease the window itself runs under ("" when it has none, as the auto-dispatcher)."""
    if table_text is None: return False, "REFUSED: the lease table on origin/campaign-coordination cannot be read"
    if own_lease and not SAFE_ID.fullmatch(own_lease): return False, "REFUSED: the window's own lease id is not a valid lease id"
    active = active_leases(table_text, now)
    if active is None: return False, "REFUSED: the lease table's section 1 or an ACTIVE row's expiry cannot be read"
    foreign = [lease for lease in active if lease != own_lease]
    if foreign: return False, "REFUSED: a production lease other than the window's own is ACTIVE: " + ", ".join(foreign)
    if own_lease and own_lease not in active: return False, f"REFUSED: the window's own lease {own_lease} is not ACTIVE and unexpired"
    return True, "OK: no foreign production lease is ACTIVE" + (f" (own lease {own_lease})" if own_lease else "")


def read_table(repo: str) -> str | None:
    """Refresh origin/campaign-coordination and return the lease table text; None on any failure (fail closed)."""
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATING_VARS}   # an inherited GIT_DIR beats -C
    try:
        if subprocess.run(["git", "-C", repo, "fetch", "-q", "origin", "campaign-coordination"], capture_output=True, text=True, env=env, timeout=120).returncode: return None
        p = subprocess.run(["git", "-C", repo, "show", f"origin/campaign-coordination:{COORD_PATH}"], capture_output=True, text=True, env=env, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return p.stdout if p.returncode == 0 else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", required=True, help="a checkout whose origin carries the campaign-coordination branch")
    ap.add_argument("--own-lease", default="", help="the lease the window runs under; omit when it has none")
    args = ap.parse_args(argv)
    ok, why = verdict(read_table(args.repo), args.own_lease.strip())
    print(why)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
