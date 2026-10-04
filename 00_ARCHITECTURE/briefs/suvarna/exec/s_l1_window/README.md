---
artifact: S_L1_WINDOW_RUNBOOK_LANDING_NOTE
version: 1.0
status: CURRENT
produced_by: runbook-pr (execution worker, Exec Suvarna)
produced_on: 2026-10-04
scope: sidecar note for the S-L1 window runbook v1.3 and its pinned window scripts. Documentation and ops only. No migration, no writer change.
changelog:
  - "1.0 (2026-10-04): first version. Lands the approved S-L1 window runbook (N-123) and the seven pinned window scripts byte-identical to the evidence copy."
---

# S-L1 window runbook v1.3 and pinned window scripts

This folder lands, byte-identical, the approved S-L1 window runbook and the production scripts it pins by hash. The window runs from the evidence copy; this copy carries the same bytes.

The runbook has its own front matter (status field `DRAFT-FOR-SS-REVIEW` inside the file). It was not edited here; approval is recorded in decision N-123, not in the runbook bytes.

## Source and pins

| file | sha256 |
|---|---|
| `S_L1_WINDOW_RUNBOOK_v1_3.md` | `042a70f339f5cdfc6efaf02ed42a30ce151fdd0ec708a7274c5f168350b7625d` |
| `scripts/with_app_db.py` | `aa47ad4a46e0b5f483c7c3fc96aaf1405b310774ba65aba822df3f19e87b1c54` |
| `scripts/image_routeB.py` | `e2c80fab33de06b670dc7241eac916cc5bd1f2d5e10839e97ed84ad2b7972207` |
| `scripts/t4_stale_prod.py` | `a904048425cd2dad944860864567d50ce50154fc5d5b6f9d3c16b1906c6df31d` |
| `scripts/wstep_checks_prod.py` | `a8638989b7a8fb0e7fb0c44c49062d9c999217987a8f90a1234f85e0694df6da` |
| `scripts/h_extract.py` | `ac0a944774eeb0697d06304d63b304b4be35e93e2c59421cba9da1aeb42eea93` |
| `scripts/rotate_reader_password.py` | `550ba889e7d3a10bfb0a0cb5bba66703f9e669f3a4c64228bf38f20de81e8d6a` |
| `scripts/admin_login_probe.py` | `c4fcfba21f1c07c4482e72c4916f717b0ab0452b0a0cfed3664acb3ea5c64489` |
| `scripts/MANIFEST.sha256` | `87dfe2ba7b9658e36ce05c6c157c85bad25b87b0932291325eb9b6249570e302` |

`scripts/MANIFEST.sha256` is the copy of the evidence manifest and lists the first six scripts only. `admin_login_probe.py` is not in that manifest; its sha256 is recorded in the table above (the manifest file was not altered).

Verify with `cd scripts && shasum -a 256 -c MANIFEST.sha256`, then compare the probe's sha256 against this note.

## Contents rule

The scripts hold names and paths only; no credential value and no birth detail. Fixture strings inside `with_app_db.py` are synthetic placeholders for a URL-rewrite self-check.
